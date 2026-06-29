import json
import os

def main():
    notebook_path = "Performance_Analytics.ipynb" if os.path.basename(os.getcwd()) == "notebooks" else "notebooks/Performance_Analytics.ipynb"
    if os.path.dirname(notebook_path):
        os.makedirs(os.path.dirname(notebook_path), exist_ok=True)
        
    cells = []
    
    # 1. Title cell
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Mutual Fund Quantitative Performance & Risk Analytics\n",
            "\n",
            "This notebook performs a comprehensive financial and risk analytics evaluation on 40 mutual fund schemes using historical daily Net Asset Value (NAV) data from 2022 to 2026.\n",
            "\n",
            "### Objectives:\n",
            "1. **Daily Returns Analysis**: Compute and validate returns distributions for all 40 schemes.\n",
            "2. **CAGR Analysis**: Compute 1-year, 3-year, and 5-year compounded annualized growth rates.\n",
            "3. **Risk-Adjusted Returns**: Calculate Sharpe and Sortino Ratios using RBI Repo Rate proxy (6.5%).\n",
            "4. **OLS Regression (Alpha & Beta)**: Regress fund returns on Nifty 100 returns to calculate Alpha and Beta.\n",
            "5. **Maximum Drawdown**: Compute peak-to-trough declines and identify the worst drawdown date range.\n",
            "6. **Fund Scorecard**: Build a composite ranking score (0-100) based on weighted risk-return metrics.\n",
            "7. **Benchmark Comparison**: Plot the top 5 funds vs Nifty 50 and Nifty 100 over a 3-year horizon."
        ]
    })
    
    # 2. Imports and Setup
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import sqlite3\n",
            "import numpy as np\n",
            "import pandas as pd\n",
            "import scipy.stats as stats\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "from datetime import datetime, timedelta\n",
            "\n",
            "# Set visual style\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "plt.rcParams[\"figure.figsize\"] = (12, 6)\n",
            "plt.rcParams[\"font.size\"] = 10\n",
            "plt.rcParams[\"font.family\"] = \"sans-serif\"\n",
            "\n",
            "# Ensure output directories exist\n",
            "os.makedirs(\"../reports/plots\", exist_ok=True)\n",
            "os.makedirs(\"../reports\", exist_ok=True)\n",
            "print(\"Libraries loaded and folders verified.\")"
        ]
    })
    
    # 3. Database Connection and Loading Data
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Connect to processed SQLite database\n",
            "db_path = \"../Data/processed/mutual_funds.db\"\n",
            "if not os.path.exists(db_path):\n",
            "    db_path = \"Data/processed/mutual_funds.db\"\n",
            "\n",
            "conn = sqlite3.connect(db_path)\n",
            "print(f\"Connected successfully to database: {db_path}\")\n",
            "\n",
            "# Load daily NAV joined with fund details\n",
            "query = \"\"\"\n",
            "    SELECT fn.scheme_code, df.scheme_name, df.fund_house, df.category, df.sub_category, df.risk_grade, fn.date_key AS date, fn.nav\n",
            "    FROM fact_nav fn\n",
            "    JOIN dim_fund df ON fn.scheme_code = df.scheme_code\n",
            "\"\"\"\n",
            "df_nav_raw = pd.read_sql_query(query, conn)\n",
            "df_nav_raw['date'] = pd.to_datetime(df_nav_raw['date'])\n",
            "df_nav_raw = df_nav_raw.sort_values(['scheme_code', 'date']).reset_index(drop=True)\n",
            "\n",
            "# Load expense ratios and performance metrics from fact_performance\n",
            "perf_query = \"SELECT scheme_code, expense_ratio FROM fact_performance\"\n",
            "df_perf = pd.read_sql_query(perf_query, conn)\n",
            "\n",
            "print(f\"Loaded {len(df_nav_raw)} NAV rows across {df_nav_raw['scheme_code'].nunique()} funds.\")"
        ]
    })
    
    # 4. Reconstruct Benchmarks
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 1. Benchmark Reconstruction & Simulation\n",
            "\n",
            "We reconstruct the underlying market returns `market_returns` from `generate_eda_data.py` (which represents **Nifty 100**) using the identical seed `42` and date range. We then simulate the **Nifty 50** returns series using seed `50` to represent a highly correlated but distinct benchmark index."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import random\n",
            "\n",
            "start_date = datetime(2022, 1, 1)\n",
            "end_date = datetime(2026, 12, 31)\n",
            "num_days = (end_date - start_date).days + 1\n",
            "dates = [start_date + timedelta(days=i) for i in range(num_days)]\n",
            "\n",
            "# Reconstruct Nifty 100 returns (matching generate_eda_data.py seed 42)\n",
            "random.seed(42)\n",
            "np.random.seed(42)\n",
            "nifty100_returns = []\n",
            "for d in dates:\n",
            "    y, m = d.year, d.month\n",
            "    if y == 2022:\n",
            "        drift = -0.05 / 365\n",
            "        vol = 0.01\n",
            "    elif y == 2023:\n",
            "        drift = 0.28 / 365\n",
            "        vol = 0.008\n",
            "    elif y == 2024:\n",
            "        if m in [5, 6]:\n",
            "            drift = -0.45 / 365\n",
            "            vol = 0.015\n",
            "        else:\n",
            "            drift = 0.22 / 365\n",
            "            vol = 0.009\n",
            "    elif y == 2025:\n",
            "        drift = 0.32 / 365\n",
            "        vol = 0.0085\n",
            "    else: # 2026\n",
            "        drift = 0.06 / 365\n",
            "        vol = 0.007\n",
            "    nifty100_returns.append(np.random.normal(drift, vol))\n",
            "\n",
            "# Simulate Nifty 50 returns using seed 50\n",
            "random.seed(50)\n",
            "np.random.seed(50)\n",
            "nifty50_returns = []\n",
            "for d in dates:\n",
            "    y, m = d.year, d.month\n",
            "    if y == 2022:\n",
            "        drift = -0.04 / 365\n",
            "        vol = 0.0095\n",
            "    elif y == 2023:\n",
            "        drift = 0.26 / 365\n",
            "        vol = 0.0075\n",
            "    elif y == 2024:\n",
            "        if m in [5, 6]:\n",
            "            drift = -0.40 / 365\n",
            "            vol = 0.014\n",
            "        else:\n",
            "            drift = 0.20 / 365\n",
            "            vol = 0.0085\n",
            "    elif y == 2025:\n",
            "        drift = 0.30 / 365\n",
            "        vol = 0.008\n",
            "    else: # 2026\n",
            "        drift = 0.05 / 365\n",
            "        vol = 0.0065\n",
            "    nifty50_returns.append(np.random.normal(drift, vol))\n",
            "\n",
            "# Create benchmark returns DataFrames\n",
            "df_benchmarks = pd.DataFrame({\n",
            "    'date': dates,\n",
            "    'nifty100_return': nifty100_returns,\n",
            "    'nifty50_return': nifty50_returns\n",
            "})\n",
            "df_benchmarks['nifty100_nav'] = np.cumprod(1 + np.array(nifty100_returns)) * 10000.0\n",
            "df_benchmarks['nifty50_nav'] = np.cumprod(1 + np.array(nifty50_returns)) * 10000.0\n",
            "\n",
            "print(\"Benchmark returns and NAV indices successfully constructed.\")"
        ]
    })
    
    # 5. Compute Daily Returns
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Daily Returns Computation & Validation\n",
            "\n",
            "Daily returns are computed as:\n",
            "$$daily\\_return_t = \\frac{NAV_t}{NAV_{t-1}} - 1$$"
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Pivot NAV data to get dates as index and scheme codes as columns\n",
            "df_pivot = df_nav_raw.pivot(index='date', columns='scheme_code', values='nav')\n",
            "df_pivot = df_pivot.ffill()\n",
            "\n",
            "# Compute daily returns\n",
            "df_returns = df_pivot.pct_change()\n",
            "\n",
            "# Map scheme codes to names for columns\n",
            "fund_name_map = dict(zip(df_nav_raw['scheme_code'], df_nav_raw['scheme_name']))\n",
            "df_returns_named = df_returns.rename(columns=fund_name_map)\n",
            "\n",
            "print(f\"Daily returns computed. Shape: {df_returns.shape}\")"
        ]
    })
    
    # 6. Distribution Validation
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "### Distribution Validation\n",
            "\n",
            "We inspect the daily returns distribution using descriptive statistics (mean, std, min, max, skewness, and kurtosis) and visually plot return distributions to verify they look reasonable and are centered close to 0 with standard financial fat-tailed profiles."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Validate return distribution with summary statistics\n",
            "returns_summary = []\n",
            "for code in df_returns.columns:\n",
            "    ret_series = df_returns[code].dropna()\n",
            "    returns_summary.append({\n",
            "        'scheme_code': code,\n",
            "        'scheme_name': fund_name_map[code],\n",
            "        'mean': ret_series.mean(),\n",
            "        'std': ret_series.std(),\n",
            "        'min': ret_series.min(),\n",
            "        'max': ret_series.max(),\n",
            "        'skew': ret_series.skew(),\n",
            "        'kurtosis': ret_series.kurtosis()\n",
            "    })\n",
            "df_returns_summary = pd.DataFrame(returns_summary)\n",
            "\n",
            "# Display a subset of summary statistics\n",
            "print(\"Daily Returns Summary Statistics (First 10 Schemes):\")\n",
            "print(df_returns_summary.head(10).to_string(index=False))\n",
            "\n",
            "# Plot returns distribution for a sample of 5 funds\n",
            "plt.figure(figsize=(12, 6))\n",
            "sample_schemes = list(df_pivot.columns[:5])\n",
            "for code in sample_schemes:\n",
            "    sns.kdeplot(df_returns[code].dropna(), label=fund_name_map[code][:35], fill=True, alpha=0.08)\n",
            "plt.title(\"Distribution of Daily Returns (Sample of 5 Funds)\", fontweight='bold', fontsize=12)\n",
            "plt.xlabel(\"Daily Return\")\n",
            "plt.ylabel(\"Density\")\n",
            "plt.legend(loc='upper right', framealpha=0.9)\n",
            "plt.tight_layout()\n",
            "plt.savefig(\"../reports/plots/returns_distribution.png\", dpi=150)\n",
            "plt.show()"
        ]
    })
    
    # 7. CAGR Calculation
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Compounded Annual Growth Rate (CAGR) Analysis\n",
            "\n",
            "CAGR is calculated as:\n",
            "$$CAGR = \\left(\\frac{NAV_{end}}{NAV_{start}}\\right)^{\\frac{1}{n}} - 1$$\n",
            "\n",
            "We compute CAGR for three specific horizons:\n",
            "- **1 Year**: 2025-12-31 to 2026-12-31 ($n = 1.0$)\n",
            "- **3 Year**: 2023-12-31 to 2026-12-31 ($n = 3.0$)\n",
            "- **5 Year**: 2022-01-01 to 2026-12-31 ($n = 1825 / 365.25 \\approx 5.0$)"
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "cagr_data = []\n",
            "for code in df_pivot.columns:\n",
            "    navs = df_pivot[code]\n",
            "    \n",
            "    # 1yr CAGR\n",
            "    nav_end_1y = navs.loc['2026-12-31']\n",
            "    nav_start_1y = navs.loc['2025-12-31']\n",
            "    cagr_1y = (nav_end_1y / nav_start_1y) ** (1.0) - 1\n",
            "    \n",
            "    # 3yr CAGR\n",
            "    nav_end_3y = navs.loc['2026-12-31']\n",
            "    nav_start_3y = navs.loc['2023-12-31']\n",
            "    cagr_3y = (nav_end_3y / nav_start_3y) ** (1.0 / 3.0) - 1\n",
            "    \n",
            "    # 5yr CAGR (first day 2022-01-01 to 2026-12-31)\n",
            "    nav_end_5y = navs.loc['2026-12-31']\n",
            "    nav_start_5y = navs.loc['2022-01-01']\n",
            "    days_5y = (datetime(2026,12,31) - datetime(2022,1,1)).days\n",
            "    years_5y = days_5y / 365.25\n",
            "    cagr_5y = (nav_end_5y / nav_start_5y) ** (1.0 / years_5y) - 1\n",
            "    \n",
            "    cagr_data.append({\n",
            "        'scheme_code': code,\n",
            "        'scheme_name': fund_name_map[code],\n",
            "        'cagr_1yr': cagr_1y,\n",
            "        'cagr_3yr': cagr_3y,\n",
            "        'cagr_5yr': cagr_5y\n",
            "    })\n",
            "\n",
            "df_cagr = pd.DataFrame(cagr_data)\n",
            "print(\"Compounded Annualized Growth Rates (First 10 Schemes):\")\n",
            "print(df_cagr.head(10).to_string(index=False))"
        ]
    })
    
    # 8. Sharpe and Sortino Ratios
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. Sharpe and Sortino Ratios\n",
            "\n",
            "Ratios evaluate risk-adjusted performance using an annual risk-free rate proxy of $R_f = 6.5\\%$ (daily $R_f = 6.5\\% / 252$). Both ratios are annualized using $\\sqrt{252}$:\n",
            "\n",
            "- **Sharpe Ratio**:\n",
            "$$Sharpe = \\frac{R_p - R_f}{Std(R_p)} \\times \\sqrt{252}$$\n",
            "\n",
            "- **Sortino Ratio**:\n",
            "$$Sortino = \\frac{R_p - R_f}{DownsideStd(R_p)} \\times \\sqrt{252}$$\n",
            "where downside volatility is computed on negative return days only ($R_p < 0$)."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "rf_annual = 0.065\n",
            "rf_daily = rf_annual / 252\n",
            "\n",
            "ratios_data = []\n",
            "for code in df_returns.columns:\n",
            "    ret = df_returns[code].dropna()\n",
            "    mean_ret = ret.mean()\n",
            "    std_ret = ret.std()\n",
            "    \n",
            "    # Sharpe Ratio\n",
            "    sharpe = (mean_ret - rf_daily) / std_ret * np.sqrt(252) if std_ret > 0 else 0\n",
            "    \n",
            "    # Downside Volatility\n",
            "    downside_ret = ret[ret < 0]\n",
            "    downside_std = downside_ret.std()\n",
            "    \n",
            "    # Sortino Ratio\n",
            "    sortino = (mean_ret - rf_daily) / downside_std * np.sqrt(252) if downside_std > 0 else 0\n",
            "    \n",
            "    ratios_data.append({\n",
            "        'scheme_code': code,\n",
            "        'scheme_name': fund_name_map[code],\n",
            "        'sharpe_ratio': sharpe,\n",
            "        'sortino_ratio': sortino\n",
            "    })\n",
            "\n",
            "df_ratios = pd.DataFrame(ratios_data)\n",
            "print(\"Risk-Adjusted Ratios (First 10 Schemes):\")\n",
            "print(df_ratios.head(10).to_string(index=False))"
        ]
    })
    
    # 9. Alpha, Beta, Tracking Error
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 5. Alpha, Beta, and Tracking Error Analysis\n",
            "\n",
            "We regress daily fund returns on daily Nifty 100 returns using Ordinary Least Squares (OLS) regression (`scipy.stats.linregress`):\n",
            "- **Beta ($\\beta$)**: Slope of regression.\n",
            "- **Alpha ($\\alpha$)**: Intercept annualized, $\\alpha = intercept \\times 252$.\n",
            "- **Tracking Error**: Annualized standard deviation of active returns:\n",
            "$$Tracking\\_Error = Std(R_{fund} - R_{benchmark}) \\times \\sqrt{252}$$\n",
            "\n",
            "We also calculate tracking error relative to both benchmarks for robust analysis."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "nifty100_ret_series = df_benchmarks.set_index('date')['nifty100_return']\n",
            "nifty50_ret_series = df_benchmarks.set_index('date')['nifty50_return']\n",
            "\n",
            "alpha_beta_data = []\n",
            "for code in df_returns.columns:\n",
            "    fund_ret = df_returns[code].dropna()\n",
            "    # Align dates\n",
            "    aligned = pd.concat([fund_ret, nifty100_ret_series, nifty50_ret_series], axis=1, join='inner').dropna()\n",
            "    \n",
            "    fund_aligned = aligned.iloc[:, 0]\n",
            "    n100_aligned = aligned.iloc[:, 1]\n",
            "    n50_aligned = aligned.iloc[:, 2]\n",
            "    \n",
            "    # Regression against Nifty 100\n",
            "    slope, intercept, r_value, p_value, std_err = stats.linregress(n100_aligned, fund_aligned)\n",
            "    beta = slope\n",
            "    alpha = intercept * 252\n",
            "    \n",
            "    # Tracking Errors\n",
            "    te_n100 = (fund_aligned - n100_aligned).std() * np.sqrt(252)\n",
            "    te_n50 = (fund_aligned - n50_aligned).std() * np.sqrt(252)\n",
            "    \n",
            "    alpha_beta_data.append({\n",
            "        'scheme_code': code,\n",
            "        'scheme_name': fund_name_map[code],\n",
            "        'alpha': alpha,\n",
            "        'beta': beta,\n",
            "        'tracking_error_nifty100': te_n100,\n",
            "        'tracking_error_nifty50': te_n50\n",
            "    })\n",
            "\n",
            "df_alpha_beta = pd.DataFrame(alpha_beta_data)\n",
            "print(\"Alpha, Beta & Tracking Error (First 10 Schemes):\")\n",
            "print(df_alpha_beta.head(10).to_string(index=False))\n",
            "\n",
            "# Export alpha_beta.csv file\n",
            "df_alpha_beta.to_csv(\"../reports/alpha_beta.csv\", index=False)\n",
            "df_alpha_beta.to_csv(\"../alpha_beta.csv\", index=False) # save in root too\n",
            "print(\"Saved alpha_beta.csv successfully.\")"
        ]
    })
    
    # 10. Max Drawdown
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 6. Maximum Drawdown & Date Ranges\n",
            "\n",
            "Maximum drawdown is calculated as:\n",
            "$$Drawdown_t = \\frac{NAV_t}{RunningMax(NAV)_t} - 1$$\n",
            "$$MaxDrawdown = \\min(Drawdown)$$\n",
            "\n",
            "For each scheme, we identify the peak date (the last date running max was updated before the drawdown valley) and the trough date (the date of the worst drawdown valley) to establish the worst drawdown date range."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "mdd_data = []\n",
            "for code in df_pivot.columns:\n",
            "    navs = df_pivot[code]\n",
            "    running_max = navs.cummax()\n",
            "    drawdowns = navs / running_max - 1\n",
            "    max_dd = drawdowns.min()\n",
            "    \n",
            "    trough_date = drawdowns.idxmin()\n",
            "    peak_date = navs.loc[:trough_date].idxmax()\n",
            "    \n",
            "    mdd_data.append({\n",
            "        'scheme_code': code,\n",
            "        'scheme_name': fund_name_map[code],\n",
            "        'max_drawdown': max_dd,\n",
            "        'drawdown_peak_date': peak_date.strftime('%Y-%m-%d'),\n",
            "        'drawdown_trough_date': trough_date.strftime('%Y-%m-%d')\n",
            "    })\n",
            "\n",
            "df_mdd = pd.DataFrame(mdd_data)\n",
            "print(\"Maximum Drawdowns and Peak-to-Trough Date Ranges (First 10 Schemes):\")\n",
            "print(df_mdd.head(10).to_string(index=False))"
        ]
    })
    
    # 11. Fund Scorecard
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Fund Scorecard Compilation\n",
            "\n",
            "We construct a composite scorecard index $(0-100)$ to rank all 40 schemes based on the following weighted ranks:\n",
            "- **30%** weight on **3-year return rank**\n",
            "- **25%** weight on **Sharpe ratio rank**\n",
            "- **20%** weight on **Alpha rank**\n",
            "- **15%** weight on **Expense Ratio rank (inverse)** (lower is better)\n",
            "- **10%** weight on **Maximum Drawdown rank (inverse)** (less negative/higher is better)\n",
            "\n",
            "All ranks are percentile-normalized: $R_{metric} = \\frac{rank - 1}{N - 1} \\times 100$ so the worst fund gets $0$ and the best gets $100$."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Compile all metrics into one DataFrame\n",
            "df_master_metrics = df_cagr.merge(df_ratios, on=['scheme_code', 'scheme_name'])\n",
            "df_master_metrics = df_master_metrics.merge(df_alpha_beta, on=['scheme_code', 'scheme_name'])\n",
            "df_master_metrics = df_master_metrics.merge(df_mdd, on=['scheme_code', 'scheme_name'])\n",
            "df_master_metrics = df_master_metrics.merge(df_perf[['scheme_code', 'expense_ratio']], on='scheme_code')\n",
            "\n",
            "# Calculate ranks (1 to 40)\n",
            "df_master_metrics['rank_3yr'] = df_master_metrics['cagr_3yr'].rank(ascending=True)\n",
            "df_master_metrics['rank_sharpe'] = df_master_metrics['sharpe_ratio'].rank(ascending=True)\n",
            "df_master_metrics['rank_alpha'] = df_master_metrics['alpha'].rank(ascending=True)\n",
            "df_master_metrics['rank_expense'] = df_master_metrics['expense_ratio'].rank(ascending=False) # Lower expense is better\n",
            "df_master_metrics['rank_max_dd'] = df_master_metrics['max_drawdown'].rank(ascending=True) # Less negative is better\n",
            "\n",
            "# Normalize ranks to 0-100 scale\n",
            "N = len(df_master_metrics)\n",
            "for col in ['rank_3yr', 'rank_sharpe', 'rank_alpha', 'rank_expense', 'rank_max_dd']:\n",
            "    df_master_metrics[f'{col}_norm'] = (df_master_metrics[col] - 1) / (N - 1) * 100\n",
            "\n",
            "# Compute composite score\n",
            "df_master_metrics['scorecard_score'] = (\n",
            "    0.30 * df_master_metrics['rank_3yr_norm'] +\n",
            "    0.25 * df_master_metrics['rank_sharpe_norm'] +\n",
            "    0.20 * df_master_metrics['rank_alpha_norm'] +\n",
            "    0.15 * df_master_metrics['rank_expense_norm'] +\n",
            "    0.10 * df_master_metrics['rank_max_dd_norm']\n",
            ")\n",
            "\n",
            "# Sort and assign overall rank\n",
            "df_master_metrics = df_master_metrics.sort_values(by='scorecard_score', ascending=False).reset_index(drop=True)\n",
            "df_master_metrics['overall_rank'] = df_master_metrics.index + 1\n",
            "\n",
            "# Select scorecard report columns\n",
            "scorecard_cols = [\n",
            "    'overall_rank', 'scheme_name', 'scheme_code', 'scorecard_score',\n",
            "    'cagr_3yr', 'sharpe_ratio', 'alpha', 'expense_ratio', 'max_drawdown',\n",
            "    'drawdown_peak_date', 'drawdown_trough_date'\n",
            "]\n",
            "df_scorecard_report = df_master_metrics[scorecard_cols]\n",
            "\n",
            "print(\"Top 10 Schemes by Composite Scorecard Score:\")\n",
            "print(df_scorecard_report.head(10).to_string(index=False))\n",
            "\n",
            "# Export scorecard to CSV\n",
            "df_scorecard_report.to_csv(\"../reports/fund_scorecard.csv\", index=False)\n",
            "df_scorecard_report.to_csv(\"../fund_scorecard.csv\", index=False) # save in root too\n",
            "print(\"Saved fund_scorecard.csv successfully.\")"
        ]
    })
    
    # 12. Benchmark Comparison Chart
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 8. Benchmark Comparison Chart (3-Year Timeline)\n",
            "\n",
            "We select the **top 5 funds** based on our scorecard composite index and plot their cumulative performance (Growth of 10,000 INR starting on `2024-01-01`) against both **Nifty 50** and **Nifty 100** benchmarks through `2026-12-31`."
        ]
    })
    
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Filter top 5 schemes\n",
            "top_5_schemes = list(df_scorecard_report.head(5)['scheme_code'])\n",
            "\n",
            "start_3y = '2024-01-01'\n",
            "df_nav_3y = df_pivot[top_5_schemes].loc[start_3y:'2026-12-31']\n",
            "\n",
            "# Normalize growth of 10k\n",
            "df_growth_3y = (df_nav_3y / df_nav_3y.iloc[0]) * 10000.0\n",
            "\n",
            "# Add benchmark series standardized to 2024-01-01\n",
            "df_benchmarks_3y = df_benchmarks.set_index('date').loc[start_3y:'2026-12-31']\n",
            "bench_growth_100 = (df_benchmarks_3y['nifty100_nav'] / df_benchmarks_3y['nifty100_nav'].iloc[0]) * 10000.0\n",
            "bench_growth_50 = (df_benchmarks_3y['nifty50_nav'] / df_benchmarks_3y['nifty50_nav'].iloc[0]) * 10000.0\n",
            "\n",
            "# Plotting\n",
            "plt.figure(figsize=(14, 8))\n",
            "for code in top_5_schemes:\n",
            "    plt.plot(df_growth_3y.index, df_growth_3y[code], label=f\"{fund_name_map[code][:35]}...\", linewidth=1.5)\n",
            "\n",
            "# Plot benchmarks with distinct styling\n",
            "plt.plot(bench_growth_100.index, bench_growth_100, label=\"Nifty 100 Benchmark\", color='black', linestyle='--', linewidth=2.5)\n",
            "plt.plot(bench_growth_50.index, bench_growth_50, label=\"Nifty 50 Benchmark\", color='red', linestyle='-.', linewidth=2.5)\n",
            "\n",
            "plt.title(\"3-Year Cumulative Growth of 10,000 INR: Top 5 Funds vs Benchmarks (2024-2026)\", fontsize=14, fontweight='bold', pad=15)\n",
            "plt.xlabel(\"Date\", fontsize=12)\n",
            "plt.ylabel(\"Investment Value (INR)\", fontsize=12)\n",
            "plt.legend(loc='upper left', frameon=True, shadow=True, facecolor='white', framealpha=0.9)\n",
            "plt.tight_layout()\n",
            "\n",
            "# Save chart PNG\n",
            "plt.savefig(\"../reports/plots/benchmark_comparison.png\", dpi=300)\n",
            "plt.savefig(\"../benchmark_comparison.png\", dpi=300) # save in root too\n",
            "plt.show()\n",
            "print(\"Benchmark comparison chart generated and saved successfully.\")"
        ]
    })
    
    # 13. Closing Connection
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "conn.close()\n",
            "print(\"Database connection closed.\")"
        ]
    })
    
    # Notebook structure JSON
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1)
        
    print(f"[SUCCESS] Notebook template generated at {notebook_path}")

if __name__ == "__main__":
    main()
