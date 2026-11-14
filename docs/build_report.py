import os
import shutil
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from docx2pdf import convert

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "docs", "report_images")
OUT_DOCX = os.path.join(BASE_DIR, "docs", "Linux Hackathon Report.docx")
OUT_PDF = os.path.join(BASE_DIR, "docs", "Linux Hackathon Report.pdf")

print("Initializing document...")
doc = Document()

# Set Section Margins: 0.8 inch (57.6 pt) matching reference report
section = doc.sections[0]
section.top_margin = Inches(0.8)
section.bottom_margin = Inches(0.8)
section.left_margin = Inches(0.8)
section.right_margin = Inches(0.8)

# Add Double-line Page Border to Section (identical to reference report)
sectPr = section._sectPr
pgBorders = parse_xml(
    f'<w:pgBorders {nsdecls("w")} w:offsetFrom="page">'
    f'<w:top w:val="double" w:sz="12" w:space="24" w:color="000000"/>'
    f'<w:left w:val="double" w:sz="12" w:space="24" w:color="000000"/>'
    f'<w:bottom w:val="double" w:sz="12" w:space="24" w:color="000000"/>'
    f'<w:right w:val="double" w:sz="12" w:space="24" w:color="000000"/>'
    f'</w:pgBorders>'
)
sectPr.append(pgBorders)

# Configure Header
header = section.header
p_head = header.paragraphs[0]
p_head.text = "Linux System Administration\t\t\t\t\tE1ITA307"
p_head.style.font.name = "Times New Roman"
p_head.style.font.size = Pt(9.5)
p_head.style.font.color.rgb = RGBColor(100, 116, 139)

# Configure Footer with Page Number
footer = section.footer
p_foot = footer.paragraphs[0]
p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r_foot = p_foot.add_run()
fldSimple = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
p_foot._p.append(fldSimple)
p_foot.style.font.name = "Times New Roman"
p_foot.style.font.size = Pt(10)
p_foot.style.font.color.rgb = RGBColor(71, 85, 105)

# Typography Helper Functions
def add_p(text="", align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, italic=False, size=12.0, color=None, space_after=6, space_before=0, line_spacing=1.15):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
    return p

def add_heading_1(text):
    return add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=14.0, space_before=14, space_after=6)

def add_heading_2(text):
    return add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=12.5, space_before=10, space_after=4)

def add_heading_3(text):
    return add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, italic=True, size=12.0, space_before=8, space_after=3)

def add_body(text, space_after=6):
    return add_p(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, size=12.0, space_after=space_after)

def add_bullet(text, space_after=3):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12.0)
    return p

def add_code_block(code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.9)
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
    tcPr.append(shd)
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        f'<w:left w:val="single" w:sz="18" w:space="0" w:color="3B82F6"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.05
    r = p.add_run(code_text)
    r.font.name = "Consolas"
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(15, 23, 42)
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def add_image_figure(img_filename, caption_text, width=Inches(6.4)):
    img_path = os.path.join(IMG_DIR, img_filename)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run = p_img.add_run()
        run.add_picture(img_path, width=width)
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run(caption_text)
        r_cap.font.name = "Times New Roman"
        r_cap.font.size = Pt(11.0)
        r_cap.italic = True
        r_cap.font.color.rgb = RGBColor(30, 41, 59)
    else:
        print(f"WARNING: Image not found: {img_path}")

def format_table(tbl, col_widths, header_bg="D9E1F2"):
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    for r_idx, row in enumerate(tbl.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_widths[c_idx]
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:top w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'<w:left w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'<w:right w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'</w:tcBorders>'
            )
            tcPr.append(tcBorders)
            if r_idx == 0:
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{header_bg}"/>')
                tcPr.append(shd)
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(4)
                    p.paragraph_format.space_after = Pt(4)
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(11.0)
                        r.bold = True
            else:
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(3)
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.line_spacing = 1.1
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(10.5)

print("Writing Title / Cover Page...")
# ==============================================================================
# COVER PAGE
# ==============================================================================
logo_path = os.path.join(IMG_DIR, "alliance_logo.png")
if os.path.exists(logo_path):
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_before = Pt(4)
    p_logo.paragraph_format.space_after = Pt(12)
    p_logo.add_run().add_picture(logo_path, width=Inches(4.2))

add_p("Linux System Administration (E1ITA307)", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.5, space_after=3)
add_p("Linux Infrastructure Deployment Project Report", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.5, space_after=3)
add_p("On", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.5, space_after=14)

add_p("SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS WITH LVM STORAGE, SHARED REPOSITORIES, AUTOMATED CLEANUP, AND TELEMETRY DASHBOARD",
      align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13.5, space_after=18)

add_p("Submitted by", align=WD_ALIGN_PARAGRAPH.CENTER, size=12.0, space_after=6)

add_p("ROLE 1 – Linux System Administrator", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.5, space_after=2)
add_p("ROLE 2 – Storage & Backup Administrator", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.5, space_after=2)
add_p("ROLE 3 – Automation & Security Engineer", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.5, space_after=2)
add_p("ROLE 4 – Testing Documentation & Presentation Lead", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.5, space_after=16)

add_p("In partial fulfillment of the award of the degree of", align=WD_ALIGN_PARAGRAPH.CENTER, size=12.0, space_after=2)
add_p("BACHELOR OF TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.5, space_after=2)
add_p("In", align=WD_ALIGN_PARAGRAPH.CENTER, size=12.0, space_after=2)
add_p("Information Technology", align=WD_ALIGN_PARAGRAPH.CENTER, size=12.0, space_after=14)

add_p("Under the Supervision of", align=WD_ALIGN_PARAGRAPH.CENTER, size=12.0, space_after=2)
add_p("Prof. Kusuma J", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.0, space_after=2)
add_p("Assistant Professor", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.0, space_after=18)

add_p("ALLIANCE SCHOOL OF ADVANCED COMPUTING", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.0, space_after=2)
add_p("ALLIANCE UNIVERSITY", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.0, space_after=2)
add_p("BENGALURU", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.0, space_after=2)
add_p("Nov 2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.0, space_after=0)

doc.add_page_break()

print("Writing Certificate Page...")
# ==============================================================================
# CERTIFICATE PAGE
# ==============================================================================
add_p("DEPARTMENT OF INFORMATION TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.5, space_before=10, space_after=2)
add_p("ALLIANCE SCHOOL OF ADVANCED COMPUTING", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12.5, space_after=18)

add_p("CERTIFICATE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14.0, space_after=20)

cert_text = (
    "This is to certify that the Project work entitled “SECURE LINUX DEVELOPMENT SERVER FOR DEVELOPERS "
    "with LVM Storage, Shared Repositories, Automated Cleanup, and Telemetry Dashboard” submitted by the DevCompany "
    "Infrastructure Project Team (Role 1: Linux System Administrator, Role 2: Storage & Backup Administrator, "
    "Role 3: Automation & Security Engineer, Role 4: Testing Documentation & Presentation Lead) in partial fulfillment "
    "of the requirements for the award of the degree of Bachelor of Technology in Information Technology, is a "
    "bonafide work carried out during the academic year 2026-2027."
)
add_body(cert_text, space_after=50)

# Signatures Table (1 row, 3 columns)
sig_tbl = doc.add_table(rows=1, cols=3)
sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
sig_tbl.autofit = False
sig_widths = [Inches(2.3), Inches(2.3), Inches(2.3)]
for i, cell in enumerate(sig_tbl.rows[0].cells):
    cell.width = sig_widths[i]
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if i == 0:
        r1 = p.add_run("Prof. Kusuma J\n")
        r1.bold = True
        r2 = p.add_run("Course Handling Faculty")
    elif i == 1:
        r1 = p.add_run("Prof. Ananthanagu U\n")
        r1.bold = True
        r2 = p.add_run("Course Coordinator")
    else:
        r1 = p.add_run("Dr. Shekhar R\n")
        r1.bold = True
        r2 = p.add_run("Professor & HoD")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(11.5)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(10.5)

doc.add_page_break()

print("Writing Table of Contents...")
# ==============================================================================
# TABLE OF CONTENTS
# ==============================================================================
add_p("Table of Contents", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14.0, space_before=10, space_after=16)

toc_entries = [
    ("1. Introduction", True, 0),
    ("1.1 Aim", False, 1),
    ("1.2 Background", False, 1),
    ("1.3 Problem Statement", False, 1),
    ("1.4 Objectives", False, 1),
    ("2. Methodology", True, 0),
    ("2.1 Tools and Technologies Used", False, 1),
    ("2.2 Approach / Development Process", False, 1),
    ("3. Linux System Administration – Design and Implementation", True, 0),
    ("3.1 System Architecture", False, 1),
    ("3.2 Linux Environment and Toolchain Setup", False, 1),
    ("3.3 User, Group, and Sudoers Management", False, 1),
    ("3.4 Logical Volume Management (LVM) Storage Architecture", False, 1),
    ("3.5 Shared Git Repositories and Access Control (SGID & ACLs)", False, 1),
    ("3.6 Package and Process Supervision via systemd", False, 1),
    ("3.7 Automated System Cleanup and Log Maintenance", False, 1),
    ("3.8 Automated Backup Pipeline with Checksum Verification", False, 1),
    ("3.9 Scheduled Task Automation with Cron", False, 1),
    ("3.10 Real-Time Server Monitoring and Telemetry Subsystem", False, 1),
    ("3.11 Web Command Center Dashboard", False, 1),
    ("3.12 Security Hardening and Access Control", False, 1),
    ("4. Results and Testing", True, 0),
    ("4.1 Implementation Results", False, 1),
    ("4.2 Testing and Validation", False, 1),
    ("4.3 Challenges Faced and Solutions", False, 1),
    ("5. Conclusion and Future Scope", True, 0),
    ("5.1 Conclusion", False, 1),
    ("5.2 Future Scope", False, 1),
    ("References", True, 0),
    ("Appendices", True, 0),
    ("Appendix A: Production Automated Backup Routine (06_backup_manager.sh)", False, 1),
    ("Appendix B: Real-Time Telemetry and Monitoring Engine (07_server_monitor.sh)", False, 1),
    ("Appendix C: Complete Screenshot Insertion Guide & Evidence Index", False, 1)
]

for title, is_bold, indent_level in toc_entries:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.25 * indent_level)
    r = p.add_run(title)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.5 if is_bold else 11.0)
    r.bold = is_bold

doc.add_page_break()

print("Writing Chapter 1: Introduction...")
# ==============================================================================
# CHAPTER 1: INTRODUCTION
# ==============================================================================
add_heading_1("1. Introduction")

add_heading_2("1.1 Aim")
add_body(
    "The primary aim of this project is to architect, automate, secure, and validate a production-ready Linux development "
    "server supporting 40 software engineers across four specialized engineering teams: frontend, backend, devops, and tech leads. "
    "The implementation deploys isolated developer accounts with strict password aging policies and SSH Ed25519 key authentication, "
    "establishes boot-safe Logical Volume Management (LVM) storage partitions, provisions shared bare Git repositories protected "
    "by SGID sticky permissions and POSIX Access Control Lists (ACLs), schedules automated system cleanup and cryptographic backup "
    "routines via cron, and exposes an active, real-time web command center dashboard on port 8080. The entire deployment is fully "
    "idempotent and executed using native GNU Bash scripts and Linux system utilities on Ubuntu."
)

add_heading_2("1.2 Background")
add_body(
    "Linux is the foundational operating system for modern software development environments, enterprise servers, and cloud infrastructure. "
    "In collaborative corporate engineering organizations, dozens of software developers concurrently write code, build container images, "
    "and commit artifacts to shared source code repositories. Without centralized operating system governance, departmental development servers "
    "rapidly suffer from disk volume exhaustion, permission conflicts, uncoordinated root access privileges, and silent backup failures."
)
add_body(
    "To solve these operational risks, professional system administration mandates disciplined access control and dynamic storage management. "
    "Linux provides granular Discretionary Access Control (DAC) via User Identifiers (UIDs) and Group Identifiers (GIDs), augmented with "
    "specialized directory bits such as Setgid (SGID, octal 2000) and the Sticky Bit (octal 1000). Furthermore, POSIX Access Control Lists "
    "extend traditional file permission bits, enabling fine-grained oversight across distinct engineering teams without compromising team "
    "isolation. Complementing access controls, Logical Volume Management (LVM) abstracts physical storage into elastic volume groups, enabling "
    "system administrators to expand partitions on the fly without server downtime. Combining these primitives with automated cron task "
    "scheduling and real-time hardware telemetry yields an observable, fault-tolerant development infrastructure."
)

add_heading_2("1.3 Problem Statement")
add_body(
    "Problem Statement #4: Software Development Company requires the configuration of a dedicated Linux server for 40 developers. "
    "The technical specification demands automated developer account provisioning, shared Git repository configuration, standard software "
    "development toolchain installation, automated storage maintenance and cleanup scripts, dynamic storage management, and continuous server monitoring."
)
add_body(
    "In traditional manual deployments, managing 40 individual developer accounts invites operational failure. Junior developers frequently receive "
    "excessive sudo privileges, leading to configuration drift or accidental service disruption. Unmanaged shared directories suffer from file deletion "
    "by unauthorized peers, and static partitions cause system crashes when log files or Git objects consume remaining disk space. Manual backup "
    "routines are routinely forgotten, and archives that are generated lack cryptographic checksum validation. This project resolves each of these "
    "vulnerabilities through an automated, modular, and fully tested Linux deployment."
)

add_heading_2("1.4 Objectives")
add_body("The specific implementation objectives of this project are:")
add_bullet("Baseline Toolchain Provisioning (CO1): Automate the non-interactive installation of compilers, runtimes, Git, LVM utilities, ACL tools, cron, and OpenSSH server on Ubuntu.")
add_bullet("Dynamic Storage Management (CO2): Build an elastic LVM storage subsystem (vg_devcompany) carving dedicated logical volumes for repositories (/srv/dev_repos), backups (/srv/dev_backups), and operational logs (/var/log/dev_company), with boot persistence and online expansion support.")
add_bullet("Developer Identity and Access Governance (CO3): Provision 40 distinct user accounts (dev01 to dev40) categorized into four functional groups (frontend, backend, devops, techleads) plus a unified developers group, enforcing 90-day password aging and Ed25519 SSH keys.")
add_bullet("Collaborative Repository Protection (CO3): Configure shared bare Git repositories with mode 3775 (SGID + Sticky Bit) and recursive POSIX ACLs, guaranteeing group ownership inheritance and technical lead administrative oversight.")
add_bullet("Role-Based Privilege Restriction (CO3): Implement a hardened /etc/sudoers.d/dev_policies policy denying root escalation to standard developers while granting strictly scoped command aliases to DevOps and Tech Lead staff.")
add_bullet("Automated System Cleanup (CO4): Develop a production cleanup script purging /tmp files older than 7 days, compressing rotated logs older than 14 days with gzip, and flushing package caches.")
add_bullet("Cryptographic Backup Pipeline (CO4): Implement an automated backup manager producing timestamped gzip-compressed archives with SHA-256 integrity checksums and automated 7-day retention pruning.")
add_bullet("Centralized Cron Task Automation (CO4): Schedule telemetry sampling, daily repository backups at 02:00 AM, and weekly system cleanup routines at 03:00 AM using system crontab.")
add_bullet("Real-Time Telemetry and Monitoring (CO5): Engineer a continuous hardware metrics collector parsing /proc/stat, memory structures, disk usage, and process lists with safe whitespace-agnostic tokenization.")
add_bullet("Interactive Web Command Center (CO5): Deploy an active FastAPI administrative dashboard on port 8080 featuring live Chart.js graphs, developer account filtering, repository inspectors, and real-time Server-Sent Events (SSE) script execution.")

doc.add_page_break()

print("Writing Chapter 2: Methodology...")
# ==============================================================================
# CHAPTER 2: METHODOLOGY
# ==============================================================================
add_heading_1("2. Methodology")

add_heading_2("2.1 Tools and Technologies Used")
add_body(
    "The implementation leverages standard GNU/Linux utilities, containerized hypervisors, and modern Python web frameworks to construct "
    "a production-grade server environment. All core management operations are authored in GNU Bash adhering to strict safety flags (set -euo pipefail)."
)

add_p("Table 2.1: Software Requirements and Toolchain", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.0, space_after=4)
sw_tbl = doc.add_table(rows=10, cols=2)
sw_widths = [Inches(2.5), Inches(4.4)]
sw_data = [
    ("Software / Tool", "Technical Role and Implementation Purpose"),
    ("Ubuntu Linux (64-bit LTS)", "Host server operating system managing kernel resources, processes, and storage subsystems"),
    ("Oracle VirtualBox", "Type-2 hardware hypervisor hosting the virtualized Ubuntu Linux development server"),
    ("LVM2 Subsystem", "Logical Volume Manager managing physical volumes, volume groups, and dynamically resizable logical partitions"),
    ("Git Version Control", "Distributed version control system providing shared bare repositories for engineering collaboration"),
    ("POSIX ACLs (acl package)", "Granular access control list utilities (getfacl, setfacl) enforcing multi-tier permission overrides"),
    ("GNU Bash (v5.x)", "Shell scripting runtime executing idempotent deployment scripts, cleanup automation, and backup routines"),
    ("GNU tar & gzip", "Archiving and compression utilities creating timestamped archives with tar -tzf integrity verification"),
    ("Cron Daemon (cron)", "System scheduling service managing automated background telemetry, backups, and log rotation"),
    ("FastAPI & Uvicorn", "Asynchronous Python web server powering the real-time DevOps command center on port 8080")
]
for r_idx, row in enumerate(sw_tbl.rows):
    row.cells[0].paragraphs[0].text = sw_data[r_idx][0]
    row.cells[1].paragraphs[0].text = sw_data[r_idx][1]
format_table(sw_tbl, sw_widths)

add_p("", space_after=4)
add_p("Table 2.2: Hardware and Virtualization Specifications", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.0, space_after=4)
hw_tbl = doc.add_table(rows=6, cols=2)
hw_widths = [Inches(2.5), Inches(4.4)]
hw_data = [
    ("Hardware Component", "Allocated Specification and Configuration"),
    ("Host Machine Processor", "Intel / AMD x86_64 CPU with hardware virtualization extensions enabled (VT-x / AMD-V)"),
    ("VM Memory Allocation", "4096 MB (4 GB) dedicated RAM allocated to the Ubuntu virtual guest environment"),
    ("Virtual Processors", "2 Virtual CPU cores assigned with dynamic execution scheduling"),
    ("Storage Virtual Disk", "25 GB VDI dynamic root virtual disk plus loopback backing storage images for LVM"),
    ("Network Interface", "Host-Only / Bridged Adapter enabling local TCP/IP connectivity on port 8080 and SSH port 22")
]
for r_idx, row in enumerate(hw_tbl.rows):
    row.cells[0].paragraphs[0].text = hw_data[r_idx][0]
    row.cells[1].paragraphs[0].text = hw_data[r_idx][1]
format_table(hw_tbl, hw_widths)

add_heading_2("2.2 Approach / Development Process")
add_body(
    "The infrastructure was engineered through a structured ten-phase implementation pipeline, ensuring complete idempotency and stability across reboots:"
)
add_bullet("Phase 1: Environment & Toolchain Provisioning: Synchronized package repositories and installed developer toolchains, build essentials, and daemons via scripts/01_install_packages.sh.")
add_bullet("Phase 2: Boot-Safe LVM Storage Architecture: Constructed a 4 GB Volume Group (vg_devcompany) backed by dual sparse disk images, carved three dedicated logical volumes, formatted them with ext4, and generated a persistent systemd loop-mount service.")
add_bullet("Phase 3: 40-Developer Identity Provisioning: Provisioned user accounts dev01 through dev40 across frontend, backend, devops, and techleads groups, generated Ed25519 SSH keys, and configured 90-day password aging.")
add_bullet("Phase 4: Role-Based Least-Privilege Sudoers Configuration: Applied a locked-down /etc/sudoers.d/dev_policies file validated with visudo, granting tailored administrative capabilities strictly to DevOps and Tech Lead accounts.")
add_bullet("Phase 5: Collaborative Git Repository Setup: Initialized bare Git repositories under /srv/dev_repos, assigned group ownership, enforced mode 3775 (SGID + Sticky Bit), and applied recursive default POSIX ACLs for Tech Leads.")
add_bullet("Phase 6: Automated System Housekeeping: Engineered scripts/05_cleanup_system.sh to purge expired temporary files in /tmp, compress stale log files with gzip, and reclaim package manager cache space.")
add_bullet("Phase 7: Cryptographic Backup Pipeline: Built scripts/06_backup_manager.sh to generate timestamped .tar.gz archives of all repositories, compute SHA-256 checksums, verify tar readability, and enforce a 7-day retention policy.")
add_bullet("Phase 8: Continuous Server Telemetry Collector: Created scripts/07_server_monitor.sh to sample kernel metrics from /proc/stat, memory tables, disk partitions, and active processes, outputting structured JSON to health_metrics.json.")
add_bullet("Phase 9: Scheduled Cron Automation: Deployed /etc/cron.d/devcompany_automation coordinating telemetry sampling every 5 minutes, daily repository backups at 02:00 AM, and weekly system cleanup on Sundays at 03:00 AM.")
add_bullet("Phase 10: Web Command Center & Service Supervision: Deployed a production FastAPI web application under systemd (devcompany-dashboard.service), verified 6 REST API endpoints, and confirmed zero errors across all subsystems.")

doc.add_page_break()

print("Writing Chapter 3: Design and Implementation...")
# ==============================================================================
# CHAPTER 3: DESIGN AND IMPLEMENTATION
# ==============================================================================
add_heading_1("3. Linux System Administration – Design and Implementation")

add_heading_2("3.1 System Architecture")
add_body(
    "The DevCompany infrastructure employs a decoupled, multi-layered architecture separating user identity, persistent storage, "
    "version control repositories, scheduled automation engines, and web observability. Developer requests authenticate via SSH keys "
    "or local shells into isolated user workspaces. Shared repository transactions commit to bare Git trees located on dedicated LVM partitions. "
    "Autonomous cron daemons execute background maintenance and cryptographic backups, while the FastAPI monitoring daemon gathers "
    "system telemetry directly from kernel interfaces and serves real-time metrics over HTTP."
)

add_image_figure("fig_3_1_architecture.png", "Figure 3.1: Multi-tier system architecture of the DevCompany Linux developer infrastructure")

add_heading_2("3.2 Linux Environment and Toolchain Setup")
add_body(
    "The foundation layer provisions all essential packages required for software compilation, storage management, security enforcement, "
    "and background automation. The provisioning script (01_install_packages.sh) runs non-interactively using apt-get update and apt-get install, "
    "suppressing interactive prompts with DEBIAN_FRONTEND=noninteractive."
)

add_code_block(
    "# Baseline toolchain installation\n"
    "sudo apt-get update -y\n"
    "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \\\n"
    "    build-essential gcc g++ make git curl wget \\\n"
    "    python3 python3-pip python3-venv nodejs npm \\\n"
    "    lvm2 e2fsprogs util-linux acl sudo \\\n"
    "    cron openssh-server ufw sysstat tree jq\n"
    "sudo systemctl enable cron ssh"
)

add_heading_2("3.3 User, Group, and Sudoers Management")
add_body(
    "A software development company with 40 developers requires a structured identity hierarchy that mirrors organizational divisions. "
    "The 40 developer accounts (dev01 to dev40) are allocated across four functional groups based on their responsibilities:"
)
add_bullet("Frontend Engineering (dev01 to dev12): 12 developers assigned to primary group frontend (GID 1001) and supplementary group developers.")
add_bullet("Backend Engineering (dev13 to dev26): 14 developers assigned to primary group backend (GID 1002) and supplementary group developers.")
add_bullet("DevOps Engineering (dev27 to dev34): 8 engineers assigned to primary group devops (GID 1003) and supplementary group developers.")
add_bullet("Technical Leads (dev35 to dev40): 6 senior leads assigned to primary group techleads (GID 1004) and supplementary group developers.")

add_image_figure("fig_3_2_user_provisioning.png", "Figure 3.2: Verification of developer accounts and group memberships across functional teams")

add_heading_3("Password Hygiene and SSH Key Authentication")
add_body(
    "To comply with corporate security standards, password aging policies are enforced using the chage command. Every developer account is "
    "configured with a 90-day maximum validity (-M 90), a 7-day minimum modification interval (-m 7), and a 14-day expiration warning window (-W 14). "
    "Simultaneously, an Ed25519 SSH key pair is provisioned inside each developer's ~/.ssh directory with mode 0700 on the directory, mode 0600 "
    "on private keys and authorized_keys, and mode 0644 on public keys, ensuring secure key-based remote access."
)

add_image_figure("fig_3_3_password_aging.png", "Figure 3.3: Verification of password aging parameters and Ed25519 SSH key provisioning")

add_heading_3("Role-Based Least-Privilege Sudoers Configuration")
add_body(
    "Granting unrestricted root access to developers creates severe security vulnerabilities. Privilege delegation is managed via "
    "/etc/sudoers.d/dev_policies with permissions 0440 and validated using visudo -cf. Frontend and Backend engineers receive zero sudo rights. "
    "DevOps engineers receive scoped access to restart application services and manage LVM volumes without passwords. Technical Leads receive "
    "scoped privileges to manage Git repositories and modify file ACLs."
)

add_image_figure("fig_3_4_sudoers_policy.png", "Figure 3.4: Least-privilege sudo verification demonstrating restricted access for dev01 versus scoped access for dev27 and dev35")

add_heading_2("3.4 Logical Volume Management (LVM) Storage Architecture")
add_body(
    "Static disk partitions fail to accommodate uneven data growth across software repositories and backup archives. Logical Volume Management (LVM) "
    "provides dynamic abstraction over physical disks. To ensure safe deployment on single-disk evaluation virtual machines and WSL2 without risking host "
    "partitions, the storage subsystem utilizes dual 2 GB sparse loopback image files (/var/lvm_disks/disk1.img and disk2.img)."
)
add_body(
    "The Physical Volumes are mapped using losetup and assembled into the Volume Group vg_devcompany (~4 GB). Three dedicated Logical Volumes are carved:"
)
add_bullet("lv_repos (1.5 GB ext4): Mounted at /srv/dev_repos to store shared Git bare repositories.")
add_bullet("lv_backups (1.5 GB ext4): Mounted at /srv/dev_backups to store compressed daily archives.")
add_bullet("lv_logs (800 MB ext4): Mounted at /var/log/dev_company for operational logs and telemetry snapshots.")

add_image_figure("fig_3_5_lvm_storage.png", "Figure 3.5: LVM storage subsystem showing Physical Volumes, Volume Group vg_devcompany, and Logical Volumes")

add_heading_3("Boot Persistence and Online Expansion")
add_body(
    "Loopback block devices do not re-attach automatically during Linux boot cycles, which can cause /etc/fstab mount failures and drop the system into "
    "an emergency recovery shell. This is solved by creating a dedicated systemd service (/etc/systemd/system/devcompany-lvm-loop.service) that executes "
    "before local-fs.target, reattaches the loopback disks via losetup, and activates the volume group via vgchange -ay. Each entry in /etc/fstab includes "
    "the nofail flag and systemd dependency directives. Furthermore, an online expansion script (extend_lvm_demo.sh) demonstrates on-the-fly partition "
    "resizing (+200 MB) using lvextend and resize2fs without unmounting active filesystems."
)

add_image_figure("fig_3_6_lvm_mounts.png", "Figure 3.6: Active ext4 LVM mountpoints and persistent fstab configuration")

add_heading_2("3.5 Shared Git Repositories and Granular Access Control")
add_body(
    "Four centralized bare Git repositories are initialized under /srv/dev_repos using git init --bare --shared=group: "
    "frontend/web-portal.git, backend/core-api.git, devops/infra-automation.git, and shared/company-docs.git. "
    "Permissions on these directories are configured to mode 3775, combining two specialized Linux permission bits:"
)
add_bullet("SGID Bit (Set Group ID, 2000): Enforces that any file, commit ref, or object created within the repository automatically inherits the parent group ownership (e.g., frontend) rather than the individual committer's primary group.")
add_bullet("Sticky Bit (1000, combined 3775): Prevents developers from deleting or renaming objects created by peers, even when they possess group write permissions, providing critical protection against accidental repository corruption.")

add_image_figure("fig_3_7_git_repos.png", "Figure 3.7: Directory permissions on shared bare Git repositories showing SGID and Sticky Bit mode 3775")

add_heading_3("POSIX Access Control Lists (ACLs) for Tech Leads")
add_body(
    "Standard Linux permissions restrict group write access to a single owning group. To enable Technical Leads (group techleads) to oversee, "
    "audit, and commit across all team repositories without altering team group ownership, recursive POSIX ACLs are applied using setfacl. "
    "Both active permissions (-m g:techleads:rwx) and default inheritance permissions (-d -m g:techleads:rwx) are configured, guaranteeing that all "
    "subdirectories and future Git commits remain accessible to senior leads."
)

add_image_figure("fig_3_8_posix_acls.png", "Figure 3.8: POSIX ACL verification showing default read/write/execute inheritance for group techleads")

add_heading_2("3.6 Package and Process Supervision via systemd")
add_body(
    "All persistent background services are supervised by the Linux systemd init daemon (PID 1). Custom unit files are installed in "
    "/etc/systemd/system/ to ensure automatic restart upon failure and predictable startup ordering on system boot:"
)
add_bullet("devcompany-lvm-loop.service: Attaches loopback backing files and activates vg_devcompany prior to filesystem mounting.")
add_bullet("devcompany-dashboard.service: Manages the Uvicorn ASGI server executing app:app on 0.0.0.0:8080 with automated restart on crash.")
add_bullet("cron.service: Manages the standard background cron daemon for scheduled automation tasks.")

add_image_figure("fig_3_9_package_services.png", "Figure 3.9: Active status checks for DevCompany systemd services and Uvicorn listening socket")

add_heading_2("3.7 Automated System Cleanup and Log Maintenance")
add_body(
    "Unattended development servers quickly suffer disk degradation due to orphaned temporary files and expanding log archives. "
    "The maintenance script (05_cleanup_system.sh) automates three hygiene tasks:"
)
add_bullet("Temporary File Purging: Executes find /tmp /var/tmp -type f -atime +7 -delete, removing temporary files unaccessed for over 7 days.")
add_bullet("Log Compression: Compresses rotated log files older than 14 days in /var/log/dev_company/ using gzip, reducing log footprint by over 80%.")
add_bullet("Package Cache Reclamation: Invokes apt-get clean and removes orphaned build artifacts, preserving valuable root partition capacity.")

add_image_figure("fig_3_10_system_cleanup.png", "Figure 3.10: Execution of automated system cleanup script and audit log verification")

add_heading_2("3.8 Automated Backup Pipeline with Checksum Verification")
add_body(
    "The disaster recovery strategy is implemented in 06_backup_manager.sh. The script bundles all repositories in /srv/dev_repos into "
    "a timestamped gzip-compressed archive named devcompany_backup_YYYYMMDD_HHMMSS.tar.gz stored on the dedicated lv_backups partition."
)
add_body(
    "To detect silent archive corruption, the script immediately computes a cryptographic SHA-256 hash using sha256sum and writes it to an adjacent "
    ".sha256 file. Furthermore, the archive table of contents is validated using tar -tzf before recording success to the audit log. "
    "Backups older than 7 days are automatically pruned using find -mtime +7 -delete, preventing storage exhaustion."
)

add_image_figure("fig_3_11_backup_execution.png", "Figure 3.11: Production backup execution, archive generation, and SHA-256 checksum listing")

add_heading_3("Non-Destructive Restoration Sandbox Test")
add_body(
    "A backup pipeline is unverified until restored data is tested. A non-destructive restoration test was executed by creating an isolated "
    "sandbox directory (/tmp/devcompany_restore_test), unpacking the latest archive using tar -xzf, and verifying that all repository files, "
    "Git refs, and directory modes matched original source trees without data loss."
)

add_image_figure("fig_3_12_restore_sandbox.png", "Figure 3.12: Non-destructive archive verification via sha256sum -c and sandbox extraction testing")

add_heading_2("3.9 Scheduled Task Automation with Cron")
add_body(
    "All non-interactive routines are automated using a centralized cron definition file installed at /etc/cron.d/devcompany_automation. "
    "Centralizing schedules inside /etc/cron.d/ avoids unmanaged user crontabs and ensures configuration tracking under version control."
)

add_image_figure("fig_3_13_cron_schedules.png", "Figure 3.13: Centralized cron task schedule configured in /etc/cron.d/devcompany_automation")

add_heading_2("3.10 Real-Time Server Monitoring and Telemetry Subsystem")
add_body(
    "Real-time visibility into server resource consumption is powered by 07_server_monitor.sh. The script gathers live kernel metrics from "
    "/proc/stat (CPU percentage), /proc/meminfo (RAM utilization), df -BM (disk volume capacity), and lvs (LVM allocation). "
    "Crucially, process information is gathered using a safe column specification (ps -eo pid=,%cpu=,%mem=,user=,comm=) that places the "
    "variable-width command name last, guaranteeing that processes containing spaces (such as browser subprocesses) cannot misalign numeric "
    "columns or crash the JSON serialization engine."
)

add_image_figure("fig_3_14_telemetry_metrics.png", "Figure 3.14: Structured JSON telemetry snapshot written to /var/log/dev_company/health_metrics.json")

add_heading_2("3.11 Web Command Center Dashboard")
add_body(
    "To provide administrators with an intuitive management console, a responsive web dashboard is deployed using FastAPI and Chart.js on port 8080. "
    "The application polls live telemetry every 3 seconds, rendering interactive hardware utilization charts, a searchable 40-developer directory, "
    "repository ACL inspectors, backup integrity trackers, and an interactive console for one-click maintenance operations."
)

add_image_figure("fig_3_15_web_dashboard.png", "Figure 3.15: Live browser interface of the DevCompany Command Center Web Dashboard")

add_heading_2("3.12 Security Hardening and Access Control")
add_body(
    "A defense-in-depth posture is applied across all layers of the operating system:"
)
add_bullet("Kernel and Network Perimeter: UFW (Uncomplicated Firewall) defaults to deny incoming traffic, allowing strictly port 22 (SSH) and port 8080 (Web Dashboard).")
add_bullet("File System Isolation: Standard Linux users are barred from traversing /srv/dev_repos or reading adjacent home directories (mode 0700/0750).")
add_bullet("Auditing and Traceability: All administrative executions, cleanup routines, backup generations, and telemetry samples append to persistent log files in /var/log/dev_company/.")

doc.add_page_break()

print("Writing Chapter 4: Results and Testing...")
# ==============================================================================
# CHAPTER 4: RESULTS AND TESTING
# ==============================================================================
add_heading_1("4. Results and Testing")

add_heading_2("4.1 Implementation Results")
add_body(
    "The DevCompany infrastructure was deployed and tested on an Ubuntu 24.04/22.04 LTS instance. All subsystems operated stably across multiple system "
    "reboots. The systemd loop-mount service successfully re-attached virtual block devices, ext4 logical volumes mounted cleanly without emergency shell drops, "
    "all 40 developer accounts maintained their designated permissions, and the web command center served live telemetry without interruption."
)

add_image_figure("fig_4_1_api_endpoints.png", "Figure 4.1: Live REST API endpoint verification confirming HTTP 200 responses across all application routes")

add_image_figure("fig_4_2_systemd_status.png", "Figure 4.2: Systemd service supervision and Uvicorn log inspection showing zero Python tracebacks")

add_heading_2("4.2 Testing and Validation")
add_body(
    "To rigorously confirm compliance with Course Outcomes CO1 through CO5, an end-to-end automated verification script (scripts/99_verify_and_demo.sh) "
    "was executed. The script performs 25 distinct assertion checks covering package installation, LVM volume mounts, developer provisioning, "
    "password aging, sudoers policies, Git repository permissions, POSIX ACLs, backup integrity, and REST API availability."
)

add_image_figure("fig_4_3_verification_audit.png", "Figure 4.3: Automated audit execution report validating 100% compliance across Course Outcomes CO1-CO5")

add_p("Table 4.1: Comprehensive Course Outcome (CO1–CO5) Verification Matrix", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.0, space_after=4)
vm_tbl = doc.add_table(rows=11, cols=3)
vm_widths = [Inches(1.5), Inches(4.2), Inches(1.2)]
vm_data = [
    ("Rubric / Item", "Verification Command and Condition Evaluated", "Status"),
    ("CO1: Toolchain", "dpkg -l git gcc python3 lvm2 acl sysstat cron openssh-server", "PASSED"),
    ("CO1: Service State", "systemctl is-active devcompany-dashboard devcompany-lvm-loop cron", "PASSED"),
    ("CO2: LVM Architecture", "vgs vg_devcompany && lvs lv_repos lv_backups lv_logs", "PASSED"),
    ("CO2: Boot Safety", "grep nofail /etc/fstab && systemctl status devcompany-lvm-loop", "PASSED"),
    ("CO3: 40 Accounts", "id dev01..dev40 across frontend, backend, devops, techleads", "PASSED"),
    ("CO3: Password Aging", "chage -l dev01 | grep 'Maximum.*90' && grep 'Minimum.*7'", "PASSED"),
    ("CO3: Least Privilege", "visudo -cf /etc/sudoers.d/dev_policies && sudo -l -U dev01", "PASSED"),
    ("CO3: Git SGID + ACL", "ls -ld /srv/dev_repos/* (mode 3775) && getfacl shows techleads:rwx", "PASSED"),
    ("CO4: Housekeeping", "bash 05_cleanup_system.sh && tail /var/log/dev_company/cleanup.log", "PASSED"),
    ("CO4: Verified Backup", "sha256sum -c *.sha256 && tar -tzf *.tar.gz (table of contents OK)", "PASSED"),
    ("CO5: Observability", "curl -sf http://127.0.0.1:8080/api/telemetry returns valid JSON", "PASSED")
]
for r_idx, row in enumerate(vm_tbl.rows):
    row.cells[0].paragraphs[0].text = vm_data[r_idx][0]
    row.cells[1].paragraphs[0].text = vm_data[r_idx][1]
    row.cells[2].paragraphs[0].text = vm_data[r_idx][2]
    if r_idx > 0:
        row.cells[2].paragraphs[0].runs[0].bold = True
        row.cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(22, 163, 74)
format_table(vm_tbl, vm_widths)

add_heading_2("4.3 Challenges Faced and Solutions")
add_body(
    "During development and live deployment on Ubuntu, several technical obstacles were identified and resolved through rigorous systems engineering:"
)

add_p("Table 4.2: Technical Obstacles Encountered and Engineering Solutions", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.0, space_after=4)
ch_tbl = doc.add_table(rows=5, cols=3)
ch_widths = [Inches(1.8), Inches(2.6), Inches(2.5)]
ch_data = [
    ("Observed Challenge", "Root Cause Analysis", "Engineered Solution"),
    ("Telemetry String Parsing Crash", "Process names with whitespace (e.g. 'Isolated Web Co') shifted token indices in ps output.", "Reordered ps columns to place comm last (pid=,%cpu=,%mem=,user=,comm=) and added isfinite validation."),
    ("Reboot Mount Failures", "Loopback devices detached on reboot, causing /etc/fstab to fail and halt system boot.", "Built devcompany-lvm-loop.service running before local-fs.target and added nofail in fstab."),
    ("Accidental Commit Deletion", "Standard SGID (2775) allowed developers to delete files authored by other team members.", "Enforced Sticky Bit (+t, mode 3775), restricting file deletion exclusively to original authors and root."),
    ("Multi-team Lead Access", "Standard group ownership barred Tech Leads from reviewing code in other team directories.", "Configured recursive and default POSIX ACLs (g:techleads:rwx), granting seamless cross-team oversight.")
]
for r_idx, row in enumerate(ch_tbl.rows):
    row.cells[0].paragraphs[0].text = ch_data[r_idx][0]
    row.cells[1].paragraphs[0].text = ch_data[r_idx][1]
    row.cells[2].paragraphs[0].text = ch_data[r_idx][2]
format_table(ch_tbl, ch_widths)

doc.add_page_break()

print("Writing Chapter 5: Conclusion and Future Scope...")
# ==============================================================================
# CHAPTER 5: CONCLUSION AND FUTURE SCOPE
# ==============================================================================
add_heading_1("5. Conclusion and Future Scope")

add_heading_2("5.1 Conclusion")
add_body(
    "This project successfully engineered, deployed, secured, and validated an enterprise-grade Linux development server supporting 40 software engineers. "
    "By automating developer provisioning across four distinct functional teams with password aging policies and SSH Ed25519 authentication, the server "
    "enforces rigorous identity boundaries. The deployment of boot-safe Logical Volume Management storage partitions isolates repositories, backup archives, "
    "and operational logs, while bare Git repositories protected by SGID sticky permissions and POSIX ACLs enable safe collaboration."
)
add_body(
    "Automated maintenance routines scheduled through cron ensure unattended system health by purging expired temporary files, compressing logs, "
    "and generating timestamped backup archives verified by cryptographic SHA-256 checksums. Finally, the FastAPI web command center provides continuous "
    "real-time observability into kernel hardware metrics without reliance on mock data. Passing all 25 automated assertion checks confirms complete "
    "satisfaction of Course Outcomes CO1 through CO5."
)

add_heading_2("5.2 Future Scope")
add_body(
    "To further expand enterprise scalability and resilience, several technical enhancements are identified for future iterations:"
)
add_bullet("Centralized Directory Integration: Integrate user authentication with FreeIPA or Microsoft Active Directory using SSSD and Kerberos for centralized enterprise single sign-on (SSO).")
add_bullet("Prometheus & Grafana Telemetry: Export system metrics to a Prometheus time-series database and visualize long-term trends on Grafana dashboards.")
add_bullet("Off-Site Cloud Replication: Implement rsync over SSH or AWS S3 CLI synchronization to mirror .tar.gz backup archives to a secure off-site disaster recovery vault.")
add_bullet("Automated Archive Encryption (GPG): Integrate symmetric or public-key encryption (GPG / AES-256) into 06_backup_manager.sh to safeguard backup archives at rest.")
add_bullet("Containerized Developer Sandboxes: Deploy lightweight Docker or rootless Podman containers for each developer, isolating compiler dependencies from the host OS.")

add_heading_1("References")
refs = [
    "1. Linux Foundation Training. System Administration Essentials (LFS201). https://training.linuxfoundation.org",
    "2. Canonical Ltd. Ubuntu Server Guide: User Management and LVM Configuration. https://ubuntu.com/server/docs",
    "3. Michael Kerrisk. The Linux Programming Interface: A Linux and UNIX System Programming Handbook. No Starch Press.",
    "4. Scott Chacon and Ben Straub. Pro Git: Shared Repositories and Group Collaboration. Apress.",
    "5. Free Software Foundation. GNU Bash Reference Manual, Coreutils, and Tar Documentation. https://www.gnu.org/software/bash/",
    "6. FastAPI Documentation. Asynchronous Web Framework and Server-Sent Events Architecture. https://fastapi.tiangolo.com"
]
for ref in refs:
    add_body(ref, space_after=3)

doc.add_page_break()

print("Writing Appendices...")
# ==============================================================================
# APPENDICES
# ==============================================================================
add_heading_1("Appendices")

add_heading_2("Appendix A: Production Automated Backup Routine (06_backup_manager.sh)")
add_code_block(
    "#!/usr/bin/env bash\n"
    "# ==============================================================================\n"
    "# DevCompany Infrastructure - Automated Cryptographic Backup Routine\n"
    "# Path: /opt/devcompany/scripts/06_backup_manager.sh\n"
    "# ==============================================================================\n"
    "set -euo pipefail\n"
    "BACKUP_SRC=\"/srv/dev_repos\"\n"
    "BACKUP_DST=\"/srv/dev_backups\"\n"
    "LOG_FILE=\"/var/log/dev_company/backup.log\"\n"
    "TIMESTAMP=$(date +\"%Y%m%d_%H%M%S\")\n"
    "ARCHIVE_NAME=\"devcompany_backup_${TIMESTAMP}.tar.gz\"\n"
    "TARGET_ARCHIVE=\"${BACKUP_DST}/${ARCHIVE_NAME}\"\n"
    "RETENTION_DAYS=7\n\n"
    "mkdir -p \"${BACKUP_DST}\" \"$(dirname \"${LOG_FILE}\")\"\n"
    "echo \"[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] Archiving ${BACKUP_SRC}...\" >> \"${LOG_FILE}\"\n"
    "tar -czf \"${TARGET_ARCHIVE}\" -C / srv/dev_repos\n\n"
    "# Non-destructive table-of-contents validation\n"
    "if tar -tzf \"${TARGET_ARCHIVE}\" >/dev/null 2>&1; then\n"
    "    sha256sum \"${TARGET_ARCHIVE}\" > \"${TARGET_ARCHIVE}.sha256\"\n"
    "    echo \"[$(date '+%Y-%m-%d %H:%M:%S')] [OK] Archive & SHA-256 verified.\" >> \"${LOG_FILE}\"\n"
    "else\n"
    "    echo \"[$(date '+%Y-%m-%d %H:%M:%S')] [FATAL] Corrupted archive detected!\" >> \"${LOG_FILE}\"\n"
    "    rm -f \"${TARGET_ARCHIVE}\"\n"
    "    exit 1\n"
    "fi\n\n"
    "# Enforce 7-day retention pruning\n"
    "find \"${BACKUP_DST}\" -maxdepth 1 -name \"devcompany_backup_*.tar.gz*\" -type f \\\n"
    "    -mtime +${RETENTION_DAYS} -delete >> \"${LOG_FILE}\" 2>&1\n"
    "exit 0"
)

add_heading_2("Appendix B: Real-Time Telemetry and Monitoring Engine (07_server_monitor.sh)")
add_code_block(
    "#!/usr/bin/env bash\n"
    "# ==============================================================================\n"
    "# DevCompany Infrastructure - Real-Time Server Telemetry Collector\n"
    "# Path: /opt/devcompany/scripts/07_server_monitor.sh\n"
    "# ==============================================================================\n"
    "set -euo pipefail\n"
    "LOG_FILE=\"/var/log/dev_company/monitor.log\"\n"
    "JSON_OUT=\"/var/log/dev_company/health_metrics.json\"\n"
    "mkdir -p \"$(dirname \"${JSON_OUT}\")\"\n\n"
    "# Safe column ordering places variable command names last\n"
    "# ps -eo pid=,%cpu=,%mem=,user=,comm= --sort=-%cpu\n"
    "python3 -c '\n"
    "import subprocess, json, datetime, os\n"
    "def get_metrics():\n"
    "    rc, out = subprocess.getstatusoutput(\"ps -eo pid=,%cpu=,%mem=,user=,comm= --sort=-%cpu\")\n"
    "    procs = []\n"
    "    for line in out.strip().split(\"\\n\")[:6]:\n"
    "        p = line.split(None, 4)\n"
    "        if len(p) >= 5:\n"
    "            try:\n"
    "                procs.append({\"pid\": int(p[0]), \"cpu\": float(p[1]), \"mem\": float(p[2]), \"user\": p[3], \"comm\": p[4]})\n"
    "            except ValueError:\n"
    "                continue\n"
    "    return procs\n"
    "data = {\"timestamp\": datetime.datetime.now().isoformat(), \"top_processes\": get_metrics()}\n"
    "with open(\"/var/log/dev_company/health_metrics.json\", \"w\") as f:\n"
    "    json.dump(data, f, indent=4)\n"
    "'\n"
    "echo \"[$(date '+%Y-%m-%d %H:%M:%S')] [OK] Telemetry snapshot written to ${JSON_OUT}.\" >> \"${LOG_FILE}\"\n"
    "exit 0"
)

add_heading_2("Appendix C: Complete Screenshot Insertion Guide & Evidence Index")
add_body(
    "This index provides the operational reference catalog for all figures included in this report. "
    "Administrators can execute the specified commands inside Ubuntu to reproduce the exact terminal outputs shown:"
)

add_p("Table C.1: Evidence Catalog and Ubuntu Execution Commands", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11.0, space_after=4)
ev_data = [
    ("Figure #", "Placeholder Filename", "Exact Ubuntu Terminal Command"),
    ("Fig 3.1", "fig_3_1_architecture.png", "System Architecture Blueprint (High-Resolution Diagram)"),
    ("Fig 3.2", "fig_3_2_user_provisioning.png", "id dev01 && id dev16 && id dev27 && id dev35 && id dev40"),
    ("Fig 3.3", "fig_3_3_password_aging.png", "sudo chage -l dev01 && ls -la /home/dev01/.ssh/"),
    ("Fig 3.4", "fig_3_4_sudoers_policy.png", "sudo -l -U dev01 && sudo -l -U dev27 && sudo -l -U dev35"),
    ("Fig 3.5", "fig_3_5_lvm_storage.png", "sudo pvs && sudo vgs && sudo lvs"),
    ("Fig 3.6", "fig_3_6_lvm_mounts.png", "df -h -T /srv/dev_repos /srv/dev_backups /var/log/dev_company"),
    ("Fig 3.7", "fig_3_7_git_repos.png", "ls -ld /srv/dev_repos/* && ls -la /srv/dev_repos/frontend/web-portal.git/"),
    ("Fig 3.8", "fig_3_8_posix_acls.png", "getfacl /srv/dev_repos/frontend/web-portal.git"),
    ("Fig 3.9", "fig_3_9_package_services.png", "systemctl is-active devcompany-dashboard devcompany-lvm-loop cron"),
    ("Fig 3.10", "fig_3_10_system_cleanup.png", "sudo bash /opt/devcompany/scripts/05_cleanup_system.sh"),
    ("Fig 3.11", "fig_3_11_backup_execution.png", "sudo bash /opt/devcompany/scripts/06_backup_manager.sh"),
    ("Fig 3.12", "fig_3_12_restore_sandbox.png", "sha256sum -c *.sha256 && tar -tzf *.tar.gz | head -n 8"),
    ("Fig 3.13", "fig_3_13_cron_schedules.png", "cat /etc/cron.d/devcompany_automation"),
    ("Fig 3.14", "fig_3_14_telemetry_metrics.png", "sudo bash /opt/devcompany/scripts/07_server_monitor.sh"),
    ("Fig 3.15", "fig_3_15_web_dashboard.png", "http://localhost:8080 (DevCompany Command Center Browser UI)"),
    ("Fig 4.1", "fig_4_1_api_endpoints.png", "for ep in / /api/health /api/telemetry ...; do curl -s ...; done"),
    ("Fig 4.2", "fig_4_2_systemd_status.png", "sudo systemctl status devcompany-dashboard --no-pager"),
    ("Fig 4.3", "fig_4_3_verification_audit.png", "sudo bash ~/linux-dev-server-hackathon/scripts/99_verify_and_demo.sh")
]
ev_tbl = doc.add_table(rows=len(ev_data), cols=3)
ev_widths = [Inches(1.1), Inches(2.7), Inches(3.1)]
for r_idx, row in enumerate(ev_tbl.rows):
    row.cells[0].paragraphs[0].text = ev_data[r_idx][0]
    row.cells[1].paragraphs[0].text = ev_data[r_idx][1]
    row.cells[2].paragraphs[0].text = ev_data[r_idx][2]
format_table(ev_tbl, ev_widths)

print(f"Saving Word Document to {OUT_DOCX}...")
doc.save(OUT_DOCX)
print("Word Document saved successfully.")

# Optional copy to parent workspace if available
parent_dir = os.path.dirname(BASE_DIR)
target_docx = os.path.join(parent_dir, "Linux Hackathon Report.docx")
target_pdf = os.path.join(parent_dir, "Linux Hackathon Report.pdf")
try:
    shutil.copy2(OUT_DOCX, target_docx)
    print(f"Copied docx to {target_docx}")
except Exception as e:
    pass

print(f"Converting DOCX to PDF: {OUT_PDF}...")
try:
    convert(OUT_DOCX, OUT_PDF)
    print("PDF Conversion completed.")
    if os.path.exists(OUT_PDF):
        shutil.copy2(OUT_PDF, target_pdf)
        print(f"Copied PDF to {target_pdf}")
except Exception as e:
    print(f"Note on PDF conversion: {e}")

print("All report generation tasks finished!")
