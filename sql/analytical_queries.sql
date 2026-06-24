-- 1. Top 5 funds by AUM
SELECT df.scheme_code, df.scheme_name, fa.aum_amount AS aum_crores
FROM fact_aum fa
JOIN dim_fund df ON fa.scheme_code = df.scheme_code
ORDER BY fa.aum_amount DESC
LIMIT 5;

-- 2. Average NAV per month for each scheme
SELECT df.scheme_name, dd.year, dd.month, AVG(fn.nav) AS avg_nav
FROM fact_nav fn
JOIN dim_fund df ON fn.scheme_code = df.scheme_code
JOIN dim_date dd ON fn.date_key = dd.date_key
GROUP BY df.scheme_code, dd.year, dd.month
ORDER BY df.scheme_name, dd.year, dd.month;

-- 3. SIP Year-over-Year (YoY) growth
WITH sip_by_year AS (
    SELECT dd.year, SUM(ft.amount) AS total_sip_amount
    FROM fact_transactions ft
    JOIN dim_date dd ON ft.date_key = dd.date_key
    WHERE ft.transaction_type = 'SIP'
    GROUP BY dd.year
)
SELECT 
    curr.year, 
    curr.total_sip_amount,
    prev.total_sip_amount AS prev_year_sip_amount,
    CASE 
        WHEN prev.total_sip_amount IS NULL THEN NULL
        ELSE ROUND(((curr.total_sip_amount - prev.total_sip_amount) / prev.total_sip_amount) * 100, 2)
    END AS yoy_growth_percent
FROM sip_by_year curr
LEFT JOIN sip_by_year prev ON curr.year = prev.year + 1
ORDER BY curr.year;

-- 4. Transactions count and volume by investor state
SELECT state, COUNT(*) AS txn_count, SUM(amount) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense_ratio < 1%
SELECT df.scheme_code, df.scheme_name, fp.expense_ratio
FROM fact_performance fp
JOIN dim_fund df ON fp.scheme_code = df.scheme_code
WHERE fp.expense_ratio < 1.0
ORDER BY fp.expense_ratio ASC;

-- 6. KYC status breakdown (counts and percentages of transactions)
SELECT 
    kyc_status, 
    COUNT(*) AS txn_count,
    ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM fact_transactions), 2) AS percentage
FROM fact_transactions
GROUP BY kyc_status
ORDER BY txn_count DESC;

-- 7. Top 3 states with highest average redemption amounts
SELECT state, COUNT(*) AS redemption_count, AVG(amount) AS avg_redemption_amount
FROM fact_transactions
WHERE transaction_type = 'Redemption'
GROUP BY state
ORDER BY avg_redemption_amount DESC
LIMIT 3;

-- 8. Monthly transaction inflows (SIP/Lumpsum) vs outflows (Redemption)
SELECT 
    dd.year, 
    dd.month,
    SUM(CASE WHEN ft.transaction_type IN ('SIP', 'Lumpsum') THEN ft.amount ELSE 0 END) AS total_inflow,
    SUM(CASE WHEN ft.transaction_type = 'Redemption' THEN ft.amount ELSE 0 END) AS total_outflow,
    SUM(CASE WHEN ft.transaction_type IN ('SIP', 'Lumpsum') THEN ft.amount ELSE -ft.amount END) AS net_flow
FROM fact_transactions ft
JOIN dim_date dd ON ft.date_key = dd.date_key
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month;

-- 9. Return-to-Expense ratio per scheme (Return 3yr / Expense Ratio)
SELECT 
    df.scheme_name, 
    fp.return_3yr, 
    fp.expense_ratio, 
    ROUND(fp.return_3yr / fp.expense_ratio, 2) AS return_to_expense_ratio
FROM fact_performance fp
JOIN dim_fund df ON fp.scheme_code = df.scheme_code
WHERE fp.expense_ratio > 0
ORDER BY return_to_expense_ratio DESC;

-- 10. Transaction volume and count per fund house
SELECT 
    df.fund_house, 
    COUNT(ft.transaction_id) AS txn_count, 
    SUM(ft.amount) AS total_txn_amount
FROM fact_transactions ft
JOIN dim_fund df ON ft.scheme_code = df.scheme_code
GROUP BY df.fund_house
ORDER BY total_txn_amount DESC;
