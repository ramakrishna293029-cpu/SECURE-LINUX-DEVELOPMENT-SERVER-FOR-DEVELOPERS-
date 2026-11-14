# Team Roles & System Ownership Matrix

This document outlines the four specialized engineering roles defined for the **SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard** project. It details the operational responsibilities, technical scope, and specific module ownership associated with each role.

---

## Role Definitions & System Scope

```
+---------------------------------------------------------------------------------------------------+
|                        ROLE ARCHITECTURE & SYSTEM SCOPE MATRIX                                    |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ROLE 1: Linux System Administrator]                                                             |
|   ├── User Provisioning: dev01..dev40 across 4 Functional Teams                                   |
|   ├── Linux Groups: developers, frontend, backend, devops, techleads                              |
|   ├── Credential & Authentication: Ed25519 SSH Keys, Password Aging (chage 90d/7d/14d)             |
|   └── Sudoers Policy: /etc/sudoers.d/dev_policies (Least-Privilege RBAC)                          |
|                                                                                                   |
|  [ROLE 2: Storage & Backup Administrator]                                                         |
|   ├── LVM Subsystem: Volume Group vg_devcompany (4 GB Resizable)                                  |
|   ├── Logical Volumes: lv_repos (/srv/dev_repos), lv_backups (/srv/dev_backups), lv_logs          |
|   ├── Mount Persistence: Loopback Systemd Unit (devcompany-lvm-loop.service) & UUID fstab         |
|   └── Backup Engine: Automated .tar.gz Archives, SHA-256 Checksums, 7-Day Retention               |
|                                                                                                   |
|  [ROLE 3: Automation & Security Engineer]                                                         |
|   ├── Shared Git Repositories: Bare Repositories with Mode 3775 (SGID + Sticky Bit)               |
|   ├── POSIX ACLs: Recursive Oversight for Tech Leads (setfacl -d -m g:techleads:rwx)              |
|   ├── Automated Housekeeping: /tmp Purge (>7d), Log Compression (>14d), APT Cache Cleanup         |
|   ├── Telemetry Engine: Continuous Kernel /proc & Safe Process Monitoring (07_server_monitor.sh)  |
|   └── Cron Scheduling: /etc/cron.d/devcompany_automation Orchestration                            |
|                                                                                                   |
|  [ROLE 4: Testing Documentation & Presentation Lead]                                              |
|   ├── Automated Infrastructure Audit: scripts/99_verify_and_demo.sh (CO1-CO5 Controls)            |
|   ├── Test Engineering: pytest Integration Suites (Static, API, Presentation Validation)          |
|   ├── Web Command Center: FastAPI & Chart.js Real-Time Admin Dashboard (:8080)                    |
|   ├── Evidence & Verification: Screenshot Capture, Verification Matrices, Failure Logs            |
|   └── Technical Artifacts: Comprehensive Documentation, Presentation Decks, and Reports           |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## Detailed Role Responsibilities

### ROLE 1 – Linux System Administrator

The **Linux System Administrator** owns identity lifecycle management, operating system baseline configuration, developer access controls, and least-privilege privilege escalation rules.

#### Key Responsibilities
- **Operating System Baseline Configuration:** Provisioning baseline developer packages, build tools, compiler toolchains (`gcc`, `g++`, `make`), runtimes (`python3`, `nodejs`), and system services on Ubuntu Linux.
- **Account Creation & Lifecycle Management:** Automating the creation and maintenance of 40 developer accounts (`dev01` through `dev40`) with home directories, default shells (`/bin/bash`), and GECOS descriptive metadata.
- **Group Hierarchy & Team Segmentation:** Implementing five distinct Linux system groups:
  - `developers`: Unified group containing all 40 engineering accounts.
  - `frontend`: GID 1001, containing developers `dev01` through `dev12` (12 developers).
  - `backend`: GID 1002, containing developers `dev13` through `dev26` (14 developers).
  - `devops`: GID 1003, containing developers `dev27` through `dev34` (8 developers).
  - `techleads`: GID 1004, containing developers `dev35` through `dev40` (6 technical leads).
- **SSH Key Infrastructure:** Generating and configuring Ed25519 SSH key pairs (`~/.ssh/id_ed25519`) for each developer account, enforcing secure directory permissions (`0700` `.ssh`, `0600` private keys and `authorized_keys`, `0644` public keys).
- **Password Aging & Security Policies:** Implementing corporate password rotation standards using `chage`:
  - Maximum password age: 90 days (`-M 90`)
  - Minimum days between password changes: 7 days (`-m 7`)
  - Expiration warning window: 14 days (`-W 14`)
- **Least-Privilege Sudo Access:** Authoring and maintaining `/etc/sudoers.d/dev_policies` validated with `visudo -cf`, completely restricting root escalation for standard developers while granting scoped command aliases to DevOps and Tech Lead accounts.

#### Owned Modules & Files
- `scripts/01_install_packages.sh`
- `scripts/03_provision_40_devs.sh`
- `scripts/lib/common.sh` (identity and user validation helpers)
- Sudoers policy definitions (`/etc/sudoers.d/dev_policies`)

---

### ROLE 2 – Storage & Backup Administrator

The **Storage & Backup Administrator** owns physical and logical block storage allocation, filesystem formatting, mount lifecycle persistence, shared bare repository storage, and the disaster recovery backup pipeline.

#### Key Responsibilities
- **Logical Volume Management (LVM):** Provisioning dual sparse backing disk images (`/var/lvm_disks/disk1.img`, `disk2.img`), initializing LVM Physical Volumes (`pvcreate`), and aggregating storage into Volume Group `vg_devcompany` (~4 GB).
- **Logical Volume Allocation:** Carving and formatting three dedicated `ext4` block volumes:
  - `lv_repos` (1536 MB): Mounted at `/srv/dev_repos` for shared team source trees.
  - `lv_backups` (1536 MB): Mounted at `/srv/dev_backups` for disaster recovery archives.
  - `lv_logs` (800 MB): Mounted at `/var/log/dev_company` for operational logs and telemetry snapshots.
- **Boot Persistence & Mount Resilience:** Engineering the custom systemd unit `systemd/devcompany-lvm-loop.service` to reattach loopback block devices before `local-fs.target`, and configuring `/etc/fstab` with `nofail` and systemd mount dependencies to prevent boot hangs.
- **Online Storage Expansion:** Implementing `scripts/extend_lvm_demo.sh` to demonstrate live, zero-downtime volume expansion (`+200MB`) via `lvextend` and `resize2fs`.
- **Disaster Recovery Backup Pipeline:** Engineering `scripts/06_backup_manager.sh` to bundle `/srv/dev_repos` into timestamped `.tar.gz` archives in `/srv/dev_backups`.
- **Cryptographic Verification & Retention:** Generating SHA-256 checksums (`.sha256`) for every archive, confirming non-destructive readability via `tar -tzf`, and enforcing an automated 7-day archive retention pruning policy.

#### Owned Modules & Files
- `scripts/02_setup_lvm_storage.sh`
- `scripts/extend_lvm_demo.sh`
- `systemd/devcompany-lvm-loop.service`
- `scripts/06_backup_manager.sh`
- Mount point and filesystem configuration (`/etc/fstab`)

---

### ROLE 3 – Automation & Security Engineer

The **Automation & Security Engineer** owns repository access security, POSIX Access Control Lists, automated system housekeeping, kernel telemetry sampling, and centralized task scheduling via cron.

#### Key Responsibilities
- **Shared Git Repository Initialization:** Provisioning bare Git repositories (`git init --bare --shared=group`) under `/srv/dev_repos` for Frontend (`web-portal.git`), Backend (`core-api.git`), DevOps (`infra-automation.git`), and Shared (`company-docs.git`).
- **Permissions & Collaboration Security:** Enforcing octal mode `3775` across all repository directories:
  - **Setgid (SGID, 2000):** Ensures newly created files, branch refs, and Git objects automatically inherit the parent team group ownership.
  - **Sticky Bit (1000):** Restricts file deletion and renaming exclusively to the original file creator and `root`, preventing cross-developer data deletion within shared directories.
- **POSIX Access Control Lists (ACLs):** Applying recursive and default POSIX ACLs (`setfacl -R -m g:techleads:rwx` and `-d -m g:techleads:rwx`) to grant all 6 Technical Leads read, write, and execute oversight across all team repositories.
- **Automated System Cleanup:** Engineering `scripts/05_cleanup_system.sh` to purge unaccessed temporary files in `/tmp` older than 7 days, compress rotated logs older than 14 days with gzip, and reclaim package manager caches (`apt-get clean`).
- **Kernel Telemetry & Hardware Monitoring:** Developing `scripts/07_server_monitor.sh` to sample CPU usage from `/proc/stat`, memory from `/proc/meminfo`, disk capacity from `df -BM`, and top processes using a safe column specification (`ps -eo pid=,%cpu=,%mem=,user=,comm=`) that handles command names with spaces without parsing misalignment.
- **Cron Automation Orchestration:** Deploying `/etc/cron.d/devcompany_automation` coordinating telemetry sampling (every 5 minutes), nightly repository backups (02:00 AM), and weekly system housekeeping (Sunday 03:00 AM).
- **Master Orchestration & Teardown:** Developing `scripts/00_master_setup.sh` for one-click deployment and `scripts/00_teardown.sh` for clean, idempotent environment resetting.

#### Owned Modules & Files
- `scripts/00_master_setup.sh`
- `scripts/00_teardown.sh`
- `scripts/04_setup_shared_repos.sh`
- `scripts/05_cleanup_system.sh`
- `scripts/07_server_monitor.sh`
- `scripts/08_configure_cron.sh`
- Centralized cron configuration (`/etc/cron.d/devcompany_automation`)

---

### ROLE 4 – Testing Documentation & Presentation Lead

The **Testing Documentation & Presentation Lead** owns quality assurance, automated infrastructure auditing, test suite authoring, web dashboard development, technical reporting, and presentation delivery.

#### Key Responsibilities
- **Automated Infrastructure Auditing:** Authoring `scripts/99_verify_and_demo.sh`, executing 25+ comprehensive assertion checks evaluating package status, active systemd daemons, LVM volume mounts, 40-developer group memberships, SSH keys, sudoers policies, Git SGID permissions, and backup integrity.
- **Pytest Test Engineering:** Authoring and maintaining 45 automated unit and integration tests across three test suites:
  - `tests/test_scripts_static.py`: Validates LF line endings, `set -euo pipefail`, `bash -n` syntax, and requirement coverage.
  - `tests/test_dashboard_api.py`: Validates FastAPI REST endpoints, SSE stream execution, developer filtering, and telemetry parsing resilience against whitespace.
  - `tests/test_generate_ppt.py`: Validates 15-slide academic presentation structure and slide titles.
- **DevOps Command Center Dashboard:** Building and refining the browser-based FastAPI web application (`dashboard/app.py`), Chart.js real-time graph engine (`dashboard/static/app.js`), and responsive dark-mode management interface (`dashboard/templates/index.html`) on port `8080`.
- **Systemd Service Supervision:** Authoring and managing `systemd/devcompany-dashboard.service` for automated daemon restart and boot supervision.
- **Documentation & Verification Records:** Cataloging verification screenshots, recording command outputs, maintaining the audit trail, and authoring formal documentation:
  - `README.md`
  - `TEAM_ROLES.md`
  - `CONTRIBUTIONS.md`
  - `PROJECT_STRUCTURE.md`
  - `docs/PROJECT_DOCUMENTATION.md`
  - `docs/DevCompany_Linux_Hackathon.pptx` (and generator `docs/generate_ppt.py`)
  - Formal academic project report (`Linux Hackathon Report.docx` and `.pdf`)

#### Owned Modules & Files
- `scripts/99_verify_and_demo.sh`
- `tests/test_scripts_static.py`
- `tests/test_dashboard_api.py`
- `tests/test_generate_ppt.py`
- `dashboard/app.py`
- `dashboard/templates/index.html`
- `dashboard/static/app.js`
- `systemd/devcompany-dashboard.service`
- `docs/` and `screenshots/` directories
- Root documentation files (`README.md`, `TEAM_ROLES.md`, `CONTRIBUTIONS.md`, `PROJECT_STRUCTURE.md`)

---

## Inter-Role Collaboration Matrix

The following matrix illustrates how the four roles interface across technical boundaries:

| Technical Boundary | Role 1 (SysAdmin) | Role 2 (Storage) | Role 3 (Automation) | Role 4 (QA & Lead) |
|---|---|---|---|---|
| **User Provisioning & Storage** | Creates `dev01`–`dev40` | Allocates `/srv/dev_repos` LVM volume | Applies mode `3775` & ACLs | Verifies accounts via `99_verify_and_demo.sh` |
| **Shared Repositories** | Defines team groups & permissions | Formats & mounts `lv_repos` | Initializes bare Git repos | Tests repo permissions in dashboard |
| **Backup & Housekeeping** | Restricts backup access to `root` | Executes backup & SHA-256 | Schedules cron jobs | Validates archive integrity via tests |
| **System Monitoring & Web UI** | Provisions `sysstat` & packages | Provides LVM usage telemetry | Implements `07_server_monitor.sh` | Builds FastAPI UI & Chart.js frontend |
| **Audit & Quality Assurance** | Validates `visudo` syntax | Verifies online `lvextend` | Ensures script idempotency | Runs 45 pytest tests & verification |
