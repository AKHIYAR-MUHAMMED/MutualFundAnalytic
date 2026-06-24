# Mutual Fund Data Ingestion & Quality Report

## 1. Raw Dataset Properties

| Dataset | Rows | Columns | Duplicates | Missing Values | Anomalies (Daily Return > 50%) |
| --- | --- | --- | --- | --- | --- |
| axis_bluechip_119092.csv | 3581 | 4 | 0 | None | 1 extreme NAV jumps |
| fund_master.csv | 8 | 6 | 0 | None | None |
| hdfc_top_100_125497.csv | 3107 | 4 | 0 | None | None |
| hdfc_top_100_actual_119062.csv | 3315 | 4 | 0 | None | None |
| icici_bluechip_120503.csv | 3323 | 4 | 0 | None | 2 extreme NAV jumps |
| kotak_bluechip_120841.csv | 3317 | 4 | 0 | None | None |
| nav_history.csv | 26507 | 3 | 0 | None | 3 extreme NAV jumps |
| nippon_large_cap_118632.csv | 3314 | 4 | 0 | None | None |
| sbi_bluechip_119551.csv | 3252 | 4 | 0 | None | None |
| sbi_bluechip_actual_119777.csv | 3298 | 4 | 0 | None | None |

## 2. Detailed Raw Data Anomalies Identified

### axis_bluechip_119092.csv:
- **30-08-2015:** NAV shifted from `30.2219` to `3023.47` (change of `9904.24%`). This indicates a **100x decimal shift anomaly**.
### icici_bluechip_120503.csv:
- **07-04-2013:** NAV shifted from `14.0479` to `0.0` (change of `-100.00%`). This indicates a **zero NAV entry error**.
- **08-04-2013:** NAV shifted from `0.0` to `14.0224` (change of `inf%`). This indicates a **100x decimal shift anomaly**.

## 3. Cleaned Datasets Verification (Data/processed/)

The raw anomalies were corrected and saved to the `Data/processed/` folder for database ingestion. Below is the quality check on the cleaned files:

| Cleaned Dataset | Rows | Columns | Remaining Anomalies | Actions Taken |
| --- | --- | --- | --- | --- |
| axis_bluechip_119092.csv | 4923 | 4 | 0 | Multiplied NAV entries before 30-08-2015 by 100 to fix 100x shift. |
| hdfc_top_100_125497.csv | 4601 | 4 | 0 | Checked / No action needed |
| hdfc_top_100_actual_119062.csv | 4922 | 4 | 0 | Checked / No action needed |
| icici_bluechip_120503.csv | 4921 | 4 | 0 | Interpolated zero-NAV on 07-04-2013 using neighboring entries. |
| kotak_bluechip_120841.csv | 4916 | 4 | 0 | Checked / No action needed |
| nippon_large_cap_118632.csv | 4921 | 4 | 0 | Checked / No action needed |
| sbi_bluechip_119551.csv | 4921 | 4 | 0 | Checked / No action needed |
| sbi_bluechip_actual_119777.csv | 4914 | 4 | 0 | Checked / No action needed |
| nav_history.csv | 39039 | 3 | 0 | Applied both 100x shift and zero-NAV corrections per scheme. |
| fund_master.csv | 8 | 6 | 0 | Checked / No action needed |

## 4. Fund Master Exploration

- **Total Fund Houses:** 7
- **Total Categories:** 4
- **Total Sub-categories:** 8
- **Total Risk Grades:** 2

### Scheme Categories:
- Equity Scheme
- Debt Scheme
- Hybrid Scheme
- Other Scheme

### Risk Grades:
- Very High
- Moderate

## 5. AMFI Code Validation Results

- **Unique scheme codes in `fund_master`:** 8
- **Unique scheme codes in `nav_history`:** 8
- **Status:** PASSED (All codes exist in history)
