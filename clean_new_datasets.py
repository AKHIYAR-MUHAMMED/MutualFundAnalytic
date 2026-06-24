import os
import pandas as pd
import numpy as np

def parse_date(date_str):
    if not isinstance(date_str, str):
        return pd.NaT
    # Try common formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d/%m/%y", "%Y-%m-%d %H:%M:%S"):
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

def clean_type(val):
    if not isinstance(val, str):
        return np.nan
    val_clean = val.strip().lower().replace('_', '').replace(' ', '')
    if 'sip' in val_clean:
        return 'SIP'
    elif 'lump' in val_clean:
        return 'Lumpsum'
    elif 'redeem' in val_clean or 'redemp' in val_clean or 'redemption' in val_clean:
        return 'Redemption'
    return np.nan

def clean_kyc(val):
    if not isinstance(val, str):
        return 'Pending'
    val_clean = val.strip().lower()
    if val_clean in ['verified', 'yes', 'y']:
        return 'Verified'
    elif val_clean in ['failed', 'no', 'n']:
        return 'Failed'
    elif val_clean in ['pending']:
        return 'Pending'
    else:
        return 'Pending' # default for invalid or unknown

def clean_return_val(val):
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

def clean_expense_ratio(val):
    if val is None:
        return np.nan
    if not isinstance(val, str):
        if pd.isna(val):
            return np.nan
        return float(val)
    val_clean = val.strip().replace('%', '')
    try:
        return float(val_clean)
    except ValueError:
        return np.nan

def clean_transactions():
    raw_path = "Data/raw/investor_transactions.csv"
    processed_path = "Data/processed/investor_transactions.csv"
    
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} does not exist.")
        return
        
    df = pd.read_csv(raw_path)
    print("=" * 60)
    print("Cleaning investor_transactions.csv")
    print(f"Initial shape: {df.shape}")
    
    # 1. Fix date formats
    df['parsed_date'] = df['transaction_date'].apply(parse_date)
    unparsed_dates = df[df['parsed_date'].isna()]['transaction_date'].unique()
    if len(unparsed_dates) > 0:
        print(f"  - Warning: Could not parse dates: {unparsed_dates}")
    df['transaction_date'] = df['parsed_date'].dt.strftime('%Y-%m-%d')
    df = df.drop(columns=['parsed_date'])
    
    # 2. Standardise transaction types
    df['transaction_type'] = df['transaction_type'].apply(clean_type)
    missing_type = df['transaction_type'].isna().sum()
    if missing_type > 0:
        print(f"  - Flagged {missing_type} transactions with invalid transaction type.")
        
    # 3. Validate amount > 0
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    invalid_amount_mask = df['amount'].isna() | (df['amount'] <= 0)
    invalid_amount_count = invalid_amount_mask.sum()
    if invalid_amount_count > 0:
        print(f"  - Dropping {invalid_amount_count} rows with invalid amount (<= 0 or NaN).")
        # Log samples of dropped data
        print("    Sample dropped rows:")
        print(df[invalid_amount_mask][['transaction_id', 'amount']].head(3))
        df = df[~invalid_amount_mask]
        
    # 4. Check KYC status enum values
    # Standardise
    df['kyc_cleaned'] = df['kyc_status'].apply(clean_kyc)
    invalid_kyc_mask = ~df['kyc_status'].astype(str).str.strip().str.lower().isin(
        ['verified', 'yes', 'y', 'failed', 'no', 'n', 'pending']
    )
    invalid_kyc_count = invalid_kyc_mask.sum()
    if invalid_kyc_count > 0:
        print(f"  - Standardised {invalid_kyc_count} rows with invalid KYC status to default 'Pending'.")
    df['kyc_status'] = df['kyc_cleaned']
    df = df.drop(columns=['kyc_cleaned'])
    
    # Drop rows where critical primary columns became NaN
    df = df.dropna(subset=['transaction_id', 'transaction_date', 'transaction_type', 'scheme_code'])
    
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    print(f"Cleaned transactions shape: {df.shape}")
    print(f"Saved to {processed_path}")

def clean_performance():
    raw_path = "Data/raw/scheme_performance.csv"
    processed_path = "Data/processed/scheme_performance.csv"
    
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} does not exist.")
        return
        
    df = pd.read_csv(raw_path)
    print("=" * 60)
    print("Cleaning scheme_performance.csv")
    print(f"Initial shape: {df.shape}")
    
    # 1. Clean return values and validate they are numeric
    for col in ['return_1yr', 'return_3yr', 'return_5yr']:
        df[col] = df[col].apply(clean_return_val)
        
    # 2. Flag return anomalies (e.g. returns > 100% or < -50%)
    print("  - Checking for return anomalies...")
    for col in ['return_1yr', 'return_3yr', 'return_5yr']:
        anomalies = df[(df[col] > 100) | (df[col] < -50)]
        for idx, row in anomalies.iterrows():
            print(f"    * ANOMALY: Scheme {row['scheme_code']} has {col} = {row[col]}% (Out of normal range -50% to 100%)")
            
    # 3. Check expense_ratio range (0.1% - 2.5%)
    df['expense_ratio'] = df['expense_ratio'].apply(clean_expense_ratio)
    out_of_range_expense = df[(df['expense_ratio'] < 0.1) | (df['expense_ratio'] > 2.5)]
    for idx, row in out_of_range_expense.iterrows():
        print(f"    * EXPENSE RATIO OUT OF RANGE: Scheme {row['scheme_code']} has expense_ratio = {row['expense_ratio']}% (Normal: 0.1% to 2.5%)")
        
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    print(f"Cleaned performance shape: {df.shape}")
    print(f"Saved to {processed_path}")

if __name__ == "__main__":
    clean_transactions()
    clean_performance()
