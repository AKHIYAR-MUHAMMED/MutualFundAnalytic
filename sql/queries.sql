-- 1. Get unique fund houses, categories, sub-categories, and risk grades
SELECT DISTINCT fund_house, category, sub_category, risk_grade FROM fund_master;

-- 2. Verify all scheme codes in fund_master have historical NAV data
SELECT fm.scheme_code, fm.scheme_name, COUNT(nh.nav) as nav_records
FROM fund_master fm
LEFT JOIN nav_history nh ON fm.scheme_code = nh.scheme_code
GROUP BY fm.scheme_code, fm.scheme_name;

-- 3. Calculate min, max, and average NAV for each scheme
SELECT fm.scheme_name, MIN(nh.nav) as min_nav, MAX(nh.nav) as max_nav, AVG(nh.nav) as avg_nav
FROM nav_history nh
JOIN fund_master fm ON nh.scheme_code = fm.scheme_code
GROUP BY fm.scheme_code;
