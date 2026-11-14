#!/usr/bin/env bash
# Shared utilities, constants, and idempotent helpers for DevCompany Linux Infrastructure.

# Prevent double-sourcing
if [[ "${_DEVCOMPANY_COMMON_LOADED:-0}" -eq 1 ]]; then
    return 0
fi
_DEVCOMPANY_COMMON_LOADED=1

# Ensure admin sbin binaries (lvm, chage, visudo, ufw, sshd) are on PATH
case ":${PATH}:" in
    *:/usr/sbin:*) ;;
    *) export PATH="${PATH}:/usr/local/sbin:/usr/sbin:/sbin" ;;
esac

# Standard infrastructure paths and constants
export DEVCOMPANY_OPT_DIR="/opt/devcompany"
export LVM_DISK_DIR="/var/lvm_disks"
export LVM_VG="vg_devcompany"
export REPO_ROOT="/srv/dev_repos"
export BACKUP_ROOT="/srv/dev_backups"
export LOG_ROOT="/var/log/dev_company"
export CRON_FILE="/etc/cron.d/devcompany_automation"
export SUDOERS_FILE="/etc/sudoers.d/dev_policies"

# Color definitions (respect NO_COLOR)
if [[ -z "${NO_COLOR:-}" ]]; then
    C_RESET='\033[0m'
    C_BLUE='\033[1;34m'
    C_GREEN='\033[1;32m'
    C_YELLOW='\033[1;33m'
    C_RED='\033[1;31m'
    C_CYAN='\033[1;36m'
else
    C_RESET=''
    C_BLUE=''
    C_GREEN=''
    C_YELLOW=''
    C_RED=''
    C_CYAN=''
fi

_ts() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_info() {
    printf '%b[%s] [INFO]%b %s\n' "${C_BLUE}" "$(_ts)" "${C_RESET}" "$*"
}

log_ok() {
    printf '%b[%s] [OK]%b %s\n' "${C_GREEN}" "$(_ts)" "${C_RESET}" "$*"
}

log_warn() {
    printf '%b[%s] [WARN]%b %s\n' "${C_YELLOW}" "$(_ts)" "${C_RESET}" "$*"
}

log_err() {
    printf '%b[%s] [ERROR]%b %s\n' "${C_RED}" "$(_ts)" "${C_RESET}" "$*" >&2
}

log_step() {
    printf '\n%b=====================================================================%b\n' "${C_CYAN}" "${C_RESET}"
    printf '%b>>> %s%b\n' "${C_CYAN}" "$*" "${C_RESET}"
    printf '%b=====================================================================%b\n' "${C_CYAN}" "${C_RESET}"
}

require_root() {
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
        log_err "Root privileges required. Run with: sudo bash $0"
        exit 1
    fi
}

is_wsl() {
    grep -qiE '(microsoft|wsl)' /proc/version /proc/sys/kernel/osrelease 2>/dev/null
}

has_systemd() {
    command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]
}

ensure_dir() {
    local dir_path="$1"
    local perms="${2:-0755}"
    if [[ ! -d "${dir_path}" ]]; then
        mkdir -p "${dir_path}"
    fi
    chmod "${perms}" "${dir_path}"
}

resolve_service_name() {
    local candidate
    for candidate in "$@"; do
        if has_systemd; then
            if systemctl list-unit-files "${candidate}.service" --no-legend 2>/dev/null | grep -q "${candidate}"; then
                printf '%s\n' "${candidate}"
                return 0
            fi
        elif command -v service >/dev/null 2>&1; then
            if service "${candidate}" status >/dev/null 2>&1 || [[ -f "/etc/init.d/${candidate}" ]]; then
                printf '%s\n' "${candidate}"
                return 0
            fi
        fi
    done
    printf '%s\n' "$1"
}

start_enable_service() {
    local svc_name
    svc_name="$(resolve_service_name "$@")"
    if has_systemd; then
        systemctl unmask "${svc_name}" >/dev/null 2>&1 || true
        systemctl enable "${svc_name}" >/dev/null 2>&1 || true
        if systemctl restart "${svc_name}" >/dev/null 2>&1 || systemctl start "${svc_name}" >/dev/null 2>&1; then
            log_ok "Service '${svc_name}' enabled and running via systemd."
        else
            log_warn "systemd could not start '${svc_name}' immediately; attempting service fallback."
            service "${svc_name}" start >/dev/null 2>&1 || true
        fi
    elif command -v service >/dev/null 2>&1; then
        service "${svc_name}" start >/dev/null 2>&1 || service "${svc_name}" restart >/dev/null 2>&1 || true
        log_ok "Service '${svc_name}' started via SysV service manager."
    else
        log_warn "No service manager detected to start '${svc_name}'."
    fi
}

sync_project_to_opt() {
    local src_root="$1"
    if [[ ! -d "${src_root}/scripts" ]]; then
        log_err "Invalid project root passed to sync_project_to_opt: ${src_root}"
        return 1
    fi
    ensure_dir "${DEVCOMPANY_OPT_DIR}" 0755
    ensure_dir "${DEVCOMPANY_OPT_DIR}/scripts/lib" 0755
    ensure_dir "${DEVCOMPANY_OPT_DIR}/systemd" 0755
    ensure_dir "${DEVCOMPANY_OPT_DIR}/dashboard" 0755

    cp -f "${src_root}/scripts/"*.sh "${DEVCOMPANY_OPT_DIR}/scripts/"
    cp -f "${src_root}/scripts/lib/"*.sh "${DEVCOMPANY_OPT_DIR}/scripts/lib/"
    if [[ -d "${src_root}/systemd" ]]; then
        cp -f "${src_root}/systemd/"*.service "${DEVCOMPANY_OPT_DIR}/systemd/"
    fi
    if [[ -d "${src_root}/dashboard" ]]; then
        cp -rf "${src_root}/dashboard/." "${DEVCOMPANY_OPT_DIR}/dashboard/"
    fi
    if [[ -f "${src_root}/requirements.txt" ]]; then
        cp -f "${src_root}/requirements.txt" "${DEVCOMPANY_OPT_DIR}/requirements.txt"
        cp -f "${src_root}/requirements.txt" "${DEVCOMPANY_OPT_DIR}/dashboard/requirements.txt"
    fi

    # Normalize line endings defensively in case files came from Windows mount and mark executable
    find "${DEVCOMPANY_OPT_DIR}/scripts" -type f -name "*.sh" -exec sed -i 's/\r$//' {} +
    find "${DEVCOMPANY_OPT_DIR}/scripts" -type f -name "*.sh" -exec chmod 0755 {} +
    log_ok "Synchronized runtime scripts & dashboard to ${DEVCOMPANY_OPT_DIR}"
}
