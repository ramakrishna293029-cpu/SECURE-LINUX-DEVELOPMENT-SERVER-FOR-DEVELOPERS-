#!/usr/bin/env bash
# 00_master_setup.sh - One-click orchestrator running Steps 01..08, deploying dashboard service & verifying.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "DevCompany Linux Infrastructure - Master Setup Orchestrator"

# Ensure all local scripts are normalized & executable
find "${SCRIPT_DIR}" -type f -name "*.sh" -exec sed -i 's/\r$//' {} +
find "${SCRIPT_DIR}" -type f -name "*.sh" -exec chmod 0755 {} +

STEPS=(
    "01_install_packages.sh"
    "02_setup_lvm_storage.sh"
    "03_provision_40_devs.sh"
    "04_setup_shared_repos.sh"
    "05_cleanup_system.sh"
    "06_backup_manager.sh"
    "07_server_monitor.sh"
    "08_configure_cron.sh"
)

for step_script in "${STEPS[@]}"; do
    bash "${SCRIPT_DIR}/${step_script}"
done

# Deploy Python virtualenv and FastAPI Command Center service under /opt/devcompany
log_step "Deploying Web Admin Dashboard Service (Port 8080)"
sync_project_to_opt "${PROJECT_ROOT}"

VENV_DIR="${DEVCOMPANY_OPT_DIR}/venv"
if [[ ! -x "${VENV_DIR}/bin/uvicorn" ]]; then
    log_info "Creating Python virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade pip --quiet || true
    "${VENV_DIR}/bin/pip" install -r "${DEVCOMPANY_OPT_DIR}/requirements.txt" --quiet
else
    log_info "Dashboard virtualenv already ready at ${VENV_DIR}; refreshing requirements..."
    "${VENV_DIR}/bin/pip" install -r "${DEVCOMPANY_OPT_DIR}/requirements.txt" --quiet || true
fi

if has_systemd && [[ -f "${DEVCOMPANY_OPT_DIR}/systemd/devcompany-dashboard.service" ]]; then
    cp -f "${DEVCOMPANY_OPT_DIR}/systemd/devcompany-dashboard.service" /etc/systemd/system/devcompany-dashboard.service
    chmod 0644 /etc/systemd/system/devcompany-dashboard.service
    systemctl daemon-reload
    start_enable_service devcompany-dashboard
else
    log_warn "systemd unavailable; starting dashboard in background via nohup..."
    pkill -f "uvicorn app:app --host 0.0.0.0 --port 8080" >/dev/null 2>&1 || true
    cd "${DEVCOMPANY_OPT_DIR}/dashboard"
    DEVCOMPANY_ROOT="${DEVCOMPANY_OPT_DIR}" nohup "${VENV_DIR}/bin/uvicorn" app:app --host 0.0.0.0 --port 8080 \
        > "${LOG_ROOT}/dashboard.log" 2>&1 &
fi

# Wait up to 15s for the FastAPI dashboard to bind port 8080, then refresh telemetry
for _ in $(seq 1 15); do
    if curl -sf http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

bash "${DEVCOMPANY_OPT_DIR}/scripts/07_server_monitor.sh"
bash "${SCRIPT_DIR}/99_verify_and_demo.sh"

log_step "SETUP COMPLETE"
log_ok "Web Admin Dashboard: http://localhost:8080"
log_ok "Shared Repositories: ${REPO_ROOT}/{frontend,backend,devops,shared}"
log_ok "Automated Backups:   ${BACKUP_ROOT}"
log_ok "Health & Logs:       ${LOG_ROOT}"
