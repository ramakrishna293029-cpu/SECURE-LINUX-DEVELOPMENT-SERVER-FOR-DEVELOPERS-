import os, shutil
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "docs", "report_images")
os.makedirs(OUT_DIR, exist_ok=True)

# Copy Web Dashboard screenshot
src_dash = r"C:\Users\rama krishna\.gemini\antigravity\brain\8ca8012f-6bd5-4748-bee4-98d4e4657ea7\browser_evidence\c6b0f325-9c67-45e2-b9a2-c8e5d66f9a8a\final_step_14.png"
dst_dash = os.path.join(OUT_DIR, "fig_3_15_web_dashboard.png")
if os.path.exists(src_dash):
    shutil.copy2(src_dash, dst_dash)
    print(f"Copied {src_dash} -> {dst_dash}")

# Also copy Alliance University Logo from ref_images
src_logo = r"C:\Users\rama krishna\OneDrive\Desktop\Linux Hackathon\linux-dev-server-hackathon\docs\ref_images\image1.png"
dst_logo = os.path.join(OUT_DIR, "alliance_logo.png")
if os.path.exists(src_logo):
    shutil.copy2(src_logo, dst_logo)
    print(f"Copied {src_logo} -> {dst_logo}")

# Generate Figure 3.1: System Architecture Diagram
# Dimensions: 1200 x 750
w, h = 1200, 750
img = Image.new("RGB", (w, h), (248, 250, 252)) # Light slate background
draw = ImageDraw.Draw(img)

FONT_PATH = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf")
FONT_BOLD_PATH = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")

f_title = ImageFont.truetype(FONT_BOLD_PATH, 20)
f_box_title = ImageFont.truetype(FONT_BOLD_PATH, 15)
f_box_sub = ImageFont.truetype(FONT_PATH, 13)
f_detail = ImageFont.truetype(FONT_PATH, 12)

# Colors
C_BORDER = (51, 65, 85)
C_PRIMARY = (30, 58, 138)
C_BLUE_BG = (239, 246, 255)
C_BLUE_BOX = (219, 234, 254)
C_GREEN_BG = (240, 253, 244)
C_PURPLE_BG = (250, 245, 255)
C_AMBER_BG = (254, 243, 199)

# Draw Title
draw.text((w // 2 - 290, 25), "DevCompany 40-Developer Linux Architecture", fill=(15, 23, 42), font=f_title)

def draw_card(box, title, subtitle, items, bg_color, border_color):
    draw.rounded_rectangle(box, radius=8, fill=bg_color, outline=border_color, width=2)
    # Header inside card
    draw.text((box[0] + 16, box[1] + 12), title, fill=(15, 23, 42), font=f_box_title)
    draw.text((box[0] + 16, box[1] + 32), subtitle, fill=(71, 85, 105), font=f_box_sub)
    y = box[1] + 55
    for it in items:
        draw.text((box[0] + 20, y), "• " + it, fill=(30, 41, 59), font=f_detail)
        y += 18

# Layer 1: Developer Access (Top)
draw_card((60, 75, 1140, 195),
          "Layer 1: Identity & Access Management (CO1, CO3)",
          "40 Developers in 4 Specialized Functional Teams + 'developers' Unified Group",
          [
              "Frontend (12 dev accounts: dev01..dev12) | Backend (14 dev accounts: dev13..dev26)",
              "DevOps (8 dev accounts: dev27..dev34) | Tech Leads (6 lead accounts: dev35..dev40)",
              "Ed25519 SSH Authentication (0700/0600) | Password Aging (90d max, 7d min, 14d warn via chage)",
              "Least-Privilege Sudoers (/etc/sudoers.d/dev_policies): Zero root for junior devs; scoped daemon & LVM controls for DevOps"
          ],
          C_BLUE_BG, (147, 197, 253))

# Layer 2: Shared Repositories (Middle Left)
draw_card((60, 220, 580, 395),
          "Layer 2: Shared Git Storage & ACLs (CO3)",
          "Centralized Bare Repositories (/srv/dev_repos)",
          [
              "Bare Git Repos: frontend/web-portal.git, backend/core-api.git,",
              "  devops/infra-automation.git, shared/company-docs.git",
              "SGID (2775): Enforces parent team group ownership on new commits",
              "Sticky Bit (+t, 3775): Prevents cross-member deletion of branch objects",
              "POSIX ACLs: Recursive 'techleads' read/write/execute oversight"
          ],
          C_GREEN_BG, (134, 239, 172))

# Layer 3: LVM Storage Subsystem (Middle Right)
draw_card((620, 220, 1140, 395),
          "Layer 3: Boot-Safe LVM Storage Subsystem (CO2)",
          "Volume Group: vg_devcompany (4 GB Resizable)",
          [
              "Physical Volumes: /dev/loop0 & /dev/loop1 (backed by sparse disk.img files)",
              "lv_repos (1.5G ext4) -> /srv/dev_repos (Git source trees)",
              "lv_backups (1.5G ext4) -> /srv/dev_backups (archive destination)",
              "lv_logs (800M ext4) -> /var/log/dev_company (telemetry & cleanup logs)",
              "Boot Safety: systemd devcompany-lvm-loop.service + nofail in /etc/fstab"
          ],
          C_PURPLE_BG, (216, 180, 254))

# Layer 4: Maintenance & Automation (Bottom Left)
draw_card((60, 420, 580, 680),
          "Layer 4: Automated Maintenance & Backups (CO4)",
          "Centralized Cron Job Daemon (/etc/cron.d/devcompany_automation)",
          [
              "Differential/Full Backups (02:00 AM Daily):",
              "  - Bundles /srv/dev_repos into .tar.gz archives",
              "  - Cryptographic SHA-256 verification (sha256sum -c)",
              "  - Automatic 7-day retention pruning to prevent disk exhaustion",
              "System Housekeeping (03:00 AM Sundays):",
              "  - Deletes /tmp files older than 7 days",
              "  - Compresses rotated logs (>14d) with gzip",
              "  - Flushes APT/pip/npm caches to maintain root volume headroom"
          ],
          C_AMBER_BG, (252, 211, 77))

# Layer 5: Observability & Web Command Center (Bottom Right)
draw_card((620, 420, 1140, 680),
          "Layer 5: Monitoring & Web Command Center (CO5)",
          "FastAPI Telemetry Daemon & UI (Port 8080)",
          [
              "Systemd Managed: devcompany-dashboard.service (Uvicorn / FastAPI)",
              "Telemetry Sampling (Every 5 mins):",
              "  - Kernel CPU, RAM, Disk, and LVM free capacity from /proc & df",
              "  - Safe process tokenization (resilient to spaces & parentheses)",
              "  - Writes live snapshot to /var/log/dev_company/health_metrics.json",
              "DevOps Command Center Web UI:",
              "  - Responsive Chart.js real-time telemetry graphs",
              "  - RBAC developer search, Repo ACL inspector, Backup integrity status",
              "  - Live Server-Sent Events (SSE) script triggering console"
          ],
          C_BLUE_BG, (147, 197, 253))

# Connecting Arrows (Vertical lines with arrowheads)
def draw_arrow(x1, y1, x2, y2, color=(100, 116, 139)):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
    draw.polygon([(x2, y2), (x2 - 6, y2 - 8), (x2 + 6, y2 - 8)], fill=color)

draw_arrow(320, 195, 320, 220)
draw_arrow(880, 195, 880, 220)
draw_arrow(320, 395, 320, 420)
draw_arrow(880, 395, 880, 420)

out_arch = os.path.join(OUT_DIR, "fig_3_1_architecture.png")
img.save(out_arch, "PNG")
print(f"Generated {out_arch} ({w}x{h})")
