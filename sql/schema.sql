-- Schema for Mutual Fund SQLite Star Schema

-- 1. Dimension: Fund details
CREATE TABLE IF NOT EXISTS dim_fund (
    scheme_code INTEGER PRIMARY KEY CHECK (scheme_code > 0),
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
    day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31),
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year INTEGER NOT NULL CHECK (year > 0),
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    day_of_week TEXT NOT NULL,
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

-- 3. Fact: Daily NAV history
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code INTEGER NOT NULL,
    date_key TEXT NOT NULL,
    nav REAL NOT NULL CHECK (nav > 0),
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- 4. Fact: Investor transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    investor_id TEXT NOT NULL,
    scheme_code INTEGER NOT NULL,
    date_key TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount REAL NOT NULL CHECK (amount > 0),
    units REAL NOT NULL CHECK (units > 0),
    kyc_status TEXT NOT NULL CHECK (kyc_status IN ('Verified', 'Failed', 'Pending')),
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
    expense_ratio REAL CHECK (expense_ratio >= 0.1 AND expense_ratio <= 2.5),
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 6. Fact: Scheme AUM (Assets Under Management)
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code INTEGER NOT NULL,
    date_key TEXT NOT NULL,
    aum_amount REAL NOT NULL CHECK (aum_amount > 0), -- In Crores
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- 7. Indexes for optimization
CREATE INDEX IF NOT EXISTS idx_fact_nav_scheme_date ON fact_nav(scheme_code, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_tx_scheme_date ON fact_transactions(scheme_code, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_aum_scheme_date ON fact_aum(scheme_code, date_key);

-- 8. Dimension: Investor Demographics
CREATE TABLE IF NOT EXISTS dim_investor (
    investor_id TEXT PRIMARY KEY,
    age_group TEXT NOT NULL CHECK (age_group IN ('18-25', '26-35', '36-45', '46-55', '56+')),
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    state TEXT NOT NULL,
    city_tier TEXT NOT NULL CHECK (city_tier IN ('T30', 'B30')),
    sip_amount REAL NOT NULL CHECK (sip_amount >= 0)
);

-- 9. Fact: Portfolio holdings and weights
CREATE TABLE IF NOT EXISTS fact_holdings (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_code INTEGER NOT NULL,
    sector TEXT NOT NULL,
    weight_pct REAL NOT NULL CHECK (weight_pct >= 0 AND weight_pct <= 100),
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

-- 10. Fact: Monthly market-wide stats (SIP inflows & folios)
CREATE TABLE IF NOT EXISTS fact_market_stats (
    month TEXT PRIMARY KEY, -- 'YYYY-MM'
    total_sip_inflow REAL NOT NULL CHECK (total_sip_inflow >= 0),
    total_folios REAL NOT NULL CHECK (total_folios >= 0),
    net_inflow_equity REAL NOT NULL,
    net_inflow_debt REAL NOT NULL,
    net_inflow_hybrid REAL NOT NULL,
    net_inflow_other REAL NOT NULL
);

-- 11. Fact: Year-wise AUM growth by fund house
CREATE TABLE IF NOT EXISTS fact_aum_growth (
    aum_growth_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 2022 AND year <= 2025),
    aum_lakh_cr REAL NOT NULL CHECK (aum_lakh_cr >= 0)
);

-- 12. Indexes for new tables and optimization
CREATE INDEX IF NOT EXISTS idx_fact_holdings_scheme ON fact_holdings(scheme_code);
CREATE INDEX IF NOT EXISTS idx_fact_aum_growth_house_year ON fact_aum_growth(fund_house, year);
CREATE INDEX IF NOT EXISTS idx_fact_tx_type_date ON fact_transactions(transaction_type, date_key, amount);
CREATE INDEX IF NOT EXISTS idx_fact_tx_state_amount ON fact_transactions(state, amount);
CREATE INDEX IF NOT EXISTS idx_fact_tx_kyc ON fact_transactions(kyc_status);

