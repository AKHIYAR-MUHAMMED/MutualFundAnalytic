-- Schema for Mutual Fund SQLite Star Schema

-- 1. Dimension: Fund details
CREATE TABLE IF NOT EXISTS dim_fund (
    scheme_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    risk_grade TEXT NOT NULL
);

-- 2. Dimension: Date hierarchy
CREATE TABLE IF NOT EXISTS dim_date (
    date_key TEXT PRIMARY KEY, -- 'YYYY-MM-DD'
    date TEXT NOT NULL,        -- 'YYYY-MM-DD'
    day INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day_of_week TEXT NOT NULL,
    is_weekend INTEGER NOT NULL -- 0 or 1
);

-- 3. Fact: Daily NAV history
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code INTEGER NOT NULL,
    date_key TEXT NOT NULL,
    nav REAL NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- 4. Fact: Investor transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    investor_id TEXT NOT NULL,
    scheme_code INTEGER NOT NULL,
    date_key TEXT NOT NULL,
    transaction_type TEXT NOT NULL, -- SIP, Lumpsum, Redemption
    amount REAL NOT NULL,
    units REAL NOT NULL,
    kyc_status TEXT NOT NULL,       -- Verified, Failed, Pending
    state TEXT NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- 5. Fact: Scheme performance metrics
CREATE TABLE IF NOT EXISTS fact_performance (
    scheme_code INTEGER PRIMARY KEY,
    return_1yr REAL,
    return_3yr REAL,
    return_5yr REAL,
    expense_ratio REAL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 6. Fact: Scheme AUM (Assets Under Management)
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code INTEGER NOT NULL,
    date_key TEXT NOT NULL,
    aum_amount REAL NOT NULL, -- In Crores
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);
