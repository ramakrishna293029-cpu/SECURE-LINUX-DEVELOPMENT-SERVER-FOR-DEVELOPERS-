#!/usr/bin/env bash
# 08_configure_cron.sh - Install system cron schedule in /etc/cron.d/devcompany_automation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 08: Configuring Automated Cron Jobs (/etc/cron.d/devcompany_automation)"

# Ensure scripts are deployed cleanly under /opt/devcompany (space-free, native ext4, +x)
sync_project_to_opt "${PROJECT_ROOT}"
ensure_dir "${LOG_ROOT}" 0755

cat << 'EOF' > "${CRON_FILE}"
# /etc/cron.d/devcompany_automation - Automated SysAdmin Operations for DevCompany
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Collect telemetry & health metrics every 5 minutes
*/5 * * * * root /opt/devcompany/scripts/07_server_monitor.sh >/dev/null 2>&1

# Run full repository + auth backup daily at 2:00 AM
0 2 * * * root /opt/devcompany/scripts/06_backup_manager.sh >> /var/log/dev_company/cron.log 2>&1

# Run automated temp/log/cache cleanup weekly on Sunday at 3:00 AM
0 3 * * 0 root /opt/devcompany/scripts/05_cleanup_system.sh >> /var/log/dev_company/cron.log 2>&1
EOF

chown root:root "${CRON_FILE}"
chmod 0644 "${CRON_FILE}"

start_enable_service cron
log_ok "Step 08 complete: Installed ${CRON_FILE} and ensured cron service is active."
