#!/usr/bin/env bash
# 06_backup_manager.sh - Timestamped backup of repositories & user/RBAC configs with SHA-256 verification and 7d retention.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 06: Running Automated Backup Manager & SHA-256 Verification"

ensure_dir "${BACKUP_ROOT}" 0750
ensure_dir "${LOG_ROOT}" 0755
ensure_dir "${REPO_ROOT}" 0755

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
ARCHIVE_NAME="repos_backup_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_ROOT}/${ARCHIVE_NAME}"
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"
BACKUP_LOG="${LOG_ROOT}/backup.log"

# Collect targets relative to / (only include existing paths so tar never fails)
TAR_TARGETS=()
for rel_target in "srv/dev_repos" "etc/passwd" "etc/group" "etc/sudoers.d"; do
    if [[ -e "/${rel_target}" ]]; then
        TAR_TARGETS+=("${rel_target}")
    else
        log_warn "Target /${rel_target} missing; skipping from archive."
    fi
done

log_info "Creating archive ${ARCHIVE_PATH}..."
tar --warning=no-file-changed -czpf "${ARCHIVE_PATH}" -C / "${TAR_TARGETS[@]}"
chmod 0640 "${ARCHIVE_PATH}"

log_info "Generating and verifying SHA-256 integrity checksum..."
(
    cd "${BACKUP_ROOT}"
    sha256sum "${ARCHIVE_NAME}" > "${ARCHIVE_NAME}.sha256"
    sha256sum -c "${ARCHIVE_NAME}.sha256"
)
chmod 0640 "${CHECKSUM_PATH}"

# Prune backups older than 7 days
pruned_count="$(find "${BACKUP_ROOT}" -maxdepth 1 -type f -name "repos_backup_*.tar.gz*" -mtime +7 2>/dev/null | wc -l | tr -d '[:space:]')"
find "${BACKUP_ROOT}" -maxdepth 1 -type f -name "repos_backup_*.tar.gz*" -mtime +7 -delete 2>/dev/null || true

archive_size="$(du -h "${ARCHIVE_PATH}" | awk '{print $1}')"
sha256_hash="$(awk '{print $1}' "${CHECKSUM_PATH}")"

log_entry="[$(date '+%Y-%m-%d %H:%M:%S')] BACKUP_OK file=${ARCHIVE_NAME} size=${archive_size} sha256=${sha256_hash} pruned=${pruned_count}"
printf '%s\n' "${log_entry}" >> "${BACKUP_LOG}"
log_ok "${log_entry}"
