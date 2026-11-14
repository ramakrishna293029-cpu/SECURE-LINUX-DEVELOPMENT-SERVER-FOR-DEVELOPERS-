/* DevCompany Linux Infrastructure Command Center - Enterprise Frontend Engine */

let telemetryChart = null;
let currentTeamFilter = "";
let activeStream = null;

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function initChart() {
  const ctx = document.getElementById("telemetryChart");
  if (!ctx || typeof Chart === "undefined") return;

  const canvasCtx = ctx.getContext("2d");
  
  // Create enterprise smooth area gradients
  const cpuGradient = canvasCtx.createLinearGradient(0, 0, 0, 240);
  cpuGradient.addColorStop(0, "rgba(6, 182, 212, 0.32)");
  cpuGradient.addColorStop(1, "rgba(6, 182, 212, 0.0)");

  const ramGradient = canvasCtx.createLinearGradient(0, 0, 0, 240);
  ramGradient.addColorStop(0, "rgba(16, 185, 129, 0.28)");
  ramGradient.addColorStop(1, "rgba(16, 185, 129, 0.0)");

  telemetryChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "CPU %",
          data: [],
          borderColor: "#06b6d4",
          backgroundColor: cpuGradient,
          tension: 0.35,
          fill: true,
          borderWidth: 2.2,
          pointRadius: 2,
          pointHoverRadius: 5,
          pointBackgroundColor: "#06b6d4",
          pointBorderColor: "#ffffff",
        },
        {
          label: "RAM %",
          data: [],
          borderColor: "#10b981",
          backgroundColor: ramGradient,
          tension: 0.35,
          fill: true,
          borderWidth: 2.2,
          pointRadius: 2,
          pointHoverRadius: 5,
          pointBackgroundColor: "#10b981",
          pointBorderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      interaction: {
        mode: "index",
        intersect: false,
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          grid: {
            color: "rgba(255, 255, 255, 0.04)",
            drawBorder: false,
          },
          ticks: {
            color: "#64748b",
            font: { family: "JetBrains Mono", size: 11 },
            stepSize: 25,
            callback: (v) => `${v}%`,
          },
        },
        x: {
          grid: { display: false },
          ticks: {
            color: "#64748b",
            maxTicksLimit: 8,
            font: { family: "JetBrains Mono", size: 10 },
          },
        },
      },
      plugins: {
        legend: {
          display: false, // Custom legend in HTML
        },
        tooltip: {
          backgroundColor: "rgba(11, 17, 32, 0.95)",
          borderColor: "rgba(255, 255, 255, 0.12)",
          borderWidth: 1,
          padding: 10,
          titleFont: { family: "JetBrains Mono", size: 12 },
          bodyFont: { family: "Plus Jakarta Sans", size: 12 },
          displayColors: true,
          boxPadding: 4,
          callbacks: {
            label: (context) => ` ${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`,
          },
        },
      },
    },
  });
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const badge = document.getElementById("provision-badge");
    const banner = document.getElementById("setup-banner");
    if (data.provisioned) {
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-indicator shadow-[0_0_8px_#34d399]"></span><span>PROVISIONED (${data.developer_count} DEVS)</span>`;
      badge.className = "px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 inline-flex items-center gap-1.5 shadow-sm";
      banner.classList.add("hidden");
    } else {
      badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span><span>SETUP REQUIRED</span>`;
      badge.className = "px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 inline-flex items-center gap-1.5 shadow-sm";
      banner.classList.remove("hidden");
    }
  } catch (err) {
    console.error("Health check error:", err);
  }
}

async function loadTelemetry() {
  try {
    const res = await fetch("/api/telemetry");
    const data = await res.json();

    document.getElementById("host-meta").innerHTML = `
      <span class="text-cyan-300">${esc(data.hostname)}</span>
      <span class="text-slate-600">&middot;</span>
      <span>${esc(data.kernel)}</span>
      <span class="text-slate-600">&middot;</span>
      <span class="text-slate-500">${esc(data.local_time)}</span>
    `;

    // CPU KPI
    const cpu = Number(data.cpu_percent || 0);
    document.getElementById("kpi-cpu").textContent = `${cpu.toFixed(1)}%`;
    const cpuBar = document.getElementById("kpi-cpu-bar");
    cpuBar.style.width = `${Math.min(cpu, 100)}%`;
    cpuBar.className = `h-full rounded-full transition-all duration-300 ${
      cpu > 80
        ? "bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.7)]"
        : "bg-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.6)]"
    }`;

    const load = data.load_average || { "1m": 0, "5m": 0, "15m": 0 };
    document.getElementById("kpi-load").textContent = `load: ${load["1m"]} / ${load["5m"]}`;

    // RAM KPI
    const mem = data.memory || {};
    const ramPct = Number(mem.usage_percent || 0);
    document.getElementById("kpi-ram").textContent = `${ramPct.toFixed(1)}%`;
    document.getElementById("kpi-ram-detail").textContent = `${mem.used_mb || 0} / ${mem.total_mb || 0} MB`;
    const ramBar = document.getElementById("kpi-ram-bar");
    ramBar.style.width = `${Math.min(ramPct, 100)}%`;
    ramBar.className = `h-full rounded-full transition-all duration-300 ${
      ramPct > 85
        ? "bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.7)]"
        : "bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.6)]"
    }`;

    // Developer Sessions KPI
    const sessions = data.ssh_sessions || [];
    document.getElementById("kpi-online").textContent = String(data.active_developers_online ?? sessions.length);
    document.getElementById("kpi-ssh-summary").innerHTML =
      sessions.length > 0
        ? `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span><span>Active SSH: ${sessions.map((s) => esc(s.user)).join(", ")}</span>`
        : `<span class="w-1.5 h-1.5 rounded-full bg-slate-600"></span><span>No active developer SSH sessions</span>`;

    document.getElementById("kpi-uptime").textContent = data.uptime || "--";

    // Service Status Pills
    const svcs = data.services || {};
    const svcItems = [
      ["cron", svcs.cron],
      ["ssh", svcs.ssh],
      ["lvm-loop", svcs.devcompany_lvm_loop],
    ];
    document.getElementById("service-pills").innerHTML = svcItems
      .map(([name, state]) => {
        const ok = state === "active";
        const dotCls = ok ? "bg-emerald-400 pulse-indicator" : "bg-slate-500";
        const borderCls = ok
          ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30 shadow-sm"
          : "bg-slate-800 text-slate-400 border-slate-700/80";
        return `<span class="px-2.5 py-0.5 rounded-md border text-[10px] inline-flex items-center gap-1.5 ${borderCls}"><span class="w-1.5 h-1.5 rounded-full ${dotCls}"></span><span>${esc(name)}: ${esc(state || "unknown")}</span></span>`;
      })
      .join("");

    // Alerts
    const alertBanner = document.getElementById("alert-banner");
    const alerts = data.alerts || [];
    if (alerts.length > 0) {
      document.getElementById("alert-banner-text").innerHTML = alerts
        .map((a) => `<div>${esc(a.message)}</div>`)
        .join("");
      alertBanner.classList.remove("hidden");
    } else {
      alertBanner.classList.add("hidden");
    }

    // Chart update
    if (telemetryChart && Array.isArray(data.history)) {
      telemetryChart.data.labels = data.history.map((h) => h.time);
      telemetryChart.data.datasets[0].data = data.history.map((h) => h.cpu);
      telemetryChart.data.datasets[1].data = data.history.map((h) => h.memory);
      telemetryChart.update();
    }

    // LVM volumes (Rich distinct card rows)
    const disks = data.disks || [];
    const lvmContainer = document.getElementById("lvm-volumes");
    if (disks.length === 0) {
      lvmContainer.innerHTML = `<p class="text-xs text-slate-400">No mounted LVM volumes detected yet.</p>`;
    } else {
      lvmContainer.innerHTML = disks
        .map((d) => {
          const pct = Number(d.usage_percent || 0);
          const isFull = pct > 85;
          let barColor = isFull
            ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.7)]"
            : d.name === "root"
            ? "bg-slate-400"
            : d.name === "lv_repos"
            ? "bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.6)]"
            : d.name === "lv_backups"
            ? "bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.6)]"
            : "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.6)]";

          return `
            <div class="rounded-xl border border-slate-800/80 bg-slate-900/50 p-2.5 hover:border-slate-700/80 transition">
              <div class="flex items-center justify-between text-xs mb-1.5 font-mono">
                <div class="flex items-center gap-2">
                  <span class="text-white font-bold">${esc(d.name)}</span>
                  <span class="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-cyan-300/90 border border-slate-700/60">${esc(d.mount)}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-400 text-[11px]">${esc(d.used_mb)} / ${esc(d.total_mb)} MB</span>
                  <span class="px-1.5 py-0.2 rounded text-[10px] font-bold ${isFull ? "bg-rose-500/20 text-rose-300 border border-rose-500/40" : "bg-slate-800 text-slate-300"}">${pct}%</span>
                </div>
              </div>
              <div class="h-2 rounded-full bg-slate-800 overflow-hidden p-0.5 border border-slate-700/40">
                <div class="h-full ${barColor} rounded-full transition-all duration-300" style="width: ${Math.min(pct, 100)}%"></div>
              </div>
            </div>`;
        })
        .join("");
    }

    // Top processes (Clean structured mini-table)
    const procs = data.top_processes || [];
    const topContainer = document.getElementById("top-processes");
    if (procs.length === 0) {
      topContainer.innerHTML = `<div class="text-slate-500 text-xs">No process telemetry available.</div>`;
    } else {
      topContainer.innerHTML = procs
        .slice(0, 4)
        .map(
          (p) => `
          <div class="flex items-center justify-between py-1 px-2 rounded-lg bg-slate-900/60 border border-slate-800/60 text-xs">
            <div class="flex items-center gap-2 truncate">
              <span class="text-slate-500 font-mono text-[11px]">#${esc(p.pid)}</span>
              <span class="text-white font-semibold truncate">${esc(p.command)}</span>
              <span class="text-slate-500 text-[10px]">(${esc(p.user)})</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0 font-mono text-[11px]">
              <span class="px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">${p.cpu_percent}% CPU</span>
              <span class="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">${p.mem_percent}% RAM</span>
            </div>
          </div>`
        )
        .join("");
    }

    // Recent logs
    const logs = data.recent_logs || [];
    if (logs.length > 0) {
      document.getElementById("recent-logs-box").textContent = logs.join("\n");
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (err) {
    console.error("Telemetry error:", err);
  }
}

async function loadDevelopers() {
  const q = document.getElementById("dev-search").value || "";
  const params = new URLSearchParams();
  if (currentTeamFilter) params.set("team", currentTeamFilter);
  if (q) params.set("q", q);

  try {
    const res = await fetch(`/api/developers?${params.toString()}`);
    const data = await res.json();
    const tbody = document.getElementById("developers-tbody");
    const rows = data.developers || [];
    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-4 py-8 text-center text-slate-400">No developer accounts match the current search or filter.</td></tr>`;
      return;
    }

    const teamStyles = {
      frontend: { badge: "bg-sky-500/15 text-sky-300 border-sky-500/30", avatar: "bg-sky-500/20 text-sky-300 border-sky-500/40" },
      backend: { badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30", avatar: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" },
      devops: { badge: "bg-amber-500/15 text-amber-300 border-amber-500/30", avatar: "bg-amber-500/20 text-amber-300 border-amber-500/40" },
      techleads: { badge: "bg-purple-500/15 text-purple-300 border-purple-500/30", avatar: "bg-purple-500/20 text-purple-300 border-purple-500/40" },
    };

    tbody.innerHTML = rows
      .map((d) => {
        const tconf = teamStyles[d.team] || { badge: "bg-slate-800 text-slate-300 border-slate-700", avatar: "bg-slate-800 text-slate-300 border-slate-700" };
        const initials = esc(d.username.toUpperCase());

        const sudoBadge =
          d.sudo_access === "None"
            ? `<span class="px-2 py-0.5 rounded text-[11px] text-slate-400 bg-slate-800/60 border border-slate-700/50">Restricted (None)</span>`
            : `<span class="px-2.5 py-0.5 rounded text-[11px] text-amber-300 bg-amber-500/15 border border-amber-500/30 font-semibold inline-flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-amber-400 pulse-indicator"></span>${esc(d.sudo_access)}</span>`;

        const sshBadge = d.ssh_key_present
          ? `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span><span>ed25519 ready</span></span>`
          : `<span class="px-2 py-0.5 rounded text-[11px] text-slate-500 bg-slate-800">pending</span>`;

        return `
          <tr class="hover:bg-slate-800/40 transition">
            <td class="px-4 py-2.5">
              <div class="flex items-center gap-2.5">
                <div class="w-7 h-7 rounded-lg ${tconf.avatar} border flex items-center justify-center font-bold text-[11px]">
                  ${initials.slice(-3)}
                </div>
                <span class="text-white font-bold text-xs tracking-wide">${esc(d.username)}</span>
              </div>
            </td>
            <td class="px-4 py-2.5">
              <span class="px-2.5 py-0.5 rounded-full border text-[11px] font-semibold ${tconf.badge}">${esc(d.team)}</span>
            </td>
            <td class="px-4 py-2.5 text-slate-300">
              <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">${esc(d.uid)}</span>
              <span class="text-slate-500 text-[11px] ml-1.5">${esc(d.shell)}</span>
            </td>
            <td class="px-4 py-2.5 text-slate-400 text-xs">${esc(d.password_aging)}</td>
            <td class="px-4 py-2.5">${sshBadge}</td>
            <td class="px-4 py-2.5">${sudoBadge}</td>
          </tr>`;
      })
      .join("");

    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (err) {
    console.error("Developers error:", err);
  }
}

async function loadRepos() {
  try {
    const res = await fetch("/api/repos");
    const data = await res.json();
    const grid = document.getElementById("repos-grid");
    grid.innerHTML = (data.teams || [])
      .map((t) => {
        const modeBadge = t.exists
          ? `<span class="px-2.5 py-1 rounded-md font-mono text-xs font-semibold ${
              t.sgid && t.sticky
                ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm"
                : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
            }">mode ${esc(t.mode)} ${t.sgid ? "SGID" : ""} ${t.sticky ? "+Sticky" : ""}</span>`
          : `<span class="px-2.5 py-1 rounded-md font-mono text-xs bg-slate-800 text-slate-400 border border-slate-700">not created</span>`;

        const reposHtml = (t.repos || []).length
          ? t.repos
              .map(
                (r) => `
                <div class="rounded-xl bg-slate-950/80 border border-slate-800/90 p-3 text-xs hover:border-slate-700 transition">
                  <div class="flex items-center justify-between font-mono">
                    <span class="font-bold text-cyan-300 flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                      <span>${esc(r.name)}</span>
                    </span>
                    <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">${r.commit_count} commit(s)</span>
                  </div>
                  <div class="text-slate-400 mt-2 font-mono text-[11px] truncate flex items-center gap-1.5">
                    <span class="text-slate-600">ref:</span>
                    <span>${esc(r.last_commit)}</span>
                  </div>
                </div>`
              )
              .join("")
          : `<div class="text-xs text-slate-500 font-mono py-2">No bare repositories found.</div>`;

        const aclText = (t.acl_lines || []).length
          ? t.acl_lines.join("\n")
          : "Run on Linux host to inspect live getfacl entries.";

        return `
          <div class="glass-panel rounded-2xl border border-slate-800 p-5 space-y-4 hover:border-slate-700/80 transition shadow-lg">
            <div class="flex items-center justify-between gap-3 pb-3 border-b border-slate-800">
              <div>
                <h3 class="text-sm font-bold text-white uppercase tracking-wider">${esc(t.team)}</h3>
                <p class="text-xs font-mono text-slate-400 mt-0.5">${esc(t.path)} <span class="text-cyan-400">(${esc(t.owner_group)})</span></p>
              </div>
              ${modeBadge}
            </div>

            <div class="space-y-2.5">${reposHtml}</div>

            <details class="text-xs group">
              <summary class="cursor-pointer text-slate-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1.5 transition">
                <span>View POSIX ACLs (getfacl)</span>
              </summary>
              <pre class="mt-2.5 rounded-xl bg-[#040711] border border-slate-800/90 p-3 text-[11px] font-mono text-emerald-300 overflow-x-auto leading-relaxed shadow-inner">${esc(aclText)}</pre>
            </details>
          </div>`;
      })
      .join("");

    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (err) {
    console.error("Repos error:", err);
  }
}

async function loadBackups() {
  try {
    const res = await fetch("/api/backups");
    const data = await res.json();

    const cronGrid = document.getElementById("cron-grid");
    const jobs = data.cron_jobs || [];
    cronGrid.innerHTML = jobs.length
      ? jobs
          .map(
            (j) => `
          <div class="glass-panel rounded-xl border border-slate-800 p-3.5 hover:border-slate-700 transition">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="font-mono font-bold text-cyan-300 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">${esc(j.schedule)}</span>
              <span class="text-slate-400 font-medium text-[11px]">${esc(j.human_schedule)}</span>
            </div>
            <div class="mt-2 text-[11px] font-mono text-slate-300 truncate bg-slate-950/80 p-2 rounded-lg border border-slate-800/80">${esc(j.command)}</div>
          </div>`
          )
          .join("")
      : `<div class="text-xs text-slate-400 font-mono py-2">No cron automation file installed yet.</div>`;

    const tbody = document.getElementById("backups-tbody");
    const backups = data.backups || [];
    tbody.innerHTML = backups.length
      ? backups
          .map((b) => {
            const badge = b.checksum_valid
              ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 inline-flex items-center gap-1.5 shadow-sm"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-indicator"></span><span>SHA-256 VERIFIED</span></span>`
              : `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">CHECKSUM MISMATCH</span>`;

            return `
              <tr class="hover:bg-slate-800/40 transition">
                <td class="px-4 py-3 text-white font-semibold flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
                  <span>${esc(b.filename)}</span>
                </td>
                <td class="px-4 py-3 text-slate-300 font-mono">${esc(b.size_human)}</td>
                <td class="px-4 py-3 text-slate-400 text-xs">${esc(b.created_at)}</td>
                <td class="px-4 py-3 text-slate-400 font-mono text-[11px]">
                  <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">${esc((b.sha256 || "").slice(0, 16))}...</span>
                </td>
                <td class="px-4 py-3">${badge}</td>
              </tr>`;
          })
          .join("")
      : `<tr><td colspan="5" class="px-4 py-8 text-center text-slate-400 font-mono">No backup archives generated yet. Click "Run Backup Now" above.</td></tr>`;

    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (err) {
    console.error("Backups error:", err);
  }
}

function setTeamFilter(team) {
  currentTeamFilter = team;
  document.querySelectorAll(".team-pill").forEach((el) => {
    const active = el.dataset.team === team;
    el.className = active
      ? "team-pill px-3.5 py-1.5 rounded-full text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm transition"
      : "team-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-800/80 text-slate-300 border border-slate-700 hover:bg-slate-700 transition";
  });
  loadDevelopers();
}

function switchTab(tabName) {
  document.querySelectorAll(".tab-panel").forEach((el) => el.classList.add("hidden"));
  document.getElementById(`tab-${tabName}`).classList.remove("hidden");
  document.querySelectorAll(".tab-btn").forEach((el) => {
    const active = el.dataset.tab === tabName;
    el.className = active
      ? "tab-btn px-4 py-2.5 text-xs sm:text-sm font-bold border-b-2 border-cyan-400 text-cyan-300 flex items-center gap-2 transition"
      : "tab-btn px-4 py-2.5 text-xs sm:text-sm font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 transition";
  });
  if (tabName === "repos") loadRepos();
  if (tabName === "backups") loadBackups();
}

function toggleConsole(open) {
  const drawer = document.getElementById("console-drawer");
  if (open) {
    drawer.classList.remove("translate-y-full");
  } else {
    drawer.classList.add("translate-y-full");
  }
}

function clearConsole() {
  document.getElementById("console-output").textContent = "";
}

function triggerAction(action) {
  toggleConsole(true);
  const outEl = document.getElementById("console-output");
  const statusEl = document.getElementById("console-status");
  const titleEl = document.getElementById("console-title");

  if (activeStream) {
    activeStream.close();
  }

  outEl.textContent = `[session] launching action '${action}' on Linux host...\n`;
  titleEl.innerHTML = `<span class="text-cyan-400">&gt;_</span><span>Live Action Console &mdash; ${action}</span>`;
  statusEl.textContent = "RUNNING";
  statusEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 pulse-indicator";

  const es = new EventSource(`/api/actions/${encodeURIComponent(action)}/stream`);
  activeStream = es;

  es.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.type === "start") {
      outEl.textContent += `[stream] started ${msg.script}\n`;
    } else if (msg.type === "log") {
      outEl.textContent += `${msg.line}\n`;
      outEl.scrollTop = outEl.scrollHeight;
    } else if (msg.type === "done") {
      const ok = msg.exit_code === 0;
      statusEl.textContent = `EXIT ${msg.exit_code} (${msg.duration_ms}ms)`;
      statusEl.className = ok
        ? "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
        : "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40";
      es.close();
      activeStream = null;
      // Refresh dashboard panels after action finishes
      loadHealth();
      loadTelemetry();
      loadRepos();
      loadBackups();
    }
  };

  es.onerror = () => {
    statusEl.textContent = "STREAM CLOSED";
    statusEl.className = "px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40";
    es.close();
    activeStream = null;
  };
}

document.addEventListener("DOMContentLoaded", () => {
  if (typeof lucide !== "undefined") lucide.createIcons();
  initChart();
  loadHealth();
  loadTelemetry();
  loadDevelopers();
  loadRepos();
  loadBackups();

  setInterval(() => {
    loadTelemetry();
  }, 3000);
});
