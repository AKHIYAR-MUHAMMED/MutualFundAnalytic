import os
import pandas as pd
from sqlalchemy import create_engine, text

def main():
    db_path = "Data/processed/mutual_funds.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create engine for SQLite
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Paths for cleaned CSV files
    fund_master_path = "Data/processed/fund_master.csv"
    nav_history_path = "Data/processed/nav_history.csv"
    transactions_path = "Data/processed/investor_transactions.csv"
    performance_path = "Data/processed/scheme_performance.csv"
    
    # Check if necessary files exist
    for p in [fund_master_path, nav_history_path, transactions_path, performance_path]:
        if not os.path.exists(p):
            print(f"Error: Required file {p} is missing in Data/processed/.")
            return

    # Execute schema.sql to set up tables with primary/foreign keys
    schema_path = "sql/schema.sql"
    if os.path.exists(schema_path):
        print("Executing schema.sql to set up tables and constraints...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with engine.connect() as conn:
            # Drop old tables and star schema tables in order to ensure clean load
            conn.execute(text("DROP TABLE IF EXISTS fact_aum;"))
            conn.execute(text("DROP TABLE IF EXISTS fact_performance;"))
            conn.execute(text("DROP TABLE IF EXISTS fact_transactions;"))
            conn.execute(text("DROP TABLE IF EXISTS fact_nav;"))
            conn.execute(text("DROP TABLE IF EXISTS dim_date;"))
            conn.execute(text("DROP TABLE IF EXISTS dim_fund;"))
            
            # Old tables from Day 1/3 if any
            conn.execute(text("DROP TABLE IF EXISTS nav_history;"))
            conn.execute(text("DROP TABLE IF EXISTS fund_master;"))
            
            # Execute schema statements
            for statement in schema_sql.split(";"):
                if statement.strip():
                    conn.execute(text(statement + ";"))
            conn.commit()
            print("Database schema created successfully.")
            
    # Load raw dataframes
    df_fund = pd.read_csv(fund_master_path)
    df_nav = pd.read_csv(nav_history_path)
    df_tx = pd.read_csv(transactions_path)
    df_perf = pd.read_csv(performance_path)

    # 1. Standardise date formats in nav history to YYYY-MM-DD
    # Currently nav_history dates are DD-MM-YYYY
    df_nav['parsed_date'] = pd.to_datetime(df_nav['date'], format='%d-%m-%Y', errors='coerce')
    df_nav['date_key'] = df_nav['parsed_date'].dt.strftime('%Y-%m-%d')
    df_nav = df_nav.drop(columns=['date', 'parsed_date'])

    # Standardise date formats in transactions to YYYY-MM-DD (already YYYY-MM-DD but ensure)
    df_tx['parsed_date'] = pd.to_datetime(df_tx['transaction_date'], format='%Y-%m-%d', errors='coerce')
    df_tx['date_key'] = df_tx['parsed_date'].dt.strftime('%Y-%m-%d')
    df_tx = df_tx.drop(columns=['transaction_date', 'parsed_date'])

    # 2. Build dim_date programmatically
    # Combine all unique dates from NAV history and transactions
    unique_dates_nav = set(df_nav['date_key'].dropna().unique())
    unique_dates_tx = set(df_tx['date_key'].dropna().unique())
    all_unique_dates = sorted(list(unique_dates_nav.union(unique_dates_tx)))
    
    dim_date_records = []
    for dt_str in all_unique_dates:
        dt = pd.to_datetime(dt_str, format='%Y-%m-%d')
        dim_date_records.append({
            "date_key": dt_str,
            "date": dt_str,
            "day": dt.day,
            "month": dt.month,
            "year": dt.year,
            "quarter": (dt.month - 1) // 3 + 1,
            "day_of_week": dt.strftime('%A'),
            "is_weekend": 1 if dt.weekday() >= 5 else 0
        })
    df_dim_date = pd.DataFrame(dim_date_records)

    # 3. Load into SQLite database
    print("\nLoading data into Star Schema...")
    
    # Dimension 1: dim_fund (from fund_master.csv)
    print("Loading dim_fund...")
    df_fund.to_sql("dim_fund", con=engine, if_exists="append", index=False)
    
    # Dimension 2: dim_date
    print("Loading dim_date...")
    df_dim_date.to_sql("dim_date", con=engine, if_exists="append", index=False)
    
    # Fact 1: fact_nav
    print("Loading fact_nav...")
    df_nav_fact = df_nav[['scheme_code', 'date_key', 'nav']]
    df_nav_fact.to_sql("fact_nav", con=engine, if_exists="append", index=False)
    
    # Fact 2: fact_transactions
    print("Loading fact_transactions...")
    df_tx_fact = df_tx[[
        'transaction_id', 'investor_id', 'scheme_code', 'date_key',
        'transaction_type', 'amount', 'units', 'kyc_status', 'state'
    ]]
    df_tx_fact.to_sql("fact_transactions", con=engine, if_exists="append", index=False)
    
    # Fact 3: fact_performance
    print("Loading fact_performance...")
    df_perf_fact = df_perf[['scheme_code', 'return_1yr', 'return_3yr', 'return_5yr', 'expense_ratio']]
    df_perf_fact.to_sql("fact_performance", con=engine, if_exists="append", index=False)
    
    # Fact 4: fact_aum
    print("Loading fact_aum...")
    # Load AUM as of the latest transaction date key
    latest_date_key = df_dim_date['date_key'].max()
    df_aum_fact = df_perf[['scheme_code', 'aum']].copy()
    df_aum_fact.rename(columns={"aum": "aum_amount"}, inplace=True)
    df_aum_fact['date_key'] = latest_date_key
    df_aum_fact = df_aum_fact[['scheme_code', 'date_key', 'aum_amount']]
    df_aum_fact.to_sql("fact_aum", con=engine, if_exists="append", index=False)

    print("\nDatabase loaded successfully.")
    
    # 4. Verify row counts match source CSVs
    print("\n" + "="*40)
    print("Row Count Verification:")
    print("="*40)
    
    expected_counts = {
        "dim_fund": len(df_fund),
        "dim_date": len(df_dim_date),
        "fact_nav": len(df_nav_fact),
        "fact_transactions": len(df_tx_fact),
        "fact_performance": len(df_perf_fact),
        "fact_aum": len(df_aum_fact)
    }
    
    with engine.connect() as conn:
        for table, expected in expected_counts.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
            db_count = result.fetchone()[0]
            status = "PASSED" if db_count == expected else "FAILED"
            print(f"Table {table:18}: Expected = {expected:5}, Database = {db_count:5} -> {status}")
            assert db_count == expected, f"Row count mismatch in table {table}!"

    print("\nAll database row counts verified successfully.")

if __name__ == "__main__":
    main()
