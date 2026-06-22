import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

def main():
    db_path = "data/processed/mutual_funds.db"
    if not os.path.exists(db_path):
        print("Error: Database mutual_funds.db not found.")
        return
        
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Load nav history joined with master
    query = """
        SELECT nh.scheme_code, fm.scheme_name, fm.fund_house, fm.category, nh.date, nh.nav
        FROM nav_history nh
        JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
    """
    df = pd.read_sql(query, con=engine)
    
    # Parse date and sort
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
    df = df.sort_values(['scheme_name', 'date']).reset_index(drop=True)
    
    # Pivot to get date as index and scheme names as columns
    df_pivot = df.pivot(index='date', columns='scheme_name', values='nav')
    # Fill any missing values using forward fill
    df_pivot = df_pivot.ffill().dropna()
    
    print(f"Pivoted dataset shape: {df_pivot.shape}")
    
    # 1. Cumulative Returns (Growth of 10,000 INR)
    initial_val = 10000
    df_growth = (df_pivot / df_pivot.iloc[0]) * initial_val
    
    # Plot Growth of 10,000 INR
    plt.figure(figsize=(12, 7))
    sns.set_theme(style="whitegrid")
    
    for col in df_growth.columns:
        plt.plot(df_growth.index, df_growth[col], label=col, linewidth=1.5)
        
    plt.title("Growth of 10,000 INR Investment Over Time", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Investment Value (INR)", fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    plt.tight_layout()
    
    os.makedirs("reports/plots", exist_ok=True)
    growth_plot_path = "reports/plots/growth_investment.png"
    plt.savefig(growth_plot_path, dpi=300)
    plt.close()
    print(f"Saved growth plot to {growth_plot_path}")
    
    # 2. Daily returns and volatility
    df_returns = df_pivot.pct_change().dropna()
    
    # Calculate performance metrics
    metrics = []
    
    # Risk-free rate (assumed 6% annualized, daily approx: 6% / 252)
    rf_daily = 0.06 / 252
    
    for col in df_pivot.columns:
        # Cumulative Return
        cum_ret = (df_pivot[col].iloc[-1] / df_pivot[col].iloc[0]) - 1
        
        # Annualized Return (compounded)
        n_days = (df_pivot.index[-1] - df_pivot.index[0]).days
        years = n_days / 365.25
        ann_ret = (cum_ret + 1) ** (1 / years) - 1 if years > 0 else 0
        
        # Annualized Volatility
        daily_vol = df_returns[col].std()
        ann_vol = daily_vol * np.sqrt(252)
        
        # Sharpe Ratio
        excess_returns = df_returns[col] - rf_daily
        sharpe = (excess_returns.mean() / daily_vol) * np.sqrt(252) if daily_vol > 0 else 0
        
        # Maximum Drawdown
        running_max = df_pivot[col].cummax()
        drawdown = (df_pivot[col] / running_max) - 1
        max_dd = drawdown.min()
        
        metrics.append({
            "Scheme Name": col,
            "Total Days": len(df_pivot),
            "Cumulative Return (%)": round(cum_ret * 100, 2),
            "Annualized Return (%)": round(ann_ret * 100, 2),
            "Annualized Volatility (%)": round(ann_vol * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown (%)": round(max_dd * 100, 2)
        })
        
    df_metrics = pd.DataFrame(metrics)
    
    # Save metrics to reports
    df_metrics.to_csv("reports/performance_metrics.csv", index=False)
    print("Saved performance_metrics.csv")
    
    # 3. Risk vs Return Scatter Plot
    plt.figure(figsize=(10, 6))
    scatter = sns.scatterplot(
        data=df_metrics, 
        x="Annualized Volatility (%)", 
        y="Annualized Return (%)", 
        s=150, 
        hue="Scheme Name",
        palette="deep",
        legend=False
    )
    
    # Annotate points
    for idx, row in df_metrics.iterrows():
        plt.text(
            row["Annualized Volatility (%)"] + 0.2, 
            row["Annualized Return (%)"], 
            row["Scheme Name"].split(" - ")[0][:20], # Short name
            fontsize=9, 
            verticalalignment='center'
        )
        
    plt.title("Risk-Return Tradeoff Analysis", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Annualized Volatility (%) - (Risk)", fontsize=12)
    plt.ylabel("Annualized Return (%) - (Reward)", fontsize=12)
    plt.tight_layout()
    
    risk_plot_path = "reports/plots/risk_return_tradeoff.png"
    plt.savefig(risk_plot_path, dpi=300)
    plt.close()
    print(f"Saved risk-return plot to {risk_plot_path}")
    
    # 4. Generate Financial Analysis Markdown Report
    report_path = "reports/financial_analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Mutual Fund Portfolio Analysis Report\n\n")
        f.write("This report provides a financial analysis of the historical Net Asset Value (NAV) performance, risk metrics, and drawdowns for the ingested mutual fund schemes.\n\n")
        
        f.write("## 1. Executive Performance Metrics Table\n\n")
        f.write("| Scheme Name | Cumulative Return | Annualized Return | Annualized Volatility | Sharpe Ratio | Max Drawdown |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        
        for m in metrics:
            f.write(f"| {m['Scheme Name']} | {m['Cumulative Return (%)']}% | {m['Annualized Return (%)']}% | {m['Annualized Volatility (%)']}% | {m['Sharpe Ratio']} | {m['Max Drawdown (%)']}% |\n")
        f.write("\n\n")
        
        f.write("## 2. Investment Growth Visualisation\n\n")
        f.write("The chart below illustrates the growth of an initial investment of 10,000 INR across all funds based on daily historical NAV data.\n\n")
        f.write("![Growth of 10k Investment](plots/growth_investment.png)\n\n")
        
        f.write("## 3. Risk-Reward Tradeoff Analysis\n\n")
        f.write("The chart below shows the risk (annualized volatility) vs. reward (annualized returns) of the funds. In general, higher returns are expected to carry higher risk (volatility).\n\n")
        f.write("![Risk Return Tradeoff](plots/risk_return_tradeoff.png)\n\n")
        
        f.write("## 4. Key Financial Observations\n\n")
        f.write("- **Highest Performing Scheme:** " + df_metrics.loc[df_metrics["Annualized Return (%)"].idxmax()]["Scheme Name"] + " with an annualized return of " + str(df_metrics["Annualized Return (%)"].max()) + "%.\n")
        f.write("- **Lowest Volatility (Safest) Scheme:** " + df_metrics.loc[df_metrics["Annualized Volatility (%)"].idxmin()]["Scheme Name"] + " with an annualized volatility of " + str(df_metrics["Annualized Volatility (%)"].min()) + "%.\n")
        f.write("- **Best Risk-Adjusted Returns (Highest Sharpe Ratio):** " + df_metrics.loc[df_metrics["Sharpe Ratio"].idxmax()]["Scheme Name"] + " with a Sharpe ratio of " + str(df_metrics["Sharpe Ratio"].max()) + ".\n")
        f.write("- **Worst Peak-to-Trough Decline (Max Drawdown):** " + df_metrics.loc[df_metrics["Max Drawdown (%)"].idxmin()]["Scheme Name"] + " with a drawdown of " + str(df_metrics["Max Drawdown (%)"].min()) + "%.\n")
        
    print(f"Generated text report at {report_path}")

if __name__ == "__main__":
    main()
