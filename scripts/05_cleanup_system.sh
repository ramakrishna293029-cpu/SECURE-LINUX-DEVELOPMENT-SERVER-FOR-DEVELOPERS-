#!/usr/bin/env bash
# 05_cleanup_system.sh - Purge aged temp files, compress old logs, clear package caches, log freed space.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 05: Running Automated System Cleanup & Housekeeping"

ensure_dir "${LOG_ROOT}" 0755
CLEANUP_LOG="${LOG_ROOT}/cleanup.log"

get_avail_kb() {
    local target="$1"
    df -Pk "${target}" 2>/dev/null | awk 'NR==2 {print $4}'
}

root_before_kb="$(get_avail_kb /)"
log_before_kb="$(get_avail_kb "${LOG_ROOT}")"

# 1. Purge /tmp and /var/tmp files older than 7 days (preserving active systemd private dirs and sockets)
tmp_deleted=0
for tmp_dir in /tmp /var/tmp; do
    if [[ -d "${tmp_dir}" ]]; then
        count="$(find "${tmp_dir}" -mindepth 1 -type f -mtime +7 ! -path '*/systemd-private-*' 2>/dev/null | wc -l | tr -d '[:space:]')"
        find "${tmp_dir}" -mindepth 1 -type f -mtime +7 ! -path '*/systemd-private-*' -delete 2>/dev/null || true
        tmp_deleted=$((tmp_deleted + count))
    fi
done
log_info "Purged ${tmp_deleted} temp file(s) older than 7 days from /tmp and /var/tmp."

# 2. Rotate/compress logs in /var/log/dev_company older than 14 days
logs_compressed=0
if [[ -d "${LOG_ROOT}" ]]; then
    logs_compressed="$(find "${LOG_ROOT}" -maxdepth 2 -type f -name "*.log" -mtime +14 ! -name "*.gz" 2>/dev/null | wc -l | tr -d '[:space:]')"
    find "${LOG_ROOT}" -maxdepth 2 -type f -name "*.log" -mtime +14 ! -name "*.gz" -exec gzip -f {} + 2>/dev/null || true
fi
log_info "Compressed ${logs_compressed} log file(s) older than 14 days in ${LOG_ROOT}."

# 3. Clean APT, PIP, and NPM caches safely
if command -v apt-get >/dev/null 2>&1; then
    apt-get autoclean -y >/dev/null 2>&1 || true
    apt-get clean -y >/dev/null 2>&1 || true
    log_info "Cleaned APT package cache."
fi

if command -v pip3 >/dev/null 2>&1; then
    pip3 cache purge >/dev/null 2>&1 || true
    log_info "Cleared pip3 cache (if present)."
fi

if command -v npm >/dev/null 2>&1; then
    npm cache clean --force >/dev/null 2>&1 || true
    log_info "Cleared npm cache."
fi

root_after_kb="$(get_avail_kb /)"
log_after_kb="$(get_avail_kb "${LOG_ROOT}")"

freed_root_kb=$((root_after_kb - root_before_kb))
freed_log_kb=$((log_after_kb - log_before_kb))
total_freed_kb=$((freed_root_kb + freed_log_kb))
if [[ "${total_freed_kb}" -lt 0 ]]; then
    total_freed_kb=0
fi

summary_line="[$(date '+%Y-%m-%d %H:%M:%S')] CLEANUP_OK tmp_purged=${tmp_deleted} logs_compressed=${logs_compressed} freed_kb=${total_freed_kb} root_avail_kb=${root_after_kb}"
printf '%s\n' "${summary_line}" >> "${CLEANUP_LOG}"
log_ok "${summary_line}"
