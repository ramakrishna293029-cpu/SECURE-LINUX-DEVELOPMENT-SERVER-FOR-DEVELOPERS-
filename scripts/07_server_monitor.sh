#!/usr/bin/env bash
# 07_server_monitor.sh - Collect CPU, RAM, LVM, process, SSH & service health into JSON + monitor.log with [ALERT] rules.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

ensure_dir "${LOG_ROOT}" 0755

METRICS_JSON="${LOG_ROOT}/health_metrics.json"
MONITOR_LOG="${LOG_ROOT}/monitor.log"
TMP_JSON="$(mktemp "${LOG_ROOT}/.health_metrics.XXXXXX.json")"

python3 - << 'PYEOF' > "${TMP_JSON}"
import json
import math
import os
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone


def parse_int(raw: str):
    try:
        return int(raw.strip())
    except (ValueError, TypeError, AttributeError):
        return None


def parse_float(raw: str):
    try:
        val = float(raw.strip())
    except (ValueError, TypeError, AttributeError):
        return None
    return val if math.isfinite(val) else None


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        return proc.returncode, proc.stdout.strip()
    except Exception:
        return 1, ""


def read_cpu_percent() -> float:
    def _stat() -> tuple[int, int]:
        with open("/proc/stat", "r", encoding="utf-8") as fh:
            parts = fh.readline().split()[1:]
        nums = [int(x) for x in parts]
        idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
        return sum(nums), idle

    try:
        t1, i1 = _stat()
        time.sleep(0.35)
        t2, i2 = _stat()
        dt = max(t2 - t1, 1)
        di = max(i2 - i1, 0)
        return round(100.0 * (dt - di) / dt, 2)
    except Exception:
        return 0.0


def read_memory() -> dict:
    info: dict[str, int] = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                key, val = line.split(":", 1)
                num = int(val.strip().split()[0])
                info[key] = num
        total_kb = info.get("MemTotal", 0)
        avail_kb = info.get("MemAvailable", info.get("MemFree", 0))
        used_kb = max(total_kb - avail_kb, 0)
        pct = round(100.0 * used_kb / total_kb, 2) if total_kb else 0.0
        return {
            "total_mb": round(total_kb / 1024.0, 1),
            "used_mb": round(used_kb / 1024.0, 1),
            "available_mb": round(avail_kb / 1024.0, 1),
            "usage_percent": pct,
        }
    except Exception:
        return {"total_mb": 0.0, "used_mb": 0.0, "available_mb": 0.0, "usage_percent": 0.0}


def read_load_and_uptime() -> tuple[dict, str, float]:
    load = {"1m": 0.0, "5m": 0.0, "15m": 0.0}
    try:
        with open("/proc/loadavg", "r", encoding="utf-8") as fh:
            parts = fh.read().split()
        load = {"1m": float(parts[0]), "5m": float(parts[1]), "15m": float(parts[2])}
    except Exception:
        pass

    uptime_sec = 0.0
    uptime_human = "unknown"
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as fh:
            uptime_sec = float(fh.read().split()[0])
        mins = int(uptime_sec // 60)
        hrs, mins = divmod(mins, 60)
        days, hrs = divmod(hrs, 24)
        uptime_human = f"{days}d {hrs}h {mins}m" if days else f"{hrs}h {mins}m"
    except Exception:
        pass
    return load, uptime_human, round(uptime_sec, 1)


def read_disks() -> list[dict]:
    targets = [
        ("root", "/"),
        ("lv_repos", "/srv/dev_repos"),
        ("lv_backups", "/srv/dev_backups"),
        ("lv_logs", "/var/log/dev_company"),
    ]
    disks: list[dict] = []
    seen_devs: set[str] = set()
    for label, path in targets:
        if not os.path.exists(path):
            continue
        rc, out = run_cmd(["df", "-BM", "--output=source,target,size,used,avail,pcent", path])
        if rc != 0 or len(out.splitlines()) < 2:
            usage = shutil.disk_usage(path)
            pct = round(100.0 * usage.used / usage.total, 1) if usage.total else 0.0
            disks.append(
                {
                    "name": label,
                    "device": "unknown",
                    "mount": path,
                    "total_mb": round(usage.total / (1024 * 1024), 1),
                    "used_mb": round(usage.used / (1024 * 1024), 1),
                    "avail_mb": round(usage.free / (1024 * 1024), 1),
                    "usage_percent": pct,
                }
            )
            continue
        cols = out.splitlines()[1].split()
        if len(cols) < 6:
            continue
        dev, mnt, sz, used, avail, pct_str = cols[0], cols[1], cols[2], cols[3], cols[4], cols[5]
        if label != "root" and mnt == "/":
            # Directory exists on root FS because LVM LV is not mounted yet
            continue
        if label != "root" and dev in seen_devs:
            continue
        total_mb = parse_float(sz.rstrip("M"))
        used_mb = parse_float(used.rstrip("M"))
        avail_mb = parse_float(avail.rstrip("M"))
        usage_pct = parse_float(pct_str.rstrip("%"))
        if total_mb is None or used_mb is None or avail_mb is None or usage_pct is None:
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
    return disks


def read_top_processes() -> list[dict]:
    rc, out = run_cmd(["ps", "-eo", "pid=,%cpu=,%mem=,user=,comm=", "--sort=-%cpu"])
    procs: list[dict] = []
    if rc == 0 and out:
        for raw_line in out.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            pid = parse_int(parts[0])
            cpu_pct = parse_float(parts[1])
            mem_pct = parse_float(parts[2])
            if pid is None or cpu_pct is None or mem_pct is None:
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
            if len(procs) >= 6:
                break
    return procs


def read_active_ssh_sessions() -> list[dict]:
    sessions: list[dict] = []
    rc, out = run_cmd(["who"])
    if rc == 0 and out:
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                sessions.append(
                    {
                        "user": parts[0],
                        "tty": parts[1],
                        "started": " ".join(parts[2:4]),
                        "host": parts[4].strip("()") if len(parts) > 4 else "local",
                    }
                )
    return sessions


def check_service(candidates: list[str]) -> str:
    for svc in candidates:
        rc, out = run_cmd(["systemctl", "is-active", svc])
        if rc == 0 and out == "active":
            return "active"
        rc_p, _ = run_cmd(["pgrep", "-x", svc])
        if rc_p == 0:
            return "active"
    return "inactive"


cpu_pct = read_cpu_percent()
mem = read_memory()
load, uptime_human, uptime_sec = read_load_and_uptime()
disks = read_disks()
top_procs = read_top_processes()
ssh_sessions = read_active_ssh_sessions()

services = {
    "cron": check_service(["cron", "crond"]),
    "ssh": check_service(["ssh", "sshd"]),
    "devcompany_lvm_loop": check_service(["devcompany-lvm-loop"]),
    "devcompany_dashboard": check_service(["devcompany-dashboard"]),
    "cron_config_present": os.path.isfile("/etc/cron.d/devcompany_automation"),
}

alerts: list[dict] = []
if cpu_pct > 80.0:
    alerts.append(
        {
            "level": "ALERT",
            "metric": "cpu",
            "message": f"[ALERT] High CPU utilization: {cpu_pct}% (threshold > 80%)",
        }
    )
for d in disks:
    if d["usage_percent"] > 85.0:
        alerts.append(
            {
                "level": "ALERT",
                "metric": f"disk:{d['name']}",
                "message": f"[ALERT] High disk usage on {d['mount']} ({d['name']}): {d['usage_percent']}% (threshold > 85%)",
            }
        )

payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "hostname": socket.gethostname(),
    "kernel": os.uname().release if hasattr(os, "uname") else "unknown",
    "uptime": uptime_human,
    "uptime_seconds": uptime_sec,
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

print(json.dumps(payload, indent=2))
PYEOF

mv -f "${TMP_JSON}" "${METRICS_JSON}"
chmod 0644 "${METRICS_JSON}"

# Append concise summary + any [ALERT] lines to monitor.log
python3 - "${METRICS_JSON}" "${MONITOR_LOG}" << 'PYEOF'
import json
import sys

metrics_path, log_path = sys.argv[1], sys.argv[2]
with open(metrics_path, "r", encoding="utf-8") as fh:
    data = json.load(fh)

disk_summary = ", ".join(f"{d['name']}={d['usage_percent']}%" for d in data.get("disks", [])) or "none"
line = (
    f"[{data['local_time']}] CPU={data['cpu_percent']}% "
    f"LOAD={data['load_average']['1m']}/{data['load_average']['5m']}/{data['load_average']['15m']} "
    f"RAM={data['memory']['usage_percent']}% ({data['memory']['used_mb']}/{data['memory']['total_mb']}MB) "
    f"DISKS=[{disk_summary}] SSH_SESSIONS={len(data.get('ssh_sessions', []))} "
    f"CRON={data['services']['cron']} SSH={data['services']['ssh']}\n"
)

with open(log_path, "a", encoding="utf-8") as out:
    out.write(line)
    for alert in data.get("alerts", []):
        out.write(f"[{data['local_time']}] {alert['message']}\n")
PYEOF

log_ok "Telemetry snapshot written to ${METRICS_JSON} and appended to ${MONITOR_LOG}."
