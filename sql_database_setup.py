import os
import pandas as pd
from sqlalchemy import create_engine, text

def main():
    db_path = "data/processed/mutual_funds.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create engine for SQLite
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Load CSV files
    fund_master_path = "data/processed/fund_master.csv"
    nav_history_path = "data/processed/nav_history.csv"
    
    if not os.path.exists(fund_master_path) or not os.path.exists(nav_history_path):
        print("Error: fund_master.csv or nav_history.csv missing in data/processed/.")
        return
        
    df_master = pd.read_csv(fund_master_path)
    df_history = pd.read_csv(nav_history_path)
    
    # Load into SQL database
    print("Loading fund_master into database...")
    df_master.to_sql("fund_master", con=engine, if_exists="replace", index=False)
    print("Loading nav_history into database...")
    df_history.to_sql("nav_history", con=engine, if_exists="replace", index=False)
    print("Database loaded successfully.")
    
    # Verify by running a sample query
    with engine.connect() as conn:
        print("\nVerifying database with sample query (Historical summary per scheme):")
        result = conn.execute(text("""
            SELECT fm.scheme_name, COUNT(nh.nav) as nav_count, MIN(nh.nav) as min_nav, MAX(nh.nav) as max_nav
            FROM nav_history nh
            JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
            GROUP BY fm.scheme_code
        """))
        for row in result:
            print(f"Scheme: {row[0]}")
            print(f"  NAV Count: {row[1]}, Min: {row[2]}, Max: {row[3]}")

if __name__ == "__main__":
    main()
