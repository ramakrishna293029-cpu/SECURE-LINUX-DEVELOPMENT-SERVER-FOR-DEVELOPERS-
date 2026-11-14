"""SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("devcompany.dashboard")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

TEAM_META = {
    "frontend": {"label": "Frontend", "target_count": 12, "sudo_access": "None"},
    "backend": {"label": "Backend", "target_count": 14, "sudo_access": "None"},
    "devops": {"label": "DevOps", "target_count": 8, "sudo_access": "Scoped Ops & Services"},
    "techleads": {"label": "Tech Leads", "target_count": 6, "sudo_access": "Scoped Service & Monitor"},
}

ALLOWED_ACTIONS: dict[str, dict[str, str]] = {
    "backup": {
        "script": "06_backup_manager.sh",
        "title": "Run Backup Now",
        "description": "Archive /srv/dev_repos + auth configs with SHA-256 verification",
    },
    "cleanup": {
        "script": "05_cleanup_system.sh",
        "title": "Run Cleanup Now",
        "description": "Purge aged /tmp files, compress old logs & clear package caches",
    },
    "extend_lvm": {
        "script": "extend_lvm_demo.sh",
        "title": "Expand LVM Storage (+200MB)",
        "description": "Run online lvextend +200M & resize2fs on lv_repos",
    },
    "verify": {
        "script": "99_verify_and_demo.sh",
        "title": "Run Full System Audit",
        "description": "Verify all CO1-CO5 controls, 40 users, LVM, ACLs & cron",
    },
    "monitor": {
        "script": "07_server_monitor.sh",
        "title": "Refresh Telemetry Snapshot",
        "description": "Collect fresh server telemetry into health_metrics.json",
    },
}


@dataclass
class InfraConfig:
    """Resolved filesystem paths for Linux infrastructure inspection."""

    project_root: Path
    scripts_dir: Path
    log_root: Path
    repo_root: Path
    backup_root: Path
    cron_file: Path
    passwd_file: Path
    group_file: Path
    shadow_file: Path = Path("/etc/shadow")

    @classmethod
    def from_env(cls) -> "InfraConfig":
        dashboard_dir = Path(__file__).resolve().parent
        repo_base = Path(os.environ.get("DEVCOMPANY_ROOT", str(dashboard_dir.parent)))
        scripts_dir = Path(os.environ.get("DEVCOMPANY_SCRIPTS_DIR", str(repo_base / "scripts")))
        if not scripts_dir.is_dir():
            scripts_dir = dashboard_dir.parent / "scripts"
        return cls(
            project_root=repo_base,
            scripts_dir=scripts_dir,
            log_root=Path(os.environ.get("DEVCOMPANY_LOG_ROOT", "/var/log/dev_company")),
            repo_root=Path(os.environ.get("DEVCOMPANY_REPO_ROOT", "/srv/dev_repos")),
            backup_root=Path(os.environ.get("DEVCOMPANY_BACKUP_ROOT", "/srv/dev_backups")),
            cron_file=Path(os.environ.get("DEVCOMPANY_CRON_FILE", "/etc/cron.d/devcompany_automation")),
            passwd_file=Path(os.environ.get("DEVCOMPANY_PASSWD_FILE", "/etc/passwd")),
            group_file=Path(os.environ.get("DEVCOMPANY_GROUP_FILE", "/etc/group")),
            shadow_file=Path(os.environ.get("DEVCOMPANY_SHADOW_FILE", "/etc/shadow")),
        )


def _run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return proc.returncode, proc.stdout.strip()
    except Exception:
        return 1, ""


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _human_cron_schedule(expr: str) -> str:
    mapping = {
        "*/5 * * * *": "Every 5 minutes",
        "0 2 * * *": "Daily at 02:00 AM",
        "0 3 * * 0": "Weekly on Sunday at 03:00 AM",
    }
    return mapping.get(expr, f"Custom cron ({expr})")


def _parse_int(raw: str) -> int | None:
    try:
        return int(raw.strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _parse_float(raw: str) -> float | None:
    try:
        val = float(raw.strip())
    except (ValueError, TypeError, AttributeError):
        return None
    return val if math.isfinite(val) else None


def _parse_ps_processes(out_ps: str, limit: int = 6) -> list[dict[str, Any]]:
    """Parse `ps -eo pid=,%cpu=,%mem=,user=,comm= --sort=-%cpu` safely.

    Putting fixed numeric fields and username first ensures process names containing
    spaces, parentheses, or special characters (e.g. `Isolated Web Co`, `(sd-pam)`)
    stay intact in the final field without misaligning numeric columns.
    """
    procs: list[dict[str, Any]] = []
    for raw_line in out_ps.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(None, 4)
        if len(parts) < 5:
            logger.debug("Skipping malformed ps output row: %r", raw_line)
            continue

        pid = _parse_int(parts[0])
        cpu_pct = _parse_float(parts[1])
        mem_pct = _parse_float(parts[2])
        if pid is None or cpu_pct is None or mem_pct is None:
            # Skip header line cleanly if present without warning
            if parts[0].upper() != "PID":
                logger.warning("Skipping unparseable ps process row: %r", raw_line)
            continue

        procs.append(
            {
                "pid": pid,
                "user": parts[3],
                "command": parts[4].strip() or "unknown",
                "cpu_percent": cpu_pct,
                "mem_percent": mem_pct,
            }
        )
        if len(procs) >= limit:
            break
    return procs


def _collect_live_linux_metrics(cfg: InfraConfig) -> dict[str, Any]:
    """Collect real-time Linux host metrics directly from /proc and system utilities."""
    # CPU utilization over short 150ms sample window
    cpu_pct = 0.0
    try:
        def _stat() -> tuple[int, int]:
            with open("/proc/stat", "r", encoding="utf-8") as fh:
                vals = [int(x) for x in fh.readline().split()[1:]]
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            return sum(vals), idle

        t1, i1 = _stat()
        time.sleep(0.15)
        t2, i2 = _stat()
        dt = max(t2 - t1, 1)
        di = max(i2 - i1, 0)
        cpu_pct = round(100.0 * (dt - di) / dt, 2)
    except Exception:
        cpu_pct = 0.0

    # Memory stats
    mem = {"total_mb": 0.0, "used_mb": 0.0, "available_mb": 0.0, "usage_percent": 0.0}
    try:
        minfo: dict[str, int] = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                k, v = line.split(":", 1)
                minfo[k] = int(v.strip().split()[0])
        total_kb = minfo.get("MemTotal", 0)
        avail_kb = minfo.get("MemAvailable", minfo.get("MemFree", 0))
        used_kb = max(total_kb - avail_kb, 0)
        mem = {
            "total_mb": round(total_kb / 1024.0, 1),
            "used_mb": round(used_kb / 1024.0, 1),
            "available_mb": round(avail_kb / 1024.0, 1),
            "usage_percent": round(100.0 * used_kb / total_kb, 2) if total_kb else 0.0,
        }
    except Exception:
        pass

    # Load average & uptime
    load = {"1m": 0.0, "5m": 0.0, "15m": 0.0}
    uptime_human = "unknown"
    uptime_sec = 0.0
    try:
        parts = Path("/proc/loadavg").read_text(encoding="utf-8").split()
        load = {"1m": float(parts[0]), "5m": float(parts[1]), "15m": float(parts[2])}
    except Exception:
        pass
    try:
        uptime_sec = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
        mins = int(uptime_sec // 60)
        hrs, mins = divmod(mins, 60)
        days, hrs = divmod(hrs, 24)
        uptime_human = f"{days}d {hrs}h {mins}m" if days else f"{hrs}h {mins}m"
    except Exception:
        pass

    # LVM & Root partitions
    disks: list[dict[str, Any]] = []
    seen_devs: set[str] = set()
    for label, path in [
        ("root", Path("/")),
        ("lv_repos", cfg.repo_root),
        ("lv_backups", cfg.backup_root),
        ("lv_logs", cfg.log_root),
    ]:
        if not path.exists():
            continue
        rc, out = _run_cmd(["df", "-BM", "--output=source,target,size,used,avail,pcent", str(path)])
        if rc != 0 or len(out.splitlines()) < 2:
            continue
        cols = out.splitlines()[1].split()
        if len(cols) < 6:
            continue
        dev, mnt, sz, used, avail, pct_str = cols[0], cols[1], cols[2], cols[3], cols[4], cols[5]
        if label != "root" and mnt == "/":
            continue
        if label != "root" and dev in seen_devs:
            continue
        total_mb = _parse_float(sz.rstrip("M"))
        used_mb = _parse_float(used.rstrip("M"))
        avail_mb = _parse_float(avail.rstrip("M"))
        usage_pct = _parse_float(pct_str.rstrip("%"))
        if total_mb is None or used_mb is None or avail_mb is None or usage_pct is None:
            logger.warning("Skipping malformed df disk row for %s: %r", path, out.splitlines()[1])
            continue
        seen_devs.add(dev)
        disks.append(
            {
                "name": label,
                "device": dev,
                "mount": mnt,
                "total_mb": total_mb,
                "used_mb": used_mb,
                "avail_mb": avail_mb,
                "usage_percent": usage_pct,
            }
        )

    # Top processes (variable-length comm placed last so spaces/parens never break numeric fields)
    top_procs: list[dict[str, Any]] = []
    rc_ps, out_ps = _run_cmd(["ps", "-eo", "pid=,%cpu=,%mem=,user=,comm=", "--sort=-%cpu"])
    if rc_ps == 0 and out_ps:
        top_procs = _parse_ps_processes(out_ps, limit=6)

    # SSH sessions
    ssh_sessions: list[dict[str, str]] = []
    rc_who, out_who = _run_cmd(["who"])
    if rc_who == 0 and out_who:
        for line in out_who.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                ssh_sessions.append(
                    {
                        "user": parts[0],
                        "tty": parts[1],
                        "started": " ".join(parts[2:4]),
                        "host": parts[4].strip("()") if len(parts) > 4 else "local",
                    }
                )

    def _svc_state(names: list[str]) -> str:
        for name in names:
            rc_s, out_s = _run_cmd(["systemctl", "is-active", name])
            if rc_s == 0 and out_s == "active":
                return "active"
            rc_p, _ = _run_cmd(["pgrep", "-x", name])
            if rc_p == 0:
                return "active"
        return "inactive"

    services = {
        "cron": _svc_state(["cron", "crond"]),
        "ssh": _svc_state(["ssh", "sshd"]),
        "devcompany_lvm_loop": _svc_state(["devcompany-lvm-loop"]),
        "devcompany_dashboard": "active",
        "cron_config_present": cfg.cron_file.is_file(),
    }

    alerts: list[dict[str, str]] = []
    if cpu_pct > 80.0:
        alerts.append({"level": "ALERT", "metric": "cpu", "message": f"High CPU usage: {cpu_pct}% (>80%)"})
    for d in disks:
        if d["usage_percent"] > 85.0:
            alerts.append(
                {
                    "level": "ALERT",
                    "metric": f"disk:{d['name']}",
                    "message": f"High disk usage on {d['mount']}: {d['usage_percent']}% (>85%)",
                }
            )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "kernel": platform.release(),
        "uptime": uptime_human,
        "uptime_seconds": round(uptime_sec, 1),
        "cpu_percent": cpu_pct,
        "load_average": load,
        "memory": mem,
        "disks": disks,
        "top_processes": top_procs,
        "ssh_sessions": ssh_sessions,
        "active_developers_online": len({s["user"] for s in ssh_sessions if re.match(r"^dev\d{2}$", s["user"])}),
        "services": services,
        "alerts": alerts,
    }


def _get_telemetry(cfg: InfraConfig, history: deque[dict[str, Any]]) -> dict[str, Any]:
    cached = _read_json_file(cfg.log_root / "health_metrics.json")
    if platform.system() == "Linux" and Path("/proc/stat").exists():
        data = _collect_live_linux_metrics(cfg)
        # Merge cached disks if LVM wasn't mounted directly inside test override
        if not data["disks"] and cached and cached.get("disks"):
            data["disks"] = cached["disks"]
    elif cached:
        data = dict(cached)
    else:
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hostname": socket.gethostname(),
            "kernel": platform.platform(),
            "uptime": "unprovisioned",
            "uptime_seconds": 0,
            "cpu_percent": 0.0,
            "load_average": {"1m": 0.0, "5m": 0.0, "15m": 0.0},
            "memory": {"total_mb": 0.0, "used_mb": 0.0, "available_mb": 0.0, "usage_percent": 0.0},
            "disks": [],
            "top_processes": [],
            "ssh_sessions": [],
            "active_developers_online": 0,
            "services": {
                "cron": "inactive",
                "ssh": "inactive",
                "devcompany_lvm_loop": "inactive",
                "devcompany_dashboard": "active",
                "cron_config_present": cfg.cron_file.is_file(),
            },
            "alerts": [],
        }

    history.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "cpu": data.get("cpu_percent", 0.0),
            "memory": data.get("memory", {}).get("usage_percent", 0.0),
        }
    )
    data["history"] = list(history)
    data["recent_logs"] = _tail_logs(cfg)
    return data


def _tail_logs(cfg: InfraConfig, limit: int = 12) -> list[str]:
    lines: list[str] = []
    for fname in ("monitor.log", "backup.log", "cleanup.log"):
        fpath = cfg.log_root / fname
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
                lines.extend(f"[{fname}] {line}" for line in content[-4:])
            except Exception:
                pass
    return lines[-limit:]


def _parse_groups(group_file: Path) -> tuple[dict[int, str], dict[str, set[str]]]:
    gid_to_name: dict[int, str] = {}
    user_groups: dict[str, set[str]] = {}
    if not group_file.is_file():
        return gid_to_name, user_groups
    for raw in group_file.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split(":")
        if len(parts) < 4:
            continue
        gname, _, gid_str, members_str = parts[0], parts[1], parts[2], parts[3]
        try:
            gid = int(gid_str)
        except ValueError:
            continue
        gid_to_name[gid] = gname
        for member in [m.strip() for m in members_str.split(",") if m.strip()]:
            user_groups.setdefault(member, set()).add(gname)
    return gid_to_name, user_groups


def _read_shadow_aging(shadow_file: Path) -> dict[str, str]:
    aging: dict[str, str] = {}
    if not shadow_file.is_file():
        return aging
    try:
        for line in shadow_file.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split(":")
            if len(parts) >= 7 and re.match(r"^dev\d{2}$", parts[0]):
                min_d = parts[3] or "7"
                max_d = parts[4] or "90"
                warn_d = parts[5] or "14"
                aging[parts[0]] = f"Max {max_d}d / Min {min_d}d / Warn {warn_d}d"
    except PermissionError:
        pass
    return aging


def _parse_developers(cfg: InfraConfig) -> dict[str, Any]:
    gid_to_name, extra_groups = _parse_groups(cfg.group_file)
    shadow_aging = _read_shadow_aging(cfg.shadow_file)

    developers: list[dict[str, Any]] = []
    summary = {"frontend": 0, "backend": 0, "devops": 0, "techleads": 0}

    if cfg.passwd_file.is_file():
        for raw in cfg.passwd_file.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = raw.split(":")
            if len(parts) < 7:
                continue
            uname, _, uid_str, gid_str, gecos, home, shell = parts[:7]
            if not re.match(r"^dev\d{2}$", uname):
                continue
            try:
                uid = int(uid_str)
                gid = int(gid_str)
            except ValueError:
                continue
            primary_team = gid_to_name.get(gid, "developers")
            all_groups = sorted({primary_team} | extra_groups.get(uname, set()))
            if primary_team not in TEAM_META:
                for candidate in TEAM_META:
                    if candidate in all_groups:
                        primary_team = candidate
                        break

            if primary_team in summary:
                summary[primary_team] += 1

            meta = TEAM_META.get(primary_team, {"sudo_access": "None"})
            ssh_key_path = Path(home) / ".ssh" / "id_ed25519"
            developers.append(
                {
                    "username": uname,
                    "uid": uid,
                    "gid": gid,
                    "team": primary_team,
                    "groups": all_groups,
                    "role": gecos or primary_team,
                    "home": home,
                    "shell": shell,
                    "ssh_key_present": ssh_key_path.is_file(),
                    "password_aging": shadow_aging.get(uname, "Max 90d / Min 7d / Warn 14d"),
                    "sudo_access": meta["sudo_access"],
                }
            )

    developers.sort(key=lambda d: d["username"])
    return {
        "provisioned": len(developers) > 0,
        "total": len(developers),
        "summary": summary,
        "developers": developers,
    }


def _inspect_repos(cfg: InfraConfig) -> dict[str, Any]:
    teams_spec = [
        ("frontend", "frontend"),
        ("backend", "backend"),
        ("devops", "devops"),
        ("shared", "developers"),
    ]
    results: list[dict[str, Any]] = []
    for team_name, expected_group in teams_spec:
        tdir = cfg.repo_root / team_name
        exists = tdir.is_dir()
        mode_octal = "0000"
        sgid = False
        sticky = False
        owner_group = f"root:{expected_group}"
        acl_lines: list[str] = []
        repos: list[dict[str, Any]] = []

        if exists:
            st = tdir.stat()
            mode_bits = stat.S_IMODE(st.st_mode)
            mode_octal = f"{mode_bits:04o}"
            sgid = bool(mode_bits & stat.S_ISGID)
            sticky = bool(mode_bits & stat.S_ISVTX)
            if platform.system() == "Linux":
                rc_s, out_s = _run_cmd(["stat", "-c", "%U:%G", str(tdir)])
                if rc_s == 0 and out_s:
                    owner_group = out_s
                rc_acl, out_acl = _run_cmd(["getfacl", "-p", str(tdir)])
                if rc_acl == 0 and out_acl:
                    acl_lines = [ln for ln in out_acl.splitlines() if ln.strip()]

            for item in sorted(tdir.iterdir()):
                if item.is_dir() and (item.name.endswith(".git") or (item / "HEAD").is_file()):
                    last_commit = "Initialized bare repository"
                    commit_count = 0
                    rc_log, out_log = _run_cmd(
                        ["git", "-C", str(item), "log", "-1", "--pretty=format:%h | %s (%an, %ar)"]
                    )
                    if rc_log == 0 and out_log:
                        last_commit = out_log
                    rc_cnt, out_cnt = _run_cmd(["git", "-C", str(item), "rev-list", "--count", "--all"])
                    if rc_cnt == 0 and out_cnt.isdigit():
                        commit_count = int(out_cnt)
                    repos.append(
                        {
                            "name": item.name,
                            "path": str(item),
                            "commit_count": commit_count,
                            "last_commit": last_commit,
                        }
                    )

        results.append(
            {
                "team": team_name,
                "path": str(tdir),
                "exists": exists,
                "owner_group": owner_group,
                "mode": mode_octal,
                "sgid": sgid,
                "sticky": sticky,
                "repos": repos,
                "acl_lines": acl_lines,
            }
        )
    return {"repo_root": str(cfg.repo_root), "teams": results}


def _verify_sha256(archive: Path, sha_file: Path) -> tuple[str, bool]:
    if not sha_file.is_file():
        return "", False
    try:
        expected = sha_file.read_text(encoding="utf-8").strip().split()[0].lower()
    except Exception:
        return "", False
    h = hashlib.sha256()
    with archive.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return expected, h.hexdigest().lower() == expected


def _inspect_backups_and_cron(cfg: InfraConfig) -> dict[str, Any]:
    backups: list[dict[str, Any]] = []
    if cfg.backup_root.is_dir():
        archives = sorted(
            cfg.backup_root.glob("repos_backup_*.tar.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for arc in archives:
            st = arc.stat()
            sha_file = Path(f"{arc}.sha256")
            digest, valid = _verify_sha256(arc, sha_file)
            backups.append(
                {
                    "filename": arc.name,
                    "path": str(arc),
                    "size_bytes": st.st_size,
                    "size_human": f"{st.st_size / 1024:.1f} KB"
                    if st.st_size < 1024 * 1024
                    else f"{st.st_size / (1024 * 1024):.2f} MB",
                    "created_at": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "sha256": digest,
                    "checksum_valid": valid,
                }
            )

    cron_jobs: list[dict[str, str]] = []
    if cfg.cron_file.is_file():
        for raw in cfg.cron_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" in line.split()[0]:
                continue
            parts = line.split(None, 6)
            if len(parts) >= 7:
                expr = " ".join(parts[:5])
                cron_jobs.append(
                    {
                        "schedule": expr,
                        "human_schedule": _human_cron_schedule(expr),
                        "user": parts[5],
                        "command": parts[6],
                    }
                )

    return {"backup_root": str(cfg.backup_root), "backups": backups, "cron_jobs": cron_jobs}


def _resolve_action_script(cfg: InfraConfig, action: str) -> Path:
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=404, detail=f"Unknown action '{action}'")
    script_name = ALLOWED_ACTIONS[action]["script"]
    candidate = cfg.scripts_dir / script_name
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail=f"Script not found: {candidate}")
    return candidate


def _find_bash() -> str | None:
    if platform.system() == "Windows":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if git_bash.is_file():
            return str(git_bash)
    return shutil.which("bash")


def create_app(config: InfraConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI DevOps dashboard application."""
    cfg = config or InfraConfig.from_env()
    dashboard_dir = Path(__file__).resolve().parent
    history: deque[dict[str, Any]] = deque(maxlen=30)

    app = FastAPI(title="SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard", version="1.0.0")
    static_dir = dashboard_dir / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        html_path = dashboard_dir / "templates" / "index.html"
        return HTMLResponse(html_path.read_text(encoding="utf-8"))

    @app.get("/api/health")
    def api_health() -> dict[str, Any]:
        devs = _parse_developers(cfg)
        return {
            "status": "ok",
            "provisioned": devs["provisioned"],
            "developer_count": devs["total"],
            "os": f"{platform.system()} {platform.release()}",
            "hostname": socket.gethostname(),
            "actions": ALLOWED_ACTIONS,
        }

    @app.get("/api/telemetry")
    def api_telemetry() -> dict[str, Any]:
        return _get_telemetry(cfg, history)

    @app.get("/api/developers")
    def api_developers(
        team: str = Query(default="", description="Filter by team name"),
        q: str = Query(default="", description="Search username or role"),
    ) -> dict[str, Any]:
        data = _parse_developers(cfg)
        items = data["developers"]
        if team:
            items = [d for d in items if d["team"] == team]
        if q:
            needle = q.strip().lower()
            items = [
                d
                for d in items
                if needle in d["username"].lower()
                or needle in d["team"].lower()
                or needle in d["role"].lower()
            ]
        return {
            "provisioned": data["provisioned"],
            "total": len(items),
            "total_provisioned": data["total"],
            "summary": data["summary"],
            "developers": items,
        }

    @app.get("/api/repos")
    def api_repos() -> dict[str, Any]:
        return _inspect_repos(cfg)

    @app.get("/api/backups")
    def api_backups() -> dict[str, Any]:
        return _inspect_backups_and_cron(cfg)

    @app.post("/api/actions/{action}")
    def api_run_action(action: str) -> dict[str, Any]:
        script_path = _resolve_action_script(cfg, action)
        bash_exe = _find_bash()
        if not bash_exe:
            raise HTTPException(status_code=500, detail="bash executable not found on host")

        env = os.environ.copy()
        env["NO_COLOR"] = "1"
        started = time.monotonic()
        proc = subprocess.run(
            [bash_exe, str(script_path)],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        combined = ANSI_RE.sub("", (proc.stdout or "") + (proc.stderr or ""))
        return {
            "action": action,
            "script": script_path.name,
            "exit_code": proc.returncode,
            "duration_ms": duration_ms,
            "output": combined,
        }

    @app.get("/api/actions/{action}/stream")
    def api_stream_action(action: str) -> StreamingResponse:
        script_path = _resolve_action_script(cfg, action)
        bash_exe = _find_bash()
        if not bash_exe:
            raise HTTPException(status_code=500, detail="bash executable not found on host")

        def _event_stream() -> Iterator[str]:
            env = os.environ.copy()
            env["NO_COLOR"] = "1"
            started = time.monotonic()
            yield f"data: {json.dumps({'type': 'start', 'script': script_path.name})}\n\n"
            proc = subprocess.Popen(
                [bash_exe, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
            assert proc.stdout is not None
            for raw_line in proc.stdout:
                clean = ANSI_RE.sub("", raw_line.rstrip("\r\n"))
                yield f"data: {json.dumps({'type': 'log', 'line': clean})}\n\n"
            rc = proc.wait()
            duration_ms = int((time.monotonic() - started) * 1000)
            yield f"data: {json.dumps({'type': 'done', 'exit_code': rc, 'duration_ms': duration_ms})}\n\n"

        return StreamingResponse(_event_stream(), media_type="text/event-stream")

    return app


app = create_app()
