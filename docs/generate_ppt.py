#!/usr/bin/env python3
"""Generate the 15-slide DevCompany Linux Hackathon PowerPoint deck using python-pptx."""

from __future__ import annotations

import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# Dark Corporate Engineering Palette
BG_DARK = RGBColor(0x0B, 0x11, 0x20)
CARD_BG = RGBColor(0x13, 0x1C, 0x31)
CARD_ALT = RGBColor(0x18, 0x24, 0x3D)
BORDER_CLR = RGBColor(0x28, 0x38, 0x57)

CYAN = RGBColor(0x22, 0xD3, 0xEE)
EMERALD = RGBColor(0x34, 0xD3, 0x99)
AMBER = RGBColor(0xFB, 0xBF, 0x24)
INDIGO = RGBColor(0x81, 0x8C, 0xF8)
ROSE = RGBColor(0xFB, 0x71, 0x85)

TEXT_PRIMARY = RGBColor(0xF8, 0xFA, 0xFC)
TEXT_BODY = RGBColor(0xCB, 0xD5, 0xE1)
TEXT_MUTED = RGBColor(0x94, 0xA3, 0xB8)

FONT_HEAD = "Segoe UI"
FONT_MONO = "Consolas"


def set_bg(slide, color: RGBColor = BG_DARK) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, slide_num: int, category: str, title: str, subtitle: str = "") -> None:
    # Top accent bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN
    bar.line.fill.background()

    # Category pill text
    cat_box = slide.shapes.add_textbox(Inches(0.65), Inches(0.28), Inches(6.0), Inches(0.32))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0
    p_c = tf_c.paragraphs[0]
    p_c.text = f"{category.upper()}  |  SLIDE {slide_num:02d} OF 15"
    p_c.font.name = FONT_HEAD
    p_c.font.size = Pt(11)
    p_c.font.bold = True
    p_c.font.color.rgb = CYAN

    # Slide title
    title_box = slide.shapes.add_textbox(Inches(0.65), Inches(0.58), Inches(12.0), Inches(0.62))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.name = FONT_HEAD
    p_t.font.size = Pt(26)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_PRIMARY

    if subtitle:
        sub_box = slide.shapes.add_textbox(Inches(0.65), Inches(1.18), Inches(12.0), Inches(0.38))
        tf_s = sub_box.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = 0
        p_s = tf_s.paragraphs[0]
        p_s.text = subtitle
        p_s.font.name = FONT_HEAD
        p_s.font.size = Pt(13)
        p_s.font.color.rgb = TEXT_MUTED

    # Subtle divider line
    line_y = Inches(1.58) if subtitle else Inches(1.28)
    div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.65), line_y, Inches(12.03), Inches(0.02))
    div.fill.solid()
    div.fill.fore_color.rgb = BORDER_CLR
    div.line.fill.background()


def add_footer(slide, slide_num: int, label: str = "DevCompany Linux Hackathon | Problem Statement #4") -> None:
    box = slide.shapes.add_textbox(Inches(0.65), Inches(7.05), Inches(12.03), Inches(0.3))
    tf = box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = f"{label}   •   {slide_num} / 15"
    p.alignment = PP_ALIGN.RIGHT
    p.font.name = FONT_HEAD
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED


def add_card(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    title: str,
    bullets: list[str],
    accent: RGBColor = CYAN,
    bg_color: RGBColor = CARD_BG,
    body_size: int = 13,
    mono: bool = False,
):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.adjustments[0] = 0.04
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = BORDER_CLR
    shape.line.width = Pt(1)

    # Top accent strip inside card
    strip = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left + 0.14),
        Inches(top + 0.12),
        Inches(0.55),
        Inches(0.05),
    )
    strip.fill.solid()
    strip.fill.fore_color.rgb = accent
    strip.line.fill.background()

    tb = slide.shapes.add_textbox(
        Inches(left + 0.16),
        Inches(top + 0.22),
        Inches(width - 0.32),
        Inches(height - 0.32),
    )
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.name = FONT_HEAD
    p0.font.size = Pt(15)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_PRIMARY
    p0.space_after = Pt(7)

    for b in bullets:
        p = tf.add_paragraph()
        p.text = f"•  {b}" if not mono else b
        p.font.name = FONT_MONO if mono else FONT_HEAD
        p.font.size = Pt(body_size)
        p.font.color.rgb = TEXT_BODY
        p.space_after = Pt(5)


def add_table(
    slide,
    left: float,
    top: float,
    width: float,
    height: float,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float] | None = None,
    font_size: int = 12,
):
    tbl_shape = slide.shapes.add_table(
        len(rows) + 1,
        len(headers),
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    tbl = tbl_shape.table
    if col_widths:
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Inches(cw)

    # Header row
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x16, 0x26, 0x42)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.name = FONT_HEAD
        p.font.size = Pt(font_size)
        p.font.bold = True
        p.font.color.rgb = CYAN

    # Data rows
    for r_idx, row in enumerate(rows, start=1):
        row_bg = CARD_BG if r_idx % 2 == 1 else CARD_ALT
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_HEAD
            p.font.size = Pt(font_size - 1)
            p.font.color.rgb = TEXT_BODY if c_idx > 0 else TEXT_PRIMARY
            if c_idx == 0:
                p.font.bold = True


def set_notes(slide, text: str) -> None:
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


def build_presentation(
    output_path: Path,
    team_name: str,
    members: str,
    course: str,
    institution: str,
) -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ------------------------------------------------------------------
    # SLIDE 1: Title Slide
    # ------------------------------------------------------------------
    s1 = prs.slides.add_slide(blank)
    set_bg(s1)
    top_band = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.14))
    top_band.fill.solid()
    top_band.fill.fore_color.rgb = CYAN
    top_band.line.fill.background()

    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.1), Inches(5.3), Inches(0.45))
    badge.adjustments[0] = 0.25
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(0x11, 0x2B, 0x3C)
    badge.line.color.rgb = CYAN
    p_b = badge.text_frame.paragraphs[0]
    p_b.text = "LINUX SYSTEM ADMINISTRATION HACKATHON  |  PROBLEM #4"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.name = FONT_HEAD
    p_b.font.size = Pt(12)
    p_b.font.bold = True
    p_b.font.color.rgb = CYAN

    title_tb = s1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.6))
    tf1 = title_tb.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Software Development Company Infrastructure"
    p1.font.name = FONT_HEAD
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_PRIMARY

    p2 = tf1.add_paragraph()
    p2.text = "Automated Multi-Team Linux Server Provisioning, Loopback LVM Storage, RBAC Security & Real-Time DevOps Command Center"
    p2.font.name = FONT_HEAD
    p2.font.size = Pt(17)
    p2.font.color.rgb = TEXT_BODY
    p2.space_before = Pt(10)

    add_card(
        s1, 0.8, 4.15, 5.7, 2.3,
        "Project & Team Details",
        [
            f"Team: {team_name}",
            f"Contributors: {members}",
            f"Course / Exam: {course}",
            f"Institution: {institution}",
        ],
        accent=CYAN,
        body_size=13,
    )
    add_card(
        s1, 6.8, 4.15, 5.7, 2.3,
        "Infrastructure Scale & Coverage",
        [
            "40 Developer Accounts (dev01–dev40) across 4 Teams",
            "4GB Loopback LVM Pool (lv_repos, lv_backups, lv_logs)",
            "SGID + Sticky Bit + POSIX ACLs + Scoped Sudoers",
            "Live FastAPI Web Dashboard + Cron Automation (CO1–CO5)",
        ],
        accent=EMERALD,
        body_size=13,
    )
    add_footer(s1, 1)
    set_notes(s1, "Welcome judges. Today we present our end-to-end solution for Problem Statement #4: Software Development Company Infrastructure.")

    # ------------------------------------------------------------------
    # SLIDE 2: Problem Statement
    # ------------------------------------------------------------------
    s2 = prs.slides.add_slide(blank)
    set_bg(s2)
    add_header(s2, 2, "Context & Motivation", "Problem Statement", "Why manual Linux server administration fails at 40-developer engineering scale")
    add_card(
        s2, 0.65, 1.8, 5.85, 2.35,
        "1. Unstructured User & Access Sprawl",
        [
            "Onboarding 40 engineers across Frontend, Backend, DevOps & Tech Leads manually is error-prone.",
            "Granting broad sudo access violates least-privilege; zero isolation risks cross-team code deletion.",
        ],
        accent=ROSE,
    )
    add_card(
        s2, 6.83, 1.8, 5.85, 2.35,
        "2. Rigid Disk Partitioning Bottlenecks",
        [
            "Static ext4 partitions fill up unpredictably from Git repositories, backups, and telemetry logs.",
            "Single-disk VMs and WSL2 instances lack extra physical drives for traditional LVM evaluation.",
        ],
        accent=AMBER,
    )
    add_card(
        s2, 0.65, 4.35, 5.85, 2.35,
        "3. Missing Collaboration Guardrails",
        [
            "Shared Git directories break without SGID group inheritance or sticky-bit deletion protection.",
            "Tech Leads need cross-team read/write oversight without becoming file owners or needing root.",
        ],
        accent=INDIGO,
    )
    add_card(
        s2, 6.83, 4.35, 5.85, 2.35,
        "4. Reactive Maintenance & Zero Visibility",
        [
            "Unchecked /tmp files, unrotated logs, and unverified backups cause outages and silent data loss.",
            "Operators lack a real-time browser control plane to monitor health and run live diagnostics.",
        ],
        accent=CYAN,
    )
    add_footer(s2, 2)
    set_notes(s2, "Highlight the four concrete infrastructure challenges faced by a growing 40-developer company.")

    # ------------------------------------------------------------------
    # SLIDE 3: Objectives
    # ------------------------------------------------------------------
    s3 = prs.slides.add_slide(blank)
    set_bg(s3)
    add_header(s3, 3, "Academic & Engineering Goals", "Objectives & CO1–CO5 Alignment", "Every requirement mapped directly to Course Outcomes CO1 through CO5")
    add_table(
        s3,
        0.65, 1.8, 12.03, 4.9,
        ["Course Outcome", "Objective Focus", "Implemented Deliverables"],
        [
            ["CO1: Linux Fundamentals & CLI", "Standardized toolchain & package baseline", "01_install_packages.sh installs 21+ compiler, Git, Python, Node, sysstat, cron & SSH packages"],
            ["CO2: Filesystems & Storage", "Flexible, resizable LVM storage architecture", "02_setup_lvm_storage.sh + extend_lvm_demo.sh build loopback LVM with UUID fstab & systemd loop attach"],
            ["CO3: Users, Groups & Permissions", "40-dev RBAC, SGID, Sticky Bit & POSIX ACLs", "03_provision_40_devs.sh & 04_setup_shared_repos.sh enforce 4 teams, aging, SSH keys, 3775 & setfacl"],
            ["CO4: Shell Scripting & Automation", "Idempotent housekeeping, backups & cron", "05_cleanup_system.sh, 06_backup_manager.sh, 07_server_monitor.sh & 08_configure_cron.sh"],
            ["CO5: System Monitoring & Admin UI", "Real-time telemetry, alerts & verification", "JSON health monitor + FastAPI Web Command Center (port 8080) + 99_verify_and_demo.sh audit"],
        ],
        col_widths=[2.7, 3.3, 6.03],
        font_size=13,
    )
    add_footer(s3, 3)
    set_notes(s3, "Walk through the direct mapping from CO1 through CO5 to concrete files and verifiable behaviors.")

    # ------------------------------------------------------------------
    # SLIDE 4: Proposed Solution & Project Overview
    # ------------------------------------------------------------------
    s4 = prs.slides.add_slide(blank)
    set_bg(s4)
    add_header(s4, 4, "Solution Blueprint", "Proposed Solution & Project Overview", "Three integrated layers delivering infrastructure-as-code, observability, and documentation")
    add_card(
        s4, 0.65, 1.85, 3.8, 4.85,
        "Layer 1: Bash Automation",
        [
            "11 modular scripts under scripts/ with set -euo pipefail.",
            "Shared lib/common.sh logging, root checks, and /opt/devcompany sync.",
            "Fully idempotent: safe to re-run at any time without breaking existing state.",
            "One-click 00_master_setup.sh & clean 00_teardown.sh reset.",
        ],
        accent=CYAN,
    )
    add_card(
        s4, 4.76, 1.85, 3.8, 4.85,
        "Layer 2: Enterprise Linux Core",
        [
            "Loopback LVM Pool (vg_devcompany) split into repos, backups, and logs.",
            "Systemd unit devcompany-lvm-loop.service guarantees clean boot mounts.",
            "40 accounts (dev01–dev40) with Ed25519 keys, chage & visudo policies.",
            "Bare Git repos protected by 3775 SGID+Sticky and techleads POSIX ACLs.",
        ],
        accent=EMERALD,
    )
    add_card(
        s4, 8.87, 1.85, 3.8, 4.85,
        "Layer 3: Live Web Command Center",
        [
            "FastAPI + Uvicorn backend running on port 8080 (systemd managed).",
            "Tailwind CSS + Chart.js UI polling live kernel CPU/RAM/LVM every 3s.",
            "Searchable 40-dev RBAC table, live getfacl viewer & SHA-256 backup verifier.",
            "Server-Sent Events (SSE) console drawer runs real scripts live in browser.",
        ],
        accent=INDIGO,
    )
    add_footer(s4, 4)
    set_notes(s4, "Explain how the three layers work together seamlessly from terminal scripts to the live browser dashboard.")

    # ------------------------------------------------------------------
    # SLIDE 5: System Architecture / Workflow Diagram
    # ------------------------------------------------------------------
    s5 = prs.slides.add_slide(blank)
    set_bg(s5)
    add_header(s5, 5, "Architecture", "System Architecture & Workflow Diagram", "End-to-end data flow from developer access through storage, automation, and telemetry")

    def arch_box(x, y, w, h, hdr, body, clr):
        add_card(s5, x, y, w, h, hdr, body, accent=clr, body_size=11)

    arch_box(0.65, 1.85, 3.6, 2.1, "40 Developers (SSH + RBAC)", [
        "frontend (dev01–12) • Zero sudo",
        "backend (dev13–26) • Zero sudo",
        "devops (dev27–34) • Ops + Service sudo",
        "techleads (dev35–40) • Oversight ACL",
    ], CYAN)
    arch_box(4.85, 1.85, 3.6, 2.1, "Shared Bare Git Repos", [
        "/srv/dev_repos/{frontend,backend,",
        "  devops,shared}/*.git",
        "Mode 3775 (SGID + Sticky Bit)",
        "setfacl -d g:techleads:rwx",
    ], EMERALD)
    arch_box(9.05, 1.85, 3.6, 2.1, "LVM Loopback Storage", [
        "disk1.img (2G) + disk2.img (2G)",
        "VG: vg_devcompany (4GB pool)",
        "LVs: lv_repos, lv_backups, lv_logs",
        "UUID fstab + systemd loop attach",
    ], AMBER)

    arch_box(0.65, 4.35, 3.6, 2.25, "Cron Automation Engine", [
        "/etc/cron.d/devcompany_automation",
        "*/5 * * * * -> 07_server_monitor.sh",
        "0 2 * * *   -> 06_backup_manager.sh",
        "0 3 * * 0   -> 05_cleanup_system.sh",
    ], INDIGO)
    arch_box(4.85, 4.35, 3.6, 2.25, "Backups & Health Logs", [
        "/srv/dev_backups/*.tar.gz + .sha256",
        "7-day backup retention pruning",
        "/var/log/dev_company/health_metrics.json",
        "monitor.log / cleanup.log / [ALERT]",
    ], ROSE)
    arch_box(9.05, 4.35, 3.6, 2.25, "FastAPI Web UI (:8080)", [
        "Live /proc CPU, RAM, Disk charts",
        "40-Dev RBAC search & ACL inspector",
        "SSE Live Console Action Triggers",
        "Backup SHA-256 & Cron viewer",
    ], CYAN)

    # Arrows between boxes
    for ax, ay in [(4.32, 2.72), (8.52, 2.72), (4.32, 5.30), (8.52, 5.30)]:
        arr = s5.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(ay), Inches(0.45), Inches(0.32))
        arr.fill.solid()
        arr.fill.fore_color.rgb = CYAN
        arr.line.fill.background()

    add_footer(s5, 5)
    set_notes(s5, "Trace the horizontal workflow across users, repositories, LVM volumes, cron jobs, backups/logs, and the FastAPI UI.")

    # ------------------------------------------------------------------
    # SLIDE 6: Tools, Technologies & Linux Environment Used
    # ------------------------------------------------------------------
    s6 = prs.slides.add_slide(blank)
    set_bg(s6)
    add_header(s6, 6, "Technology Stack", "Tools, Technologies & Linux Environment Used", "Production-grade Linux utilities paired with a lightweight modern web stack")
    add_table(
        s6,
        0.65, 1.8, 12.03, 4.9,
        ["Layer", "Technologies & Packages", "Role in Infrastructure"],
        [
            ["OS & Init", "Ubuntu 26.04 LTS (WSL2 & VM), systemd, GNU Bash 5.x", "Host kernel, daemon lifecycle, loopback LVM boot ordering"],
            ["Storage & FS", "losetup, lvm2 (pvcreate, vgcreate, lvcreate, lvextend), ext4, blkid", "Dynamic file-backed block storage, UUID mounts & online resize"],
            ["Identity & Security", "useradd, chage, ssh-keygen (ed25519), visudo, acl (setfacl/getfacl)", "40 developer accounts, password aging, least-privilege RBAC & ACLs"],
            ["Collaboration", "git (--bare --shared=group), OpenSSH server", "Isolated team repositories with SGID group inheritance & sticky bit"],
            ["Automation & Audit", "cron, tar, gzip, sha256sum, sysstat (sar), df, ps, who", "Scheduled cleanup, integrity-verified backups & threshold alerting"],
            ["Web Command Center", "Python 3, FastAPI, Uvicorn, Tailwind CSS, Chart.js, python-pptx", "Live browser telemetry, SSE script runner & automated 15-slide deck"],
        ],
        col_widths=[2.3, 4.7, 5.03],
        font_size=12,
    )
    add_footer(s6, 6)
    set_notes(s6, "Emphasize zero heavy build toolchains—standard Ubuntu packages plus FastAPI and CDN Tailwind/Chart.js.")

    # ------------------------------------------------------------------
    # SLIDE 7: Linux Commands, Configurations & Scripts Implemented
    # ------------------------------------------------------------------
    s7 = prs.slides.add_slide(blank)
    set_bg(s7)
    add_header(s7, 7, "Implementation Catalog", "Linux Commands, Configurations & Scripts Implemented", "12 modular scripts engineered for deterministic execution and clean teardown")
    add_table(
        s7,
        0.65, 1.75, 12.03, 5.0,
        ["Script / Config", "Key Linux Commands Used", "Primary Responsibility"],
        [
            ["00_master_setup.sh", "bash, python3 -m venv, systemctl, sed", "One-click orchestrator running 01–08, dashboard venv & verification"],
            ["01_install_packages.sh", "apt-get, ssh-keygen -A, systemctl, ufw", "Installs 21+ packages including cron & openssh-server; stages UFW"],
            ["02_setup_lvm_storage.sh", "truncate, losetup, pvcreate, vgcreate, lvcreate, mkfs.ext4", "Builds 4GB loopback LVM pool, UUID /etc/fstab & systemd loop service"],
            ["extend_lvm_demo.sh", "vgs, vgextend, lvextend, resize2fs", "Expands lv_repos +200MB live online (auto-adds PV if VG is full)"],
            ["03_provision_40_devs.sh", "groupadd, useradd, chpasswd, chage, ssh-keygen, visudo", "Provisions dev01–dev40, aging, Ed25519 keys & /etc/sudoers.d/dev_policies"],
            ["04_setup_shared_repos.sh", "git init --bare, chmod 2775/+t, setfacl -R -d", "Initializes 4 team Git repos with SGID, Sticky Bit & techleads ACLs"],
            ["05_cleanup_system.sh", "find -mtime +7/+14, gzip, apt-get clean, df", "Purges old /tmp files, compresses logs, clears caches, writes cleanup.log"],
            ["06_backup_manager.sh", "tar -czpf, sha256sum -c, find -mtime +7 -delete", "Creates SHA-256 verified repo+auth backups & prunes archives >7 days"],
            ["07_server_monitor.sh", "/proc/stat, free, df, ps, who, systemctl is-active", "Exports atomic health_metrics.json + monitor.log with [ALERT] rules"],
            ["08 / 99 / 00 scripts", "/etc/cron.d, getfacl, stat, userdel, lvremove, losetup -d", "Installs cron schedules, runs full [PASS]/[FAIL] audit, clean teardown"],
        ],
        col_widths=[2.55, 4.35, 5.13],
        font_size=11,
    )
    add_footer(s7, 7)
    set_notes(s7, "Point out that every script begins with set -euo pipefail and uses shared lib/common.sh helpers.")

    # ------------------------------------------------------------------
    # SLIDE 8: Storage Management / LVM / Backup & Recovery
    # ------------------------------------------------------------------
    s8 = prs.slides.add_slide(blank)
    set_bg(s8)
    add_header(s8, 8, "Storage & Resilience", "Storage Management, LVM & Backup/Recovery", "Safe loopback physical volumes, UUID boot persistence, online resize, and SHA-256 backups")
    add_card(
        s8, 0.65, 1.8, 5.85, 2.4,
        "Loopback LVM Topology (vg_devcompany)",
        [
            "Backing Files: /var/lvm_disks/disk1.img (2GB) & disk2.img (2GB).",
            "Attached via losetup -> initialized as PVs -> pooled into vg_devcompany.",
            "lv_repos (1.5GB) -> /srv/dev_repos  |  lv_backups (1.5GB) -> /srv/dev_backups.",
            "lv_logs (800MB) -> /var/log/dev_company (all formatted ext4).",
        ],
        accent=CYAN,
    )
    add_card(
        s8, 6.83, 1.8, 5.85, 2.4,
        "Boot-Safe fstab & Online Resize",
        [
            "Persisted via UUID= in /etc/fstab with nofail + x-systemd.requires.",
            "devcompany-lvm-loop.service attaches loop devices BEFORE local-fs mounts.",
            "extend_lvm_demo.sh runs lvextend -L +200M & resize2fs with zero downtime.",
            "Auto-creates disk3.img PV via vgextend if repeated demos exhaust VG space.",
        ],
        accent=EMERALD,
    )
    add_card(
        s8, 0.65, 4.4, 12.03, 2.3,
        "Backup & Integrity Recovery Pipeline (06_backup_manager.sh)",
        [
            "Archives /srv/dev_repos along with /etc/passwd, /etc/group, and /etc/sudoers.d into timestamped repos_backup_YYYYMMDD_HHMMSS.tar.gz.",
            "Generates repos_backup_*.tar.gz.sha256 and immediately runs sha256sum -c to guarantee zero silent archive corruption.",
            "Enforces 7-day retention policy via find -mtime +7 -delete and surfaces live SHA-256 verification status inside the Web UI.",
        ],
        accent=AMBER,
    )
    add_footer(s8, 8)
    set_notes(s8, "Highlight the systemd loop-attach unit—this prevents VM/WSL2 boot failures when mounting loop LVM volumes from fstab.")

    # ------------------------------------------------------------------
    # SLIDE 9: Automation & Shell Scripting (Cleanup & Cron Jobs)
    # ------------------------------------------------------------------
    s9 = prs.slides.add_slide(blank)
    set_bg(s9)
    add_header(s9, 9, "Operations Automation", "Automation & Shell Scripting (Cleanup & Cron)", "Zero-touch scheduled maintenance, log lifecycle management, and threshold alerting")
    add_table(
        s9,
        0.65, 1.8, 12.03, 2.25,
        ["Cron Expression", "Frequency", "Automated Task", "Output & Logging"],
        [
            ["*/5 * * * *", "Every 5 minutes", "/opt/devcompany/scripts/07_server_monitor.sh", "Atomic health_metrics.json + monitor.log"],
            ["0 2 * * *", "Daily at 02:00 AM", "/opt/devcompany/scripts/06_backup_manager.sh", "/srv/dev_backups/*.tar.gz + backup.log"],
            ["0 3 * * 0", "Sunday at 03:00 AM", "/opt/devcompany/scripts/05_cleanup_system.sh", "Frees /tmp, compresses logs -> cleanup.log"],
        ],
        col_widths=[2.1, 2.3, 4.5, 3.13],
        font_size=12,
    )
    add_card(
        s9, 0.65, 4.3, 5.85, 2.4,
        "Housekeeping Engine (05_cleanup_system.sh)",
        [
            "Purges /tmp & /var/tmp files older than 7 days while protecting systemd-private dirs.",
            "Compresses *.log files in /var/log/dev_company older than 14 days using gzip.",
            "Cleans APT, pip3, and npm caches and records exact KB freed to cleanup.log.",
        ],
        accent=AMBER,
    )
    add_card(
        s9, 6.83, 4.3, 5.85, 2.4,
        "Telemetry & Alerting (07_server_monitor.sh)",
        [
            "Samples live /proc/stat CPU%, /proc/meminfo RAM%, LVM disk usage & SSH sessions.",
            "Monitors cron, ssh, devcompany-lvm-loop & dashboard service states.",
            "Raises [ALERT] events in monitor.log & JSON whenever CPU > 80% or Disk > 85%.",
        ],
        accent=ROSE,
    )
    add_footer(s9, 9)
    set_notes(s9, "Mention why /etc/cron.d/devcompany_automation runs scripts synced to /opt/devcompany—clean paths without spaces and native ext4 +x bits.")

    # ------------------------------------------------------------------
    # SLIDE 10: Security & User/Permission Management
    # ------------------------------------------------------------------
    s10 = prs.slides.add_slide(blank)
    set_bg(s10)
    add_header(s10, 10, "Identity & Access Control", "Security, 40-Dev RBAC, SGID, Sticky Bit & ACLs", "Defense-in-depth multi-team isolation without blocking legitimate engineering workflow")
    add_table(
        s10,
        0.65, 1.78, 12.03, 2.45,
        ["Team Group", "Accounts", "Count", "Repository Path & Mode", "Sudo Privilege Scope (/etc/sudoers.d/dev_policies)"],
        [
            ["frontend", "dev01 – dev12", "12", "/srv/dev_repos/frontend (3775)", "None (Zero root access enforced)"],
            ["backend", "dev13 – dev26", "14", "/srv/dev_repos/backend (3775)", "None (Zero root access enforced)"],
            ["devops", "dev27 – dev34", "8", "/srv/dev_repos/devops (3775)", "NOPASSWD scoped service restarts + cleanup/backup/monitor scripts"],
            ["techleads", "dev35 – dev40", "6", "All repos via POSIX ACL rwx", "NOPASSWD scoped service status/restart + monitor/verify scripts"],
        ],
        col_widths=[1.6, 1.7, 0.9, 3.3, 4.53],
        font_size=12,
    )
    add_card(
        s10, 0.65, 4.45, 5.85, 2.25,
        "Account Hardening & SSH Keys",
        [
            "All 40 users also join master 'developers' group for /srv/dev_repos/shared.",
            "Password aging enforced via chage -M 90 -m 7 -W 14 on every account.",
            "Dedicated Ed25519 SSH key pair (~/.ssh/id_ed25519) provisioned per user.",
        ],
        accent=CYAN,
    )
    add_card(
        s10, 6.83, 4.45, 5.85, 2.25,
        "SGID + Sticky Bit + POSIX ACLs",
        [
            "SGID (2775): new files/commits inherit owning team group automatically.",
            "Sticky Bit (+t -> 3775): prevents engineers from deleting teammates' files.",
            "setfacl -R -m & -d g:techleads:rwx grants Tech Leads seamless oversight.",
        ],
        accent=EMERALD,
    )
    add_footer(s10, 10)
    set_notes(s10, "Walk through the exact counts (12+14+8+6=40) and explain how 3775 + setfacl solves collaboration vs deletion protection.")

    # ------------------------------------------------------------------
    # SLIDE 11: Live Demonstration Walkthrough & Web Command Center
    # ------------------------------------------------------------------
    s11 = prs.slides.add_slide(blank)
    set_bg(s11)
    add_header(s11, 11, "Live Demonstration", "Live Demonstration Walkthrough & Dashboard UI", "Side-by-side terminal verification and real-time browser control at http://localhost:8080")
    add_card(
        s11, 0.65, 1.8, 5.85, 4.9,
        "Terminal Demo Sequence (WSL2 / Ubuntu VM)",
        [
            "1. Deploy entire stack: sudo bash scripts/00_master_setup.sh",
            "2. Inspect LVM pool: sudo lvs && df -h /srv/dev_* /var/log/dev_company",
            "3. Verify 40 accounts & RBAC: id dev01; sudo -l -U dev01; sudo -l -U dev35",
            "4. Inspect SGID/Sticky/ACLs: stat -c '%a' /srv/dev_repos/frontend; getfacl /srv/dev_repos/frontend",
            "5. Run full automated audit: sudo bash scripts/99_verify_and_demo.sh",
            "6. Clean reset anytime: sudo bash scripts/00_teardown.sh --yes",
        ],
        accent=CYAN,
        body_size=12,
    )
    add_card(
        s11, 6.83, 1.8, 5.85, 4.9,
        "Web Admin Command Center Features",
        [
            "Real-Time Telemetry: CPU %, Load, RAM MB, Active SSH & 3s Chart.js stream.",
            "LVM Partition Bars: Live capacity meters for lv_repos, lv_backups, lv_logs.",
            "40-Dev Matrix: Filter by team or search dev01–dev40 with aging & sudo scope.",
            "Repo & ACL Inspector: Shows bare Git commits, 3775 badges & getfacl output.",
            "One-Click Action Triggers: Stream live SSE logs for Backup, Cleanup, +200MB LVM Expand & System Audit.",
        ],
        accent=EMERALD,
        body_size=12,
    )
    add_footer(s11, 11)
    set_notes(s11, "Use this slide as your live demo cue card during grading.")

    # ------------------------------------------------------------------
    # SLIDE 12: Testing, Results & Observations
    # ------------------------------------------------------------------
    s12 = prs.slides.add_slide(blank)
    set_bg(s12)
    add_header(s12, 12, "Verification & QA", "Testing, Results & Observations", "Automated static checks, FastAPI pytest suite, PPTX validation, and live Linux audit")
    add_card(
        s12, 0.65, 1.8, 5.85, 2.35,
        "1. Script & Syntax Verification",
        [
            "Every Bash script validated with 'bash -n' and strict LF line-ending checks.",
            "Idempotency verified: re-running scripts preserves existing data & mounts safely.",
            "visudo -cf validates /etc/sudoers.d/dev_policies prior to installation.",
        ],
        accent=EMERALD,
    )
    add_card(
        s12, 6.83, 1.8, 5.85, 2.35,
        "2. Automated Pytest Suite",
        [
            "tests/test_scripts_static.py checks syntax, LF endings & spec requirements.",
            "tests/test_dashboard_api.py tests telemetry, 40-dev filter, repos, SHA-256 & SSE.",
            "tests/test_generate_ppt.py guarantees exact 15-slide deck compliance.",
        ],
        accent=CYAN,
    )
    add_card(
        s12, 0.65, 4.35, 12.03, 2.35,
        "3. Live Linux Audit Observations (99_verify_and_demo.sh)",
        [
            "Confirms all 21+ packages, active cron/ssh daemons, loopback PVs/VG/LVs, and UUID /etc/fstab mounts.",
            "Verifies 40/40 user accounts, 90-day password aging, Ed25519 keys, zero sudo on dev01 vs scoped sudo on dev35.",
            "Confirms 3775 permissions + techleads ACLs across all 4 Git repos, verified .tar.gz + .sha256 backup, and HTTP 200 dashboard health.",
        ],
        accent=INDIGO,
    )
    add_footer(s12, 12)
    set_notes(s12, "Summarize both unit-level pytest coverage and runtime audit checks.")

    # ------------------------------------------------------------------
    # SLIDE 13: Challenges Faced & Solutions
    # ------------------------------------------------------------------
    s13 = prs.slides.add_slide(blank)
    set_bg(s13)
    add_header(s13, 13, "Engineering Trade-offs", "Challenges Faced & Solutions", "Real OS-level obstacles solved during architecture and WSL2/VM compatibility testing")
    add_table(
        s13,
        0.65, 1.8, 12.03, 4.9,
        ["Challenge Encountered", "Root Cause", "Implemented Engineering Solution"],
        [
            ["LVM on Single-Disk VM / WSL2", "No spare physical block devices available during evaluation", "Created 2GB sparse files in /var/lvm_disks attached safely via losetup"],
            ["Boot Failure Risk with fstab", "Loop devices vanish on reboot before /etc/fstab mounts UUIDs", "Added devcompany-lvm-loop.service + nofail + x-systemd.requires in fstab"],
            ["Repeated Online LVM Demos", "Initial 3.8GB LVs leave ~200MB free; 2nd +200MB click would fail", "extend_lvm_demo.sh auto-creates disk3.img + pvcreate + vgextend when <220MB free"],
            ["Spaces & Windows Mount Paths", "WSL2 /mnt/c paths with spaces break cron & lose Linux +x bits", "Scripts & venv sync cleanly to /opt/devcompany with LF normalization"],
            ["Bare Repo Access vs Isolation", "Teams need collaboration without deleting teammates' Git objects", "Combined mode 3775 (SGID + Sticky Bit) with recursive default POSIX ACLs"],
        ],
        col_widths=[3.2, 3.8, 5.03],
        font_size=12,
    )
    add_footer(s13, 13)
    set_notes(s13, "Judges love hearing real engineering hurdles like boot-time fstab ordering and repeated LVM demo headroom.")

    # ------------------------------------------------------------------
    # SLIDE 14: Conclusion & Future Enhancements
    # ------------------------------------------------------------------
    s14 = prs.slides.add_slide(blank)
    set_bg(s14)
    add_header(s14, 14, "Wrap-Up & Roadmap", "Conclusion & Future Enhancements", "Production-ready baseline today with clear paths to enterprise scale")
    add_card(
        s14, 0.65, 1.85, 5.85, 4.8,
        "Key Achievements & Conclusion",
        [
            "Delivered full CO1–CO5 Linux infrastructure automated end-to-end.",
            "Zero-risk, portable loopback LVM storage supporting live online expansion.",
            "Strict least-privilege isolation across 40 developers with SGID, Sticky Bit & ACLs.",
            "Automated cron lifecycle for monitoring, housekeeping, and SHA-256 backups.",
            "Real-time FastAPI Web Command Center enabling instant visual grading.",
        ],
        accent=EMERALD,
    )
    add_card(
        s14, 6.83, 1.85, 5.85, 4.8,
        "Future Enhancements",
        [
            "Prometheus Node Exporter + Grafana dashboards for multi-month metrics history.",
            "Centralized LDAP / FreeIPA authentication replacing local /etc/passwd entries.",
            "Off-site encrypted S3 / Restic backup replication with automated restore drills.",
            "Webhook-driven CI/CD runners inside isolated Docker/Podman containers.",
            "Token-authenticated HTTPS reverse proxy (Nginx/Caddy) in front of the Web UI.",
        ],
        accent=CYAN,
    )
    add_footer(s14, 14)
    set_notes(s14, "Conclude crisply on what is achieved today and realistic next steps for multi-server scale.")

    # ------------------------------------------------------------------
    # SLIDE 15: References
    # ------------------------------------------------------------------
    s15 = prs.slides.add_slide(blank)
    set_bg(s15)
    add_header(s15, 15, "Citations & Standards", "References", "Official Linux, storage, security, and Python documentation consulted")
    add_card(
        s15, 0.65, 1.85, 12.03, 4.8,
        "Technical Documentation & Official Manuals",
        [
            "Linux Foundation Training — https://training.linuxfoundation.org (Primary curriculum reference for CO1–CO5).",
            "Ubuntu Server Documentation & systemd.mount(5) / fstab(5) Manual Pages — Canonical / Ubuntu.",
            "Red Hat / Linux LVM2 Administration Guide — lvcreate(8), lvextend(8), resize2fs(8), losetup(8).",
            "POSIX Access Control Lists & Linux File Permissions — setfacl(1), getfacl(1), chmod(1), sudoers(5), chage(1).",
            "Git Internals & Shared Bare Repositories — Pro Git Book (git-init --bare --shared=group).",
            "GNU Bash Reference Manual (set -euo pipefail), Vixie Cron (crontab(5)), FastAPI, Chart.js & python-pptx.",
        ],
        accent=INDIGO,
        body_size=14,
    )
    add_footer(s15, 15)
    set_notes(s15, "Thank the panel and invite questions or live dashboard demonstrations.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path


def main() -> None:
    default_out = Path(__file__).resolve().parent / "DevCompany_Linux_Hackathon.pptx"
    parser = argparse.ArgumentParser(description="Generate the 15-slide DevCompany Linux Hackathon PPTX deck.")
    parser.add_argument("--output", type=Path, default=default_out, help="Output .pptx file path")
    parser.add_argument("--team", default="DevCompany Infrastructure Team", help="Team name on Title Slide")
    parser.add_argument("--members", default="Linux Systems & DevOps Engineering Track", help="Team members on Title Slide")
    parser.add_argument("--course", default="Linux System Administration Hackathon (Problem Statement #4)", help="Course/Exam title")
    parser.add_argument("--institution", default="Department of Computer Science & Engineering", help="Institution name")
    args = parser.parse_args()

    saved = build_presentation(
        output_path=args.output,
        team_name=args.team,
        members=args.members,
        course=args.course,
        institution=args.institution,
    )
    print(f"Generated 15-slide presentation at: {saved}")


if __name__ == "__main__":
    main()
