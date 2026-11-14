#!/usr/bin/env bash
# 04_setup_shared_repos.sh - Create team Git repositories with SGID (2775), Sticky Bit (+t), and POSIX ACL oversight.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_root
log_step "Step 04: Configuring Shared Team Git Repositories, SGID/Sticky Bits & ACLs"

for cmd in git setfacl getfacl; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        log_err "Required command '${cmd}' not found. Run 01_install_packages.sh first."
        exit 1
    fi
done

ensure_dir "${REPO_ROOT}" 0755
chown root:developers "${REPO_ROOT}"

# Allow root and dashboard inspection tools to read bare repositories owned by team groups
if ! git config --system --get-all safe.directory 2>/dev/null | grep -qx '\*'; then
    git config --system --add safe.directory '*'
fi

# Format: team_subdir|owning_group|repo_name|description
TEAM_REPO_SPECS=(
    "frontend|frontend|web-portal.git|Customer Web Portal & Design System"
    "backend|backend|core-api.git|Core Microservices & REST/gRPC APIs"
    "devops|devops|infra-automation.git|CI/CD Pipelines, Terraform & Server Configs"
    "shared|developers|company-docs.git|Cross-Team Architecture RFCs & Runbooks"
)

seed_initial_commit() {
    local bare_repo="$1"
    local repo_title="$2"
    local team_group="$3"

    if git -C "${bare_repo}" rev-parse --verify HEAD >/dev/null 2>&1; then
        return 0
    fi

    local work_tmp
    work_tmp="$(mktemp -d)"
    git -C "${work_tmp}" init -q -b main
    git -C "${work_tmp}" config user.name "DevCompany Infra Bot"
    git -C "${work_tmp}" config user.email "infra@devcompany.local"
    cat << EOF > "${work_tmp}/README.md"
# ${repo_title}

- **Team Group:** \`${team_group}\`
- **Repository Path:** \`${bare_repo}\`
- **Permissions:** SGID (\`2775\`) + Sticky Bit (\`+t\`) + POSIX ACL Oversight (\`techleads:rwx\`)
EOF
    git -C "${work_tmp}" add README.md
    git -C "${work_tmp}" commit -q -m "chore: initialize ${repo_title}"
    git -C "${bare_repo}" fetch -q "${work_tmp}" main:main
    git -C "${bare_repo}" symbolic-ref HEAD refs/heads/main
    rm -rf "${work_tmp}"
}

for spec in "${TEAM_REPO_SPECS[@]}"; do
    IFS='|' read -r subdir team_group repo_name repo_desc <<< "${spec}"
    team_dir="${REPO_ROOT}/${subdir}"
    repo_dir="${team_dir}/${repo_name}"

    ensure_dir "${team_dir}" 0755
    chown "root:${team_group}" "${team_dir}"

    if [[ -f "${repo_dir}/HEAD" ]]; then
        log_info "Bare Git repository already initialized: ${repo_dir}"
    else
        log_info "Initializing bare shared Git repo: ${repo_dir}"
        git init --bare --shared=group "${repo_dir}" >/dev/null
    fi

    seed_initial_commit "${repo_dir}" "${repo_desc}" "${team_group}"

    # Apply group ownership and enterprise permission model:
    # 2775 = SGID (group inheritance) + rwxrwxr-x, plus +t = Sticky Bit (prevents deleting others' files) => 3775
    chown -R "root:${team_group}" "${team_dir}"
    find "${team_dir}" -type d -exec chmod 2775 {} +
    chmod +t "${team_dir}"
    find "${repo_dir}" -type f -exec chmod g+rw,o+r {} +

    # POSIX ACLs: grant techleads full rwx oversight (current & default inherited) on all team repos
    setfacl -R -m "g:techleads:rwx" "${team_dir}"
    setfacl -R -d -m "g:techleads:rwx" "${team_dir}"
    setfacl -R -d -m "g:${team_group}:rwx" "${team_dir}"
    setfacl -R -d -m "o::rx" "${team_dir}"

    log_ok "Configured ${team_dir} (owner=root:${team_group}, mode=$(stat -c '%a' "${team_dir}"), ACL=techleads:rwx)"
done

log_ok "Step 04 complete: Shared bare Git repos, SGID, Sticky Bit, and ACL oversight active."
