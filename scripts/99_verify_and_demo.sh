#!/usr/bin/env bash
# 99_verify_and_demo.sh - Automated CO1-CO5 Infrastructure Audit with [PASS]/[FAIL] summary.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

PASS_COUNT=0
FAIL_COUNT=0

record_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '%b[PASS]%b %s\n' "${C_GREEN}" "${C_RESET}" "$1"
}

record_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '%b[FAIL]%b %s\n' "${C_RED}" "${C_RESET}" "$1"
}

check_cmd() {
    local label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        record_pass "${label}"
    else
        record_fail "${label}"
    fi
}

log_step "DevCompany Infrastructure Verification Audit (CO1 - CO5)"

# 1. Required Tools & Services (CO1, CO2)
for tool in git gcc g++ python3 node npm htop sar setfacl lvcreate tree ufw cron sshd; do
    check_cmd "Package/Tool installed: ${tool}" command -v "${tool}"
done

if has_systemd; then
    check_cmd "Service active: cron" systemctl is-active --quiet cron
    check_cmd "Service active: ssh" systemctl is-active --quiet ssh
    check_cmd "Service enabled: devcompany-lvm-loop" systemctl is-enabled --quiet devcompany-lvm-loop.service
else
    check_cmd "Process running: cron" pgrep -x cron
    check_cmd "Process running: sshd" pgrep -x sshd
fi

# 2. LVM Loopback Storage & Mounts (CO2, CO5)
check_cmd "Loop image exists: ${LVM_DISK_DIR}/disk1.img" test -f "${LVM_DISK_DIR}/disk1.img"
check_cmd "Loop image exists: ${LVM_DISK_DIR}/disk2.img" test -f "${LVM_DISK_DIR}/disk2.img"
check_cmd "Volume Group active: ${LVM_VG}" vgs "${LVM_VG}"

for lv_spec in "lv_repos:${REPO_ROOT}" "lv_backups:${BACKUP_ROOT}" "lv_logs:${LOG_ROOT}"; do
    lv_name="${lv_spec%%:*}"
    mnt="${lv_spec##*:}"
    check_cmd "LV exists: ${lv_name}" lvs "${LVM_VG}/${lv_name}"
    check_cmd "Mounted: ${mnt}" findmnt -M "${mnt}"
    check_cmd "UUID in /etc/fstab for ${mnt}" grep -qE "UUID=.*${mnt}.*# devcompany-lvm" /etc/fstab
done

# 3. Users, Groups, SSH Keys & Sudoers (CO3, CO4)
for grp in developers frontend backend devops techleads; do
    check_cmd "Group exists: ${grp}" getent group "${grp}"
done

dev_ok=0
ssh_ok=0
auth_ok=0
chage_ok=0
for i in $(seq 1 40); do
    u="$(printf 'dev%02d' "${i}")"
    if id "${u}" >/dev/null 2>&1; then
        dev_ok=$((dev_ok + 1))
    fi
    home_dir="$(getent passwd "${u}" 2>/dev/null | cut -d: -f6 || true)"
    if [[ -n "${home_dir}" && -f "${home_dir}/.ssh/id_ed25519" && -f "${home_dir}/.ssh/id_ed25519.pub" ]]; then
        ssh_ok=$((ssh_ok + 1))
    fi
    if [[ -n "${home_dir}" && -f "${home_dir}/.ssh/authorized_keys" ]]; then
        auth_ok=$((auth_ok + 1))
    fi
    if LC_ALL=C chage -l "${u}" 2>/dev/null | grep -q "Maximum number of days between password change.*: 90"; then
        chage_ok=$((chage_ok + 1))
    fi
done

if [[ "${dev_ok}" -eq 40 ]]; then
    record_pass "All 40 developer accounts provisioned (dev01..dev40)"
else
    record_fail "Expected 40 developer accounts, found ${dev_ok}"
fi

if [[ "${ssh_ok}" -eq 40 ]]; then
    record_pass "All 40 developers have Ed25519 SSH key pairs"
else
    record_fail "Expected 40 SSH key pairs, found ${ssh_ok}"
fi

if [[ "${auth_ok}" -eq 40 ]]; then
    record_pass "All 40 developers have SSH authorized_keys configured"
else
    record_fail "Expected 40 authorized_keys files, found ${auth_ok}"
fi

if [[ "${chage_ok}" -eq 40 ]]; then
    record_pass "All 40 developers enforce 90-day password aging (chage)"
else
    record_fail "Expected 40 users with 90-day aging, found ${chage_ok}"
fi

check_cmd "Sudoers policy syntax valid (${SUDOERS_FILE})" visudo -cf "${SUDOERS_FILE}"
if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    if LC_ALL=C sudo -l -U dev01 2>&1 | grep -q "not allowed to run sudo"; then
        record_pass "Least privilege: junior dev01 has zero sudo privileges"
    else
        record_fail "Least privilege breach: dev01 appears to have sudo access"
    fi
    if LC_ALL=C sudo -l -U dev35 2>&1 | grep -q "devcompany-dashboard"; then
        record_pass "RBAC: techlead dev35 granted scoped service controls"
    else
        record_fail "RBAC missing scoped sudo rules for techlead dev35"
    fi
fi

# 4. Shared Repos, SGID, Sticky Bit & POSIX ACLs (CO3, CO4)
for pair in "frontend:web-portal.git" "backend:core-api.git" "devops:infra-automation.git" "shared:company-docs.git"; do
    subdir="${pair%%:*}"
    repo="${pair##*:}"
    dir_path="${REPO_ROOT}/${subdir}"
    repo_path="${dir_path}/${repo}"
    perms="$(stat -c '%a' "${dir_path}" 2>/dev/null || echo '000')"
    if [[ "${perms}" == "3775" ]]; then
        record_pass "Permissions 3775 (SGID+Sticky) verified on ${dir_path}"
    else
        record_fail "Expected mode 3775 on ${dir_path}, got ${perms}"
    fi
    check_cmd "Bare Git repo valid: ${repo_path}" git -C "${repo_path}" rev-parse --verify HEAD
    if getfacl -p "${dir_path}" 2>/dev/null | grep -q "group:techleads:rwx" && \
       getfacl -p "${dir_path}" 2>/dev/null | grep -q "default:group:techleads:rwx"; then
        record_pass "ACL oversight (techleads:rwx + default ACL) verified on ${dir_path}"
    else
        record_fail "Missing techleads POSIX ACL on ${dir_path}"
    fi
done

# 5. Cron, Telemetry, Backups & Dashboard (CO4, CO5)
check_cmd "Cron configuration exists: ${CRON_FILE}" test -f "${CRON_FILE}"
check_cmd "Health metrics JSON valid" python3 -m json.tool "${LOG_ROOT}/health_metrics.json"

latest_backup="$(ls -1t "${BACKUP_ROOT}"/repos_backup_*.tar.gz 2>/dev/null | head -n1 || true)"
if [[ -n "${latest_backup}" && -f "${latest_backup}.sha256" ]]; then
    if (cd "${BACKUP_ROOT}" && sha256sum -c "$(basename "${latest_backup}").sha256" >/dev/null 2>&1); then
        record_pass "Backup archive & SHA-256 integrity verified: $(basename "${latest_backup}")"
    else
        record_fail "Backup SHA-256 verification failed for ${latest_backup}"
    fi
else
    record_fail "No verified backup archive found in ${BACKUP_ROOT}"
fi

if curl -sf http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
    record_pass "Web Admin Dashboard responding at http://127.0.0.1:8080/api/health"
else
    record_fail "Web Admin Dashboard not reachable at http://127.0.0.1:8080/api/health"
fi

printf '\n%b==================== AUDIT SUMMARY ====================%b\n' "${C_CYAN}" "${C_RESET}"
printf 'Total Checks Passed: %b%d%b\n' "${C_GREEN}" "${PASS_COUNT}" "${C_RESET}"
printf 'Total Checks Failed: %b%d%b\n' "${C_RED}" "${FAIL_COUNT}" "${C_RESET}"
printf '%b=======================================================%b\n' "${C_CYAN}" "${C_RESET}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    exit 1
fi
exit 0
