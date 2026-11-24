WITH
v1_counts AS (
    SELECT
        'V1' AS check_id,
        'Row counts per layer' AS check_name,
        'Info' AS category,
        CAST((SELECT COUNT(*) FROM edw.fact_revenue_event) AS VARCHAR) || ' fact rows' AS metric_value,
        'reported' AS expected_rule,
        'INFO' AS status,
        'stg_steam=' || (SELECT COUNT(*) FROM stg.raw_steam)
        || ', stg_itch=' || (SELECT COUNT(*) FROM stg.raw_itch)
        || ', stg_vgen=' || (SELECT COUNT(*) FROM stg.raw_vgen)
        || ', stg_fiverr=' || (SELECT COUNT(*) FROM stg.raw_fiverr)
        || ', stg_paypal=' || (SELECT COUNT(*) FROM stg.raw_paypal)
        || ', dim_date=' || (SELECT COUNT(*) FROM edw.dim_date)
        || ', dim_project=' || (SELECT COUNT(*) FROM edw.dim_project)
        || ', dim_platform=' || (SELECT COUNT(*) FROM edw.dim_platform)
        || ', dim_currency=' || (SELECT COUNT(*) FROM edw.dim_currency)
        || ', dim_stream=' || (SELECT COUNT(*) FROM edw.dim_revenue_stream)
        || ', rejects=' || (SELECT COUNT(*) FROM stg.etl_rejects) AS details
),
v2_orphan_fks AS (
    SELECT COUNT(*) AS bad_cnt
    FROM edw.fact_revenue_event f
    LEFT JOIN edw.dim_date d ON f.date_key = d.date_key
    LEFT JOIN edw.dim_project pr ON f.project_key = pr.project_key
    LEFT JOIN edw.dim_platform pl ON f.platform_key = pl.platform_key
    LEFT JOIN edw.dim_currency cu ON f.currency_key = cu.currency_key
    LEFT JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
    WHERE d.date_key IS NULL
       OR pr.project_key IS NULL
       OR pl.platform_key IS NULL
       OR cu.currency_key IS NULL
       OR rs.revenue_stream_key IS NULL
),
v3_signs AS (
    SELECT COUNT(*) AS bad_cnt
    FROM edw.fact_revenue_event
    WHERE (event_type IN ('SALE', 'TIP', 'FEE_REVERSAL') AND (amount_orig <= 0 OR amount_idr <= 0))
       OR (event_type IN ('REFUND', 'PLATFORM_FEE', 'PROCESSING_FEE') AND (amount_orig >= 0 OR amount_idr >= 0))
),
v4_dup_tx AS (
    SELECT COUNT(*) AS bad_cnt
    FROM (
        SELECT transaction_code
        FROM edw.fact_revenue_event
        GROUP BY transaction_code
        HAVING COUNT(*) > 1
    ) t
),
v5_refund_cap AS (
    SELECT COUNT(*) AS bad_cnt
    FROM (
        SELECT
            r.parent_transaction_code,
            ABS(SUM(r.amount_orig)) AS total_refund_orig,
            MAX(s.amount_orig) AS root_sale_orig
        FROM edw.fact_revenue_event r
        INNER JOIN edw.fact_revenue_event s
            ON r.parent_transaction_code = s.transaction_code
           AND s.event_type = 'SALE'
        WHERE r.event_type = 'REFUND'
        GROUP BY r.parent_transaction_code
        HAVING ABS(SUM(r.amount_orig)) > MAX(s.amount_orig) + 0.01
    ) t
),
v6_parent_ref AS (
    SELECT COUNT(*) AS bad_cnt
    FROM edw.fact_revenue_event c
    LEFT JOIN edw.fact_revenue_event p
        ON c.parent_transaction_code = p.transaction_code
       AND p.event_type = 'SALE'
    WHERE (c.event_type = 'SALE' AND c.parent_transaction_code IS NOT NULL)
       OR (c.event_type <> 'SALE' AND (c.parent_transaction_code IS NULL OR p.transaction_code IS NULL))
),
v7_multi_tip AS (
    SELECT COUNT(*) AS multi_tip_parents
    FROM (
        SELECT parent_transaction_code
        FROM edw.fact_revenue_event
        WHERE event_type = 'TIP'
        GROUP BY parent_transaction_code
        HAVING COUNT(*) >= 2
    ) t
),
v8_stream_platform AS (
    SELECT COUNT(*) AS bad_cnt
    FROM edw.fact_revenue_event f
    INNER JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
    INNER JOIN edw.dim_platform pl ON f.platform_key = pl.platform_key
    WHERE NOT (
        (rs.revenue_stream_code = 'GAME_SALES' AND pl.platform_code IN ('STEAM', 'ITCH'))
        OR (rs.revenue_stream_code = 'ASSET_SALES' AND pl.platform_code IN ('ITCH', 'VGEN'))
        OR (rs.revenue_stream_code = 'COMMISSION' AND pl.platform_code IN ('VGEN', 'FIVERR', 'PAYPAL'))
    )
),
v9_stream_project AS (
    SELECT COUNT(*) AS bad_cnt
    FROM edw.fact_revenue_event f
    INNER JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
    INNER JOIN edw.dim_project pr ON f.project_key = pr.project_key
    WHERE NOT (
        (rs.revenue_stream_code = 'GAME_SALES' AND pr.project_type = 'Game')
        OR (rs.revenue_stream_code = 'ASSET_SALES' AND pr.project_type = 'Asset Pack')
        OR (rs.revenue_stream_code = 'COMMISSION' AND pr.project_type = 'Commission Service')
    )
),
v10_fx_math AS (
    SELECT COUNT(*) AS bad_cnt
    FROM edw.fact_revenue_event
    WHERE ABS(amount_idr - ROUND(amount_orig * exchange_rate_to_idr, 2)) > 0.01
),
v11_weekend_fx AS (
    SELECT
        COUNT(*) FILTER (WHERE d.is_weekend AND cu.currency_code <> 'IDR') AS weekend_fx_cnt,
        COUNT(*) FILTER (
            WHERE d.is_weekend
              AND cu.currency_code <> 'IDR'
              AND (f.exchange_rate_to_idr IS NULL OR f.exchange_rate_to_idr <= 0)
        ) AS bad_weekend_cnt
    FROM edw.fact_revenue_event f
    INNER JOIN edw.dim_date d ON f.date_key = d.date_key
    INNER JOIN edw.dim_currency cu ON f.currency_key = cu.currency_key
),
v12_proc_fee_rev AS (
    SELECT COUNT(*) AS bad_cnt
    FROM (
        SELECT f.revenue_event_sk
        FROM edw.fact_revenue_event f
        INNER JOIN edw.dim_platform pl ON f.platform_key = pl.platform_key
        LEFT JOIN (
            SELECT parent_transaction_code, ABS(SUM(amount_orig)) AS pfee_orig
            FROM edw.fact_revenue_event
            WHERE event_type = 'PLATFORM_FEE'
            GROUP BY parent_transaction_code
        ) pf ON f.parent_transaction_code = pf.parent_transaction_code
        WHERE f.event_type = 'FEE_REVERSAL'
          AND (pl.platform_code = 'PAYPAL' OR COALESCE(pf.pfee_orig, 0) = 0 OR f.amount_orig > COALESCE(pf.pfee_orig, 0) + 0.01)
    ) t
),
v13_pii_cols AS (
    SELECT COUNT(*) AS bad_cnt
    FROM information_schema.columns
    WHERE table_schema IN ('edw', 'mart')
      AND (
          LOWER(column_name) LIKE '%email%'
          OR LOWER(column_name) LIKE '%username%'
          OR LOWER(column_name) LIKE '%payer_name%'
          OR LOWER(column_name) LIKE '%buyer%'
          OR LOWER(column_name) LIKE '%client_name%'
      )
),
v14_rejects AS (
    SELECT
        COUNT(*) AS reject_cnt,
        COALESCE(STRING_AGG(DISTINCT reason, '; '), 'none') AS reasons
    FROM stg.etl_rejects
)
SELECT * FROM v1_counts
UNION ALL
SELECT 'V2', 'Orphan FKs in fact_revenue_event', 'Integrity', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Checked date, project, platform, currency, and stream keys'
FROM v2_orphan_fks
UNION ALL
SELECT 'V3', 'Sign rule violations', 'Business Rule', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'SALE, TIP, FEE_REVERSAL > 0; REFUND, PLATFORM_FEE, PROCESSING_FEE < 0'
FROM v3_signs
UNION ALL
SELECT 'V4', 'Duplicate transaction_code', 'Integrity', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Unique degenerate dimension key per event'
FROM v4_dup_tx
UNION ALL
SELECT 'V5', 'Refunds exceeding parent sale', 'Business Rule', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Sum of refunds per parent_transaction_code <= root SALE amount_orig'
FROM v5_refund_cap
UNION ALL
SELECT 'V6', 'Broken parent_transaction_code links', 'Lineage', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Root SALE has NULL parent; child rows link to an existing SALE'
FROM v6_parent_ref
UNION ALL
SELECT 'V7', 'Multi-tip orders kept separate', 'Grain', CAST(multi_tip_parents AS VARCHAR), '> 0',
       CASE WHEN multi_tip_parents > 0 THEN 'PASS' ELSE 'FAIL' END,
       'Parents with at least 2 separate TIP rows'
FROM v7_multi_tip
UNION ALL
SELECT 'V8', 'Invalid stream and platform pair', 'Domain Rule', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'GAME: STEAM/ITCH, ASSET: ITCH/VGEN, COMMISSION: VGEN/FIVERR/PAYPAL'
FROM v8_stream_platform
UNION ALL
SELECT 'V9', 'Stream vs project_type mismatch', 'Domain Rule', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Game=GAME_SALES, Asset Pack=ASSET_SALES, Commission Service=COMMISSION'
FROM v9_stream_project
UNION ALL
SELECT 'V10', 'IDR conversion rounding check', 'Calculation', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Difference between amount_idr and ROUND(amount_orig * rate, 2) <= 0.01'
FROM v10_fx_math
UNION ALL
SELECT 'V11', 'Weekend FX fallback check', 'ETL Fallback',
       CAST(weekend_fx_cnt AS VARCHAR) || ' rows (' || CAST(bad_weekend_cnt AS VARCHAR) || ' bad)', '> 0 and 0 bad',
       CASE WHEN weekend_fx_cnt > 0 AND bad_weekend_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'Non-IDR weekend rows resolved using prior business day rate'
FROM v11_weekend_fx
UNION ALL
SELECT 'V12', 'Processing fee reversed on refund', 'Business Rule', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'No PayPal reversals and no reversal larger than original platform fee'
FROM v12_proc_fee_rev
UNION ALL
SELECT 'V13', 'PII columns in edw or mart', 'Governance', CAST(bad_cnt AS VARCHAR), '= 0',
       CASE WHEN bad_cnt = 0 THEN 'PASS' ELSE 'FAIL' END,
       'No email, username, buyer, or payer name columns outside stg'
FROM v13_pii_cols
UNION ALL
SELECT 'V14', 'Quarantined rows in stg.etl_rejects', 'Info', CAST(reject_cnt AS VARCHAR) || ' rows',
       'reported', 'INFO',
       reasons
FROM v14_rejects;
