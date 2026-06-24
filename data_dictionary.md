# Mutual Fund Analytics Database Data Dictionary

This data dictionary documents the structure, column definitions, data types, business definitions, and source data references for the star schema SQLite database loaded under `Data/processed/mutual_funds.db`.

---

## 1. Dimension Tables

### 1.1 `dim_fund`
Stores metadata and details about the mutual fund schemes.

| Column Name | Data Type | Primary/Foreign Key | Business Definition | Source File / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | Primary Key | AMFI Mutual Fund code identifier (unique). | `Data/processed/fund_master.csv` |
| `scheme_name` | TEXT | - | Full marketing and legal name of the mutual fund scheme. | `Data/processed/fund_master.csv` |
| `fund_house` | TEXT | - | Asset Management Company (AMC) managing the fund. | `Data/processed/fund_master.csv` |
| `category` | TEXT | - | High-level asset class category (e.g. Equity, Debt, Hybrid, Other). | `Data/processed/fund_master.csv` |
| `sub_category` | TEXT | - | Specific classification (e.g. Small Cap, Money Market, FoF). | `Data/processed/fund_master.csv` |
| `risk_grade` | TEXT | - | Risk rating evaluated for the fund (e.g. Very High, Moderate). | `Data/processed/fund_master.csv` |

---

### 1.2 `dim_date`
Represents the calendar dimension, supporting date-based hierarchies.

| Column Name | Data Type | Primary/Foreign Key | Business Definition | Source File / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | TEXT | Primary Key | Date formatted as 'YYYY-MM-DD' representing the day. | Programmatically generated |
| `date` | TEXT | - | Same as date_key, representing ISO formatted date string. | Programmatically generated |
| `day` | INTEGER | - | Calendar day of month (1-31). | Programmatically generated |
| `month` | INTEGER | - | Calendar month number (1-12). | Programmatically generated |
| `year` | INTEGER | - | Calendar year (e.g. 2026). | Programmatically generated |
| `quarter` | INTEGER | - | Calendar quarter of the year (1-4). | Programmatically generated |
| `day_of_week` | TEXT | - | Full name of the weekday (e.g., Monday, Tuesday). | Programmatically generated |
| `is_weekend` | INTEGER | - | Boolean flag (1 = Saturday or Sunday, 0 = Weekday). | Programmatically generated |

---

## 2. Fact Tables

### 2.1 `fact_nav`
Stores daily historical Net Asset Value (NAV) details for each fund scheme.

| Column Name | Data Type | Primary/Foreign Key | Business Definition | Source File / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `nav_id` | INTEGER | Primary Key (AI) | Auto-incremented unique record identifier. | Internal DB |
| `scheme_code` | INTEGER | Foreign Key | Fund identifier. References `dim_fund(scheme_code)`. | `Data/processed/nav_history.csv` |
| `date_key` | TEXT | Foreign Key | Date identifier. References `dim_date(date_key)`. | `Data/processed/nav_history.csv` |
| `nav` | REAL | - | Net Asset Value (NAV) per unit of the scheme on the date. | `Data/processed/nav_history.csv` |

---

### 2.2 `fact_transactions`
Stores granular investor buy/sell activity.

| Column Name | Data Type | Primary/Foreign Key | Business Definition | Source File / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | TEXT | Primary Key | Unique transaction identifier (e.g., TXN10001). | `Data/processed/investor_transactions.csv` |
| `investor_id` | TEXT | - | Unique identifier representing the investor. | `Data/processed/investor_transactions.csv` |
| `scheme_code` | INTEGER | Foreign Key | Reference to the fund invested in. References `dim_fund(scheme_code)`. | `Data/processed/investor_transactions.csv` |
| `date_key` | TEXT | Foreign Key | Date of transaction. References `dim_date(date_key)`. | `Data/processed/investor_transactions.csv` |
| `transaction_type`| TEXT | - | Type of transaction (SIP, Lumpsum, or Redemption). | `Data/processed/investor_transactions.csv` |
| `amount` | REAL | - | Value of the transaction in Indian Rupees (INR). | `Data/processed/investor_transactions.csv` |
| `units` | REAL | - | Fund units purchased or redeemed during the transaction. | `Data/processed/investor_transactions.csv` |
| `kyc_status` | TEXT | - | KYC compliance status (Verified, Failed, or Pending). | `Data/processed/investor_transactions.csv` |
| `state` | TEXT | - | Investor's state of residence in India. | `Data/processed/investor_transactions.csv` |

---

### 2.3 `fact_performance`
Stores historical return rates and expense metrics for each scheme.

| Column Name | Data Type | Primary/Foreign Key | Business Definition | Source File / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `scheme_code` | INTEGER | Primary / Foreign | References `dim_fund(scheme_code)`. | `Data/processed/scheme_performance.csv` |
| `return_1yr` | REAL | - | 1-year historical annualized return percentage (e.g. 12.5). | `Data/processed/scheme_performance.csv` |
| `return_3yr` | REAL | - | 3-year historical annualized return percentage. | `Data/processed/scheme_performance.csv` |
| `return_5yr` | REAL | - | 5-year historical annualized return percentage. | `Data/processed/scheme_performance.csv` |
| `expense_ratio` | REAL | - | Managed expense ratio (annual fee percentage). | `Data/processed/scheme_performance.csv` |

---

### 2.4 `fact_aum`
Stores Assets Under Management (AUM) history or snapshots.

| Column Name | Data Type | Primary/Foreign Key | Business Definition | Source File / Reference |
| :--- | :--- | :--- | :--- | :--- |
| `aum_id` | INTEGER | Primary Key (AI) | Auto-incremented unique record identifier. | Internal DB |
| `scheme_code` | INTEGER | Foreign Key | Fund scheme identifier. References `dim_fund(scheme_code)`. | `Data/processed/scheme_performance.csv` |
| `date_key` | TEXT | Foreign Key | Date of AUM value snapshot. References `dim_date(date_key)`. | Generated (max transaction date) |
| `aum_amount` | REAL | - | Total Assets Under Management of the scheme in Crores INR. | `Data/processed/scheme_performance.csv` |
