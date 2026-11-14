#!/usr/bin/env bash
# 02_setup_lvm_storage.sh - Provision loopback block devices, LVM VG/LVs, ext4, UUID fstab & systemd loop unit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 02: Setting up Loopback LVM Storage (${LVM_VG})"

# Verify required LVM tools exist
for cmd in losetup pvcreate vgcreate lvcreate mkfs.ext4 blkid findmnt; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        log_err "Required command '${cmd}' not found. Run 01_install_packages.sh first."
        exit 1
    fi
done

# Attempt to load kernel modules if modular (built-in on WSL2 kernels)
modprobe dm_mod >/dev/null 2>&1 || true
modprobe loop >/dev/null 2>&1 || true

ensure_dir "${LVM_DISK_DIR}" 0750

DISK1="${LVM_DISK_DIR}/disk1.img"
DISK2="${LVM_DISK_DIR}/disk2.img"

create_disk_image() {
    local img_path="$1"
    local size_spec="$2"
    if [[ -f "${img_path}" ]]; then
        log_info "Backing disk image already exists: ${img_path}"
    else
        log_info "Creating ${size_spec} loopback disk image: ${img_path}"
        if command -v truncate >/dev/null 2>&1; then
            truncate -s "${size_spec}" "${img_path}"
        else
            dd if=/dev/zero of="${img_path}" bs=1M count=2048 status=none
        fi
        chmod 0600 "${img_path}"
    fi
}

attach_loop_device() {
    local img_path="$1"
    local existing_loop
    existing_loop="$(losetup -j "${img_path}" -O NAME --noheadings 2>/dev/null | head -n1 | tr -d '[:space:]' || true)"
    if [[ -n "${existing_loop}" ]]; then
        log_info "Image ${img_path} already attached to ${existing_loop}" >&2
        printf '%s\n' "${existing_loop}"
        return 0
    fi
    local new_loop
    new_loop="$(losetup -f --show "${img_path}")"
    log_ok "Attached ${img_path} -> ${new_loop}" >&2
    printf '%s\n' "${new_loop}"
}

create_disk_image "${DISK1}" "2G"
create_disk_image "${DISK2}" "2G"

LOOP1="$(attach_loop_device "${DISK1}")"
LOOP2="$(attach_loop_device "${DISK2}")"

command -v udevadm >/dev/null 2>&1 && udevadm settle 2>/dev/null || sleep 1

# Initialize Physical Volumes idempotently
for loop_dev in "${LOOP1}" "${LOOP2}"; do
    if pvs --noheadings -o pv_name "${loop_dev}" >/dev/null 2>&1; then
        log_info "Physical Volume already initialized on ${loop_dev}"
    else
        log_info "Initializing Physical Volume on ${loop_dev}..."
        pvcreate -y -ff "${loop_dev}"
        log_ok "Created PV: ${loop_dev}"
    fi
done

# Create Volume Group idempotently
if vgs "${LVM_VG}" >/dev/null 2>&1; then
    log_info "Volume Group '${LVM_VG}' already exists."
else
    log_info "Creating Volume Group '${LVM_VG}'..."
    vgcreate "${LVM_VG}" "${LOOP1}" "${LOOP2}"
    log_ok "Created VG: ${LVM_VG}"
fi

vgchange -ay "${LVM_VG}" >/dev/null
vgmknodes >/dev/null 2>&1 || true

# Logical Volumes specification: name|size|mountpoint
LV_SPECS=(
    "lv_repos|1536M|${REPO_ROOT}"
    "lv_backups|1536M|${BACKUP_ROOT}"
    "lv_logs|800M|${LOG_ROOT}"
)

# Backup /etc/fstab once before modifications
if [[ ! -f /etc/fstab.devcompany.bak ]]; then
    cp -a /etc/fstab /etc/fstab.devcompany.bak
fi

update_fstab_entry() {
    local uuid="$1"
    local mnt="$2"
    local opts="defaults,nofail,x-systemd.requires=devcompany-lvm-loop.service,x-systemd.after=devcompany-lvm-loop.service"
    local line="UUID=${uuid} ${mnt} ext4 ${opts} 0 2 # devcompany-lvm"

    if grep -qxF "${line}" /etc/fstab 2>/dev/null; then
        log_info "/etc/fstab already configured for ${mnt} (UUID=${uuid})"
        return 0
    fi

    # Remove stale entries for this mountpoint or marker
    local tmp_fstab
    tmp_fstab="$(mktemp)"
    awk -v mnt="${mnt}" '($2 != mnt) && !($0 ~ /# devcompany-lvm$/ && $2 == mnt)' /etc/fstab > "${tmp_fstab}"
    printf '%s\n' "${line}" >> "${tmp_fstab}"
    cat "${tmp_fstab}" > /etc/fstab
    rm -f "${tmp_fstab}"
    log_ok "Persisted ${mnt} (UUID=${uuid}) in /etc/fstab"
}

for spec in "${LV_SPECS[@]}"; do
    IFS='|' read -r lv_name lv_size lv_mnt <<< "${spec}"
    lv_dev="/dev/${LVM_VG}/${lv_name}"

    if lvs "${LVM_VG}/${lv_name}" >/dev/null 2>&1; then
        log_info "Logical Volume '${lv_name}' already exists."
    else
        log_info "Creating Logical Volume '${lv_name}' (${lv_size})..."
        lvcreate -y -L "${lv_size}" -n "${lv_name}" "${LVM_VG}"
        vgchange -ay "${LVM_VG}" >/dev/null
        vgmknodes >/dev/null 2>&1 || true
        log_ok "Created LV: ${lv_dev}"
    fi

    fs_type="$(blkid -o value -s TYPE "${lv_dev}" 2>/dev/null || true)"
    if [[ "${fs_type}" != "ext4" ]]; then
        log_info "Formatting ${lv_dev} as ext4..."
        mkfs.ext4 -F -L "${lv_name}" "${lv_dev}"
        log_ok "Formatted ${lv_dev} with ext4."
    else
        log_info "${lv_dev} already formatted as ext4."
    fi

    ensure_dir "${lv_mnt}" 0755
    if findmnt -M "${lv_mnt}" >/dev/null 2>&1; then
        log_info "Mountpoint ${lv_mnt} is already mounted."
    else
        log_info "Mounting ${lv_dev} -> ${lv_mnt}..."
        mount "${lv_dev}" "${lv_mnt}"
        log_ok "Mounted ${lv_mnt}"
    fi

    lv_uuid="$(blkid -s UUID -o value "${lv_dev}")"
    if [[ -n "${lv_uuid}" ]]; then
        update_fstab_entry "${lv_uuid}" "${lv_mnt}"
    else
        log_err "Could not resolve UUID for ${lv_dev}"
        exit 1
    fi
done

# Install boot-time loopback attachment script & systemd service so reboot/WSL restart never hangs fstab
log_info "Installing systemd boot persistence for loopback LVM devices..."
cat << 'EOF' > /usr/local/sbin/devcompany-attach-lvm.sh
#!/usr/bin/env bash
set -euo pipefail

DISK_DIR="/var/lvm_disks"
VG_NAME="vg_devcompany"

if [[ -d "${DISK_DIR}" ]]; then
    shopt -s nullglob
    for img in "${DISK_DIR}"/disk*.img; do
        if [[ -z "$(losetup -j "${img}" -O NAME --noheadings 2>/dev/null || true)" ]]; then
            losetup -f --show "${img}" >/dev/null
        fi
    done
    shopt -u nullglob
fi

pvscan --cache >/dev/null 2>&1 || true
if vgs "${VG_NAME}" >/dev/null 2>&1; then
    vgchange -ay "${VG_NAME}" >/dev/null
    vgmknodes >/dev/null 2>&1 || true
fi
EOF
chmod 0755 /usr/local/sbin/devcompany-attach-lvm.sh

if [[ -f "${PROJECT_ROOT}/systemd/devcompany-lvm-loop.service" ]]; then
    cp -f "${PROJECT_ROOT}/systemd/devcompany-lvm-loop.service" /etc/systemd/system/devcompany-lvm-loop.service
    chmod 0644 /etc/systemd/system/devcompany-lvm-loop.service
    if has_systemd; then
        systemctl daemon-reload
        systemctl enable devcompany-lvm-loop.service >/dev/null 2>&1 || true
        systemctl start devcompany-lvm-loop.service >/dev/null 2>&1 || true
        log_ok "Enabled systemd unit: devcompany-lvm-loop.service"
    else
        log_warn "systemd is not active in this shell; unit installed for next systemd boot."
    fi
fi

log_info "Current LVM Volume Summary:"
lvs -o lv_name,vg_name,lv_size,lv_attr "${LVM_VG}"
df -h "${REPO_ROOT}" "${BACKUP_ROOT}" "${LOG_ROOT}"
log_ok "Step 02 complete: Loopback LVM storage active and UUID-persisted."
