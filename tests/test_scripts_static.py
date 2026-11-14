import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
SYSTEMD_DIR = ROOT / "systemd"

BASH_EXE = (
    r"C:\Program Files\Git\bin\bash.exe"
    if Path(r"C:\Program Files\Git\bin\bash.exe").exists()
    else shutil.which("bash")
)

EXPECTED_SCRIPTS = [
    "lib/common.sh",
    "00_master_setup.sh",
    "01_install_packages.sh",
    "02_setup_lvm_storage.sh",
    "extend_lvm_demo.sh",
    "03_provision_40_devs.sh",
    "04_setup_shared_repos.sh",
    "05_cleanup_system.sh",
    "06_backup_manager.sh",
    "07_server_monitor.sh",
    "08_configure_cron.sh",
    "99_verify_and_demo.sh",
    "00_teardown.sh",
]

EXPECTED_SYSTEMD_UNITS = [
    "devcompany-lvm-loop.service",
    "devcompany-dashboard.service",
]


@pytest.mark.parametrize("rel_path", EXPECTED_SCRIPTS)
def test_script_exists_and_valid_bash(rel_path: str) -> None:
    script = SCRIPTS_DIR / rel_path
    assert script.is_file(), f"Missing script: {script}"

    raw = script.read_bytes()
    assert b"\r\n" not in raw, f"CRLF line endings found in {rel_path}; Linux Bash requires LF"

    text = raw.decode("utf-8")
    assert text.startswith("#!/usr/bin/env bash") or text.startswith("#!/bin/bash"), (
        f"Missing bash shebang in {rel_path}"
    )
    if rel_path != "lib/common.sh":
        assert "set -euo pipefail" in text, f"Missing 'set -euo pipefail' in {rel_path}"

    assert BASH_EXE is not None, "bash executable not found for syntax check"
    proc = subprocess.run(
        [BASH_EXE, "-n", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"bash -n failed for {rel_path}: {proc.stderr}"


@pytest.mark.parametrize("unit_name", EXPECTED_SYSTEMD_UNITS)
def test_systemd_unit_exists_and_lf(unit_name: str) -> None:
    unit = SYSTEMD_DIR / unit_name
    assert unit.is_file(), f"Missing systemd unit: {unit}"
    raw = unit.read_bytes()
    assert b"\r\n" not in raw, f"CRLF found in {unit_name}"
    text = raw.decode("utf-8")
    assert "[Unit]" in text and "[Service]" in text and "[Install]" in text


def test_01_install_packages_includes_all_required_packages_and_services() -> None:
    content = (SCRIPTS_DIR / "01_install_packages.sh").read_text(encoding="utf-8")
    required_pkgs = [
        "git",
        "gcc",
        "g++",
        "python3",
        "python3-venv",
        "python3-pip",
        "nodejs",
        "npm",
        "build-essential",
        "curl",
        "wget",
        "htop",
        "sysstat",
        "net-tools",
        "acl",
        "lvm2",
        "tree",
        "ufw",
        "cron",
        "openssh-server",
    ]
    for pkg in required_pkgs:
        assert pkg in content, f"Missing package '{pkg}' in 01_install_packages.sh"
    assert "cron" in content and ("ssh" in content or "sshd" in content)


def _with_common(script_name: str) -> str:
    common = (SCRIPTS_DIR / "lib" / "common.sh").read_text(encoding="utf-8")
    body = (SCRIPTS_DIR / script_name).read_text(encoding="utf-8")
    return common + "\n" + body


def test_02_lvm_setup_and_extend_specifications() -> None:
    lvm = _with_common("02_setup_lvm_storage.sh")
    for token in [
        "/var/lvm_disks",
        "disk1.img",
        "disk2.img",
        "losetup",
        "pvcreate",
        "vg_devcompany",
        "lv_repos",
        "lv_backups",
        "lv_logs",
        "/srv/dev_repos",
        "/srv/dev_backups",
        "/var/log/dev_company",
        "/etc/fstab",
        "UUID=",
        "devcompany-lvm-loop.service",
        "nofail",
    ]:
        assert token in lvm, f"Missing '{token}' in 02_setup_lvm_storage.sh (+ common.sh)"

    extend = _with_common("extend_lvm_demo.sh")
    assert "lvextend" in extend
    assert "resize2fs" in extend


def test_03_provision_40_devs_specifications() -> None:
    content = _with_common("03_provision_40_devs.sh")
    for token in [
        "frontend",
        "backend",
        "devops",
        "techleads",
        "developers",
        "chage -M 90 -m 7 -W 14",
        "id_ed25519",
        "/etc/sudoers.d/dev_policies",
        "visudo",
    ]:
        assert token in content, f"Missing '{token}' in 03_provision_40_devs.sh"


def test_04_shared_repos_permissions_and_acls() -> None:
    content = _with_common("04_setup_shared_repos.sh")
    for token in [
        "--bare --shared=group",
        "2775",
        "+t",
        "setfacl",
        "techleads",
        "/srv/dev_repos",
    ]:
        assert token in content, f"Missing '{token}' in 04_setup_shared_repos.sh"


def test_05_06_07_08_operational_scripts() -> None:
    cleanup = _with_common("05_cleanup_system.sh")
    assert "/tmp" in cleanup and "/var/tmp" in cleanup and "-mtime +7" in cleanup
    assert "-mtime +14" in cleanup and "/var/log/dev_company" in cleanup and "cleanup.log" in cleanup

    backup = _with_common("06_backup_manager.sh")
    for token in [
        "repos_backup_",
        ".tar.gz",
        "sha256sum",
        "srv/dev_repos",
        "etc/passwd",
        "etc/group",
        "etc/sudoers.d",
        "-mtime +7",
    ]:
        assert token in backup, f"Missing '{token}' in 06_backup_manager.sh"

    monitor = _with_common("07_server_monitor.sh")
    assert "/var/log/dev_company" in monitor
    assert "health_metrics.json" in monitor
    assert "monitor.log" in monitor
    assert "[ALERT]" in monitor

    cron = _with_common("08_configure_cron.sh")
    for token in [
        "/etc/cron.d/devcompany_automation",
        "*/5 * * * *",
        "0 2 * * *",
        "0 3 * * 0",
    ]:
        assert token in cron, f"Missing '{token}' in 08_configure_cron.sh"


@pytest.mark.parametrize("rel_path", EXPECTED_SCRIPTS)
def test_no_bash_reserved_variable_assignments(rel_path: str) -> None:
    import re

    reserved = (
        "GROUPS",
        "UID",
        "EUID",
        "PPID",
        "SHLVL",
        "BASH_VERSION",
        "FUNCNAME",
        "PIPESTATUS",
        "DIRSTACK",
        "PWD",
        "OLDPWD",
        "RANDOM",
        "SECONDS",
        "LINENO",
    )
    pattern = re.compile(rf"^\s*(?:export\s+|declare\s+(?:-[a-zA-Z]+\s+)?|local\s+|readonly\s+)?({'|'.join(reserved)})\s*\+?=", re.MULTILINE)
    text = (SCRIPTS_DIR / rel_path).read_text(encoding="utf-8")
    matches = pattern.findall(text)
    assert not matches, f"Bash reserved variable assignment(s) {matches} found in {rel_path}"


def test_03_team_groups_and_ranges_in_bash() -> None:
    assert BASH_EXE is not None, "bash executable not found"
    script_text = (SCRIPTS_DIR / "03_provision_40_devs.sh").read_text(encoding="utf-8")
    assert "TEAM_GROUPS=(" in script_text, "Expected TEAM_GROUPS array in 03_provision_40_devs.sh"

    # Extract TEAM_GROUPS definition and team_for_index function and run them in real bash
    bash_probe = """
set -euo pipefail
eval "$(awk '/^TEAM_GROUPS=\\(/,/^\\)/' "$1")"
eval "$(awk '/^team_for_index\\(\\)/,/^\\}/' "$1")"
printf 'GROUPS=%s\\n' "${TEAM_GROUPS[*]}"
for i in $(seq 1 40); do
    printf '%02d:%s\\n' "$i" "$(team_for_index "$i")"
done
"""
    proc = subprocess.run(
        [BASH_EXE, "-c", bash_probe, "probe", str(SCRIPTS_DIR / "03_provision_40_devs.sh")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Bash probe failed: {proc.stderr}"
    lines = proc.stdout.strip().splitlines()
    assert lines[0] == "GROUPS=developers frontend backend devops techleads"

    counts = {"frontend": 0, "backend": 0, "devops": 0, "techleads": 0}
    for row in lines[1:]:
        idx_s, team = row.split(":")
        counts[team] += 1
        idx = int(idx_s)
        if idx <= 12:
            assert team == "frontend"
        elif idx <= 26:
            assert team == "backend"
        elif idx <= 34:
            assert team == "devops"
        else:
            assert team == "techleads"
    assert counts == {"frontend": 12, "backend": 14, "devops": 8, "techleads": 6}


def test_03_provision_40_devs_end_to_end_idempotent_simulation(tmp_path: Path) -> None:
    """Execute 03_provision_40_devs.sh twice in real bash with stubbed Linux account commands."""
    assert BASH_EXE is not None, "bash executable not found"

    def to_posix(p: Path) -> str:
        res = subprocess.run(
            [BASH_EXE, "-c", f'cygpath -u "{p.as_posix()}"'],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    state_dir = tmp_path / "state"
    bin_dir = tmp_path / "bin"
    home_root = tmp_path / "home"
    sudoers_target = tmp_path / "etc_sudoers_d" / "dev_policies"
    for d in (state_dir, bin_dir, home_root, sudoers_target.parent):
        d.mkdir(parents=True, exist_ok=True)

    state_u = to_posix(state_dir)
    bin_u = to_posix(bin_dir)
    home_u = to_posix(home_root)
    sudoers_u = to_posix(sudoers_target)

    # Pre-seed partial state: 'developers' group and 'dev01' exist without .ssh
    (state_dir / "groups").write_text("developers\n", encoding="utf-8", newline="\n")
    (state_dir / "users").write_text(f"dev01|frontend|{home_u}/dev01\n", encoding="utf-8", newline="\n")
    (home_root / "dev01").mkdir(parents=True, exist_ok=True)
    (state_dir / "calls.log").write_text("", encoding="utf-8", newline="\n")

    def write_stub(name: str, body: str) -> None:
        p = bin_dir / name
        p.write_text("#!/bin/bash\nset -euo pipefail\n" + body, encoding="utf-8", newline="\n")
        p.chmod(0o755)

    write_stub("getent", f"""
db="$1"; key="$2"
if [[ "$db" == "group" ]]; then
    grep -qxF "$key" "{state_u}/groups"
elif [[ "$db" == "passwd" ]]; then
    row="$(grep -E "^${{key}}\\|" "{state_u}/users" | head -n1 || true)"
    [[ -n "$row" ]] || exit 2
    IFS='|' read -r u t h <<< "$row"
    printf '%s:x:3001:2001::%s:/bin/bash\\n' "$u" "$h"
fi
""")
    write_stub("groupadd", f"""
grp="$1"
printf 'groupadd:%s\\n' "$grp" >> "{state_u}/calls.log"
printf '%s\\n' "$grp" >> "{state_u}/groups"
""")
    write_stub("id", f"""
grep -qE "^$1\\|" "{state_u}/users"
""")
    write_stub("useradd", f"""
u="${{@: -1}}"
team=""
while [[ $# -gt 1 ]]; do
    if [[ "$1" == "-g" ]]; then team="$2"; shift 2; else shift; fi
done
grep -qxF "$team" "{state_u}/groups" || {{ echo "useradd: group '$team' does not exist" >&2; exit 6; }}
h="{home_u}/$u"
mkdir -p "$h"
printf '%s|%s|%s\\n' "$u" "$team" "$h" >> "{state_u}/users"
printf 'useradd:%s:%s\\n' "$u" "$team" >> "{state_u}/calls.log"
""")
    write_stub("usermod", f"""
u="${{@: -1}}"
printf 'usermod:%s\\n' "$u" >> "{state_u}/calls.log"
""")
    write_stub("chpasswd", f"""
line="$(cat)"
printf 'chpasswd:%s\\n' "${{line%%:*}}" >> "{state_u}/calls.log"
""")
    write_stub("chage", f"""
u="${{@: -1}}"
printf 'chage:%s\\n' "$u" >> "{state_u}/calls.log"
""")
    write_stub("ssh-keygen", f"""
key_out=""
while [[ $# -gt 0 ]]; do
    if [[ "$1" == "-f" ]]; then key_out="$2"; shift 2; else shift; fi
done
printf 'PRIVATE-KEY\\n' > "$key_out"
dev_name="$(basename "$(dirname "$(dirname "$key_out")")")"
printf 'ssh-ed25519 AAAA_MOCK_%s %s@devcompany.local\\n' "$dev_name" "$dev_name" > "${{key_out}}.pub"
printf 'ssh-keygen:%s\\n' "$key_out" >> "{state_u}/calls.log"
""")
    write_stub("chown", "exit 0\n")
    write_stub("visudo", """
if [[ "$1" == "-cf" && -f "$2" ]]; then
    grep -q '%techleads' "$2" && grep -q '%devops' "$2"
    printf '%s: parsed OK\\n' "$2"
fi
""")
    write_stub("install", f"""
src="${{@: -2:1}}"
cp -f "$src" "{sudoers_u}"
printf 'install:%s\\n' "{sudoers_u}" >> "{state_u}/calls.log"
""")

    # Create a runnable wrapper script that loads real common.sh, stubs require_root for non-root test sandbox, and runs 03_provision_40_devs.sh logic
    common_text = (SCRIPTS_DIR / "lib" / "common.sh").read_text(encoding="utf-8")
    prov_lines = (SCRIPTS_DIR / "03_provision_40_devs.sh").read_text(encoding="utf-8").splitlines()
    # Replace only the source line & require_root call inside the test copy so real logic runs verbatim
    filtered_lines = [
        ln for ln in prov_lines
        if not ln.startswith("source ") and ln.strip() != "require_root"
    ]
    harness_script = tmp_path / "run_03_test.sh"
    harness_script.write_text(
        'export NO_COLOR=1\n'
        + common_text + "\n"
        + f'export SUDOERS_FILE="{sudoers_u}"\n'
        + "\n".join(filtered_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    harness_u = to_posix(harness_script)
    env_cmd = f'export PATH="{bin_u}:$PATH"; bash "{harness_u}"'
    run1 = subprocess.run([BASH_EXE, "-c", env_cmd], capture_output=True, text=True, check=False)
    assert run1.returncode == 0, f"Run 1 failed:\n{run1.stdout}\n{run1.stderr}"

    groups_created = (state_dir / "groups").read_text(encoding="utf-8").splitlines()
    assert groups_created == ["developers", "frontend", "backend", "devops", "techleads"]
    assert "0" not in groups_created

    users_created = (state_dir / "users").read_text(encoding="utf-8").splitlines()
    assert len(users_created) == 40
    assert sudoers_target.is_file()

    # Check every dev01..dev40 has exactly 1 authorized_keys line and id_ed25519 key pair
    for i in range(1, 41):
        ssh_d = home_root / f"dev{i:02d}" / ".ssh"
        assert (ssh_d / "id_ed25519").is_file()
        assert (ssh_d / "id_ed25519.pub").is_file()
        auth_lines = (ssh_d / "authorized_keys").read_text(encoding="utf-8").splitlines()
        assert len(auth_lines) == 1

    # Run 2: clear call log and re-run to assert full idempotency
    (state_dir / "calls.log").write_text("", encoding="utf-8")
    run2 = subprocess.run([BASH_EXE, "-c", env_cmd], capture_output=True, text=True, check=False)
    assert run2.returncode == 0, f"Run 2 (idempotent rerun) failed:\n{run2.stdout}\n{run2.stderr}"

    calls2 = (state_dir / "calls.log").read_text(encoding="utf-8").splitlines()
    assert not any(c.startswith("groupadd:") for c in calls2), f"Duplicate groupadd on rerun: {calls2}"
    assert not any(c.startswith("useradd:") for c in calls2), f"Duplicate useradd on rerun: {calls2}"
    assert not any(c.startswith("chpasswd:") for c in calls2), f"Password reset on rerun: {calls2}"
    assert not any(c.startswith("ssh-keygen:") for c in calls2), f"Duplicate ssh-keygen on rerun: {calls2}"
    for i in range(1, 41):
        auth_lines = (home_root / f"dev{i:02d}" / ".ssh" / "authorized_keys").read_text(encoding="utf-8").splitlines()
        assert len(auth_lines) == 1, f"Duplicate authorized_keys on dev{i:02d}"
