# Role-Wise Contribution Matrix & Verification Guide

This document presents a structured contribution matrix for the four assigned project roles in the **SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard** project. Each section details the operational responsibilities, technical deliverables, implemented features, exact verification commands, and expected verification results.

---

## Master Contribution Summary

| Role Title | Primary Focus Area | Core Modules / Scripts | Verification Artifact | Status |
|---|---|---|---|---|
| **ROLE 1 – Linux System Administrator** | User identity, groups, SSH keys, password aging, sudoers policy | `01_install_packages.sh`, `03_provision_40_devs.sh`, `/etc/sudoers.d/dev_policies` | `id dev*`, `chage -l`, `sudo -l -U` | **VERIFIED (0 Errors)** |
| **ROLE 2 – Storage & Backup Administrator** | LVM storage, loopback persistence, backup manager, SHA-256 verification | `02_setup_lvm_storage.sh`, `extend_lvm_demo.sh`, `06_backup_manager.sh`, `devcompany-lvm-loop.service` | `pvs`/`vgs`/`lvs`, `df -h`, `sha256sum -c` | **VERIFIED (0 Errors)** |
| **ROLE 3 – Automation & Security Engineer** | Shared Git repos (mode 3775), POSIX ACLs, system cleanup, monitoring, cron | `04_setup_shared_repos.sh`, `05_cleanup_system.sh`, `07_server_monitor.sh`, `08_configure_cron.sh`, `00_master_setup.sh` | `ls -ld`, `getfacl`, `crontab -l`, `health_metrics.json` | **VERIFIED (0 Errors)** |
| **ROLE 4 – Testing Documentation & Presentation Lead** | Audit suite, 45 automated tests, web dashboard, documentation, presentation | `99_verify_and_demo.sh`, `tests/`, `dashboard/app.py`, `dashboard/templates/`, `dashboard/static/`, `docs/` | `pytest -v`, `99_verify_and_demo.sh`, HTTP 200 checks | **VERIFIED (0 Errors)** |

---

## Detailed Role Deliverables & Verification Matrix

### ROLE 1 – Linux System Administrator

#### 1. Assigned Responsibilities
- Baseline package repository synchronization and toolchain deployment on Ubuntu.
- Automated creation and management of 40 developer accounts (`dev01` to `dev40`).
- Linux user group hierarchy management across 4 functional departments.
- Cryptographic Ed25519 SSH key generation and authorized key deployment.
- Strict password aging policy configuration via `chage`.
- Scoped least-privilege `sudoers` access delegation.

#### 2. Delivered Code & Configuration Artifacts
- `scripts/01_install_packages.sh`: Idempotent installation of `build-essential`, `gcc`, `g++`, `git`, `python3`, `nodejs`, `lvm2`, `acl`, `cron`, `openssh-server`, `ufw`, `sysstat`.
- `scripts/03_provision_40_devs.sh`: Loops through indices 1–40, creates user accounts, assigns primary and supplementary groups, configures SSH keys, and sets aging parameters.
- `/etc/sudoers.d/dev_policies`: Validated policy file restricting junior developers and delegating operational command aliases to DevOps and Tech Leads.

#### 3. Implemented Technical Functionality
- **Department Allocation:**
  - `dev01`–`dev12`: Primary group `frontend` (12 users)
  - `dev13`–`dev26`: Primary group `backend` (14 users)
  - `dev27`–`dev34`: Primary group `devops` (8 users)
  - `dev35`–`dev40`: Primary group `techleads` (6 users)
  - All 40 accounts hold supplementary membership in the unified `developers` group.
- **SSH Key Infrastructure:** Auto-provisioned `id_ed25519` key pairs with strict permissions (`0700` `~/.ssh`, `0600` private key and `authorized_keys`).
- **Password Aging:** Mandates 90-day maximum age (`-M 90`), 7-day minimum interval (`-m 7`), and 14-day expiry warning (`-W 14`).
- **RBAC Sudo Delegation:** Zero root privileges for `frontend` and `backend`; scoped service restart and LVM resize privileges for `devops`; scoped Git management and ACL modification for `techleads`.

#### 4. Verification Commands & Expected Output

| Test Objective | Exact Ubuntu Terminal Command | Expected Operational Result |
|---|---|---|
| **Verify Developer Accounts & Groups** | `id dev01 && id dev16 && id dev27 && id dev35` | Output shows correct UID, primary GID (`frontend`, `backend`, `devops`, `techleads`), and `developers` group membership. |
| **Verify Password Aging Policy** | `sudo chage -l dev01` | Displays: `Maximum: 90`, `Minimum: 7`, `Warning: 14`. |
| **Verify SSH Key Files & Permissions** | `ls -la /home/dev01/.ssh/` | Shows `drwx------` on directory, `-rw-------` on `id_ed25519` and `authorized_keys`, and `-rw-r--r--` on `id_ed25519.pub`. |
| **Verify Junior Developer Sudo Denial** | `sudo -l -U dev01` | Returns: `User dev01 is not allowed to run sudo on <hostname>`. |
| **Verify Scoped DevOps Sudo Privileges** | `sudo -l -U dev27` | Shows permitted commands: `systemctl restart devcompany-*`, `journalctl`, `lvextend`, `resize2fs`. |
| **Verify Sudoers File Syntax** | `sudo visudo -cf /etc/sudoers.d/dev_policies` | Returns: `/etc/sudoers.d/dev_policies: parsed OK`. |

---

### ROLE 2 – Storage & Backup Administrator

#### 1. Assigned Responsibilities
- Design and deployment of an elastic Logical Volume Management (LVM) subsystem.
- Creation, formatting (`ext4`), and mounting of dedicated logical partitions.
- Implementation of loopback block storage with boot persistence across system reboots.
- Demonstration of live, zero-downtime online volume expansion.
- Automated disaster recovery backup management with cryptographic SHA-256 verification.
- Automated archive retention pruning.

#### 2. Delivered Code & Configuration Artifacts
- `scripts/02_setup_lvm_storage.sh`: Allocates sparse backing images (`disk1.img`, `disk2.img`), maps loop devices, creates PVs, VG `vg_devcompany`, and LVs `lv_repos`, `lv_backups`, `lv_logs`.
- `systemd/devcompany-lvm-loop.service`: Custom systemd early boot unit executing loop device attachment and volume group activation prior to filesystem mounting.
- `scripts/extend_lvm_demo.sh`: Online expansion script performing `lvextend -L +200M` and `resize2fs` on active filesystems without unmounting.
- `scripts/06_backup_manager.sh`: Production backup script creating timestamped `.tar.gz` archives, calculating SHA-256 digests, and pruning archives older than 7 days.
- Filesystem mount configuration in `/etc/fstab` with `nofail` and systemd mount ordering dependencies.

#### 3. Implemented Technical Functionality
- **Storage Hierarchy:**
  - Physical Volumes: Dual loopback backing devices (`/dev/loop0`, `/dev/loop1`) aggregated into `vg_devcompany` (~4 GB).
  - Logical Volume `lv_repos` (1536 MB): Mounted at `/srv/dev_repos` for source code trees.
  - Logical Volume `lv_backups` (1536 MB): Mounted at `/srv/dev_backups` for backup archives.
  - Logical Volume `lv_logs` (800 MB): Mounted at `/var/log/dev_company` for operational logs.
- **Boot Persistence:** Pre-mount execution via systemd loop service prevents system hang or emergency shell drops on reboot.
- **Online Expansion:** Expands active partitions on the fly; automatically creates and attaches a third backing image (`disk3.img`) if Volume Group extents are depleted.
- **Disaster Recovery Pipeline:** Creates `devcompany_backup_YYYYMMDD_HHMMSS.tar.gz`, verifies readability via `tar -tzf`, writes `.sha256` checksums, and purges archives older than 7 days.

#### 4. Verification Commands & Expected Output

| Test Objective | Exact Ubuntu Terminal Command | Expected Operational Result |
|---|---|---|
| **Verify LVM Volume Group & Logical Volumes** | `sudo pvs && sudo vgs && sudo lvs` | Shows `vg_devcompany` with 2 PVs (~4 GB size) and active LVs: `lv_repos` (1.5G), `lv_backups` (1.5G), `lv_logs` (800M). |
| **Verify Active ext4 Filesystem Mounts** | `df -h -T /srv/dev_repos /srv/dev_backups /var/log/dev_company` | Confirms all three volumes mounted on `ext4` filesystems with active read/write availability. |
| **Verify Boot Persistence Configuration** | `grep vg_devcompany /etc/fstab` | Shows mount entries using `defaults,nofail,x-systemd.requires=devcompany-lvm-loop.service`. |
| **Verify Online LVM Expansion** | `sudo bash scripts/extend_lvm_demo.sh` | Successfully extends `lv_repos` by +200MB and resizes filesystem with zero downtime (`resize2fs: OK`). |
| **Verify Backup Generation & Checksum** | `sudo bash scripts/06_backup_manager.sh && ls -lh /srv/dev_backups/` | Generates `.tar.gz` archive and matching `.sha256` hash file. |
| **Verify SHA-256 Cryptographic Integrity** | `cd /srv/dev_backups && sha256sum -c *.sha256` | Output: `<archive_name>.tar.gz: OK`. |
| **Verify Archive Readability** | `tar -tzf /srv/dev_backups/devcompany_backup_*.tar.gz | head -n 8` | Displays internal repository directory structure without gzip or format errors. |

---

### ROLE 3 – Automation & Security Engineer

#### 1. Assigned Responsibilities
- Provisioning and securing shared bare Git repositories for all four teams.
- Implementing SGID and Sticky Bit directory permissions for secure multi-tenant collaboration.
- Enforcing recursive POSIX Access Control Lists (ACLs) for senior lead oversight.
- Engineering automated system cleanup routines to prevent disk exhaustion.
- Developing the continuous server telemetry monitoring engine.
- Configuring centralized cron automation schedules.
- Developing master deployment orchestration and idempotent teardown scripts.

#### 2. Delivered Code & Configuration Artifacts
- `scripts/04_setup_shared_repos.sh`: Provisions bare Git repositories under `/srv/dev_repos/{frontend,backend,devops,shared}`, applies octal mode `3775`, and sets default POSIX ACLs.
- `scripts/05_cleanup_system.sh`: Purges unaccessed `/tmp` files older than 7 days, compresses rotated logs older than 14 days with gzip, and cleans APT package caches.
- `scripts/07_server_monitor.sh`: Collects live CPU, memory, disk, and LVM metrics, and parses process lists using whitespace-safe column ordering (`ps -eo pid=,%cpu=,%mem=,user=,comm=`).
- `scripts/08_configure_cron.sh`: Installs `/etc/cron.d/devcompany_automation` coordinating periodic monitoring, backup, and cleanup execution.
- `scripts/00_master_setup.sh`: Master orchestrator sequencing scripts 01 through 08 and auditing execution.
- `scripts/00_teardown.sh`: Idempotent teardown reversing users, groups, LVM mounts, and system services.

#### 3. Implemented Technical Functionality
- **Collaboration Permissions (Mode 3775):**
  - **SGID (2000):** Every new commit or object created in the repository inherits the group ownership of the team (e.g. `frontend`).
  - **Sticky Bit (1000):** Prevents developers from unlinking or deleting files authored by other team members, safeguarding source integrity.
- **POSIX ACLs:** Grants group `techleads` default and explicit read/write/execute rights (`g:techleads:rwx`) across all team subdirectories.
- **Safe Telemetry Tokenization:** Places variable-width process command names last in `ps` output, preventing browser or daemon process names containing spaces from breaking telemetry JSON parsing.
- **Centralized Cron Schedules:**
  - `*/5 * * * *`: Server telemetry snapshot execution
  - `0 2 * * *`: Daily repository backup
  - `0 3 * * 0`: Weekly system cleanup and log rotation

#### 4. Verification Commands & Expected Output

| Test Objective | Exact Ubuntu Terminal Command | Expected Operational Result |
|---|---|---|
| **Verify Shared Repository Permissions** | `ls -ld /srv/dev_repos/*` | Shows permissions `drwxrws--t` (mode 3775) on all team folders. |
| **Verify POSIX ACL Inheritance** | `getfacl /srv/dev_repos/frontend/web-portal.git` | Shows `flags: -st`, `group:techleads:rwx`, `default:group:techleads:rwx`. |
| **Verify System Cleanup Execution** | `sudo bash scripts/05_cleanup_system.sh && tail /var/log/dev_company/cleanup.log` | Purges expired temporary files, compresses rotated logs, and logs `Status: SUCCESS`. |
| **Verify Telemetry Engine JSON Output** | `sudo bash scripts/07_server_monitor.sh && cat /var/log/dev_company/health_metrics.json` | Generates valid JSON containing `cpu_percent`, `memory`, `disks`, `lvm`, and `top_processes`. |
| **Verify Cron Schedule Installation** | `cat /etc/cron.d/devcompany_automation` | Displays the three scheduled automated tasks with correct root execution permissions. |
| **Verify Master Orchestration Idempotency** | `sudo bash scripts/00_master_setup.sh` | Executes complete deployment pipeline end-to-end without duplicating accounts or failing. |

---

### ROLE 4 – Testing Documentation & Presentation Lead

#### 1. Assigned Responsibilities
- Designing and implementing automated infrastructure verification suites.
- Authoring unit and integration tests across static scripts, APIs, and presentation artifacts.
- Developing and refining the real-time DevOps Command Center Web Dashboard.
- Supervising the web application daemon under systemd.
- Cataloging verification screenshots and maintaining the technical evidence index.
- Authoring comprehensive project documentation, presentation slides, and evaluation reports.

#### 2. Delivered Code & Configuration Artifacts
- `scripts/99_verify_and_demo.sh`: 25-point comprehensive infrastructure audit validating all CO1–CO5 controls.
- `tests/test_scripts_static.py`: Static assertion test suite validating LF endings, `set -euo pipefail`, and `bash -n` syntax.
- `tests/test_dashboard_api.py`: 9 integration tests evaluating FastAPI endpoints, SSE streaming, developer filtering, and parsing resilience.
- `tests/test_generate_ppt.py`: Validates 15-slide academic presentation structure.
- `dashboard/app.py`: Asynchronous FastAPI backend providing REST APIs and Server-Sent Events script runners.
- `dashboard/templates/index.html` & `dashboard/static/app.js`: Glassmorphic, dark-mode DevOps command center with Chart.js live graphs, sticky tables, and terminal action console.
- `systemd/devcompany-dashboard.service`: Systemd service unit managing Uvicorn on port `8080`.
- Documentation artifacts: `README.md`, `TEAM_ROLES.md`, `CONTRIBUTIONS.md`, `PROJECT_STRUCTURE.md`, `docs/PROJECT_DOCUMENTATION.md`, `docs/DevCompany_Linux_Hackathon.pptx`.

#### 3. Implemented Technical Functionality
- **Automated Verification Suite:** 25 assertion checks evaluating packages, services, LVM, accounts, SSH keys, password aging, sudoers policies, Git SGID, ACLs, and backup integrity, yielding 0 failures.
- **Pytest Quality Assurance:** 45 automated test assertions ensuring regression-free deployment across environments.
- **FastAPI Web Command Center (:8080):**
  - Live hardware telemetry polling (every 3 seconds) from `/proc` and `ps`.
  - Filterable 40-developer directory with department pills, search bar, and sticky table headers.
  - Interactive Git repository and ACL inspector.
  - Live Server-Sent Events (SSE) streaming terminal console for on-demand script triggering.
- **Systemd Process Supervision:** Automatic restart upon failure (`Restart=always`) and automated boot activation.

#### 4. Verification Commands & Expected Output

| Test Objective | Exact Ubuntu Terminal Command | Expected Operational Result |
|---|---|---|
| **Run Comprehensive Infrastructure Audit** | `sudo bash scripts/99_verify_and_demo.sh` | Output: `VERIFICATION SUMMARY: 25 Passed, 0 Warnings, 0 Failed` with status `[100% PRODUCTION READY]`. |
| **Run Pytest Automated Test Suite** | `pytest -v` | Output: `45 passed, 1 warning` in ~100s across all test modules. |
| **Verify Dashboard API Health Endpoint** | `curl -sf http://127.0.0.1:8080/api/health` | Returns: `{"status": "ok", "provisioned": true, "developer_count": 40}`. |
| **Verify Live Telemetry API Endpoint** | `curl -sf http://127.0.0.1:8080/api/telemetry | python3 -m json.tool` | Returns valid JSON with live CPU%, memory, disks, and top processes without tracebacks. |
| **Verify Developer Filtering Endpoint** | `curl -sf "http://127.0.0.1:8080/api/developers?team=frontend" | jq .total` | Returns: `12`. |
| **Verify Systemd Dashboard Service** | `sudo systemctl status devcompany-dashboard --no-pager` | Shows `Active: active (running)` with Uvicorn worker listening on port `8080`. |
| **Verify Presentation Generation** | `python docs/generate_ppt.py` | Generates 15-slide PowerPoint deck `docs/DevCompany_Linux_Hackathon.pptx`. |
