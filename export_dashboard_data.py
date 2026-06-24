import os
import json
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

def main():
    db_path = "Data/processed/mutual_funds.db"
    if not os.path.exists(db_path):
        print("Error: Database mutual_funds.db not found.")
        return
        
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Query data
    query = """
        SELECT nh.scheme_code, fm.scheme_name, fm.fund_house, fm.category, fm.sub_category, fm.risk_grade, nh.date, nh.nav
        FROM nav_history nh
        JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
    """
    df = pd.read_sql(query, con=engine)
    
    # Sort chronologically
    df['parsed_date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
    df = df.sort_values(['scheme_name', 'parsed_date']).reset_index(drop=True)
    
    # Pivot for growth and daily return calculations
    df_pivot = df.pivot(index='parsed_date', columns='scheme_name', values='nav')
    df_pivot = df_pivot.ffill().dropna()
    
    dates_str = [d.strftime('%Y-%m-%d') for d in df_pivot.index]
    
    # Daily returns
    df_returns = df_pivot.pct_change().dropna()
    rf_daily = 0.06 / 365  # 6% risk free rate
    
    # Compute metrics
    metrics = []
    growth_series = {}
    
    for col in df_pivot.columns:
        # Get scheme metadata from dataframe
        subset = df[df['scheme_name'] == col]
        meta = subset.iloc[0]
        code = int(meta['scheme_code'])
        house = meta['fund_house']
        cat = meta['category']
        sub_cat = meta['sub_category']
        risk = meta['risk_grade']
        
        # Calculate returns & risk
        cum_ret = (df_pivot[col].iloc[-1] / df_pivot[col].iloc[0]) - 1
        n_days = (df_pivot.index[-1] - df_pivot.index[0]).days
        years = n_days / 365.25
        ann_ret = (cum_ret + 1) ** (1 / years) - 1 if years > 0 else 0
        
        daily_vol = df_returns[col].std()
        ann_vol = daily_vol * np.sqrt(365)
        
        excess_returns = df_returns[col] - rf_daily
        sharpe = (excess_returns.mean() / daily_vol) * np.sqrt(365) if daily_vol > 0 else 0

        
        running_max = df_pivot[col].cummax()
        drawdown = (df_pivot[col] / running_max) - 1
        max_dd = drawdown.min()
        
        # Shorten scheme name for visual charts
        short_name = col.split(" - ")[0][:30]
        
        metrics.append({
            "code": code,
            "name": col,
            "short_name": short_name,
            "fund_house": house,
            "category": cat,
            "sub_category": sub_cat,
            "risk_grade": risk,
            "cum_return": round(cum_ret * 100, 2),
            "ann_return": round(ann_ret * 100, 2),
            "ann_volatility": round(ann_vol * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown": round(max_dd * 100, 2)
        })
        
        # Growth of 10,000 INR
        growth_values = ((df_pivot[col] / df_pivot[col].iloc[0]) * 10000).round(2).tolist()
        growth_series[col] = growth_values
        
    dashboard_data = {
        "metrics": metrics,
        "growth": {
            "dates": dates_str,
            "schemes": growth_series
        }
    }
    
    os.makedirs("dashboard", exist_ok=True)
    out_path = "dashboard/dashboard_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)
    print(f"Successfully exported data to {out_path}")

if __name__ == "__main__":
    main()
