#!/usr/bin/env bash
# 00_teardown.sh - Cleanly removes provisioned users, groups, LVM volumes, loop devices, cron, and dashboard service.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root

AUTO_CONFIRM=0
if [[ "${1:-}" == "--yes" || "${1:-}" == "-y" ]]; then
    AUTO_CONFIRM=1
fi

log_step "DevCompany Infrastructure Teardown & Clean Reset"
if [[ "${AUTO_CONFIRM}" -ne 1 ]]; then
    read -r -p "This will delete dev01..dev40, vg_devcompany LVM volumes, repos, backups, and cron jobs. Continue? [y/N] " reply
    if [[ ! "${reply}" =~ ^[Yy]$ ]]; then
        log_warn "Teardown cancelled."
        exit 0
    fi
fi

# 1. Stop dashboard & systemd services
if has_systemd; then
    systemctl stop devcompany-dashboard.service >/dev/null 2>&1 || true
    systemctl disable devcompany-dashboard.service >/dev/null 2>&1 || true
    systemctl stop devcompany-lvm-loop.service >/dev/null 2>&1 || true
    systemctl disable devcompany-lvm-loop.service >/dev/null 2>&1 || true
    rm -f /etc/systemd/system/devcompany-dashboard.service /etc/systemd/system/devcompany-lvm-loop.service
    systemctl daemon-reload >/dev/null 2>&1 || true
fi
pkill -f "uvicorn app:app --host 0.0.0.0 --port 8080" >/dev/null 2>&1 || true
rm -f /usr/local/sbin/devcompany-attach-lvm.sh

# 2. Remove cron and sudoers configs
rm -f "${CRON_FILE}" "${SUDOERS_FILE}"
log_ok "Removed cron and sudoers policy files."

# 3. Unmount LVM volumes and clean /etc/fstab
for mnt in "${REPO_ROOT}" "${BACKUP_ROOT}" "${LOG_ROOT}"; do
    if findmnt -M "${mnt}" >/dev/null 2>&1; then
        umount -l "${mnt}" || umount -f "${mnt}" || true
        log_ok "Unmounted ${mnt}"
    fi
done

if [[ -f /etc/fstab ]]; then
    tmp_fstab="$(mktemp)"
    grep -v '# devcompany-lvm' /etc/fstab > "${tmp_fstab}" || true
    cat "${tmp_fstab}" > /etc/fstab
    rm -f "${tmp_fstab}"
    log_ok "Cleaned DevCompany entries from /etc/fstab"
fi

# 4. Remove LVM Logical Volumes, Volume Group, Physical Volumes, and Loopback Devices
if vgs "${LVM_VG}" >/dev/null 2>&1; then
    vgchange -an "${LVM_VG}" >/dev/null 2>&1 || true
    lvremove -y "${LVM_VG}" >/dev/null 2>&1 || true
    vgremove -y "${LVM_VG}" >/dev/null 2>&1 || true
    log_ok "Removed LVM Volume Group ${LVM_VG} and its Logical Volumes."
fi

if [[ -d "${LVM_DISK_DIR}" ]]; then
    shopt -s nullglob
    for img in "${LVM_DISK_DIR}"/disk*.img; do
        for loop_dev in $(losetup -j "${img}" -O NAME --noheadings 2>/dev/null || true); do
            pvremove -y -ff "${loop_dev}" >/dev/null 2>&1 || true
            losetup -d "${loop_dev}" >/dev/null 2>&1 || true
            log_ok "Detached loop device ${loop_dev} (${img})"
        done
    done
    shopt -u nullglob
fi

# 5. Remove developer accounts and groups
for i in $(seq 1 40); do
    u="$(printf 'dev%02d' "${i}")"
    if id "${u}" >/dev/null 2>&1; then
        userdel -r -f "${u}" >/dev/null 2>&1 || true
    fi
done
log_ok "Removed developer accounts dev01..dev40."

for grp in frontend backend devops techleads developers; do
    if getent group "${grp}" >/dev/null 2>&1; then
        groupdel "${grp}" >/dev/null 2>&1 || true
    fi
done
log_ok "Removed team groups."

# 6. Remove runtime directories
rm -rf "${LVM_DISK_DIR}" "${REPO_ROOT}" "${BACKUP_ROOT}" "${LOG_ROOT}" "${DEVCOMPANY_OPT_DIR}"
log_ok "Teardown complete: System restored cleanly."
