import sys
import logging
import sqlite3
import pandas as pd
import numpy as np
import shutil
from pathlib import Path

# Set up basic console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def parse_date(date_str):
    """Parse a date string with multiple possible formats.
    Returns pandas.NaT on failure.
    """
    if not isinstance(date_str, str):
        return pd.NaT
    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return pd.NaT

def clean_return_val(val):
    """Convert return values to float, handling missing/invalid entries."""
    if val is None:
        return np.nan
    if not isinstance(val, str):
        if pd.isna(val):
            return np.nan
        return float(val)
    val_clean = val.strip().replace('%', '')
    if val_clean.upper() in ['N/A', 'NA', 'NULL', '']:
        return np.nan
    try:
        return float(val_clean)
    except ValueError:
        return np.nan

def clean_expense_ratio(val, scheme_code=None):
    """Sanitize expense ratio, clipping to the allowed SQLite range.
    The schema enforces 0.1 ≤ expense_ratio ≤ 2.5.
    """
    if val is None:
        return np.nan
    if not isinstance(val, str):
        if pd.isna(val):
            return np.nan
        ratio = float(val)
    else:
        val_clean = val.strip().replace('%', '')
        if val_clean.upper() in ['N/A', 'NA', 'NULL', '']:
            return np.nan
        try:
            ratio = float(val_clean)
        except ValueError:
            return np.nan
    # Clip to schema bounds
    if ratio < 0.1:
        ratio = 0.1
    elif ratio > 2.5:
        ratio = 2.5
    return ratio

def run_etl():
    # Resolve project root (one level up from this script)
    base_dir = Path(__file__).resolve().parents[1]
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    db_dir = base_dir / "data" / "db"
    schema_path = base_dir / "sql" / "schema.sql"

    # Ensure output directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    db_path = db_dir / "bluestock_mf.db"

    # Set up file logger
    file_handler = logging.FileHandler(logs_dir / "etl_pipeline.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    logging.info(f"Using database: {db_path}")

    # Verify required raw CSV files exist
    required_files = [
        "fund_master.csv",
        "nav_history.csv",
        "investor_transactions.csv",
        "investor_demographics.csv",
        "portfolio_holdings.csv",
        "scheme_performance.csv",
    ]
    for filename in required_files:
        path = raw_dir / filename
        if not path.exists():
            logging.error(f"Required raw file missing: {path}")
            return False

    # 1. Load and clean fund_master.csv
    logging.info("Processing fund_master.csv...")
    df_fund = pd.read_csv(raw_dir / "fund_master.csv")
    df_fund.to_csv(processed_dir / "fund_master.csv", index=False)

    # 2. Load and clean nav_history.csv (reindex, forward‑fill, decimal fixes)
    logging.info("Processing nav_history.csv...")
    df_nav = pd.read_csv(raw_dir / "nav_history.csv")
    df_nav["parsed_date"] = df_nav["date"].apply(parse_date)
    df_nav = df_nav.dropna(subset=["parsed_date"])
    df_nav["nav"] = pd.to_numeric(df_nav["nav"], errors="coerce")

    # Decimal anomaly for scheme 119092 before 30‑08‑2015 (multiply by 100)
    cutoff_date = pd.to_datetime("30-08-2015", format="%d-%m-%Y")
    mask_119092 = (df_nav["scheme_code"] == 119092) & (df_nav["parsed_date"] < cutoff_date)
    df_nav.loc[mask_119092, "nav"] = df_nav.loc[mask_119092, "nav"] * 100

    # Zero/negative NAV for scheme 120503 on 07‑04‑2013 -> set to NaN for interpolation
    df_nav.loc[(df_nav["scheme_code"] == 120503) & (df_nav["nav"] <= 0.0), "nav"] = np.nan

    # Reindex per scheme to fill missing dates (weekends/holidays)
    cleaned_nav_frames = []
    for code, grp in df_nav.groupby("scheme_code"):
        grp_sorted = grp.sort_values("parsed_date").copy()
        min_date, max_date = grp_sorted["parsed_date"].min(), grp_sorted["parsed_date"].max()
        full_range = pd.date_range(start=min_date, end=max_date, freq="D")
        grp_sorted = grp_sorted.set_index("parsed_date")
        grp_reindexed = grp_sorted.reindex(full_range)
        grp_reindexed.index.name = "parsed_date"
        grp_reindexed = grp_reindexed.reset_index()
        grp_reindexed["scheme_code"] = code
        grp_reindexed["nav"] = grp_reindexed["nav"].ffill().bfill()
        grp_reindexed["date"] = grp_reindexed["parsed_date"].dt.strftime("%d-%m-%Y")
        grp_reindexed["date_key"] = grp_reindexed["parsed_date"].dt.strftime("%Y-%m-%d")
        cleaned_nav_frames.append(
            grp_reindexed[["scheme_code", "date", "nav", "date_key"]]
        )
    df_nav_clean = pd.concat(cleaned_nav_frames, ignore_index=True)
    df_nav_clean[["scheme_code", "date", "nav"]].to_csv(
        processed_dir / "nav_history.csv", index=False
    )

    # 3. Load and clean investor transactions
    logging.info("Processing investor_transactions.csv...")
    df_tx = pd.read_csv(raw_dir / "investor_transactions.csv")
    df_tx["parsed_date"] = df_tx["transaction_date"].apply(parse_date)
    df_tx["date_key"] = df_tx["parsed_date"].dt.strftime("%Y-%m-%d")
    df_tx.drop(columns=["parsed_date", "transaction_date"], inplace=True)
    df_tx.to_csv(processed_dir / "investor_transactions.csv", index=False)

    # 4. Load and clean scheme performance
    logging.info("Processing scheme_performance.csv...")
    df_perf = pd.read_csv(raw_dir / "scheme_performance.csv")
    for col in ["return_1yr", "return_3yr", "return_5yr"]:
        df_perf[col] = df_perf[col].apply(clean_return_val)
    df_perf["expense_ratio"] = df_perf.apply(
        lambda row: clean_expense_ratio(row["expense_ratio"], row["scheme_code"]), axis=1
    )
    df_perf.to_csv(processed_dir / "scheme_performance.csv", index=False)

    # 5. Copy auxiliary CSV files unchanged
    aux_files = [
        "investor_demographics.csv",
        "portfolio_holdings.csv",
        "market_statistics.csv",
        "aum_growth.csv",
    ]
    for aux in aux_files:
        src = raw_dir / aux
        if src.exists():
            df_aux = pd.read_csv(src)
            df_aux.to_csv(processed_dir / aux, index=False)

    # 6. Initialise SQLite schema
    logging.info("Setting up SQLite database schema...")
    conn = sqlite3.connect(db_path)
    if not schema_path.exists():
        logging.error(f"Database schema file missing: {schema_path}")
        conn.close()
        return False
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor = conn.cursor()
    # Drop existing tables to ensure a fresh load
    tables_to_drop = [
        "fact_aum",
        "fact_performance",
        "fact_transactions",
        "fact_nav",
        "dim_date",
        "dim_fund",
        "fact_holdings",
        "dim_investor",
        "fact_market_stats",
        "fact_aum_growth",
    ]
    for tbl in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {tbl};")
    # Execute schema statements
    for stmt in schema_sql.split(";"):
        if stmt.strip():
            cursor.execute(stmt + ";")
    conn.commit()
    logging.info("SQLite database schema applied.")

    # 7. Load data into tables
    logging.info("Loading cleaned DataFrames into SQLite...")
    # dim_fund
    df_fund.to_sql("dim_fund", conn, if_exists="append", index=False)
    # dim_investor
    df_demog = pd.read_csv(processed_dir / "investor_demographics.csv")
    df_demog.to_sql("dim_investor", conn, if_exists="append", index=False)
    # fact_nav
    df_nav_fact = df_nav_clean[["scheme_code", "date_key", "nav"]].copy()
    df_nav_fact.to_sql("fact_nav", conn, if_exists="append", index=False)
    # fact_transactions
    df_tx_fact = df_tx[[
        "transaction_id",
        "investor_id",
        "scheme_code",
        "date_key",
        "transaction_type",
        "amount",
        "units",
        "kyc_status",
        "state",
    ]]
    df_tx_fact.to_sql("fact_transactions", conn, if_exists="append", index=False)
    # fact_holdings
    df_holdings = pd.read_csv(processed_dir / "portfolio_holdings.csv")
    df_holdings_fact = df_holdings[["scheme_code", "sector", "weight_pct"]].copy()
    df_holdings_fact.to_sql("fact_holdings", conn, if_exists="append", index=False)
    # fact_performance
    df_perf_fact = df_perf[["scheme_code", "return_1yr", "return_3yr", "return_5yr", "expense_ratio"]].copy()
    df_perf_fact.to_sql("fact_performance", conn, if_exists="append", index=False)
    # fact_market_stats
    df_market = pd.read_csv(processed_dir / "market_statistics.csv")
    df_market.to_sql("fact_market_stats", conn, if_exists="append", index=False)
    # fact_aum_growth
    df_aum_growth = pd.read_csv(processed_dir / "aum_growth.csv")
    df_aum_growth.to_sql("fact_aum_growth", conn, if_exists="append", index=False)

    # 8. Build dim_date dimension
    unique_dates_nav = set(df_nav_clean["date_key"].dropna().unique())
    unique_dates_tx = set(df_tx["date_key"].dropna().unique())
    all_dates = sorted(list(unique_dates_nav.union(unique_dates_tx)))
    dim_date_rows = []
    for dt_str in all_dates:
        dt = pd.to_datetime(dt_str, format="%Y-%m-%d")
        dim_date_rows.append({
            "date_key": dt_str,
            "date": dt_str,
            "day": dt.day,
            "month": dt.month,
            "year": dt.year,
            "quarter": (dt.month - 1) // 3 + 1,
            "day_of_week": dt.strftime("%A"),
            "is_weekend": 1 if dt.weekday() >= 5 else 0,
        })
    df_dim_date = pd.DataFrame(dim_date_rows)
    df_dim_date.to_sql("dim_date", conn, if_exists="append", index=False)

    # 9. Populate fact_aum with latest AUM per scheme
    latest_date_key = df_dim_date["date_key"].max()
    df_aum_fact = df_perf[["scheme_code", "aum"]].copy()
    df_aum_fact.rename(columns={"aum": "aum_amount"}, inplace=True)
    df_aum_fact["date_key"] = latest_date_key
    df_aum_fact = df_aum_fact[["scheme_code", "date_key", "aum_amount"]]
    df_aum_fact.to_sql("fact_aum", conn, if_exists="append", index=False)

    # 10. Verify row counts for each table
    logging.info("Verifying row counts...")
    expected_counts = {
        "dim_fund": len(df_fund),
        "dim_date": len(df_dim_date),
        "fact_nav": len(df_nav_fact),
        "fact_transactions": len(df_tx_fact),
        "fact_performance": len(df_perf_fact),
        "fact_aum": len(df_aum_fact),
        "dim_investor": len(df_demog),
        "fact_holdings": len(df_holdings_fact),
        "fact_market_stats": len(df_market),
        "fact_aum_growth": len(df_aum_growth),
    }
    cur = conn.cursor()
    for tbl, exp_cnt in expected_counts.items():
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        db_cnt = cur.fetchone()[0]
        if db_cnt == exp_cnt:
            logging.info(f"Table {tbl:18}: Expected = {exp_cnt:5}, Database = {db_cnt:5} -> PASSED")
        else:
            logging.error(f"Table {tbl:18}: Expected = {exp_cnt:5}, Database = {db_cnt:5} -> FAILED")
            conn.close()
            return False
    conn.close()
    logging.info("ETL Pipeline completed successfully. SQLite database matches local schema completely.")
    return True

if __name__ == "__main__":
    try:
        success = run_etl()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.exception("Unexpected error during ETL execution")
        sys.exit(2)
