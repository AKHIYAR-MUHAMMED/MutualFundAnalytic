// --- Global Dashboard State ---
let dashboardData = null;
let growthChart = null;
let riskChart = null;
let currentSearchQuery = "";
let currentSortColumn = "ann_return";
let currentSortOrder = "desc";
let activeTimeframe = "all";

// Color Palette for Schemes
const schemeColors = {
  "Aditya Birla Sun Life Banking & PSU Debt Fund  - DIRECT - IDCW": "#8b5cf6", // Purple
  "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option": "#00e5ff",         // Cyan
  "HDFC Hybrid Equity Fund - Growth Option - Direct Plan": "#10b981",          // Green
  "HDFC Money Market Fund - Growth Option - Direct Plan": "#f59e0b",           // Orange
  "Kotak Multi Asset Omni FOF - Direct Growth - Direct": "#ec4899",            // Pink
  "Nippon India Large Cap Fund - Direct Plan Growth Plan - Growth Option": "#3b82f6", // Blue
  "SBI Small Cap Fund - Direct Plan - Growth": "#ef4444",                      // Red
  "quant Mid Cap Fund - Growth Option - Direct Plan": "#a3e635"                // Lime
};

function getSchemeColor(name) {
  if (schemeColors[name]) {
    return schemeColors[name];
  }
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  return `hsl(${hue}, 70%, 50%)`;
}

// --- Page Init ---
document.addEventListener("DOMContentLoaded", () => {
  fetchDashboardData();
  setupTimeframeButtons();
  setupSearchInput();
  setupTableSort();
});

// --- Fetch JSON Data ---
async function fetchDashboardData() {
  try {
    const response = await fetch("dashboard_data.json");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    dashboardData = await response.json();
    console.log("Data loaded successfully:", dashboardData);
    
    // Initialise UI
    updateKPIs();
    renderGrowthChart();
    renderRiskChart();
    populateFundList();
    renderMetricsTable();
  } catch (error) {
    console.error("Error fetching dashboard data:", error);
    alert("Failed to load dashboard data. Please make sure the JSON file exists.");
  }
}

// --- KPI Cards Update ---
function updateKPIs() {
  const metrics = dashboardData.metrics;
  
  // Total schemes
  document.getElementById("kpi-total").innerText = metrics.length;
  
  // Safest fund (min volatility)
  const safest = [...metrics].sort((a, b) => a.ann_volatility - b.ann_volatility)[0];
  const safestVal = document.getElementById("kpi-safest-val");
  safestVal.innerText = `${safest.ann_volatility}%`;
  safestVal.nextElementSibling.innerText = safest.short_name;
  
  // Top performer (max CAGR)
  const topPerf = [...metrics].sort((a, b) => b.ann_return - a.ann_return)[0];
  const topVal = document.getElementById("kpi-top-val");
  topVal.innerText = `${topPerf.ann_return}%`;
  topVal.nextElementSibling.innerText = topPerf.short_name;
  
  // Best risk-adjusted (max Sharpe)
  const bestSharpe = [...metrics].sort((a, b) => b.sharpe_ratio - a.sharpe_ratio)[0];
  const sharpeVal = document.getElementById("kpi-sharpe-val");
  sharpeVal.innerText = bestSharpe.sharpe_ratio;
  sharpeVal.nextElementSibling.innerText = bestSharpe.short_name;
}

// --- Timeframe Filtering Helper ---
function getFilteredGrowthData() {
  const dates = dashboardData.growth.dates;
  const schemes = dashboardData.growth.schemes;
  const totalDays = dates.length;
  
  let sliceCount = totalDays;
  if (activeTimeframe === "1y") {
    sliceCount = Math.min(252, totalDays); // 1 trading year
  } else if (activeTimeframe === "3y") {
    sliceCount = Math.min(252 * 3, totalDays);
  } else if (activeTimeframe === "5y") {
    sliceCount = Math.min(252 * 5, totalDays);
  }
  
  const startIndex = totalDays - sliceCount;
  
  // Slice dates
  const slicedDates = dates.slice(startIndex);
  
  // Slice and rebase each scheme's investment to 10k at start of sliced period
  const slicedSchemes = {};
  for (const [name, values] of Object.entries(schemes)) {
    const rawSlice = values.slice(startIndex);
    const startVal = rawSlice[0] || 10000;
    // Rebase so that the initial value is exactly 10,000 INR
    slicedSchemes[name] = rawSlice.map(v => Math.round((v / startVal) * 10000));
  }
  
  return {
    dates: slicedDates,
    schemes: slicedSchemes
  };
}

// --- Render Growth Chart ---
function renderGrowthChart() {
  const ctx = document.getElementById("growthChart").getContext("2d");
  const filtered = getFilteredGrowthData();
  
  const datasets = Object.entries(filtered.schemes).map(([name, values]) => {
    const color = getSchemeColor(name);
    const shortName = name.split(" - ")[0];
    return {
      label: shortName,
      data: values,
      borderColor: color,
      backgroundColor: color + "10", // soft fill
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 5,
      tension: 0.1,
      fill: true
    };
  });
  
  if (growthChart) {
    growthChart.destroy();
  }
  
  growthChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: filtered.dates,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            font: { family: "'Inter', sans-serif", size: 11 },
            boxWidth: 12,
            padding: 15
          }
        },
        tooltip: {
          backgroundColor: "#0d1423",
          titleColor: "#ffffff",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255,255,255,0.08)",
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ₹${context.raw.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: "#64748b",
            font: { size: 10 },
            maxTicksLimit: 12
          }
        },
        y: {
          grid: { color: "rgba(255,255,255,0.03)" },
          ticks: {
            color: "#64748b",
            font: { size: 10 },
            callback: function(value) {
              return `₹${value.toLocaleString()}`;
            }
          }
        }
      }
    }
  });
}

// --- Render Risk-Reward Scatter Plot ---
function renderRiskChart() {
  const ctx = document.getElementById("riskChart").getContext("2d");
  const metrics = dashboardData.metrics;
  
  const datasets = metrics.map(m => {
    const color = getSchemeColor(m.name);
    return {
      label: m.short_name,
      data: [{ x: m.ann_volatility, y: m.ann_return }],
      backgroundColor: color,
      borderColor: color,
      pointRadius: 9,
      pointHoverRadius: 11,
      showLine: false
    };
  });
  
  if (riskChart) {
    riskChart.destroy();
  }
  
  riskChart = new Chart(ctx, {
    type: "scatter",
    data: { datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0d1423",
          padding: 12,
          callbacks: {
            title: function(items) {
              return items[0].dataset.label;
            },
            label: function(context) {
              return ` Risk (Volatility): ${context.raw.x}%\n Reward (CAGR): ${context.raw.y}%`;
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Annualised Volatility (%) - (RISK)",
            color: "#94a3b8",
            font: { weight: "600", size: 11 }
          },
          grid: { color: "rgba(255,255,255,0.03)" },
          ticks: { color: "#64748b" }
        },
        y: {
          title: {
            display: true,
            text: "Annualised Return (%) - (REWARD)",
            color: "#94a3b8",
            font: { weight: "600", size: 11 }
          },
          grid: { color: "rgba(255,255,255,0.03)" },
          ticks: { color: "#64748b" }
        }
      }
    }
  });
}

// --- Populate Quick Fund List ---
function populateFundList() {
  const container = document.getElementById("fund-mini-list");
  container.innerHTML = "";
  
  const sorted = [...dashboardData.metrics].sort((a, b) => b.ann_return - a.ann_return);
  
  sorted.forEach(m => {
    const color = getSchemeColor(m.name);
    const item = document.createElement("div");
    item.className = "fund-mini-item";
    
    const isHigh = m.risk_grade.toLowerCase().includes("very high");
    const riskBadgeClass = isHigh ? "high" : "moderate";
    
    item.innerHTML = `
      <div class="fund-info-left">
        <span class="fund-mini-name" title="${m.name}">${m.short_name}</span>
        <span class="fund-mini-house">${m.fund_house}</span>
      </div>
      <div>
        <span class="badge-risk ${riskBadgeClass}">${m.risk_grade}</span>
      </div>
    `;
    container.appendChild(item);
  });
}

// --- Render Comparative Metrics Table ---
function renderMetricsTable() {
  const tbody = document.getElementById("metrics-table-body");
  tbody.innerHTML = "";
  
  // Filter
  let filtered = dashboardData.metrics.filter(m => 
    m.name.toLowerCase().includes(currentSearchQuery.toLowerCase()) ||
    m.category.toLowerCase().includes(currentSearchQuery.toLowerCase()) ||
    m.fund_house.toLowerCase().includes(currentSearchQuery.toLowerCase())
  );
  
  // Sort
  filtered.sort((a, b) => {
    let valA = a[currentSortColumn];
    let valB = b[currentSortColumn];
    
    if (typeof valA === "string") {
      return currentSortOrder === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
    } else {
      return currentSortOrder === "asc" ? valA - valB : valB - valA;
    }
  });
  
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No funds match your query.</td></tr>`;
    return;
  }
  
  filtered.forEach(m => {
    const row = document.createElement("tr");
    
    const sharpeClass = m.sharpe_ratio > 0.6 ? "trend-up" : (m.sharpe_ratio < 0 ? "trend-down" : "");
    const returnClass = m.ann_return > 12 ? "trend-up" : "trend-down";
    
    row.innerHTML = `
      <td>
        <div class="fund-table-name" title="${m.name}">${m.short_name}</div>
        <div style="font-size: 0.78rem; color: var(--text-muted);">${m.category}</div>
      </td>
      <td>₹${m.cum_return.toLocaleString()}%</td>
      <td class="${returnClass}">${m.ann_return}%</td>
      <td>${m.ann_volatility}%</td>
      <td class="${sharpeClass}">${m.sharpe_ratio}</td>
      <td class="trend-down">${m.max_drawdown}%</td>
    `;
    tbody.appendChild(row);
  });
}

// --- Setup Timeframe Buttons ---
function setupTimeframeButtons() {
  const buttons = document.querySelectorAll(".chart-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", (e) => {
      buttons.forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      activeTimeframe = e.target.dataset.timeframe;
      
      // Update charts
      renderGrowthChart();
    });
  });
}

// --- Setup Table Search ---
function setupSearchInput() {
  const searchInput = document.getElementById("table-search");
  searchInput.addEventListener("input", (e) => {
    currentSearchQuery = e.target.value;
    renderMetricsTable();
  });
}

// --- Setup Table Column Sorting ---
function setupTableSort() {
  const headers = document.querySelectorAll(".metrics-table th[data-col]");
  headers.forEach(h => {
    h.addEventListener("click", (e) => {
      const col = e.target.dataset.col;
      
      // Toggle order if clicking same column
      if (currentSortColumn === col) {
        currentSortOrder = currentSortOrder === "asc" ? "desc" : "asc";
      } else {
        currentSortColumn = col;
        currentSortOrder = "desc"; // default to desc for metrics
      }
      
      // Update header indicators
      headers.forEach(header => {
        header.innerHTML = header.innerText.replace(" ▲", "").replace(" ▼", "");
      });
      
      e.target.innerHTML = e.target.innerText + (currentSortOrder === "asc" ? " ▲" : " ▼");
      
      renderMetricsTable();
    });
  });
}
