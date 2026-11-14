#!/usr/bin/env bash
# extend_lvm_demo.sh - Online LVM expansion demo (+200MB on lv_repos) with automatic PV expansion if VG is full.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root

TARGET_LV="${1:-lv_repos}"
EXTEND_MB="${2:-200}"
LV_PATH="/dev/${LVM_VG}/${TARGET_LV}"

log_step "Live LVM Online Storage Expansion Demo (+${EXTEND_MB}M on ${TARGET_LV})"

if ! lvs "${LVM_VG}/${TARGET_LV}" >/dev/null 2>&1; then
    log_err "Logical Volume ${LV_PATH} does not exist. Run 02_setup_lvm_storage.sh first."
    exit 1
fi

log_info "BEFORE expansion:"
df -h "${REPO_ROOT}" "${BACKUP_ROOT}" "${LOG_ROOT}" 2>/dev/null || true
vgs "${LVM_VG}"

# Check available free space in VG (in MB, integer floor)
vg_free_mb="$(vgs --noheadings --units m --nosuffix -o vg_free "${LVM_VG}" | awk '{printf "%d", $1}')"
needed_mb=$((EXTEND_MB + 16))

if [[ "${vg_free_mb}" -lt "${needed_mb}" ]]; then
    log_warn "VG '${LVM_VG}' has ${vg_free_mb}MB free (< ${needed_mb}MB needed). Provisioning an additional 1G loopback PV..."
    idx=3
    while [[ -f "${LVM_DISK_DIR}/disk${idx}.img" ]]; do
        idx=$((idx + 1))
    done
    extra_img="${LVM_DISK_DIR}/disk${idx}.img"
    truncate -s 1G "${extra_img}"
    chmod 0600 "${extra_img}"
    extra_loop="$(losetup -f --show "${extra_img}")"
    pvcreate -y -ff "${extra_loop}"
    vgextend "${LVM_VG}" "${extra_loop}"
    log_ok "Extended VG '${LVM_VG}' with ${extra_img} (${extra_loop})."
fi

log_info "Extending ${LV_PATH} by +${EXTEND_MB}M online..."
lvextend -L "+${EXTEND_MB}M" "${LV_PATH}"

log_info "Resizing ext4 filesystem online via resize2fs..."
resize2fs "${LV_PATH}"

log_info "AFTER expansion:"
lvs -o lv_name,vg_name,lv_size "${LVM_VG}"
df -h "${REPO_ROOT}" "${BACKUP_ROOT}" "${LOG_ROOT}" 2>/dev/null || true
log_ok "Online expansion complete: ${LV_PATH} grew by +${EXTEND_MB}MB with zero downtime."
