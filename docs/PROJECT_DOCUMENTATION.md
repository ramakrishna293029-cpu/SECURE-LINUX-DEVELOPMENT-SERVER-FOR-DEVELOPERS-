# SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard — Academic Project Documentation

**Problem Statement #4:** Design, automate, secure, monitor, and manage a multi-team Linux server infrastructure supporting 40 software engineers across four departments (`frontend`, `backend`, `devops`, `techleads`), backed by dynamically resizable LVM storage, integrity-verified backups, automated cron housekeeping, and a live Web Admin Command Center.

---

## 1. Problem Statement & Objectives

A growing software engineering organization with **40 developers** requires a standardized, secure, and observable Linux development server. Manual provisioning fails to scale reliably: unmanaged permissions invite accidental file deletion across teams, static disk partitions overflow under Git repositories and log growth, broad `sudo` grants create severe privilege-escalation risks, and reactive troubleshooting leaves teams vulnerable to silent backup failures or disk exhaustion.

### Project Objectives
1. **Automate Baseline Toolchain Provisioning (CO1):** Install compilers, runtimes, Git, LVM, ACLs, monitoring tools, `cron`, and `openssh-server` idempotently.
2. **Deploy Flexible, Boot-Safe LVM Storage (CO2):** Isolate repositories, backups, and operational logs onto dedicated `ext4` Logical Volumes backed by loopback disk images so the solution runs safely on single-disk VMs and WSL2 without risking host partitions.
3. **Enforce Least-Privilege Identity & Collaboration Controls (CO3):** Provision `dev01`–`dev40` with password aging, Ed25519 SSH keys, team group isolation, SGID (`2775`), Sticky Bit (`+t`), POSIX ACL oversight (`setfacl`), and `visudo`-validated `sudoers` rules.
4. **Automate Maintenance & Backup Integrity (CO4):** Schedule telemetry collection, SHA-256 verified `.tar.gz` backups with 7-day retention, and automated `/tmp`/log/cache cleanup via `/etc/cron.d/devcompany_automation`.
5. **Provide Real-Time Observability & Auditability (CO5):** Surface live kernel CPU/RAM/LVM telemetry, RBAC directories, ACL outputs, and one-click script execution in a browser-based FastAPI Web Command Center alongside `99_verify_and_demo.sh`.

---

## 2. Course Outcome (CO1–CO5) Mapping

| Course Outcome | Focus Area | Implemented Modules & Evidence |
|---|---|---|
| **CO1** | Linux Installation, CLI & Package Management | `scripts/01_install_packages.sh` (`apt-get`, `git`, `gcc`, `g++`, `python3`, `nodejs`, `sysstat`, `cron`, `openssh-server`, `ufw`) |
| **CO2** | Storage Architecture, LVM & Filesystems | `scripts/02_setup_lvm_storage.sh`, `scripts/extend_lvm_demo.sh`, `systemd/devcompany-lvm-loop.service`, UUID `/etc/fstab` |
| **CO3** | User Administration, Permissions, SGID, Sticky Bit & ACLs | `scripts/03_provision_40_devs.sh`, `scripts/04_setup_shared_repos.sh`, `/etc/sudoers.d/dev_policies`, `setfacl`/`getfacl` |
| **CO4** | Shell Scripting, Backups & Cron Automation | `scripts/lib/common.sh`, `05_cleanup_system.sh`, `06_backup_manager.sh`, `08_configure_cron.sh`, `/etc/cron.d/devcompany_automation` |
| **CO5** | Performance Monitoring, Alerts, Verification & Admin UI | `07_server_monitor.sh`, `99_verify_and_demo.sh`, `dashboard/app.py` (FastAPI + Chart.js Command Center on port `8080`) |

---

## 3. System Architecture Diagram

```text
+-----------------------------------------------------------------------------------+
|                        40 DEVELOPER ACCOUNTS (dev01..dev40)                       |
|  frontend (12): dev01-12 | backend (14): dev13-26 | devops (8): 27-34 | leads: 6  |
|  Auth: Ed25519 SSH Keys + chage (90d/7d/14d) | Sudo: /etc/sudoers.d/dev_policies  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                  SHARED BARE GIT REPOSITORIES (/srv/dev_repos)                    |
|   /frontend/web-portal.git  | /backend/core-api.git | /devops/infra-automation.git|
|   /shared/company-docs.git                                                        |
|   Permissions: mode 3775 (SGID 2775 + Sticky +t) + POSIX ACL (g:techleads:rwx)    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                LOOPBACK LVM STORAGE SUBSYSTEM (vg_devcompany - 4 GB)              |
|   /var/lvm_disks/disk1.img (2G) --losetup--> PV1 --+                              |
|   /var/lvm_disks/disk2.img (2G) --losetup--> PV2 --+--> vg_devcompany             |
|       |-- lv_repos   (1.5G ext4) --> /srv/dev_repos    (UUID + devcompany-lvm-loop|
|       |-- lv_backups (1.5G ext4) --> /srv/dev_backups   systemd boot service)     |
|       +-- lv_logs    (800M ext4) --> /var/log/dev_company                         |
+-----------------------------------------+-----------------------------------------+
                                          |
          +-------------------------------+-------------------------------+
          v                                                               v
+-----------------------------------+           +-----------------------------------+
|  CRON AUTOMATION (/etc/cron.d)    |           |  FASTAPI WEB COMMAND CENTER :8080 |
|  */5 * * * * -> 07_server_monitor |           |  - Live /proc CPU/RAM/LVM Charts  |
|  0 2 * * *   -> 06_backup_manager |---------->|  - 40-Dev RBAC Search & Filter    |
|  0 3 * * 0   -> 05_cleanup_system |           |  - Repo 3775 & getfacl Inspector  |
+-----------------------------------+           |  - SSE Live Script Action Console |
                                                +-----------------------------------+
```

---

## 4. Workspace & Runtime Directory Structure

```text
linux-dev-server-hackathon/
├── README.md
├── requirements.txt
├── scripts/
│   ├── lib/common.sh                # Color logging, root checks, systemd/WSL helpers, /opt sync
│   ├── 00_master_setup.sh          # One-click orchestrator (01..08 + dashboard + audit)
│   ├── 01_install_packages.sh       # Installs toolchain, cron, openssh-server, lvm2, acl
│   ├── 02_setup_lvm_storage.sh      # Loopback images, PV/VG/LV, ext4, UUID fstab & systemd loop unit
│   ├── extend_lvm_demo.sh           # Online +200MB lvextend & resize2fs (+ auto VG expansion)
│   ├── 03_provision_40_devs.sh      # 4 teams + developers group, dev01..dev40, SSH keys, sudoers
│   ├── 04_setup_shared_repos.sh     # Bare Git repos, 3775 (SGID + Sticky), recursive POSIX ACLs
│   ├── 05_cleanup_system.sh         # /tmp >7d purge, logs >14d gzip, apt/pip/npm cache clean
│   ├── 06_backup_manager.sh         # Timestamped .tar.gz + SHA-256 verification + 7d retention
│   ├── 07_server_monitor.sh         # Live metrics JSON + monitor.log + [ALERT] threshold rules
│   ├── 08_configure_cron.sh         # Deploys /opt/devcompany + /etc/cron.d/devcompany_automation
│   ├── 99_verify_and_demo.sh        # Automated [PASS]/[FAIL] CO1-CO5 verification suite
│   └── 00_teardown.sh               # Cleanly reverts users, groups, LVM, loop devices & services
├── systemd/
│   ├── devcompany-lvm-loop.service  # Attaches /var/lvm_disks/disk*.img prior to local-fs mounts
│   └── devcompany-dashboard.service # Runs Uvicorn FastAPI dashboard on 0.0.0.0:8080
├── dashboard/
│   ├── app.py                       # FastAPI REST API + live SSE script runner
│   ├── templates/index.html         # Dark-mode DevOps Command Center UI
│   └── static/app.js                # 3s polling, Chart.js graphs, RBAC/ACL/Backup views
├── docs/
│   ├── PROJECT_DOCUMENTATION.md     # This academic report
│   ├── generate_ppt.py              # Automated 15-slide python-pptx generator
│   └── DevCompany_Linux_Hackathon.pptx
└── tests/
    ├── test_scripts_static.py       # LF endings, bash -n syntax & spec assertions
    ├── test_dashboard_api.py        # FastAPI TestClient integration & SSE streaming tests
    └── test_generate_ppt.py         # 15-slide PPTX structure & content validation
```

---

## 5. Deep Dive: Linux Subsystems & Commands Explained

### 5.1 Loopback LVM & Boot-Safe Persistence (`02_setup_lvm_storage.sh`)
- **Why Loopback Devices?** On single-disk evaluation VMs and WSL2 instances, unused raw block partitions do not exist. Sparse 2GB backing files (`/var/lvm_disks/disk1.img`, `/var/lvm_disks/disk2.img`) created with `truncate -s 2G` and mapped via `losetup -f --show` behave identically to physical SCSI/NVMe block devices without risking the host filesystem.
- **LVM Hierarchy:**
  - `pvcreate`: initializes LVM Physical Volume metadata headers on `/dev/loopX` and `/dev/loopY`.
  - `vgcreate vg_devcompany ...`: aggregates both PVs into a ~4GB Volume Group.
  - `lvcreate -L 1536M -n lv_repos`, `lv_backups` (`1536M`), `lv_logs` (`800M`): carves three isolated block volumes formatted with `mkfs.ext4`.
- **Preventing Boot Hangs in `/etc/fstab`:** Loopback attachments do not persist automatically across reboots. If `/etc/fstab` references a loopback LVM UUID that is not yet attached at boot, Linux can drop into emergency mode. We solve this cleanly in two layers:
  1. `systemd/devcompany-lvm-loop.service` runs `/usr/local/sbin/devcompany-attach-lvm.sh` (`losetup -f --show`, `pvscan --cache`, `vgchange -ay vg_devcompany`) **before** `local-fs.target`.
  2. Every `/etc/fstab` entry uses `defaults,nofail,x-systemd.requires=devcompany-lvm-loop.service,x-systemd.after=devcompany-lvm-loop.service 0 2`.
- **Online Expansion (`extend_lvm_demo.sh`):** Checks free VG extents via `vgs`; if under 220MB free (such as during repeated live demo clicks), provisions `disk3.img`, attaches it with `losetup`, runs `pvcreate` + `vgextend`, then executes `lvextend -L +200M` and `resize2fs` with zero downtime.

### 5.2 User RBAC, SSH Keys & Sudo Policies (`03_provision_40_devs.sh`)
- **Group Structure:** `developers` (all 40 users) plus four role groups: `frontend` (`dev01`–`dev12`, 12 users), `backend` (`dev13`–`dev26`, 14 users), `devops` (`dev27`–`dev34`, 8 users), and `techleads` (`dev35`–`dev40`, 6 users).
- **Password & Key Hygiene:** `chage -M 90 -m 7 -W 14` mandates 90-day rotation, 7-day minimum age, and 14-day expiry warnings. Each developer receives an Ed25519 key pair (`~/.ssh/id_ed25519`) configured in `authorized_keys` (`0700` `.ssh`, `0600` private key/authorized_keys).
- **Least-Privilege Sudoers (`/etc/sudoers.d/dev_policies`):** Validated with `visudo -cf` and installed with `0440` permissions. `frontend` and `backend` have **zero** sudo access. `techleads` and `devops` receive explicit `Cmnd_Alias` service-restart and operational script permissions without wildcard shell escalation.

### 5.3 Shared Git Repositories, SGID, Sticky Bit & POSIX ACLs (`04_setup_shared_repos.sh`)
Each directory under `/srv/dev_repos/{frontend,backend,devops,shared}` hosts a shared bare Git repository (`git init --bare --shared=group`) and enforces mode **`3775`** (`chmod 2775` + `chmod +t`):
- **SGID (`2xxx`):** Every new file, branch ref, or object created inside the directory automatically inherits the team group (`frontend`, `backend`, `devops`, or `developers`) rather than the committer's personal group.
- **Sticky Bit (`1xxx`, combined `3775`):** Only the file owner or `root` can unlink/rename files inside the shared directory, stopping teammates from accidentally deleting another developer's work.
- **POSIX ACLs (`setfacl -R -m g:techleads:rwx` and `-d -m g:techleads:rwx`):** Grants all 6 Tech Leads read/write oversight across every existing and future subdirectory across all teams without changing owning groups.

### 5.4 Cron Schedules & Maintenance (`05`–`08`)

| Cron Schedule | Meaning | Script | Purpose |
|---|---|---|---|
| `*/5 * * * *` | Every 5 minutes | `/opt/devcompany/scripts/07_server_monitor.sh` | Samples `/proc/stat`, memory, LVM usage, top processes & services; raises `[ALERT]` if CPU > 80% or Disk > 85% |
| `0 2 * * *` | Daily at 02:00 AM | `/opt/devcompany/scripts/06_backup_manager.sh` | Archives `/srv/dev_repos`, `/etc/passwd`, `/etc/group`, `/etc/sudoers.d`; verifies `.sha256`; prunes >7 days |
| `0 3 * * 0` | Sunday at 03:00 AM | `/opt/devcompany/scripts/05_cleanup_system.sh` | Deletes `/tmp` & `/var/tmp` files >7d, gzips logs >14d, cleans APT/pip/npm caches |

---

## 6. Testing Strategy & Verification Checklist

1. **Static & Syntax Validation (`pytest tests/test_scripts_static.py`):** Verifies strict Unix `LF` line endings, `#!/usr/bin/env bash` headers, `set -euo pipefail`, `bash -n` syntax validity, and mandatory requirement coverage across all 13 shell scripts and 2 systemd units.
2. **Dashboard API & SSE Streaming (`pytest tests/test_dashboard_api.py`):** Uses FastAPI `TestClient` against synthetic Linux config fixtures to verify `/api/health`, `/api/telemetry`, `/api/developers` filtering (40 users across 4 teams), `/api/repos`, `/api/backups` live SHA-256 verification, whitelisted action security (rejecting invalid actions with HTTP 404), and live Server-Sent Events output streaming.
3. **PPTX Structural Validation (`pytest tests/test_generate_ppt.py`):** Runs `docs/generate_ppt.py` and asserts all 15 required slides exist with matching titles, speaker notes, and zero placeholders.
4. **Live Server Audit (`sudo bash scripts/99_verify_and_demo.sh`):** Executes end-to-end assertions inside Ubuntu/WSL2 checking packages, active `cron`/`ssh`/`devcompany-lvm-loop` services, `vg_devcompany` LVs & UUID `/etc/fstab` entries, all 40 accounts/keys/aging/sudo policies, `3775` permissions + `getfacl` ACLs, verified `.tar.gz` backups, and `http://127.0.0.1:8080/api/health`.

---

## 7. References

- **Linux Foundation Training:** https://training.linuxfoundation.org (Primary reference standard for CO1–CO5 Linux system administration architecture, LVM storage, identity & access management, and automation)
- **Ubuntu Server & Man Pages:** `systemd.mount(5)`, `fstab(5)`, `lvcreate(8)`, `lvextend(8)`, `resize2fs(8)`, `losetup(8)`, `setfacl(1)`, `sudoers(5)`, `chage(1)`
- **Git Shared Repositories:** Pro Git (`git init --bare --shared=group`)
