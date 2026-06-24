import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_transactions(num_records=1000):
    random.seed(42)
    np.random.seed(42)
    
    scheme_codes = [125497, 119551, 120503, 118632, 119092, 120841, 119062, 119777]
    states = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "West Bengal", "Gujarat", "Telangana", "Kerala", "Haryana", "Rajasthan", "Andhra Pradesh"]
    
    # Inconsistent transaction types
    tx_types_pool = [
        "SIP", "Sip", "sip", 
        "Lumpsum", "lumpsum", "Lumpsum ", "LUMP_SUM",
        "Redemption", "redemption", "REDEMPTION", "redeem", "REDEEM", "Redemp"
    ]
    
    # Inconsistent KYC status
    kyc_pool = [
        "Verified", "verified", "VERIFIED", "yes", "Y",
        "Failed", "failed", "no", "N",
        "Pending", "pending", "PENDING",
        "InvalidStatus" # invalid one to flag
    ]
    
    data = []
    start_date = datetime(2022, 1, 1)
    
    for i in range(num_records):
        tx_id = f"TXN{10000 + i}"
        inv_id = f"INV{random.randint(5001, 5200)}"
        scheme = random.choice(scheme_codes)
        
        # Inconsistent Date Formats
        days_offset = random.randint(0, 1600)
        dt = start_date + timedelta(days=days_offset)
        date_format_choice = random.choice(["YYYY-MM-DD", "DD-MM-YYYY", "DD/MM/YYYY", "MM/DD/YYYY", "ISO"])
        if date_format_choice == "YYYY-MM-DD":
            dt_str = dt.strftime("%Y-%m-%d")
        elif date_format_choice == "DD-MM-YYYY":
            dt_str = dt.strftime("%d-%m-%Y")
        elif date_format_choice == "DD/MM/YYYY":
            dt_str = dt.strftime("%d/%m/%y") # short year
        elif date_format_choice == "MM/DD/YYYY":
            dt_str = dt.strftime("%m/%d/%Y")
        else:
            dt_str = dt.strftime("%Y/%m/%d")
            
        tx_type = random.choice(tx_types_pool)
        
        # Valid amount > 0, but introduce some invalid (<= 0 or NaN)
        amount_rand = random.random()
        if amount_rand < 0.03:
            amount = 0
        elif amount_rand < 0.05:
            amount = -random.randint(100, 5000)
        elif amount_rand < 0.07:
            amount = np.nan
        else:
            amount = round(random.uniform(500, 100000), 2)
            
        units = round(amount / random.uniform(10, 100), 4) if not pd.isna(amount) and amount > 0 else np.nan
        
        kyc = random.choice(kyc_pool)
        state = random.choice(states)
        
        data.append({
            "transaction_id": tx_id,
            "investor_id": inv_id,
            "scheme_code": scheme,
            "transaction_date": dt_str,
            "transaction_type": tx_type,
            "amount": amount,
            "units": units,
            "kyc_status": kyc,
            "state": state
        })
        
    df = pd.DataFrame(data)
    os.makedirs("Data/raw", exist_ok=True)
    df.to_csv("Data/raw/investor_transactions.csv", index=False)
    print(f"Generated {num_records} transaction records in Data/raw/investor_transactions.csv")


def generate_performance():
    # 8 schemes
    schemes = [
        {"scheme_code": 125497, "aum": 15200.5, "expense_ratio": "1.85%"},
        {"scheme_code": 119551, "aum": 8750.2, "expense_ratio": "0.75%"},
        {"scheme_code": 120503, "aum": 12100.8, "expense_ratio": "1.92%"},
        {"scheme_code": 118632, "aum": 24500.6, "expense_ratio": "1.65%"},
        {"scheme_code": 119092, "aum": 4300.1, "expense_ratio": "0.22%"},
        {"scheme_code": 120841, "aum": 9100.4, "expense_ratio": "2.10%"},
        {"scheme_code": 119062, "aum": 18450.3, "expense_ratio": "1.45%"},
        {"scheme_code": 119777, "aum": 1250.7, "expense_ratio": "1.15%"}
    ]
    
    # Introduce invalid expense ratios
    # scheme 119551 -> change expense ratio to below 0.1% or flag it: e.g. 0.05%
    # scheme 120841 -> change expense ratio to above 2.5%: e.g. 3.20%
    
    data = []
    random.seed(42)
    
    # Let's populate return strings with % and raw floats, and N/A
    for idx, s in enumerate(schemes):
        # We will write return_1yr, return_3yr, return_5yr
        # return_1yr: numeric return with %, float string, or anomaly
        # let's introduce returns, some with % sign, some as floats, some as N/A
        
        # 1yr return
        r1_val = round(random.uniform(-10, 30), 2)
        if idx == 2:
            r1 = "N/A"
        elif idx % 2 == 0:
            r1 = f"{r1_val}%"
        else:
            r1 = str(r1_val)
            
        # 3yr return (introduce an anomaly for idx=4: e.g., 185.0% return)
        r3_val = round(random.uniform(5, 25), 2)
        if idx == 4:
            r3 = "185.20%" # anomaly!
        elif idx % 2 == 1:
            r3 = f"{r3_val}%"
        else:
            r3 = str(r3_val)
            
        # 5yr return
        r5_val = round(random.uniform(8, 28), 2)
        if idx % 2 == 0:
            r5 = f"{r5_val}%"
        else:
            r5 = str(r5_val)
            
        exp_ratio = s["expense_ratio"]
        if s["scheme_code"] == 119551:
            exp_ratio = "0.05%" # below 0.1% range!
        elif s["scheme_code"] == 120841:
            exp_ratio = "3.20%" # above 2.5% range!
            
        data.append({
            "scheme_code": s["scheme_code"],
            "return_1yr": r1,
            "return_3yr": r3,
            "return_5yr": r5,
            "expense_ratio": exp_ratio,
            "aum": s["aum"]
        })
        
    df = pd.DataFrame(data)
    df.to_csv("Data/raw/scheme_performance.csv", index=False)
    print("Generated 8 performance records in Data/raw/scheme_performance.csv")

if __name__ == "__main__":
    generate_transactions(1000)
    generate_performance()
