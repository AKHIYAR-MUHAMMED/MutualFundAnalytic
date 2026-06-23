-- Schema for Mutual Fund Database(DB)

CREATE TABLE IF NOT EXISTS fund_master (
    scheme_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    risk_grade TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nav_history (
    scheme_code INTEGER,
    date TEXT NOT NULL,
    nav REAL NOT NULL,
    FOREIGN KEY (scheme_code) REFERENCES fund_master(scheme_code)
);
