#!/usr/bin/env bash
# 01_install_packages.sh - Install developer, sysadmin, storage, and monitoring packages.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 01: Updating APT repositories & installing infrastructure packages"

export DEBIAN_FRONTEND=noninteractive

PACKAGES=(
    git
    gcc
    g++
    python3
    python3-venv
    python3-pip
    nodejs
    npm
    build-essential
    curl
    wget
    htop
    sysstat
    net-tools
    acl
    lvm2
    tree
    ufw
    cron
    openssh-server
    jq
    e2fsprogs
    util-linux
    tar
    gzip
)

log_info "Running apt-get update..."
apt-get update -y

log_info "Installing ${#PACKAGES[@]} packages (idempotent)..."
apt-get install -y --no-install-recommends "${PACKAGES[@]}"

# Enable sysstat data collection if configured
if [[ -f /etc/default/sysstat ]]; then
    sed -i 's/^ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
    start_enable_service sysstat || true
fi

# Prepare OpenSSH server runtime directory and host keys
ensure_dir /run/sshd 0755
if ! ls /etc/ssh/ssh_host_*_key >/dev/null 2>&1; then
    log_info "Generating missing SSH host keys..."
    ssh-keygen -A
fi

# Ensure cron and ssh services are enabled and running
start_enable_service cron
start_enable_service ssh sshd

# Configure firewall rules safely (WSL2 kernels may restrict netfilter/ufw enable)
if command -v ufw >/dev/null 2>&1; then
    log_info "Staging UFW firewall rules (SSH 22/tcp, Dashboard 8080/tcp)..."
    ufw allow 22/tcp >/dev/null 2>&1 || true
    ufw allow 8080/tcp >/dev/null 2>&1 || true
    if is_wsl; then
        log_warn "WSL2 detected: UFW rules staged; skipping 'ufw enable' to avoid WSL2 netfilter limitations."
    else
        ufw --force enable >/dev/null 2>&1 || log_warn "Could not activate UFW automatically."
    fi
fi

log_ok "Step 01 complete: All required packages installed and cron/ssh services verified."
