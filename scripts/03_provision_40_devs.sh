#!/usr/bin/env bash
# 03_provision_40_devs.sh - Create 4 team groups, master developers group, 40 users (dev01..dev40), SSH keys, aging & sudoers.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 03: Provisioning 40 Developer Accounts, Groups, SSH Keys & RBAC Sudoers"

# Note: Avoid Bash reserved special variable name 'GROUPS'
TEAM_GROUPS=(
    "developers"
    "frontend"
    "backend"
    "devops"
    "techleads"
)

for grp in "${TEAM_GROUPS[@]}"; do
    if getent group "${grp}" >/dev/null 2>&1; then
        log_info "Group already exists: ${grp}"
    else
        groupadd "${grp}"
        log_ok "Created group: ${grp}"
    fi
done

# Team assignment ranges (12 + 14 + 8 + 6 = 40 developers)
team_for_index() {
    local idx="$1"
    if [[ "${idx}" -le 12 ]]; then
        printf 'frontend\n'
    elif [[ "${idx}" -le 26 ]]; then
        printf 'backend\n'
    elif [[ "${idx}" -le 34 ]]; then
        printf 'devops\n'
    else
        printf 'techleads\n'
    fi
}

role_title_for_team() {
    case "$1" in
        frontend)  printf 'Frontend Engineer\n' ;;
        backend)   printf 'Backend Engineer\n' ;;
        devops)    printf 'DevOps Engineer\n' ;;
        techleads) printf 'Technical Lead\n' ;;
        *)         printf 'Software Developer\n' ;;
    esac
}

created_count=0
updated_count=0

for i in $(seq 1 40); do
    username="$(printf 'dev%02d' "${i}")"
    team="$(team_for_index "${i}")"
    role_title="$(role_title_for_team "${team}")"
    gecos="${role_title} (${username})"

    if id "${username}" >/dev/null 2>&1; then
        usermod -s /bin/bash -g "${team}" -a -G "developers" -c "${gecos}" "${username}"
        updated_count=$((updated_count + 1))
    else
        useradd -m -s /bin/bash -g "${team}" -G "developers" -c "${gecos}" "${username}"
        # Initial secure default password only set on first creation to stay idempotent
        printf '%s:%s\n' "${username}" "DevCompany@${username}#2026" | chpasswd
        created_count=$((created_count + 1))
    fi

    # Enforce password aging policy (max 90d, min 7d, warn 14d)
    chage -M 90 -m 7 -W 14 "${username}"

    # Provision Ed25519 SSH key pair and home directory idempotently
    home_dir="$(getent passwd "${username}" | cut -d: -f6)"
    if [[ -z "${home_dir}" ]]; then
        home_dir="/home/${username}"
        usermod -d "${home_dir}" "${username}"
    fi
    if [[ ! -d "${home_dir}" ]]; then
        mkdir -p "${home_dir}"
        cp -rn /etc/skel/. "${home_dir}/" 2>/dev/null || true
    fi
    chown "${username}:${team}" "${home_dir}"

    ssh_dir="${home_dir}/.ssh"
    key_file="${ssh_dir}/id_ed25519"
    auth_file="${ssh_dir}/authorized_keys"

    ensure_dir "${ssh_dir}" 0700
    if [[ ! -f "${key_file}" || ! -f "${key_file}.pub" ]]; then
        rm -f "${key_file}" "${key_file}.pub"
        ssh-keygen -t ed25519 -N "" -C "${username}@devcompany.local" -f "${key_file}" >/dev/null
    fi
    if [[ ! -f "${auth_file}" ]] || ! grep -qxFf "${key_file}.pub" "${auth_file}" 2>/dev/null; then
        cat "${key_file}.pub" >> "${auth_file}"
    fi
    chown -R "${username}:${team}" "${ssh_dir}"
    chmod 0700 "${ssh_dir}"
    chmod 0600 "${key_file}" "${auth_file}"
    chmod 0644 "${key_file}.pub"
done

log_ok "Accounts summary: ${created_count} created, ${updated_count} verified/updated (dev01..dev40)."

# Configure strict role-based sudoers policy
log_info "Writing scoped sudoers policy to ${SUDOERS_FILE}..."
SYSTEMCTL_BIN="$(command -v systemctl || echo '/usr/bin/systemctl')"
tmp_sudoers="$(mktemp)"
cat << EOF > "${tmp_sudoers}"
# /etc/sudoers.d/dev_policies - Role-Based Least-Privilege Administration
# Junior developers (frontend, backend) receive ZERO root privileges.

Cmnd_Alias DEVCOMPANY_SERVICE_RESTART = \\
    ${SYSTEMCTL_BIN} restart devcompany-dashboard, \\
    ${SYSTEMCTL_BIN} status devcompany-dashboard, \\
    ${SYSTEMCTL_BIN} restart cron, \\
    ${SYSTEMCTL_BIN} status cron, \\
    ${SYSTEMCTL_BIN} reload ssh, \\
    ${SYSTEMCTL_BIN} status ssh

Cmnd_Alias DEVCOMPANY_OPS_SCRIPTS = \\
    /opt/devcompany/scripts/05_cleanup_system.sh, \\
    /opt/devcompany/scripts/06_backup_manager.sh, \\
    /opt/devcompany/scripts/07_server_monitor.sh, \\
    /opt/devcompany/scripts/99_verify_and_demo.sh

# Tech Leads: service inspection/restart and health monitoring oversight
%techleads ALL=(root) NOPASSWD: DEVCOMPANY_SERVICE_RESTART, /opt/devcompany/scripts/07_server_monitor.sh, /opt/devcompany/scripts/99_verify_and_demo.sh

# DevOps Engineers: scoped service restarts + automated maintenance/backup scripts
%devops ALL=(root) NOPASSWD: DEVCOMPANY_SERVICE_RESTART, DEVCOMPANY_OPS_SCRIPTS
EOF

if visudo_out="$(visudo -cf "${tmp_sudoers}" 2>&1)"; then
    install -m 0440 -o root -g root "${tmp_sudoers}" "${SUDOERS_FILE}"
    rm -f "${tmp_sudoers}"
    log_ok "Validated and installed ${SUDOERS_FILE} (mode 0440): ${visudo_out}"
else
    log_err "visudo validation failed: ${visudo_out}"
    rm -f "${tmp_sudoers}"
    exit 1
fi

log_ok "Step 03 complete: 40 developers provisioned across 4 teams with SSH keys and RBAC sudoers."
