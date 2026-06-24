import os
import glob
import pandas as pd
import numpy as np

def check_nav_anomalies(df):
    anomalies = []
    if 'nav' in df.columns and 'date' in df.columns:
        df_sorted = df.copy()
        df_sorted['parsed_date'] = pd.to_datetime(df_sorted['date'], format='%d-%m-%Y')
        
        # Convert nav to numeric
        df_sorted['nav'] = pd.to_numeric(df_sorted['nav'], errors='coerce')
        df_sorted = df_sorted.dropna(subset=['nav'])
        
        # Group by scheme_code if present (e.g. in nav_history.csv)
        if 'scheme_code' in df_sorted.columns:
            for code, group in df_sorted.groupby('scheme_code'):
                group_sorted = group.sort_values('parsed_date').reset_index(drop=True)
                group_sorted['pct_change'] = group_sorted['nav'].pct_change()
                large_changes = group_sorted[group_sorted['pct_change'].abs() > 0.50]
                
                for idx, row in large_changes.iterrows():
                    prev_row = group_sorted.iloc[idx - 1]
                    anomalies.append({
                        "scheme_code": int(code),
                        "date": row['date'],
                        "prev_nav": float(prev_row['nav']),
                        "current_nav": float(row['nav']),
                        "pct_change": float(row['pct_change'])
                    })
        else:
            df_sorted = df_sorted.sort_values('parsed_date').reset_index(drop=True)
            df_sorted['pct_change'] = df_sorted['nav'].pct_change()
            large_changes = df_sorted[df_sorted['pct_change'].abs() > 0.50]
            
            for idx, row in large_changes.iterrows():
                prev_row = df_sorted.iloc[idx - 1]
                anomalies.append({
                    "date": row['date'],
                    "prev_nav": float(prev_row['nav']),
                    "current_nav": float(row['nav']),
                    "pct_change": float(row['pct_change'])
                })
    return anomalies

def load_and_inspect_datasets():
    csv_files = [f for f in glob.glob("Data/raw/*.csv") if os.path.basename(f) not in ['investor_transactions.csv', 'scheme_performance.csv']]
    print(f"Found {len(csv_files)} CSV files in Data/raw/\n")
    
    inspection_results = {}
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        print("=" * 60)
        print(f"Dataset: {filename}")
        print("=" * 60)
        try:
            df = pd.read_csv(filepath)
            print(f"Shape: {df.shape}")
            print("\nDtypes:")
            print(df.dtypes)
            print("\nHead:")
            print(df.head())
            print("\nAnomalies check:")
            
            missing = df.isnull().sum()
            has_missing = missing.any()
            missing_info = {}
            if has_missing:
                print("  - Missing values found:")
                for col, val in missing.items():
                    if val > 0:
                        print(f"    * {col}: {val} missing values")
                        missing_info[col] = val
            else:
                print("  - No missing values.")
                
            duplicates = int(df.duplicated().sum())
            if duplicates > 0:
                print(f"  - Duplicate rows found: {duplicates}")
            else:
                print("  - No duplicate rows.")
                
            # Run NAV jumps check
            nav_anomalies = check_nav_anomalies(df)
            if nav_anomalies:
                print("  - Extreme NAV jumps detected (potential anomalies):")
                for anom in nav_anomalies:
                    print(f"    * {anom['date']}: NAV shifted from {anom['prev_nav']} to {anom['current_nav']} ({anom['pct_change'] * 100:.2f}%)")
            else:
                print("  - No extreme NAV jumps.")
                
            inspection_results[filename] = {
                "shape": df.shape,
                "dtypes": {k: str(v) for k, v in df.dtypes.items()},
                "missing": missing_info,
                "duplicates": duplicates,
                "anomalies": nav_anomalies
            }
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            inspection_results[filename] = {"error": str(e)}
        print("\n" + "-" * 60 + "\n")
        
    return inspection_results

def explore_fund_master():
    fund_master_path = "Data/raw/fund_master.csv"
    if not os.path.exists(fund_master_path):
        print("fund_master.csv not found. Skipping exploration.")
        return None
        
    print("=" * 60)
    print("Exploring Fund Master")
    print("=" * 60)
    df_master = pd.read_csv(fund_master_path)
    
    unique_houses = df_master['fund_house'].unique().tolist()
    unique_categories = df_master['category'].unique().tolist()
    unique_subcategories = df_master['sub_category'].unique().tolist()
    
    risk_col = 'risk_grade' if 'risk_grade' in df_master.columns else ('risk_level' if 'risk_level' in df_master.columns else None)
    unique_risk_grades = df_master[risk_col].unique().tolist() if risk_col else []
    
    print(f"Unique Fund Houses: {len(unique_houses)}")
    print(f"Unique Categories: {len(unique_categories)}")
    print(f"Unique Sub-Categories: {len(unique_subcategories)}")
    print(f"Unique Risk Grades: {len(unique_risk_grades)}")
    
    # Understand AMFI code structure
    code_col = 'scheme_code' if 'scheme_code' in df_master.columns else ('amfi_code' if 'amfi_code' in df_master.columns else None)
    if code_col:
        codes = df_master[code_col].astype(str)
        lengths = codes.str.len().value_counts()
        print("\nAMFI Code Length Distribution:")
        for length, count in lengths.items():
            print(f"  - {length} digits: {count} schemes")
            
    return {
        "fund_houses": unique_houses,
        "categories": unique_categories,
        "sub_categories": unique_subcategories,
        "risk_grades": unique_risk_grades,
        "code_column": code_col
    }

def validate_amfi_codes():
    fund_master_path = "Data/raw/fund_master.csv"
    nav_history_path = "Data/raw/nav_history.csv"
    
    if not os.path.exists(fund_master_path) or not os.path.exists(nav_history_path):
        print("fund_master.csv or nav_history.csv missing. Skipping code validation.")
        return None
        
    df_master = pd.read_csv(fund_master_path)
    df_history = pd.read_csv(nav_history_path)
    
    master_code_col = 'scheme_code' if 'scheme_code' in df_master.columns else ('amfi_code' if 'amfi_code' in df_master.columns else None)
    history_code_col = 'scheme_code' if 'scheme_code' in df_history.columns else ('amfi_code' if 'amfi_code' in df_history.columns else None)
    
    if not master_code_col or not history_code_col:
        print("Could not identify scheme code columns in datasets.")
        return None
        
    master_codes = set(df_master[master_code_col].unique())
    history_codes = set(df_history[history_code_col].unique())
    
    missing_in_history = master_codes - history_codes
    
    print("=" * 60)
    print("AMFI Code Validation")
    print("=" * 60)
    if missing_in_history:
        print(f"WARNING: {len(missing_in_history)} codes in fund_master are missing in nav_history!")
        print("Sample missing codes:", list(missing_in_history)[:10])
    else:
        print("SUCCESS: Every scheme code in fund_master exists in nav_history.")
        
    return {
        "master_unique_codes": len(master_codes),
        "history_unique_codes": len(history_codes),
        "missing_codes": list(missing_in_history)
    }

def generate_report(inspection, cleaned_inspection, master_info, validation):
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/data_quality_summary.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Mutual Fund Data Ingestion & Quality Report\n\n")
        
        f.write("## 1. Raw Dataset Properties\n\n")
        f.write("| Dataset | Rows | Columns | Duplicates | Missing Values | Anomalies (Daily Return > 50%) |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        
        for name, info in inspection.items():
            if "error" in info:
                f.write(f"| {name} | Error | Error | - | - | {info['error']} |\n")
                continue
                
            shape = info["shape"]
            dups = info["duplicates"]
            missing = info["missing"]
            anoms = info["anomalies"]
            
            missing_str = ", ".join([f"{col}: {val}" for col, val in missing.items()]) if missing else "None"
            anomalies_str = []
            if dups > 0:
                anomalies_str.append(f"{dups} duplicates")
            if missing:
                anomalies_str.append("missing values")
            if anoms:
                # Count distinct dates with anomalies
                distinct_dates = len(set(a['date'] for a in anoms))
                anomalies_str.append(f"{distinct_dates} extreme NAV jumps")
            
            f.write(f"| {name} | {shape[0]} | {shape[1]} | {dups} | {missing_str} | {', '.join(anomalies_str) if anomalies_str else 'None'} |\n")
            
        f.write("\n")
        
        # Detailed anomalies section
        f.write("## 2. Detailed Raw Data Anomalies Identified\n\n")
        has_anoms = False
        for name, info in inspection.items():
            # Skip combined history file since it has cross-scheme anomalies in raw form
            if name == 'nav_history.csv':
                continue
            if "anomalies" in info and info["anomalies"]:
                has_anoms = True
                f.write(f"### {name}:\n")
                for anom in info["anomalies"]:
                    f.write(f"- **{anom['date']}:** NAV shifted from `{anom['prev_nav']}` to `{anom['current_nav']}` (change of `{anom['pct_change'] * 100:.2f}%`). ")
                    if abs(anom['pct_change']) > 90:
                        f.write("This indicates a **100x decimal shift anomaly**.\n")
                    elif anom['current_nav'] == 0.0 or anom['prev_nav'] == 0.0:
                        f.write("This indicates a **zero NAV entry error**.\n")
                    else:
                        f.write("This indicates an extreme daily return jump.\n")
        if not has_anoms:
            f.write("No extreme anomalies detected in individual raw historical NAV files.\n\n")
        f.write("\n")
        
        # Data Cleaning Verification section
        f.write("## 3. Cleaned Datasets Verification (Data/processed/)\n\n")
        f.write("The raw anomalies were corrected and saved to the `Data/processed/` folder for database ingestion. Below is the quality check on the cleaned files:\n\n")
        f.write("| Cleaned Dataset | Rows | Columns | Remaining Anomalies | Actions Taken |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        
        for name, info in cleaned_inspection.items():
            shape = info["shape"]
            anoms = info["anomalies"]
            
            action = "Checked / No action needed"
            if name == 'axis_bluechip_119092.csv':
                action = "Multiplied NAV entries before 30-08-2015 by 100 to fix 100x shift."
            elif name == 'icici_bluechip_120503.csv':
                action = "Interpolated zero-NAV on 07-04-2013 using neighboring entries."
            elif name == 'nav_history.csv':
                action = "Applied both 100x shift and zero-NAV corrections per scheme."
                
            f.write(f"| {name} | {shape[0]} | {shape[1]} | {len(anoms)} | {action} |\n")
            
        f.write("\n")
        
        if master_info:
            f.write("## 4. Fund Master Exploration\n\n")
            f.write(f"- **Total Fund Houses:** {len(master_info['fund_houses'])}\n")
            f.write(f"- **Total Categories:** {len(master_info['categories'])}\n")
            f.write(f"- **Total Sub-categories:** {len(master_info['sub_categories'])}\n")
            f.write(f"- **Total Risk Grades:** {len(master_info['risk_grades'])}\n\n")
            
            f.write("### Scheme Categories:\n")
            for cat in master_info['categories']:
                f.write(f"- {cat}\n")
            f.write("\n")
            
            f.write("### Risk Grades:\n")
            for rg in master_info['risk_grades']:
                f.write(f"- {rg}\n")
            f.write("\n")
            
        if validation:
            f.write("## 5. AMFI Code Validation Results\n\n")
            f.write(f"- **Unique scheme codes in `fund_master`:** {validation['master_unique_codes']}\n")
            f.write(f"- **Unique scheme codes in `nav_history`:** {validation['history_unique_codes']}\n")
            
            missing = validation["missing_codes"]
            if missing:
                f.write(f"- **WARNING:** {len(missing)} codes in `fund_master` do not have any NAV history in `nav_history.csv`.\n")
                f.write("- **Status:** FAILED (Referential Integrity check failed)\n\n")
                f.write("### Sample Missing Codes:\n")
                for c in missing[:15]:
                    f.write(f"- `{c}`\n")
            else:
                f.write("- **Status:** PASSED (All codes exist in history)\n")
                
    print(f"Data quality report saved to {report_path}")

def clean_and_save_datasets():
    print("=" * 60)
    print("Cleaning Datasets")
    print("=" * 60)
    
    os.makedirs("Data/processed", exist_ok=True)
    csv_files = glob.glob("Data/raw/*.csv")
    cleaned_inspection = {}
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        if filename in ['fund_master.csv', 'nav_history.csv', 'investor_transactions.csv', 'scheme_performance.csv']:
            continue
            
        df = pd.read_csv(filepath)
        df_clean = df.copy()
        
        # 1. Parse dates to datetime
        df_clean['parsed_date'] = pd.to_datetime(df_clean['date'], format='%d-%m-%Y', errors='coerce')
        df_clean = df_clean.dropna(subset=['parsed_date'])
        
        # 2. Validate NAV > 0 (replace <= 0 with NaN)
        df_clean['nav'] = pd.to_numeric(df_clean['nav'], errors='coerce')
        df_clean.loc[df_clean['nav'] <= 0.0, 'nav'] = np.nan
        
        # 3. Remove duplicates
        df_clean = df_clean.drop_duplicates(subset=['parsed_date'])
        
        # Correct 100x shift for axis_bluechip_119092.csv (HDFC Money Market Fund)
        if filename == 'axis_bluechip_119092.csv':
            cutoff_date = pd.to_datetime('30-08-2015', format='%d-%m-%Y')
            mask = df_clean['parsed_date'] < cutoff_date
            df_clean.loc[mask, 'nav'] = df_clean.loc[mask, 'nav'] * 100
            print(f"  - Corrected 100x shift in {filename} for {mask.sum()} rows prior to 30-08-2015.")
            
        # Clean zero-NAV for icici_bluechip_120503.csv (Axis ELSS Tax Saver)
        elif filename == 'icici_bluechip_120503.csv':
            mask_zero = df_clean['nav'].isna()
            if mask_zero.any():
                df_clean = df_clean.sort_values('parsed_date')
                df_clean['nav'] = df_clean['nav'].interpolate(method='linear')
                print(f"  - Cleaned zero NAV anomaly in {filename} on 07-04-2013 by linear interpolation.")
                
        # 4. Forward-fill missing NAV for holidays/weekends
        min_date = df_clean['parsed_date'].min()
        max_date = df_clean['parsed_date'].max()
        full_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        df_clean = df_clean.set_index('parsed_date')
        df_clean_reindexed = df_clean.reindex(full_range)
        df_clean_reindexed.index.name = 'parsed_date'
        df_clean_reindexed = df_clean_reindexed.reset_index()
        
        # Fill non-NAV columns
        scheme_code = int(df['scheme_code'].iloc[0])
        scheme_name = df['scheme_name'].iloc[0]
        df_clean_reindexed['scheme_code'] = scheme_code
        df_clean_reindexed['scheme_name'] = scheme_name
        
        # Forward fill NAV (and backward fill if any initial NaNs)
        df_clean_reindexed['nav'] = df_clean_reindexed['nav'].ffill().bfill()
        
        # Reformat date column to string '%d-%m-%Y'
        df_clean_reindexed['date'] = df_clean_reindexed['parsed_date'].dt.strftime('%d-%m-%Y')
        df_clean_reindexed = df_clean_reindexed[['scheme_code', 'scheme_name', 'date', 'nav', 'parsed_date']]
        
        # Sort chronologically (ascending date)
        df_clean_reindexed = df_clean_reindexed.sort_values('parsed_date').reset_index(drop=True)
        df_clean_reindexed = df_clean_reindexed.drop(columns=['parsed_date'])
        
        # Save cleaned file to Data/processed
        cleaned_path = f"Data/processed/{filename}"
        df_clean_reindexed.to_csv(cleaned_path, index=False)
        
        # Verify if any anomalies remain
        anoms = check_nav_anomalies(df_clean_reindexed)
        cleaned_inspection[filename] = {
            "shape": df_clean_reindexed.shape,
            "anomalies": anoms
        }
        
    # Clean nav_history.csv
    nav_history_path = "Data/raw/nav_history.csv"
    if os.path.exists(nav_history_path):
        df_hist = pd.read_csv(nav_history_path)
        df_hist_clean = df_hist.copy()
        
        # 1. Parse dates to datetime
        df_hist_clean['parsed_date'] = pd.to_datetime(df_hist_clean['date'], format='%d-%m-%Y', errors='coerce')
        df_hist_clean = df_hist_clean.dropna(subset=['parsed_date'])
        
        # 2. Validate NAV > 0 (replace <= 0 with NaN)
        df_hist_clean['nav'] = pd.to_numeric(df_hist_clean['nav'], errors='coerce')
        df_hist_clean.loc[df_hist_clean['nav'] <= 0.0, 'nav'] = np.nan
        
        # 3. Remove duplicates
        df_hist_clean = df_hist_clean.drop_duplicates(subset=['scheme_code', 'parsed_date'])
        
        # Correct 100x shift for 119092
        cutoff_date = pd.to_datetime('30-08-2015', format='%d-%m-%Y')
        mask_119092 = (df_hist_clean['scheme_code'] == 119092) & (df_hist_clean['parsed_date'] < cutoff_date)
        df_hist_clean.loc[mask_119092, 'nav'] = df_hist_clean.loc[mask_119092, 'nav'] * 100
        
        # Correct zero-NAV for 120503
        mask_120503_zero = (df_hist_clean['scheme_code'] == 120503) & (df_hist_clean['nav'].isna())
        if mask_120503_zero.any():
            # Interpolate per scheme
            history_dfs = []
            for code, group in df_hist_clean.groupby('scheme_code'):
                group_sorted = group.copy().sort_values('parsed_date')
                if code == 120503:
                    group_sorted['nav'] = group_sorted['nav'].interpolate(method='linear')
                history_dfs.append(group_sorted)
            df_hist_clean = pd.concat(history_dfs, ignore_index=True)
            
        # 4. Forward-fill missing NAV for holidays/weekends
        history_dfs = []
        for code, group in df_hist_clean.groupby('scheme_code'):
            group_sorted = group.copy().sort_values('parsed_date')
            min_date = group_sorted['parsed_date'].min()
            max_date = group_sorted['parsed_date'].max()
            full_range = pd.date_range(start=min_date, end=max_date, freq='D')
            
            group_sorted = group_sorted.set_index('parsed_date')
            group_reindexed = group_sorted.reindex(full_range)
            group_reindexed.index.name = 'parsed_date'
            group_reindexed = group_reindexed.reset_index()
            
            group_reindexed['scheme_code'] = code
            group_reindexed['nav'] = group_reindexed['nav'].ffill().bfill()
            group_reindexed['date'] = group_reindexed['parsed_date'].dt.strftime('%d-%m-%Y')
            
            group_reindexed = group_reindexed[['scheme_code', 'date', 'nav', 'parsed_date']]
            history_dfs.append(group_reindexed)
            
        df_hist_clean = pd.concat(history_dfs, ignore_index=True)
        
        # 5. Sort by amfi_code (scheme_code) + date (chronological)
        df_hist_clean = df_hist_clean.sort_values(['scheme_code', 'parsed_date']).reset_index(drop=True)
        df_hist_clean = df_hist_clean.drop(columns=['parsed_date'])
        
        cleaned_hist_path = "Data/processed/nav_history.csv"
        df_hist_clean.to_csv(cleaned_hist_path, index=False)
        print("  - Generated Data/processed/nav_history.csv with clean, forward-filled daily data, sorted by scheme_code and date.")
        
        anoms = check_nav_anomalies(df_hist_clean)
        cleaned_inspection['nav_history.csv'] = {
            "shape": df_hist_clean.shape,
            "anomalies": anoms
        }
        
    # Copy fund_master to processed
    fund_master_raw_path = "Data/raw/fund_master.csv"
    if os.path.exists(fund_master_raw_path):
        df_master = pd.read_csv(fund_master_raw_path)
        df_master.to_csv("Data/processed/fund_master.csv", index=False)
        print("  - Copied fund_master.csv to Data/processed/fund_master.csv.")
        cleaned_inspection['fund_master.csv'] = {
            "shape": df_master.shape,
            "anomalies": []
        }
        
    return cleaned_inspection


def main():
    inspection = load_and_inspect_datasets()
    master_info = explore_fund_master()
    validation = validate_amfi_codes()
    cleaned_inspection = clean_and_save_datasets()
    generate_report(inspection, cleaned_inspection, master_info, validation)

if __name__ == "__main__":
    main()

