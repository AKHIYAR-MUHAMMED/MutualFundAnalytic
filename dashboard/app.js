// --- Global Application State ---
let rawData = null;
let activeTab = "overview"; // "overview", "performance", "investor", "trends", "drilldown"
let drillFundCode = null; // Used for Page 2 -> Page 5 drill-through

// Active Filters (Slicers)
let filters = {
  performance: {
    fundHouse: "all",
    category: "all",
    riskGrade: "all"
  },
  investor: {
    state: "all",
    ageGroup: "all",
    cityTier: "all"
  }
};

// Search & Sort States
let tableSearchQuery = "";
let tableSortCol = "scorecard_score";
let tableSortOrder = "desc";

// Running Chart.js instances (tracked to destroy/re-create)
let charts = {};

// Scheme Color Mapping Hashing
function getSchemeColor(name) {
  if (!name) return "#8e9cae";
  const customColors = {
    "Nifty 100 Benchmark": "#8e9cae",
    "Nifty 50 Benchmark": "#ef4444",
    "SBI Small Cap Fund - Direct Plan - Growth": "#c5ff45", // Neon Green
    "HDFC Top 100 Fund - Direct Plan - Growth": "#a78bfa",  // Violet
    "ICICI Prudential Bluechip Fund - Direct Plan - Growth": "#10b981",
    "Axis Bluechip Fund - Direct Plan - Growth": "#00e5ff",
    "Kotak Bluechip Fund - Direct Plan - Growth": "#f59e0b"
  };
  if (customColors[name]) return customColors[name];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  return `hsl(${hue}, 65%, 60%)`;
}

// --- DOM Initialisation ---
document.addEventListener("DOMContentLoaded", () => {
  fetchDataAndStart();
});

async function fetchDataAndStart() {
  const root = document.getElementById("root");
  root.innerHTML = `<div style="padding: 3rem; text-align: center; color: var(--primary); font-size: 1.2rem; font-family: 'Outfit'; font-weight: 800;">LOADING BLUESTOCKS ANALYTICS ENGINE...</div>`;
  
  try {
    const response = await fetch("dashboard_data.json");
    if (!response.ok) throw new Error("JSON Fetch failed");
    rawData = await response.json();
    console.log("Analytics Data Ingested:", rawData);
    
    // Set default fund for drill-through
    if (rawData.metrics && rawData.metrics.length > 0) {
      drillFundCode = rawData.metrics[0].scheme_code;
    }
    
    renderApp();
  } catch (err) {
    console.error("Dashboard init error:", err);
    root.innerHTML = `<div style="padding: 3rem; text-align: center; color: var(--danger); font-size: 1.2rem; font-family: 'Outfit';">Error Loading Analytics. Make sure dashboard_data.json exists.</div>`;
  }
}

// --- Core Render Loop ---
function renderApp() {
  const root = document.getElementById("root");
  root.innerHTML = ""; // Clear
  
  // 1. Sidebar Container
  const sidebar = document.createElement("aside");
  sidebar.className = "sidebar";
  sidebar.innerHTML = `
    <div class="logo">
      <div class="logo-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#04060a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
      </div>
      <span class="logo-text">Bluestocks</span>
    </div>
    <nav>
      <ul class="nav-menu">
        <li class="nav-item ${activeTab === "overview" ? "active" : ""}" data-tab="overview">
          <a>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
            <span class="nav-text">Industry Overview</span>
          </a>
        </li>
        <li class="nav-item ${activeTab === "performance" ? "active" : ""}" data-tab="performance">
          <a>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line><line x1="2" y1="20" x2="22" y2="20"></line></svg>
            <span class="nav-text">Fund Performance</span>
          </a>
        </li>
        <li class="nav-item ${activeTab === "investor" ? "active" : ""}" data-tab="investor">
          <a>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            <span class="nav-text">Investor Analytics</span>
          </a>
        </li>
        <li class="nav-item ${activeTab === "trends" ? "active" : ""}" data-tab="trends">
          <a>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            <span class="nav-text">SIP & Market Trends</span>
          </a>
        </li>
      </ul>
    </nav>
    <div class="sidebar-footer">
      <div class="db-badge">
        <div class="db-indicator"></div>
        <span>Data Connect Active</span>
      </div>
    </div>
  `;
  
  // 2. Main Content Container
  const main = document.createElement("main");
  main.className = "main-content";
  
  root.appendChild(sidebar);
  root.appendChild(main);
  
  // Add Sidebar click listeners
  sidebar.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      activeTab = item.dataset.tab;
      renderApp();
    });
  });
  
  // Render specific page
  if (activeTab === "overview") renderOverviewPage(main);
  else if (activeTab === "performance") renderPerformancePage(main);
  else if (activeTab === "investor") renderInvestorPage(main);
  else if (activeTab === "trends") renderTrendsPage(main);
  else if (activeTab === "drilldown") renderDrilldownPage(main);
}

// --- Page 1: Industry Overview ---
function renderOverviewPage(container) {
  // Title
  container.appendChild(createHeader("Industry Overview", "High-level visual summary of AUM metrics, AMC market share, and growth."));
  
  // KPI Cards
  const kpis = rawData.industry;
  const grid = document.createElement("section");
  grid.className = "kpi-grid";
  grid.innerHTML = `
    <div class="kpi-card accent-vol">
      <div class="kpi-header">
        <span>Total AUM</span>
        <div class="kpi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg></div>
      </div>
      <div class="kpi-value">₹${kpis.total_aum}L Cr</div>
      <div class="kpi-label">Aggregated industry assets</div>
    </div>
    <div class="kpi-card accent-ret">
      <div class="kpi-header">
        <span>Monthly SIP Inflow</span>
        <div class="kpi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg></div>
      </div>
      <div class="kpi-value">₹${(kpis.total_sip / 1000).toFixed(1)}K Cr</div>
      <div class="kpi-label">Dec 2025: ₹${kpis.total_sip.toLocaleString()} Cr</div>
    </div>
    <div class="kpi-card accent-sharpe">
      <div class="kpi-header">
        <span>Total Folios</span>
        <div class="kpi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg></div>
      </div>
      <div class="kpi-value">${kpis.total_folios} Cr</div>
      <div class="kpi-label">Total active accounts</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-header">
        <span>Active Schemes</span>
        <div class="kpi-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg></div>
      </div>
      <div class="kpi-value">${kpis.total_schemes}</div>
      <div class="kpi-label">Cleaned database codes</div>
    </div>
  `;
  container.appendChild(grid);
  
  // Charts
  const chartsGrid = document.createElement("section");
  chartsGrid.className = "charts-grid";
  chartsGrid.innerHTML = `
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Industry AUM Growth Trend (2022-2025)</h2>
          <p>Compounded growth curve scaled to industry total</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 320px;">
        <canvas id="aumTrendChart"></canvas>
      </div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>AUM by Asset Management Company (AMC)</h2>
          <p>Assets Under Management in Lakh Crores (CY25)</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 320px;">
        <canvas id="aumAmcChart"></canvas>
      </div>
    </div>
  `;
  container.appendChild(chartsGrid);
  
  // Render Charts
  const ctxTrend = document.getElementById("aumTrendChart").getContext("2d");
  charts.aumTrend = new Chart(ctxTrend, {
    type: "line",
    data: {
      labels: kpis.aum_trend.years,
      datasets: [{
        label: "Industry AUM (₹ Lakh Cr)",
        data: kpis.aum_trend.values,
        borderColor: "#c5ff45", /* Neon Green */
        backgroundColor: "rgba(197, 255, 69, 0.08)",
        borderWidth: 3,
        pointRadius: 5,
        pointBackgroundColor: "#c5ff45",
        tension: 0.1,
        fill: true
      }]
    },
    options: getChartOptions("₹L Cr")
  });
  
  const ctxAmc = document.getElementById("aumAmcChart").getContext("2d");
  charts.aumAmc = new Chart(ctxAmc, {
    type: "bar",
    data: {
      labels: kpis.aum_by_amc.amcs,
      datasets: [{
        label: "AUM (₹ Lakh Cr)",
        data: kpis.aum_by_amc.values,
        backgroundColor: "rgba(167, 139, 250, 0.75)", /* Purple */
        borderColor: "#a78bfa",
        borderWidth: 1,
        borderRadius: 2
      }]
    },
    options: getChartOptions("₹L Cr")
  });
}

// --- Page 2: Fund Performance ---
function renderPerformancePage(container) {
  container.appendChild(createHeader("Fund Performance Analytics", "Evaluate fund risks, scorecard rankings, returns, and track benchmarks."));
  
  // 1. Slicers Panel
  const slicerPanel = document.createElement("div");
  slicerPanel.className = "slicers-panel";
  slicerPanel.innerHTML = `
    <div class="slicers-title">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
      <span>Slicers</span>
    </div>
  `;
  
  const amcs = ["all", ...new Set(rawData.metrics.map(m => m.fund_house))];
  const cats = ["all", ...new Set(rawData.metrics.map(m => m.category))];
  const grades = ["all", ...new Set(rawData.metrics.map(m => m.risk_grade))];
  
  slicerPanel.appendChild(createSlicer("Fund House", "slicer-perf-house", amcs, filters.performance.fundHouse));
  slicerPanel.appendChild(createSlicer("Category", "slicer-perf-cat", cats, filters.performance.category));
  slicerPanel.appendChild(createSlicer("Risk Grade", "slicer-perf-risk", grades, filters.performance.riskGrade));
  container.appendChild(slicerPanel);
  
  slicerPanel.querySelector("#slicer-perf-house").addEventListener("change", (e) => {
    filters.performance.fundHouse = e.target.value;
    updatePerformancePageCharts();
  });
  slicerPanel.querySelector("#slicer-perf-cat").addEventListener("change", (e) => {
    filters.performance.category = e.target.value;
    updatePerformancePageCharts();
  });
  slicerPanel.querySelector("#slicer-perf-risk").addEventListener("change", (e) => {
    filters.performance.riskGrade = e.target.value;
    updatePerformancePageCharts();
  });
  
  // 2. Charts Grid
  const chartsGrid = document.createElement("section");
  chartsGrid.className = "charts-grid";
  chartsGrid.innerHTML = `
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Risk-Reward Bubble Plot</h2>
          <p>X = Return (3Yr CAGR %), Y = Risk (Volatility %), Bubble Size = AUM</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 320px;">
        <canvas id="perfScatterChart"></canvas>
      </div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>NAV Performance vs Benchmarks</h2>
          <p id="nav-chart-subtitle">Compare Growth of 10,000 INR over 3 Years (2024-2026)</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 320px;">
        <canvas id="perfNavChart"></canvas>
      </div>
    </div>
  `;
  container.appendChild(chartsGrid);
  
  // 3. Scorecard Table
  const tableCard = document.createElement("section");
  tableCard.className = "grid-card table-card";
  tableCard.innerHTML = `
    <div class="table-header">
      <div class="chart-title">
        <h2>Mutual Fund Performance Scorecard Table</h2>
        <p>Composite ranking: 30% Return + 25% Sharpe + 20% Alpha + 15% Expense (Inv) + 10% MaxDD (Inv)</p>
      </div>
      <div class="search-wrapper">
        <input type="text" id="perf-search" class="search-input" value="${tableSearchQuery}" placeholder="Search name or AMC...">
      </div>
    </div>
    <div class="table-wrapper">
      <table class="metrics-table">
        <thead>
          <tr>
            <th data-col="overall_rank">Rank ${tableSortCol === "overall_rank" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="short_name">Scheme Name ${tableSortCol === "short_name" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="scorecard_score">Score ${tableSortCol === "scorecard_score" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="cagr_3yr">3Yr CAGR ${tableSortCol === "cagr_3yr" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="sharpe_ratio">Sharpe ${tableSortCol === "sharpe_ratio" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="alpha">Alpha % ${tableSortCol === "alpha" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="expense_ratio">Expense % ${tableSortCol === "expense_ratio" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th data-col="max_drawdown">Max DD ${tableSortCol === "max_drawdown" ? (tableSortOrder === "asc" ? "▲" : "▼") : ""}</th>
            <th>Drill Down</th>
          </tr>
        </thead>
        <tbody id="perf-table-body"></tbody>
      </table>
    </div>
  `;
  container.appendChild(tableCard);
  
  tableCard.querySelector("#perf-search").addEventListener("input", (e) => {
    tableSearchQuery = e.target.value;
    populatePerformanceTable();
  });
  
  tableCard.querySelectorAll("th[data-col]").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (tableSortCol === col) {
        tableSortOrder = tableSortOrder === "asc" ? "desc" : "asc";
      } else {
        tableSortCol = col;
        tableSortOrder = "desc";
      }
      renderPerformancePage(container);
    });
  });
  
  updatePerformancePageCharts();
}

function filterPerformanceMetrics() {
  return rawData.metrics.filter(m => {
    const matchHouse = filters.performance.fundHouse === "all" || m.fund_house === filters.performance.fundHouse;
    const matchCat = filters.performance.category === "all" || m.category === filters.performance.category;
    const matchRisk = filters.performance.riskGrade === "all" || m.risk_grade === filters.performance.riskGrade;
    return matchHouse && matchCat && matchRisk;
  });
}

function updatePerformancePageCharts() {
  const filtered = filterPerformanceMetrics();
  
  // 1. Bubble Plot
  const ctxScatter = document.getElementById("perfScatterChart").getContext("2d");
  const bubbleData = filtered.map(m => {
    const color = getSchemeColor(m.scheme_name);
    const size = Math.max(4, Math.min(22, (m.aum / 35000) * 18 + 4));
    return {
      label: m.short_name,
      data: [{ x: m.cagr_3yr * 100, y: m.ann_volatility, r: size }],
      backgroundColor: color + "a0",
      borderColor: color,
      borderWidth: 1,
      hoverBackgroundColor: color
    };
  });
  
  if (charts.perfScatter) charts.perfScatter.destroy();
  charts.perfScatter = new Chart(ctxScatter, {
    type: "bubble",
    data: { datasets: bubbleData },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#080d16",
          borderColor: "#162032",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            title: (items) => items[0].dataset.label,
            label: (context) => {
              const schemeName = context.dataset.label;
              const meta = filtered.find(f => f.short_name === schemeName);
              return [
                `3Yr CAGR: ${context.raw.x.toFixed(2)}%`,
                `Volatility: ${context.raw.y.toFixed(2)}%`,
                `AUM: ₹${meta.aum.toLocaleString()} Cr`
              ];
            }
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: "Return (3Yr CAGR %)", color: "#8e9cae", font: { weight: "600" } },
          grid: { color: "rgba(255,255,255,0.02)" },
          ticks: { color: "#3b4e68" }
        },
        y: {
          title: { display: true, text: "Risk (Volatility %)", color: "#8e9cae", font: { weight: "600" } },
          grid: { color: "rgba(255,255,255,0.02)" },
          ticks: { color: "#3b4e68" }
        }
      }
    }
  });
  
  populatePerformanceTable();
  renderNavBenchmarkChart();
}

function populatePerformanceTable() {
  const tbody = document.getElementById("perf-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  
  let filtered = filterPerformanceMetrics();
  
  if (tableSearchQuery.trim() !== "") {
    const q = tableSearchQuery.toLowerCase();
    filtered = filtered.filter(m => 
      m.scheme_name.toLowerCase().includes(q) || 
      m.fund_house.toLowerCase().includes(q) ||
      m.category.toLowerCase().includes(q)
    );
  }
  
  filtered.sort((a, b) => {
    let valA = a[tableSortCol];
    let valB = b[tableSortCol];
    if (typeof valA === "string") {
      return tableSortOrder === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
    } else {
      return tableSortOrder === "asc" ? valA - valB : valB - valA;
    }
  });
  
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No schemes found matching search or filters.</td></tr>`;
    return;
  }
  
  filtered.forEach(m => {
    const row = document.createElement("tr");
    if (m.scheme_code === drillFundCode) {
      row.style.background = "rgba(197, 255, 69, 0.05)";
      row.style.borderLeft = "2px solid var(--primary)";
    }
    
    row.addEventListener("click", (e) => {
      if (e.target.tagName.toLowerCase() === "button" || e.target.closest("button")) return;
      drillFundCode = m.scheme_code;
      tbody.querySelectorAll("tr").forEach(r => r.style.background = "none");
      tbody.querySelectorAll("tr").forEach(r => r.style.borderLeft = "none");
      row.style.background = "rgba(197, 255, 69, 0.05)";
      row.style.borderLeft = "2px solid var(--primary)";
      renderNavBenchmarkChart();
    });
    
    row.innerHTML = `
      <td><strong>#${m.overall_rank}</strong></td>
      <td>
        <div class="fund-table-name" title="${m.scheme_name}">${m.short_name}</div>
        <div style="font-size: 0.72rem; color: var(--text-muted);">${m.category} | ${m.fund_house}</div>
      </td>
      <td><span style="color: var(--primary); font-weight: 700;">${m.scorecard_score.toFixed(1)}</span></td>
      <td class="${m.cagr_3yr > 0.12 ? "trend-up" : "trend-down"}">${(m.cagr_3yr * 100).toFixed(2)}%</td>
      <td>${m.sharpe_ratio.toFixed(2)}</td>
      <td class="${m.alpha > 0 ? "trend-up" : "trend-down"}">${(m.alpha * 100).toFixed(2)}%</td>
      <td>${m.expense_ratio.toFixed(2)}%</td>
      <td class="trend-down">${(m.max_drawdown * 100).toFixed(2)}%</td>
      <td><button class="drill-btn" data-code="${m.scheme_code}">Drill Detail</button></td>
    `;
    tbody.appendChild(row);
    
    row.querySelector(".drill-btn").addEventListener("click", () => {
      drillFundCode = m.scheme_code;
      activeTab = "drilldown";
      renderApp();
    });
  });
}

function renderNavBenchmarkChart() {
  const ctxNav = document.getElementById("perfNavChart").getContext("2d");
  if (!ctxNav) return;
  
  const fund = rawData.metrics.find(f => f.scheme_code === drillFundCode);
  if (!fund) return;
  
  document.getElementById("nav-chart-subtitle").innerText = `Historical NAV Comparison: ${fund.short_name} vs Nifty 50 & 100 (2024-2026)`;
  
  const dates = rawData.growth.dates;
  const startIdx = dates.indexOf("2024-01-01");
  const slicedDates = dates.slice(startIdx);
  
  const fundRaw = rawData.growth.schemes[fund.scheme_code].slice(startIdx);
  const n100Raw = rawData.benchmarks.nifty100.slice(startIdx);
  const n50Raw = rawData.benchmarks.nifty50.slice(startIdx);
  
  const rebase = (arr) => {
    const startVal = arr[0] || 10000;
    return arr.map(v => Math.round((v / startVal) * 10000));
  };
  
  if (charts.perfNav) charts.perfNav.destroy();
  charts.perfNav = new Chart(ctxNav, {
    type: "line",
    data: {
      labels: slicedDates,
      datasets: [
        {
          label: fund.short_name,
          data: rebase(fundRaw),
          borderColor: "#c5ff45", /* Neon Green */
          borderWidth: 2,
          pointRadius: 0,
          fill: false
        },
        {
          label: "Nifty 100 Benchmark",
          data: rebase(n100Raw),
          borderColor: "#8e9cae",
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        },
        {
          label: "Nifty 50 Benchmark",
          data: rebase(n50Raw),
          borderColor: "#ef4444",
          borderWidth: 1.5,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#8e9cae", font: { size: 10 } }
        },
        tooltip: {
          backgroundColor: "#080d16",
          borderColor: "#162032",
          borderWidth: 1,
          callbacks: {
            label: (context) => ` ${context.dataset.label}: ₹${context.raw.toLocaleString()}`
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#3b4e68", maxTicksLimit: 10 } },
        y: { grid: { color: "rgba(255,255,255,0.02)" }, ticks: { color: "#3b4e68" } }
      }
    }
  });
}

// --- Page 3: Investor Analytics ---
function renderInvestorPage(container) {
  container.appendChild(createHeader("Investor Flows & Demographics", "Profile transaction splits, age brackets, geographic allocations, and monthly volumes."));
  
  const slicerPanel = document.createElement("div");
  slicerPanel.className = "slicers-panel";
  slicerPanel.innerHTML = `
    <div class="slicers-title">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
      <span>Slicers</span>
    </div>
  `;
  
  const states = ["all", ...new Set(rawData.investor.transactions_split_data.map(t => t[4]))].sort();
  const ages = ["all", ...new Set(rawData.investor.transactions_split_data.map(t => t[5]))].sort();
  const tiers = ["all", ...new Set(rawData.investor.transactions_split_data.map(t => t[6]))].sort();
  
  slicerPanel.appendChild(createSlicer("Investor State", "slicer-inv-state", states, filters.investor.state));
  slicerPanel.appendChild(createSlicer("Age Bracket", "slicer-inv-age", ages, filters.investor.ageGroup));
  slicerPanel.appendChild(createSlicer("City Tier", "slicer-inv-tier", tiers, filters.investor.cityTier));
  container.appendChild(slicerPanel);
  
  slicerPanel.querySelector("#slicer-inv-state").addEventListener("change", (e) => {
    filters.investor.state = e.target.value;
    updateInvestorCharts();
  });
  slicerPanel.querySelector("#slicer-inv-age").addEventListener("change", (e) => {
    filters.investor.ageGroup = e.target.value;
    updateInvestorCharts();
  });
  slicerPanel.querySelector("#slicer-inv-tier").addEventListener("change", (e) => {
    filters.investor.cityTier = e.target.value;
    updateInvestorCharts();
  });
  
  const chartsGrid = document.createElement("section");
  chartsGrid.className = "charts-grid";
  chartsGrid.innerHTML = `
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Transaction Inflows by State</h2>
          <p>Total transaction amounts in state-wise comparison</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 280px;">
        <canvas id="invStateChart"></canvas>
      </div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Transaction Type Distribution</h2>
          <p>SIP vs Lumpsum vs Redemption volume share</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 280px;">
        <canvas id="invSplitChart"></canvas>
      </div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>SIP Ticket Size by Age Group</h2>
          <p>Average transaction size across age categories</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 280px;">
        <canvas id="invAgeChart"></canvas>
      </div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Monthly Transaction Volumes</h2>
          <p>Line trend tracking transaction counts over time</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 280px;">
        <canvas id="invMonthlyChart"></canvas>
      </div>
    </div>
  `;
  container.appendChild(chartsGrid);
  
  updateInvestorCharts();
}

function filterInvestorTransactions() {
  return rawData.investor.transactions_split_data.filter(t => {
    const matchState = filters.investor.state === "all" || t[4] === filters.investor.state;
    const matchAge = filters.investor.ageGroup === "all" || t[5] === filters.investor.ageGroup;
    const matchTier = filters.investor.cityTier === "all" || t[6] === filters.investor.cityTier;
    return matchState && matchAge && matchTier;
  });
}

function updateInvestorCharts() {
  const filtered = filterInvestorTransactions();
  
  // State inflows
  const stateGroups = {};
  filtered.forEach(t => {
    stateGroups[t[4]] = (stateGroups[t[4]] || 0) + t[3];
  });
  const sortedStates = Object.entries(stateGroups).sort((a,b) => b[1]-a[1]).slice(0, 10);
  const stateLabels = sortedStates.map(x => x[0]);
  const stateVals = sortedStates.map(x => x[1]);
  
  const ctxState = document.getElementById("invStateChart").getContext("2d");
  if (charts.invState) charts.invState.destroy();
  charts.invState = new Chart(ctxState, {
    type: "bar",
    data: {
      labels: stateLabels,
      datasets: [{
        label: "Volume (₹)",
        data: stateVals,
        backgroundColor: "rgba(197, 255, 69, 0.75)", /* Neon Green */
        borderColor: "#c5ff45",
        borderWidth: 1,
        borderRadius: 2
      }]
    },
    options: getChartOptions("₹")
  });
  
  // Tx Type Split
  const typeGroups = {};
  filtered.forEach(t => {
    typeGroups[t[2]] = (typeGroups[t[2]] || 0) + t[3];
  });
  
  const ctxSplit = document.getElementById("invSplitChart").getContext("2d");
  if (charts.invSplit) charts.invSplit.destroy();
  charts.invSplit = new Chart(ctxSplit, {
    type: "doughnut",
    data: {
      labels: Object.keys(typeGroups),
      datasets: [{
        data: Object.values(typeGroups),
        backgroundColor: ["#10b981", "#a78bfa", "#ef4444"], /* Green, Purple, Red */
        borderWidth: 1,
        borderColor: "#080c14"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: "#8e9cae", font: { size: 10 } }
        },
        tooltip: {
          backgroundColor: "#080d16",
          borderColor: "#162032",
          borderWidth: 1,
          callbacks: {
            label: (context) => ` ${context.label}: ₹${context.raw.toLocaleString()}`
          }
        }
      }
    }
  });
  
  // Age Bracket Average SIP
  const ageSums = {};
  const ageCounts = {};
  filtered.forEach(t => {
    if (t[2] === "SIP") {
      ageSums[t[5]] = (ageSums[t[5]] || 0) + t[3];
      ageCounts[t[5]] = (ageCounts[t[5]] || 0) + 1;
    }
  });
  const ageOrder = ["18-25", "26-35", "36-45", "46-55", "56+"];
  const ageVals = ageOrder.map(a => ageCounts[a] > 0 ? ageSums[a]/ageCounts[a] : 0);
  
  const ctxAge = document.getElementById("invAgeChart").getContext("2d");
  if (charts.invAge) charts.invAge.destroy();
  charts.invAge = new Chart(ctxAge, {
    type: "bar",
    data: {
      labels: ageOrder,
      datasets: [{
        label: "Avg SIP (₹)",
        data: ageVals,
        backgroundColor: "rgba(167, 139, 250, 0.75)", /* Violet */
        borderColor: "#a78bfa",
        borderWidth: 1,
        borderRadius: 2
      }]
    },
    options: getChartOptions("₹")
  });
  
  // Monthly volume count
  const monthCounts = {};
  filtered.forEach(t => {
    monthCounts[t[1]] = (monthCounts[t[1]] || 0) + 1;
  });
  const sortedMonths = Object.keys(monthCounts).sort();
  const monthVals = sortedMonths.map(m => monthCounts[m]);
  
  const ctxMonthly = document.getElementById("invMonthlyChart").getContext("2d");
  if (charts.invMonthly) charts.invMonthly.destroy();
  charts.invMonthly = new Chart(ctxMonthly, {
    type: "line",
    data: {
      labels: sortedMonths,
      datasets: [{
        label: "Transaction Count",
        data: monthVals,
        borderColor: "#c5ff45", /* Neon Green */
        backgroundColor: "rgba(197, 255, 69, 0.05)",
        borderWidth: 2,
        pointRadius: 2,
        pointBackgroundColor: "#c5ff45",
        fill: true,
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#080d16",
          borderColor: "#162032",
          borderWidth: 1
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#3b4e68", maxTicksLimit: 12 } },
        y: { grid: { color: "rgba(255,255,255,0.02)" }, ticks: { color: "#3b4e68" } }
      }
    }
  });
}

// --- Page 4: SIP & Market Trends ---
function renderTrendsPage(container) {
  container.appendChild(createHeader("SIP & Market Performance Trends", "Track monthly SIP inflows against the Nifty 50 benchmark index and category inflows."));
  
  const chartsGrid = document.createElement("section");
  chartsGrid.className = "charts-grid";
  chartsGrid.innerHTML = `
    <div class="chart-card full-width">
      <div class="chart-header">
        <div class="chart-title">
          <h2>SIP Inflows vs Nifty 50 Index (2022-2025)</h2>
          <p>Monthly SIP inflow (bars, left scale in ₹Cr) vs Nifty 50 NAV (line, right scale in index pts)</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 340px;">
        <canvas id="dualAxisChart"></canvas>
      </div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Category Net Inflows Heatmap</h2>
          <p>Monthly net retail inflows in Crores INR (Green = Inflow, Red = Outflow)</p>
        </div>
      </div>
      <div class="heatmap-container" id="heatmap-panel"></div>
    </div>
    
    <div class="chart-card">
      <div class="chart-header">
        <div class="chart-title">
          <h2>Top Categories by Net Inflow (FY25)</h2>
          <p>Total net inflows from April 2024 to March 2025 (in Crores INR)</p>
        </div>
      </div>
      <div class="canvas-wrapper" style="height: 280px;">
        <canvas id="topCatsChart"></canvas>
      </div>
    </div>
  `;
  container.appendChild(chartsGrid);
  
  const trends = rawData.market_trends;
  
  // Dual Axis Chart
  const ctxDual = document.getElementById("dualAxisChart").getContext("2d");
  charts.dualAxis = new Chart(ctxDual, {
    type: "bar",
    data: {
      labels: trends.months,
      datasets: [
        {
          label: "Monthly SIP Inflow (₹Cr)",
          data: trends.sip_inflow,
          backgroundColor: "rgba(167, 139, 250, 0.45)", /* Violet */
          borderColor: "#a78bfa",
          borderWidth: 1,
          yAxisID: "y"
        },
        {
          label: "Nifty 50 Index Value",
          data: trends.nifty50_nav,
          borderColor: "#c5ff45", /* Neon Green */
          borderWidth: 2,
          pointRadius: 0,
          type: "line",
          yAxisID: "y1",
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#8e9cae", font: { size: 10 } }
        },
        tooltip: {
          backgroundColor: "#080d16",
          borderColor: "#162032",
          borderWidth: 1
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#3b4e68", maxTicksLimit: 12 } },
        y: {
          position: "left",
          title: { display: true, text: "SIP Inflow (INR Crores)", color: "#8e9cae" },
          grid: { color: "rgba(255,255,255,0.02)" },
          ticks: { color: "#3b4e68" }
        },
        y1: {
          position: "right",
          title: { display: true, text: "Nifty 50 Index Value", color: "#c5ff45" },
          grid: { drawOnChartArea: false },
          ticks: { color: "#3b4e68" }
        }
      }
    }
  });
  
  renderHeatmap();
  
  // Top Categories
  const ctxTopCats = document.getElementById("topCatsChart").getContext("2d");
  charts.topCats = new Chart(ctxTopCats, {
    type: "bar",
    data: {
      labels: trends.fy25_top_categories.categories,
      datasets: [{
        label: "Net Inflow (₹Cr)",
        data: trends.fy25_top_categories.inflows,
        backgroundColor: [
          "rgba(197, 255, 69, 0.75)", /* Neon Green */
          "rgba(167, 139, 250, 0.75)", /* Violet */
          "rgba(16, 185, 129, 0.75)",
          "rgba(245, 158, 11, 0.75)"
        ],
        borderWidth: 1,
        borderRadius: 2
      }]
    },
    options: getChartOptions("₹Cr")
  });
}

function renderHeatmap() {
  const panel = document.getElementById("heatmap-panel");
  if (!panel) return;
  panel.innerHTML = "";
  
  const trends = rawData.market_trends;
  const categories = ["Equity", "Debt", "Hybrid", "Other"];
  const categoryKeys = ["equity", "debt", "hybrid", "other"];
  
  const grid = document.createElement("div");
  grid.className = "heatmap-container";
  
  const monthHeaderRow = document.createElement("div");
  monthHeaderRow.className = "heatmap-grid";
  
  const spacer = document.createElement("div");
  spacer.className = "heatmap-label";
  spacer.style.gridColumn = "span 2";
  spacer.innerText = "Category";
  monthHeaderRow.appendChild(spacer);
  
  const recentMonthsCount = 10;
  const totalMonths = trends.months.length;
  const startIdx = totalMonths - recentMonthsCount;
  const slicedMonths = trends.months.slice(startIdx);
  
  slicedMonths.forEach(m => {
    const mLabel = document.createElement("div");
    mLabel.style.fontSize = "0.72rem";
    mLabel.style.fontWeight = "700";
    mLabel.style.textAlign = "center";
    mLabel.style.color = "var(--text-muted)";
    mLabel.innerText = m.substring(5) + "/" + m.substring(2,4);
    monthHeaderRow.appendChild(mLabel);
  });
  grid.appendChild(monthHeaderRow);
  
  categoryKeys.forEach((key, rowIdx) => {
    const row = document.createElement("div");
    row.className = "heatmap-grid";
    
    const rLabel = document.createElement("div");
    rLabel.className = "heatmap-label";
    rLabel.innerText = categories[rowIdx];
    row.appendChild(rLabel);
    
    const rowValues = trends.net_inflow_by_category[key].slice(startIdx);
    const maxVal = Math.max(...trends.net_inflow_by_category[key].map(Math.abs));
    
    rowValues.forEach(val => {
      const cell = document.createElement("div");
      cell.className = "heatmap-cell";
      
      const ratio = maxVal > 0 ? Math.min(1.0, Math.abs(val) / maxVal) : 0.5;
      
      if (val >= 0) {
        // Neon green-based fill
        cell.style.backgroundColor = `rgba(197, 255, 69, ${0.15 + ratio * 0.75})`;
        cell.style.color = ratio > 0.55 ? "#04060a" : "#ffffff";
      } else {
        // Red-based fill
        cell.style.backgroundColor = `rgba(239, 68, 68, ${0.15 + ratio * 0.75})`;
        cell.style.color = ratio > 0.55 ? "#04060a" : "#ffffff";
      }
      
      cell.innerText = Math.round(val).toLocaleString();
      cell.title = `${categories[rowIdx]} Net Flow: ₹${val.toLocaleString()} Cr`;
      row.appendChild(cell);
    });
    grid.appendChild(row);
  });
  
  const legend = document.createElement("div");
  legend.className = "heatmap-legend";
  legend.innerHTML = `
    <div style="display:flex; align-items:center; gap:0.25rem;">Outflow <div class="legend-box" style="background:#ef4444a0"></div></div>
    <div style="display:flex; align-items:center; gap:0.25rem;"><div class="legend-box" style="background:#c5ff45a0"></div> Inflow</div>
  `;
  grid.appendChild(legend);
  panel.appendChild(grid);
}

// --- Page 5: Drill Down NAV Detail ---
function renderDrilldownPage(container) {
  const fund = rawData.metrics.find(f => f.scheme_code === drillFundCode);
  if (!fund) {
    container.innerHTML = `<div style="padding:2rem;">Scheme code not found.</div>`;
    return;
  }
  
  const header = document.createElement("header");
  header.className = "dashboard-header";
  header.innerHTML = `
    <div class="welcome-section">
      <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom: 0.2rem;">
        <button class="drill-btn" id="drill-back-btn">← Back</button>
        <h1>${fund.scheme_name}</h1>
      </div>
      <p>${fund.fund_house} | Category: ${fund.category} | Sub-Category: ${fund.sub_category}</p>
    </div>
  `;
  container.appendChild(header);
  
  header.querySelector("#drill-back-btn").addEventListener("click", () => {
    activeTab = "performance";
    renderApp();
  });
  
  const grid = document.createElement("section");
  grid.className = "kpi-grid";
  grid.innerHTML = `
    <div class="kpi-card accent-vol">
      <div class="kpi-header"><span>3Yr CAGR</span></div>
      <div class="kpi-value">${(fund.cagr_3yr * 100).toFixed(2)}%</div>
      <div class="kpi-label">5Yr CAGR: ${(fund.cagr_5yr * 100).toFixed(2)}%</div>
    </div>
    <div class="kpi-card accent-ret">
      <div class="kpi-header"><span>Sharpe / Sortino</span></div>
      <div class="kpi-value">${fund.sharpe_ratio.toFixed(2)} / ${fund.sortino_ratio.toFixed(2)}</div>
      <div class="kpi-label">Risk-adjusted metric parameters</div>
    </div>
    <div class="kpi-card accent-sharpe">
      <div class="kpi-header"><span>Alpha / Beta (Nifty 100)</span></div>
      <div class="kpi-value">${(fund.alpha * 100).toFixed(2)}% / ${fund.beta.toFixed(2)}</div>
      <div class="kpi-label">Tracking Error: ${(fund.tracking_error_nifty100 * 100).toFixed(1)}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-header"><span>Max Drawdown</span></div>
      <div class="kpi-value" style="color:var(--danger);">${(fund.max_drawdown * 100).toFixed(2)}%</div>
      <div class="kpi-label">${fund.drawdown_peak_date} to ${fund.drawdown_trough_date}</div>
    </div>
  `;
  container.appendChild(grid);
  
  const chartCard = document.createElement("section");
  chartCard.className = "chart-card full-width";
  chartCard.innerHTML = `
    <div class="chart-header">
      <div class="chart-title">
        <h2>5-Year Historical Performance Cumulative Trend</h2>
        <p>Growth of 10,000 INR Investment from 2022 to 2026 vs Nifty 50 and Nifty 100 Benchmarks</p>
      </div>
    </div>
    <div class="canvas-wrapper" style="height: 380px;">
      <canvas id="drillFullChart"></canvas>
    </div>
  `;
  container.appendChild(chartCard);
  
  const ctxDrill = document.getElementById("drillFullChart").getContext("2d");
  const dates = rawData.growth.dates;
  const fundRaw = rawData.growth.schemes[fund.scheme_code];
  const n100Raw = rawData.benchmarks.nifty100;
  const n50Raw = rawData.benchmarks.nifty50;
  
  const rebase = (arr) => {
    const startVal = arr[0] || 10000;
    return arr.map(v => Math.round((v / startVal) * 10000));
  };
  
  charts.drillFull = new Chart(ctxDrill, {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        {
          label: fund.short_name,
          data: rebase(fundRaw),
          borderColor: "#c5ff45", /* Neon Green */
          borderWidth: 2.5,
          pointRadius: 0,
          fill: false
        },
        {
          label: "Nifty 100 Benchmark",
          data: rebase(n100Raw),
          borderColor: "#8e9cae",
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        },
        {
          label: "Nifty 50 Benchmark",
          data: rebase(n50Raw),
          borderColor: "#ef4444",
          borderWidth: 1.5,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#8e9cae", font: { size: 10 } }
        },
        tooltip: {
          backgroundColor: "#080d16",
          borderColor: "#162032",
          borderWidth: 1,
          callbacks: {
            label: (context) => ` ${context.dataset.label}: ₹${context.raw.toLocaleString()}`
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: "#3b4e68", maxTicksLimit: 12 } },
        y: { grid: { color: "rgba(255,255,255,0.02)" }, ticks: { color: "#3b4e68" } }
      }
    }
  });
}

// --- Dynamic Component Helper Functions ---
function createHeader(title, subtitle) {
  const header = document.createElement("header");
  header.className = "dashboard-header";
  header.innerHTML = `
    <div class="welcome-section">
      <h1>${title}</h1>
      <p>${subtitle}</p>
    </div>
    <div class="time-badge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
      <span>Bluestocks Premium SPA API v1.3</span>
    </div>
  `;
  return header;
}

function createSlicer(labelText, selectId, optionsList, activeValue) {
  const item = document.createElement("div");
  item.className = "slicer-item";
  
  let optionsHtml = "";
  optionsList.forEach(opt => {
    const cleanLabel = opt === "all" ? "All Filters" : opt;
    optionsHtml += `<option value="${opt}" ${opt === activeValue ? "selected" : ""}>${cleanLabel}</option>`;
  });
  
  item.innerHTML = `
    <label for="${selectId}">${labelText}</label>
    <select id="${selectId}" class="slicer-select">
      ${optionsHtml}
    </select>
  `;
  return item;
}

function getChartOptions(yLabelFormat = "") {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#080d16",
        borderColor: "#162032",
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const val = context.raw;
            if (yLabelFormat === "₹") {
              return ` Amount: ₹${val.toLocaleString()}`;
            } else if (yLabelFormat === "₹L Cr") {
              return ` AUM: ₹${val.toFixed(2)}L Cr`;
            } else if (yLabelFormat === "₹Cr") {
              return ` Flow: ₹${val.toLocaleString()} Cr`;
            } else {
              return ` ${context.dataset.label || "Value"}: ${val}`;
            }
          }
        }
      }
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: "#3b4e68" } },
      y: {
        grid: { color: "rgba(255,255,255,0.02)" },
        ticks: {
          color: "#3b4e68",
          callback: (value) => {
            if (yLabelFormat === "₹L Cr") return `₹${value}L Cr`;
            if (yLabelFormat === "₹Cr") return `₹${value}Cr`;
            if (yLabelFormat === "₹") {
              if (value >= 10000000) return `₹${(value/10000000).toFixed(1)}Cr`;
              if (value >= 100000) return `₹${(value/100000).toFixed(1)}L`;
              return `₹${value.toLocaleString()}`;
            }
            return value;
          }
        }
      }
    }
  };
}
