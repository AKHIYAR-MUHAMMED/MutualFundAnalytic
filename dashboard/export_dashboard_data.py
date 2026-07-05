import os
import json
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def main():
    db_path = "Data/processed/mutual_funds.db"
    if not os.path.exists(db_path):
        db_path = "../Data/processed/mutual_funds.db"
        if not os.path.exists(db_path):
            print("Error: Database mutual_funds.db not found.")
            return
            
    conn = sqlite3.connect(db_path)
    
    # 1. Load Fund Metadata and performance details
    query_perf = """
        SELECT df.scheme_code, df.scheme_name, df.fund_house, df.category, df.sub_category, df.risk_grade,
               fp.return_1yr, fp.return_3yr, fp.return_5yr, fp.expense_ratio, fa.aum_amount AS aum
        FROM dim_fund df
        LEFT JOIN fact_performance fp ON df.scheme_code = fp.scheme_code
        LEFT JOIN fact_aum fa ON df.scheme_code = fa.scheme_code AND fa.date_key = (SELECT MAX(date_key) FROM fact_aum)
    """
    df_perf = pd.read_sql_query(query_perf, conn)
    
    # 2. Daily NAV History for all funds
    query_nav = "SELECT scheme_code, date_key AS date, nav FROM fact_nav ORDER BY scheme_code, date_key"
    df_nav = pd.read_sql_query(query_nav, conn)
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    
    # Reconstruct Nifty 100 and Nifty 50 benchmarks (matching notebook calculations)
    import random
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 12, 31)
    num_days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(num_days)]
    date_strs = [d.strftime('%Y-%m-%d') for d in dates]
    
    # Nifty 100
    random.seed(42)
    np.random.seed(42)
    n100_returns = []
    for d in dates:
        y, m = d.year, d.month
        if y == 2022: drift, vol = -0.05 / 365, 0.01
        elif y == 2023: drift, vol = 0.28 / 365, 0.008
        elif y == 2024: drift, vol = (-0.45 / 365, 0.015) if m in [5, 6] else (0.22 / 365, 0.009)
        elif y == 2025: drift, vol = 0.32 / 365, 0.0085
        else: drift, vol = 0.06 / 365, 0.007
        n100_returns.append(np.random.normal(drift, vol))
        
    # Nifty 50
    random.seed(50)
    np.random.seed(50)
    n50_returns = []
    for d in dates:
        y, m = d.year, d.month
        if y == 2022: drift, vol = -0.04 / 365, 0.0095
        elif y == 2023: drift, vol = 0.26 / 365, 0.0075
        elif y == 2024: drift, vol = (-0.40 / 365, 0.014) if m in [5, 6] else (0.20 / 365, 0.0085)
        elif y == 2025: drift, vol = 0.30 / 365, 0.008
        else: drift, vol = 0.05 / 365, 0.0065
        n50_returns.append(np.random.normal(drift, vol))
        
    n100_nav = np.cumprod(1 + np.array(n100_returns)) * 10000.0
    n50_nav = np.cumprod(1 + np.array(n50_returns)) * 10000.0
    
    # Pivot NAV to get scheme growth profiles
    df_pivot = df_nav.pivot(index='date', columns='scheme_code', values='nav')
    df_pivot = df_pivot.ffill().dropna()
    dates_list = [d.strftime('%Y-%m-%d') for d in df_pivot.index]
    
    # Daily returns for metrics calculations
    df_returns = df_pivot.pct_change().dropna()
    rf_daily = 0.065 / 252
    
    # Compute scorecard composite metrics in Python (matching Performance_Analytics.ipynb)
    metrics_list = []
    growth_series = {}
    
    # We will compute 3y return, sharpe, alpha, max dd to rank them
    temp_list = []
    for code in df_pivot.columns:
        navs = df_pivot[code]
        rets = df_returns[code]
        
        # Metadata
        meta = df_perf[df_perf['scheme_code'] == code].iloc[0]
        
        # CAGR 3y
        nav_end = navs.loc['2026-12-31']
        nav_start_3y = navs.loc['2023-12-31']
        cagr_3yr = (nav_end / nav_start_3y) ** (1.0 / 3.0) - 1
        
        # CAGR 1y
        nav_start_1y = navs.loc['2025-12-31']
        cagr_1yr = (nav_end / nav_start_1y) ** (1.0) - 1
        
        # CAGR 5y
        nav_start_5y = navs.loc['2022-01-01']
        days_5y = (datetime(2026, 12, 31) - datetime(2022, 1, 1)).days
        years_5y = days_5y / 365.25
        cagr_5yr = (nav_end / nav_start_5y) ** (1.0 / years_5y) - 1
        
        # Sharpe
        std_ret = rets.std()
        sharpe = (rets.mean() - rf_daily) / std_ret * np.sqrt(252) if std_ret > 0 else 0
        
        # Sortino (Downside)
        downside_std = rets[rets < 0].std()
        sortino = (rets.mean() - rf_daily) / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        # Alpha/Beta against Nifty 100
        # Align
        bench_ret = pd.Series(n100_returns, index=dates)[1:]
        aligned = pd.concat([rets, bench_ret], axis=1).dropna()
        slope, intercept, r_val, p_val, std_err = stats_reg(aligned.iloc[:, 1], aligned.iloc[:, 0])
        beta = slope
        alpha = intercept * 252
        
        # Max Drawdown
        running_max = navs.cummax()
        drawdown = navs / running_max - 1
        max_dd = drawdown.min()
        
        trough_date = drawdown.idxmin()
        peak_date = navs.loc[:trough_date].idxmax()
        
        # Tracking errors
        bench_50_ret = pd.Series(n50_returns, index=dates)[1:]
        te_n100 = (aligned.iloc[:, 0] - aligned.iloc[:, 1]).std() * np.sqrt(252)
        te_n50 = (aligned.iloc[:, 0] - bench_50_ret).std() * np.sqrt(252)
        
        short_name = meta['scheme_name'].split(" - ")[0][:35]
        
        temp_list.append({
            'scheme_code': int(code),
            'scheme_name': meta['scheme_name'],
            'short_name': short_name,
            'fund_house': meta['fund_house'],
            'category': meta['category'],
            'sub_category': meta['sub_category'],
            'risk_grade': meta['risk_grade'],
            'expense_ratio': float(meta['expense_ratio']),
            'aum': float(meta['aum']),
            'cagr_1yr': float(cagr_1yr),
            'cagr_3yr': float(cagr_3yr),
            'cagr_5yr': float(cagr_5yr),
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'alpha': float(alpha),
            'beta': float(beta),
            'max_drawdown': float(max_dd),
            'drawdown_peak_date': peak_date.strftime('%Y-%m-%d'),
            'drawdown_trough_date': trough_date.strftime('%Y-%m-%d'),
            'tracking_error_nifty100': float(te_n100),
            'tracking_error_nifty50': float(te_n50)
        })
        
        # Growth series of 10,000 INR
        growth_vals = ((navs / navs.iloc[0]) * 10000.0).round(2).tolist()
        growth_series[str(code)] = growth_vals
        
    df_temp = pd.DataFrame(temp_list)
    
    # Scorecard ranks
    N = len(df_temp)
    df_temp['rank_3yr'] = df_temp['cagr_3yr'].rank(ascending=True)
    df_temp['rank_sharpe'] = df_temp['sharpe_ratio'].rank(ascending=True)
    df_temp['rank_alpha'] = df_temp['alpha'].rank(ascending=True)
    df_temp['rank_expense'] = df_temp['expense_ratio'].rank(ascending=False)
    df_temp['rank_max_dd'] = df_temp['max_drawdown'].rank(ascending=True)
    
    # Score
    df_temp['scorecard_score'] = (
        0.30 * ((df_temp['rank_3yr'] - 1) / (N - 1) * 100) +
        0.25 * ((df_temp['rank_sharpe'] - 1) / (N - 1) * 100) +
        0.20 * ((df_temp['rank_alpha'] - 1) / (N - 1) * 100) +
        0.15 * ((df_temp['rank_expense'] - 1) / (N - 1) * 100) +
        0.10 * ((df_temp['rank_max_dd'] - 1) / (N - 1) * 100)
    )
    
    df_temp = df_temp.sort_values(by='scorecard_score', ascending=False).reset_index(drop=True)
    df_temp['overall_rank'] = df_temp.index + 1
    
    # Export metrics as list of dicts
    final_metrics = df_temp.to_dict(orient='records')
    
    # 3. Industry Stats & Trends
    # AUM trend: sum AMC AUM growth by year, scaled so 2025 matches exactly 81 Lakh Crores
    df_aum_growth = pd.read_sql_query("SELECT year, SUM(aum_lakh_cr) AS aum FROM fact_aum_growth GROUP BY year", conn)
    aum_2025_sum = df_aum_growth[df_aum_growth['year'] == 2025]['aum'].iloc[0]
    scale_factor = 81.0 / aum_2025_sum
    df_aum_growth['scaled_aum'] = (df_aum_growth['aum'] * scale_factor).round(2)
    
    # AUM by AMC in 2025
    df_amc_2025 = pd.read_sql_query("SELECT fund_house, aum_lakh_cr AS aum FROM fact_aum_growth WHERE year = 2025 ORDER BY aum_lakh_cr DESC", conn)
    amc_names = df_amc_2025['fund_house'].str.replace(' Mutual Fund', '').str.replace(' Mahindra', '').tolist()
    amc_aums = df_amc_2025['aum'].tolist()
    
    industry_data = {
        "total_aum": 81.0,
        "total_sip": 31002,
        "total_folios": 26.12,
        "total_schemes": 1908,
        "aum_trend": {
            "years": df_aum_growth['year'].tolist(),
            "values": df_aum_growth['scaled_aum'].tolist()
        },
        "aum_by_amc": {
            "amcs": amc_names,
            "values": amc_aums
        }
    }
    
    # 4. Investor Demographics & Transactions
    # Pre-join and aggregate transactional data for client-side slicing
    # Slicing dimensions: state, age_group, city_tier
    # Sum transaction amounts and count transactions
    query_tx = """
        SELECT ft.scheme_code, ft.date_key, ft.transaction_type, ft.amount, ft.state,
               di.age_group, di.city_tier, di.gender
        FROM fact_transactions ft
        JOIN dim_investor di ON ft.investor_id = di.investor_id
    """
    df_tx_raw = pd.read_sql_query(query_tx, conn)
    
    # Save a simplified pre-joined transactions list (only needed columns to keep size compact)
    # Convert dates to Month YYYY-MM
    df_tx_raw['month'] = df_tx_raw['date_key'].str.slice(0, 7)
    tx_records = df_tx_raw[['scheme_code', 'month', 'transaction_type', 'amount', 'state', 'age_group', 'city_tier', 'gender']].to_dict(orient='split')['data']
    
    # Pre-calculated aggregates for defaults
    by_state = df_tx_raw.groupby('state')['amount'].sum().reset_index().sort_values(by='amount', ascending=False)
    txn_split = df_tx_raw.groupby('transaction_type')['amount'].sum().reset_index()
    age_avg_sip = df_tx_raw.groupby('age_group')['amount'].mean().reset_index() # using tx amount proxy
    
    # Monthly volume and amounts
    monthly_vol = df_tx_raw.groupby('month').agg(count=('amount', 'count'), amount=('amount', 'sum')).reset_index()
    
    investor_data = {
        "transactions_split_data": tx_records, # Raw slice-able data
        "by_state": {
            "states": by_state['state'].tolist(),
            "amounts": by_state['amount'].round(2).tolist()
        },
        "txn_split": {
            "types": txn_split['transaction_type'].tolist(),
            "amounts": txn_split['amount'].round(2).tolist()
        },
        "age_avg_sip": {
            "groups": age_avg_sip['age_group'].tolist(),
            "averages": age_avg_sip['amount'].round(2).tolist()
        },
        "monthly_volume": {
            "months": monthly_vol['month'].tolist(),
            "counts": monthly_vol['count'].tolist(),
            "amounts": monthly_vol['amount'].round(2).tolist()
        }
    }
    
    # 5. SIP & Market Trends
    df_market = pd.read_sql_query("SELECT * FROM fact_market_stats ORDER BY month", conn)
    
    # Nifty 50 NAV on last day of each month
    nifty50_monthly = []
    # Dates list mapping
    bench_dates = [d.strftime('%Y-%m') for d in dates]
    df_bench_monthly = pd.DataFrame({'month': bench_dates, 'nav': n50_nav})
    # Group by month and get last value
    n50_monthly_nav = df_bench_monthly.groupby('month')['nav'].last().reset_index()
    
    # Merge Nifty 50 with market stats
    df_market = df_market.merge(n50_monthly_nav, on='month', how='left')
    
    # Heatmap Net Inflows
    net_inflow_cat = {
        "equity": df_market['net_inflow_equity'].tolist(),
        "debt": df_market['net_inflow_debt'].tolist(),
        "hybrid": df_market['net_inflow_hybrid'].tolist(),
        "other": df_market['net_inflow_other'].tolist()
    }
    
    # Top categories in FY25 (April 2024 to March 2025)
    df_fy25 = df_market[(df_market['month'] >= '2024-04') & (df_market['month'] <= '2025-03')]
    fy25_totals = {
        "Equity": df_fy25['net_inflow_equity'].sum(),
        "Hybrid": df_fy25['net_inflow_hybrid'].sum(),
        "Other": df_fy25['net_inflow_other'].sum(),
        "Debt": df_fy25['net_inflow_debt'].sum()
    }
    # Sort
    sorted_fy25 = sorted(fy25_totals.items(), key=lambda x: x[1], reverse=True)
    fy25_cats = [x[0] for x in sorted_fy25]
    fy25_vals = [round(x[1], 2) for x in sorted_fy25]
    
    market_trends_data = {
        "months": df_market['month'].tolist(),
        "sip_inflow": df_market['total_sip_inflow'].tolist(),
        "nifty50_nav": df_market['nav'].round(2).tolist(),
        "net_inflow_by_category": net_inflow_cat,
        "fy25_top_categories": {
            "categories": fy25_cats,
            "inflows": fy25_vals
        }
    }
    
    # 6. Combined JSON structure
    dashboard_data = {
        "metrics": final_metrics,
        "growth": {
            "dates": dates_list,
            "schemes": growth_series
        },
        "benchmarks": {
            "dates": date_strs,
            "nifty100": n100_nav.round(2).tolist(),
            "nifty50": n50_nav.round(2).tolist()
        },
        "industry": industry_data,
        "investor": investor_data,
        "market_trends": market_trends_data
    }
    
    # Save to file
    out_dir = "dashboard"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dashboard_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)
        
    print(f"[SUCCESS] Expanded dashboard data exported to {out_path}")
    conn.close()

def stats_reg(x, y):
    """Calculates linear regression stats."""
    # We do a simple OLS linear regression
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xx = np.sum(x * x)
    sum_xy = np.sum(x * y)
    
    denom = (n * sum_xx - sum_x * sum_x)
    if denom == 0:
        return 0, 0, 0, 0, 0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept, 0, 0, 0

if __name__ == "__main__":
    main()
