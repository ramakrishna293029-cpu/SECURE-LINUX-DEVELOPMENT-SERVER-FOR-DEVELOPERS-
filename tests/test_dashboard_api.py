import hashlib
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dashboard"))


def _build_fixture_env(tmp_path: Path) -> dict[str, Path]:
    log_root = tmp_path / "var" / "log" / "dev_company"
    repo_root = tmp_path / "srv" / "dev_repos"
    backup_root = tmp_path / "srv" / "dev_backups"
    scripts_dir = tmp_path / "scripts"
    cron_file = tmp_path / "etc" / "cron.d" / "devcompany_automation"
    passwd_file = tmp_path / "etc" / "passwd"
    group_file = tmp_path / "etc" / "group"

    for d in [log_root, repo_root, backup_root, scripts_dir, cron_file.parent]:
        d.mkdir(parents=True, exist_ok=True)

    # Synthetic health_metrics.json
    metrics = {
        "timestamp": "2026-11-12T06:00:00+00:00",
        "local_time": "2026-11-12 11:30:00",
        "hostname": "devcompany-test",
        "kernel": "6.18.0-test",
        "uptime": "2h 15m",
        "uptime_seconds": 8100.0,
        "cpu_percent": 24.5,
        "load_average": {"1m": 0.42, "5m": 0.35, "15m": 0.28},
        "memory": {
            "total_mb": 8192.0,
            "used_mb": 2048.0,
            "available_mb": 6144.0,
            "usage_percent": 25.0,
        },
        "disks": [
            {
                "name": "lv_repos",
                "device": "/dev/mapper/vg_devcompany-lv_repos",
                "mount": str(repo_root),
                "total_mb": 1500.0,
                "used_mb": 120.0,
                "avail_mb": 1380.0,
                "usage_percent": 8.0,
            }
        ],
        "top_processes": [
            {"pid": 101, "user": "root", "command": "uvicorn", "cpu_percent": 1.2, "mem_percent": 0.8}
        ],
        "ssh_sessions": [{"user": "dev35", "tty": "pts/0", "started": "2026-11-12 11:20", "host": "10.0.0.5"}],
        "active_developers_online": 1,
        "services": {
            "cron": "active",
            "ssh": "active",
            "devcompany_lvm_loop": "active",
            "devcompany_dashboard": "active",
            "cron_config_present": True,
        },
        "alerts": [],
    }
    (log_root / "health_metrics.json").write_text(json.dumps(metrics), encoding="utf-8")

    # Synthetic /etc/group and /etc/passwd for 40 developers
    group_lines = [
        "developers:x:2000:",
        "frontend:x:2001:",
        "backend:x:2002:",
        "devops:x:2003:",
        "techleads:x:2004:",
    ]
    passwd_lines = []
    dev_members = []
    for i in range(1, 41):
        uname = f"dev{i:02d}"
        dev_members.append(uname)
        gid = 2001 if i <= 12 else 2002 if i <= 26 else 2003 if i <= 34 else 2004
        passwd_lines.append(f"{uname}:x:{3000 + i}:{gid}:Developer {uname}:/home/{uname}:/bin/bash")
    group_lines[0] = "developers:x:2000:" + ",".join(dev_members)
    group_file.write_text("\n".join(group_lines) + "\n", encoding="utf-8")
    passwd_file.write_text("\n".join(passwd_lines) + "\n", encoding="utf-8")

    # Synthetic repo dirs
    for team, repo in [
        ("frontend", "web-portal.git"),
        ("backend", "core-api.git"),
        ("devops", "infra-automation.git"),
        ("shared", "company-docs.git"),
    ]:
        rdir = repo_root / team / repo
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    # Synthetic backup + sha256
    archive = backup_root / "repos_backup_20261112_113000.tar.gz"
    archive.write_bytes(b"mock-tar-gz-payload")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (backup_root / "repos_backup_20261112_113000.tar.gz.sha256").write_text(
        f"{digest}  repos_backup_20261112_113000.tar.gz\n",
        encoding="utf-8",
    )

    # Synthetic cron file
    cron_file.write_text(
        "SHELL=/bin/bash\n"
        "*/5 * * * * root /opt/devcompany/scripts/07_server_monitor.sh >/dev/null 2>&1\n"
        "0 2 * * * root /opt/devcompany/scripts/06_backup_manager.sh >> /var/log/dev_company/cron.log 2>&1\n"
        "0 3 * * 0 root /opt/devcompany/scripts/05_cleanup_system.sh >> /var/log/dev_company/cron.log 2>&1\n",
        encoding="utf-8",
    )

    return {
        "log_root": log_root,
        "repo_root": repo_root,
        "backup_root": backup_root,
        "scripts_dir": scripts_dir,
        "cron_file": cron_file,
        "passwd_file": passwd_file,
        "group_file": group_file,
    }


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    from app import InfraConfig, create_app  # noqa: E402

    paths = _build_fixture_env(tmp_path)
    cfg = InfraConfig(
        project_root=tmp_path,
        scripts_dir=paths["scripts_dir"],
        log_root=paths["log_root"],
        repo_root=paths["repo_root"],
        backup_root=paths["backup_root"],
        cron_file=paths["cron_file"],
        passwd_file=paths["passwd_file"],
        group_file=paths["group_file"],
    )
    app = create_app(cfg)
    return TestClient(app)


def test_root_serves_html_dashboard(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "DevCompany" in resp.text
    assert "app.js" in resp.text


def test_health_and_telemetry_endpoints(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    hdata = health.json()
    assert hdata["status"] == "ok"
    assert hdata["provisioned"] is True

    tel = client.get("/api/telemetry")
    assert tel.status_code == 200
    tdata = tel.json()
    assert "cpu_percent" in tdata
    assert "memory" in tdata
    assert "disks" in tdata
    assert "history" in tdata
    assert isinstance(tdata["history"], list)


def test_developers_directory_and_filtering(client: TestClient) -> None:
    resp = client.get("/api/developers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 40
    assert data["summary"]["frontend"] == 12
    assert data["summary"]["backend"] == 14
    assert data["summary"]["devops"] == 8
    assert data["summary"]["techleads"] == 6

    fe = client.get("/api/developers?team=frontend")
    assert fe.status_code == 200
    assert fe.json()["total"] == 12

    search = client.get("/api/developers?q=dev35")
    assert search.status_code == 200
    items = search.json()["developers"]
    assert len(items) == 1
    assert items[0]["team"] == "techleads"
    assert items[0]["sudo_access"] != "None"

    junior = client.get("/api/developers?q=dev01").json()["developers"][0]
    assert junior["sudo_access"] == "None"


def test_repos_and_backups_endpoints(client: TestClient) -> None:
    repos = client.get("/api/repos")
    assert repos.status_code == 200
    rdata = repos.json()
    assert len(rdata["teams"]) == 4
    names = {item["team"] for item in rdata["teams"]}
    assert names == {"frontend", "backend", "devops", "shared"}

    backups = client.get("/api/backups")
    assert backups.status_code == 200
    bdata = backups.json()
    assert len(bdata["backups"]) == 1
    assert bdata["backups"][0]["checksum_valid"] is True
    assert len(bdata["cron_jobs"]) == 3


def test_unknown_action_rejected(client: TestClient) -> None:
    resp = client.post("/api/actions/rm_rf_everything")
    assert resp.status_code == 404


def test_static_js_and_action_execution(tmp_path: Path) -> None:
    from app import InfraConfig, create_app  # noqa: E402

    paths = _build_fixture_env(tmp_path)
    (paths["scripts_dir"] / "06_backup_manager.sh").write_text(
        "#!/usr/bin/env bash\necho 'BACKUP_TEST_OK'\n",
        encoding="utf-8",
        newline="\n",
    )
    cfg = InfraConfig(
        project_root=tmp_path,
        scripts_dir=paths["scripts_dir"],
        log_root=paths["log_root"],
        repo_root=paths["repo_root"],
        backup_root=paths["backup_root"],
        cron_file=paths["cron_file"],
        passwd_file=paths["passwd_file"],
        group_file=paths["group_file"],
    )
    tc = TestClient(create_app(cfg))

    js_resp = tc.get("/static/app.js")
    assert js_resp.status_code == 200
    assert "triggerAction" in js_resp.text

    post_resp = tc.post("/api/actions/backup")
    assert post_resp.status_code == 200
    pdata = post_resp.json()
    assert pdata["exit_code"] == 0
    assert "BACKUP_TEST_OK" in pdata["output"]

    stream_resp = tc.get("/api/actions/backup/stream")
    assert stream_resp.status_code == 200
    assert "BACKUP_TEST_OK" in stream_resp.text
    assert '"type": "done"' in stream_resp.text


def test_parse_ps_processes_handles_spaces_parens_and_malformed_rows() -> None:
    from app import _parse_ps_processes  # noqa: E402

    raw_ps = "\n".join(
        [
            "  PID  %CPU %MEM USER     COMMAND",
            " 4120  18.4  4.2 devadmin Isolated Web Co",
            " 2201   5.1  2.0 devadmin Web Content (Parent)",
            " 1011   1.2  0.5 root     (sd-pam)",
            "  889   0.4  0.1 root     kworker/u16:3-events_unbound",
            "  bad   9.9  1.0 root     invalid-pid",
            "  500   NaN  1.0 root     nan-cpu",
            "  501   1.0  inf root     inf-mem",
            "  502   -    -   root     dash-values",
            "  short 1.0",
            " 3300   0.3  0.8 devops   gnome-shell (wayland) [gpu]",
            " 3301   0.2  0.4 www-data uvicorn --host 0.0.0.0",
            " 3302   0.1  0.1 root     should-be-sliced-by-limit",
        ]
    )

    procs = _parse_ps_processes(raw_ps, limit=6)
    assert len(procs) == 6
    assert procs[0] == {
        "pid": 4120,
        "user": "devadmin",
        "command": "Isolated Web Co",
        "cpu_percent": 18.4,
        "mem_percent": 4.2,
    }
    assert procs[1]["command"] == "Web Content (Parent)"
    assert procs[2]["command"] == "(sd-pam)"
    assert procs[3]["command"] == "kworker/u16:3-events_unbound"
    assert procs[4]["command"] == "gnome-shell (wayland) [gpu]"
    assert procs[5]["command"] == "uvicorn --host 0.0.0.0"


def test_collect_live_linux_metrics_resilient_to_spaces_and_bad_df(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import app as app_mod  # noqa: E402

    paths = _build_fixture_env(tmp_path)
    cfg = app_mod.InfraConfig(
        project_root=tmp_path,
        scripts_dir=paths["scripts_dir"],
        log_root=paths["log_root"],
        repo_root=paths["repo_root"],
        backup_root=paths["backup_root"],
        cron_file=paths["cron_file"],
        passwd_file=paths["passwd_file"],
        group_file=paths["group_file"],
    )

    def fake_run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
        if cmd and cmd[0] == "ps":
            assert cmd[:3] == ["ps", "-eo", "pid=,%cpu=,%mem=,user=,comm="]
            return 0, (
                " 9001  22.5  3.1 devadmin Isolated Web Co\n"
                " 9002   4.0  1.2 root     (sd-pam)\n"
                " 9003  oops  1.0 root     corrupted-row\n"
            )
        if cmd and cmd[0] == "df":
            target = cmd[-1]
            if target == str(cfg.repo_root):
                return 0, "Filesystem Mounted on 1M-blocks Used Avail Use%\n/dev/mapper/vg-lv_repos /srv/dev_repos 1500M 120M 1380M 8%\n"
            return 0, "Filesystem Mounted on 1M-blocks Used Avail Use%\nnone / - - - -\n"
        if cmd and cmd[0] == "who":
            return 0, "dev01 pts/0 2026-11-12 18:00 (10.0.0.2)\n"
        if cmd and cmd[0] == "systemctl":
            return 0, "active"
        return 1, ""

    monkeypatch.setattr(app_mod, "_run_cmd", fake_run_cmd)

    # Mock Linux host checks cleanly for /api/telemetry end-to-end execution
    monkeypatch.setattr(app_mod.platform, "system", lambda: "Linux")
    orig_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if str(self).replace("\\", "/") in ("/proc/stat", "/"):
            return True
        return orig_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)

    metrics = app_mod._collect_live_linux_metrics(cfg)
    assert metrics["top_processes"] == [
        {"pid": 9001, "user": "devadmin", "command": "Isolated Web Co", "cpu_percent": 22.5, "mem_percent": 3.1},
        {"pid": 9002, "user": "root", "command": "(sd-pam)", "cpu_percent": 4.0, "mem_percent": 1.2},
    ]
    assert metrics["active_developers_online"] == 1
    assert any(d["name"] == "lv_repos" and d["usage_percent"] == 8.0 for d in metrics["disks"])

    tc = TestClient(app_mod.create_app(cfg))
    resp = tc.get("/api/telemetry")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["top_processes"][0]["command"] == "Isolated Web Co"


def test_monitor_script_uses_safe_ps_column_order() -> None:
    monitor_text = (ROOT / "scripts" / "07_server_monitor.sh").read_text(encoding="utf-8")
    assert "pid=,%cpu=,%mem=,user=,comm=" in monitor_text
    assert "pid,user,comm,%cpu,%mem" not in monitor_text
