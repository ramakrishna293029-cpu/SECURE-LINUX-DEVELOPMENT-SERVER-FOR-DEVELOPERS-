# Repository Architecture & Technical Structure

This document provides a comprehensive technical overview of the **SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard** repository layout. It explains the functional role of each file and directory, mapping each component to its respective system layer and assigned engineering role.

---

## Directory Tree Overview

```text
SECURE-LINUX-DEVELOPMENT-SERVER-FOR-DEVELOPERS/
├── README.md                           # Master project guide, architecture, deployment, and testing
├── TEAM_ROLES.md                       # Role definitions and technical ownership boundaries
├── CONTRIBUTIONS.md                    # Role-wise contribution matrix and exact verification commands
├── PROJECT_STRUCTURE.md                # Repository layout and architectural component explanation
├── requirements.txt                    # Python dependencies (FastAPI, Uvicorn, Chart.js backend tools)
├── .gitignore                          # Exclusions for virtual environments, caches, keys, and logs
│
├── scripts/                            # Production GNU Bash infrastructure automation scripts
│   ├── 00_master_setup.sh             # Master orchestrator executing phases 01 through 08
│   ├── 00_teardown.sh                 # Idempotent cleanup script reversing users, LVM, and mounts
│   ├── 01_install_packages.sh         # Package management & toolchain provisioning (CO1)
│   ├── 02_setup_lvm_storage.sh        # Boot-safe LVM storage configuration and filesystem setup (CO2)
│   ├── extend_lvm_demo.sh             # Live online LVM expansion demonstration script (CO2)
│   ├── 03_provision_40_devs.sh        # 40-developer identity provisioning, SSH keys, sudoers (CO3)
│   ├── 04_setup_shared_repos.sh       # Shared bare Git repositories, mode 3775, POSIX ACLs (CO3)
│   ├── 05_cleanup_system.sh           # Automated /tmp purging, log compression, cache cleanup (CO4)
│   ├── 06_backup_manager.sh           # Cryptographic backup engine, SHA-256 verification (CO4)
│   ├── 07_server_monitor.sh           # Kernel /proc telemetry sampling and process monitor (CO5)
│   ├── 08_configure_cron.sh           # Centralized cron automation deployment (CO4)
│   ├── 99_verify_and_demo.sh          # End-to-end 25-point automated verification audit (CO1-CO5)
│   └── lib/
│       └── common.sh                  # Shared logging, root checks, path resolution, systemd helpers
│
├── dashboard/                          # DevOps Web Command Center application (Port 8080)
│   ├── app.py                         # FastAPI REST API, telemetry collector, and SSE script runner
│   ├── templates/
│   │   └── index.html                 # Glassmorphic dark-mode web command center interface
│   └── static/
│       └── app.js                     # Chart.js live charts, 40-dev filter matrix, SSE console logic
│
├── systemd/                            # Linux systemd service unit configurations
│   ├── devcompany-dashboard.service   # Systemd service supervising the Uvicorn web dashboard
│   └── devcompany-lvm-loop.service    # Pre-mount boot service reattaching LVM loopback block devices
│
├── tests/                              # Automated Pytest quality assurance test suites (45 tests)
│   ├── test_scripts_static.py         # Static code assertions: LF endings, bash -n, spec compliance
│   ├── test_dashboard_api.py          # FastAPI TestClient integration tests and whitespace resilience
│   └── test_generate_ppt.py           # Presentation deck structure and slide count validation
│
├── docs/                               # Comprehensive project documentation and evaluation artifacts
│   ├── Linux_Hackathon_Report.pdf     # 24-page comprehensive project deployment report (PDF)
│   └── Linux_Hackathon_Presentation.pdf # 15-slide technical presentation deck (PDF)
│
└── screenshots/                        # Cataloged visual evidence for GitHub and evaluation
    ├── 01_architecture_diagram.png    # High-resolution system architecture blueprint
    ├── 02_user_provisioning.png       # 40-Developer account verification and team group memberships
    ├── 03_password_aging.png          # Password aging policy parameters (chage -l) and SSH keys
    ├── 04_sudoers_policy.png          # Least-privilege sudo verification (dev01 vs dev27/dev35)
    ├── 05_lvm_storage.png             # LVM Physical Volumes, Volume Group, and Logical Volumes
    ├── 06_lvm_mounts.png              # ext4 filesystem mount points and /etc/fstab configuration
    ├── 07_git_repos.png               # Shared bare Git repositories with SGID & Sticky Bit (mode 3775)
    ├── 08_posix_acls.png              # Recursive POSIX ACL inheritance for Tech Leads (getfacl)
    ├── 09_package_services.png        # Active systemd service status checks (dashboard, loop, cron)
    ├── 10_system_cleanup.png          # Automated system cleanup execution and log output
    ├── 11_backup_execution.png        # Production backup archive generation and SHA-256 hashes
    ├── 12_restore_sandbox.png         # SHA-256 validation and sandbox restoration testing
    ├── 13_cron_schedules.png          # Centralized cron automation schedule (/etc/cron.d/)
    ├── 14_telemetry_metrics.png       # Structured JSON telemetry snapshot (health_metrics.json)
    ├── 15_dashboard_live_command_center.png # Live browser interface of the Web Command Center
    ├── 16_api_endpoints.png           # Live REST API endpoint validation confirming HTTP 200
    ├── 17_systemd_status.png          # Systemd service status showing zero tracebacks
    └── 18_verification_audit.png      # End-to-end audit report (25 passed, 0 warnings, 0 failed)
```

---

## Technical Component Breakdown

### 1. Root Configuration & Documentation Files
- **`README.md`**: Master project handbook detailing problem statement, architecture, setup instructions, developer structures, backup procedures, security models, and verification.
- **`TEAM_ROLES.md`**: Formal specification of the four assigned engineering roles, their scopes, and module ownership.
- **`CONTRIBUTIONS.md`**: Exhaustive contribution matrix listing exact commands, verification steps, and expected outputs for each role.
- **`PROJECT_STRUCTURE.md`**: Architectural breakdown of repository files, directories, and dependencies.
- **`requirements.txt`**: Declares minimal Python runtime dependencies (`fastapi`, `uvicorn`, `pytest`, `python-docx`, `python-pptx`, `docx2pdf`, `pillow`).
- **`.gitignore`**: Excludes virtual environments, Python bytecode, temporary log files, loopback disk images, private keys, and sensitive local secrets from version control.

---

### 2. Shell Automation Pipeline (`scripts/`)
All shell scripts adhere to strict safety guidelines (`#!/usr/bin/env bash`, `set -euo pipefail`) and support idempotent re-execution without duplicate side-effects.

- **`00_master_setup.sh` (Role 3):** Sequences and executes scripts 01 through 08, verifies each phase's exit status, activates the systemd dashboard daemon, and triggers an initial system audit.
- **`01_install_packages.sh` (Role 1):** Non-interactively installs compilers (`build-essential`, `gcc`, `g++`), runtimes (`python3`, `nodejs`), utilities (`git`, `lvm2`, `acl`, `sysstat`), and system daemons (`cron`, `openssh-server`, `ufw`).
- **`02_setup_lvm_storage.sh` (Role 2):** Provisions two 2 GB sparse backing images (`/var/lvm_disks/disk1.img`, `disk2.img`), sets up loopback block devices, creates Volume Group `vg_devcompany`, carves Logical Volumes `lv_repos`, `lv_backups`, `lv_logs`, formats them with `ext4`, and writes resilient `/etc/fstab` entries.
- **`extend_lvm_demo.sh` (Role 2):** Demonstrates live, on-the-fly online volume expansion (`+200MB`) using `lvextend` and `resize2fs` without unmounting active filesystems.
- **`03_provision_40_devs.sh` (Role 1):** Provisions 40 developer accounts (`dev01`–`dev40`), assigns primary group memberships across four teams (`frontend`, `backend`, `devops`, `techleads`), adds supplementary group `developers`, generates Ed25519 SSH keys, configures 90-day password aging via `chage`, and deploys `/etc/sudoers.d/dev_policies`.
- **`04_setup_shared_repos.sh` (Role 3):** Initializes shared bare Git repositories under `/srv/dev_repos`, applies mode `3775` (SGID + Sticky Bit), and sets default and access POSIX ACLs for `techleads`.
- **`05_cleanup_system.sh` (Role 3):** Deletes temporary files in `/tmp` older than 7 days, compresses rotated log files older than 14 days with gzip, and cleans package caches.
- **`06_backup_manager.sh` (Role 2):** Bundles `/srv/dev_repos` into timestamped `.tar.gz` archives in `/srv/dev_backups`, computes cryptographic SHA-256 hashes (`.sha256`), verifies table of contents readability (`tar -tzf`), and purges archives older than 7 days.
- **`07_server_monitor.sh` (Role 3):** Samples kernel telemetry from `/proc/stat`, `/proc/meminfo`, `df -BM`, and `lvs`, uses whitespace-safe process parsing (`ps -eo pid=,%cpu=,%mem=,user=,comm=`), and outputs structured JSON to `/var/log/dev_company/health_metrics.json`.
- **`08_configure_cron.sh` (Role 3):** Deploys centralized cron task definitions into `/etc/cron.d/devcompany_automation` for scheduled monitoring, daily backups, and weekly cleanup.
- **`99_verify_and_demo.sh` (Role 4):** Comprehensive automated audit suite running 25 assertions covering packages, services, LVM, accounts, keys, aging, sudoers, Git permissions, ACLs, backups, and REST endpoints.
- **`00_teardown.sh` (Role 3):** Reversal utility cleanly unmounting filesystems, releasing loopback devices, removing user accounts and groups, and terminating systemd services.
- **`lib/common.sh` (Roles 1 & 3):** Shared library providing standardized color logging, root privilege validation, systemd/WSL environment detection, and `/opt/devcompany` directory synchronization.

---

### 3. Web Command Center (`dashboard/`) (Role 4)
Provides real-time administrative visibility and execution control via a lightweight, production-grade web stack.

- **`app.py`:** Built with FastAPI and Uvicorn. Exposes REST endpoints:
  - `GET /`: Serves the glassmorphic command center interface.
  - `GET /api/health`: Returns server status, provisioning state, and developer count.
  - `GET /api/telemetry`: Reads kernel `/proc` metrics and returns live CPU%, RAM%, disk%, and top processes.
  - `GET /api/developers`: Supports department filtering (`team=frontend|backend|devops|techleads`) and search queries.
  - `GET /api/repos`: Inspects bare repository commit logs, branch refs, directory modes, and `getfacl` ACLs.
  - `GET /api/backups`: Lists backup archives, validates SHA-256 checksums in real time, and inspects cron schedules.
  - `GET /api/actions/{action}/stream`: Server-Sent Events (SSE) endpoint streaming live script execution output to the browser console.
- **`templates/index.html`:** Responsive, modern dark-mode interface featuring glassmorphic panels, glowing card accents, sticky-headed tables, and a slide-up macOS/Linux terminal console drawer.
- **`static/app.js`:** Pure JavaScript engine managing Chart.js area gradients, 3-second live telemetry polling, interactive team filter pills, search input filtering, and SSE console event streams.

---

### 4. Systemd Service Supervision (`systemd/`) (Roles 2 & 4)
Integrates background processes into native Linux init management (PID 1).

- **`devcompany-lvm-loop.service` (Role 2):** Ensures loopback disk images are mapped and activated before local filesystems are mounted during system boot.
- **`devcompany-dashboard.service` (Role 4):** Supervises the Uvicorn web server executing `app:app` on port `8080`, providing automatic restart on failure and boot activation.

---

### 5. Automated Quality Assurance (`tests/`) (Role 4)
Guarantees code quality, syntax correctness, and system stability through 45 automated pytest assertions.

- **`test_scripts_static.py`:** Validates that all shell scripts have Unix LF line endings, valid `set -euo pipefail` safety headers, pass `bash -n` syntax compilation, and satisfy mandatory project requirements.
- **`test_dashboard_api.py`:** Uses FastAPI's `TestClient` against synthetic filesystem fixtures to test all REST endpoints, query filters, SSE streams, and verifies that process names containing whitespace (e.g. browser subprocesses) cannot crash telemetry serialization.
- **`test_generate_ppt.py`:** Asserts that the automated PowerPoint generator builds all 15 required slides with matching titles, speaker notes, and zero placeholder text.

---

### 6. Evidence & Documentation (`docs/` & `screenshots/`) (Role 4)
Provides an exhaustive audit trail, visual verification evidence, and evaluation artifacts.

- **`docs/Linux_Hackathon_Report.pdf`:** 24-page formal comprehensive academic project report detailing system architecture, Course Outcome (CO1–CO5) mapping, command syntax explanations, and testing checklists.
- **`docs/Linux_Hackathon_Presentation.pdf`:** Professional 15-slide presentation deck covering Problem Statement #4, architectural topology, implementation details, testing results, and roadmaps.
- **`screenshots/`:** Contains 18 high-resolution PNG verification images covering every subsystem, from initial user provisioning and LVM volume creation to the live Web Command Center and end-to-end automated audit results.
