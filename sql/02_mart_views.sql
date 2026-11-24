CREATE OR REPLACE VIEW edw.v_fact_enriched AS
SELECT
    f.revenue_event_sk,
    f.date_key,
    d.full_date,
    d.year,
    d.quarter,
    'Q' || CAST(d.quarter AS VARCHAR) AS quarter_label,
    d.month_number,
    d.month_name,
    PRINTF('%04d-%02d', d.year, d.month_number) AS year_month,
    d.day_of_week,
    d.day_of_week_number,
    d.is_weekend,
    CASE WHEN d.is_weekend THEN 'Akhir Pekan' ELSE 'Hari Kerja' END AS day_category,
    rs.revenue_stream_key,
    rs.revenue_stream_code,
    rs.revenue_stream_name,
    pl.platform_key,
    pl.platform_code,
    pl.platform_name,
    pl.platform_type,
    pr.project_key,
    pr.project_code,
    pr.project_name,
    pr.project_type,
    pr.production_field,
    cu.currency_key,
    cu.currency_code,
    cu.currency_name,
    cu.currency_symbol,
    f.transaction_code,
    f.parent_transaction_code,
    f.event_type,
    f.amount_orig,
    f.exchange_rate_to_idr,
    f.amount_idr
FROM edw.fact_revenue_event f
INNER JOIN edw.dim_date d ON f.date_key = d.date_key
INNER JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
INNER JOIN edw.dim_platform pl ON f.platform_key = pl.platform_key
INNER JOIN edw.dim_project pr ON f.project_key = pr.project_key
INNER JOIN edw.dim_currency cu ON f.currency_key = cu.currency_key;

CREATE OR REPLACE VIEW mart.v_revenue_monthly AS
SELECT
    d.year,
    d.quarter,
    d.month_number,
    d.month_name,
    PRINTF('%04d-%02d', d.year, d.month_number) AS year_month,
    rs.revenue_stream_code,
    rs.revenue_stream_name,
    pl.platform_code,
    pl.platform_name,
    cu.currency_code,
    COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'SALE'), 0) AS gross_sales_idr,
    COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'TIP'), 0) AS tips_idr,
    COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'PLATFORM_FEE'), 0) AS platform_fees_idr,
    COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'PROCESSING_FEE'), 0) AS processing_fees_idr,
    COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'REFUND'), 0) AS refunds_idr,
    COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'FEE_REVERSAL'), 0) AS fee_reversals_idr,
    SUM(f.amount_idr) AS net_revenue_idr,
    COUNT(*) AS event_count
FROM edw.fact_revenue_event f
INNER JOIN edw.dim_date d ON f.date_key = d.date_key
INNER JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
INNER JOIN edw.dim_platform pl ON f.platform_key = pl.platform_key
INNER JOIN edw.dim_currency cu ON f.currency_key = cu.currency_key
GROUP BY
    d.year, d.quarter, d.month_number, d.month_name,
    rs.revenue_stream_code, rs.revenue_stream_name,
    pl.platform_code, pl.platform_name, cu.currency_code;

CREATE OR REPLACE VIEW mart.v_project_performance AS
WITH agg AS (
    SELECT
        pr.project_code,
        pr.project_name,
        pr.project_type,
        pr.production_field,
        rs.revenue_stream_code,
        rs.revenue_stream_name,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'SALE'), 0) AS gross_sales_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'TIP'), 0) AS tips_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'PLATFORM_FEE'), 0) AS platform_fees_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'PROCESSING_FEE'), 0) AS processing_fees_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'REFUND'), 0) AS refunds_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'FEE_REVERSAL'), 0) AS fee_reversals_idr,
        SUM(f.amount_idr) AS net_revenue_idr,
        COUNT(*) FILTER (WHERE f.event_type = 'SALE') AS sale_count,
        COUNT(*) AS total_events
    FROM edw.fact_revenue_event f
    INNER JOIN edw.dim_project pr ON f.project_key = pr.project_key
    INNER JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
    GROUP BY
        pr.project_code, pr.project_name, pr.project_type, pr.production_field,
        rs.revenue_stream_code, rs.revenue_stream_name
)
SELECT
    *,
    -(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr) AS net_leakage_idr,
    ROUND(
        CASE
            WHEN gross_sales_idr > 0
            THEN -(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr) * 100.0 / gross_sales_idr
            ELSE 0
        END,
        2
    ) AS leakage_pct
FROM agg;

CREATE OR REPLACE VIEW mart.v_fee_refund_leakage AS
WITH agg AS (
    SELECT
        pl.platform_code,
        pl.platform_name,
        pl.platform_type,
        rs.revenue_stream_code,
        rs.revenue_stream_name,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'SALE'), 0) AS gross_sales_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'TIP'), 0) AS tips_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'PLATFORM_FEE'), 0) AS platform_fees_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'PROCESSING_FEE'), 0) AS processing_fees_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'REFUND'), 0) AS refunds_idr,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'FEE_REVERSAL'), 0) AS fee_reversals_idr,
        SUM(f.amount_idr) AS net_revenue_idr,
        COUNT(*) FILTER (WHERE f.event_type = 'SALE') AS sale_count,
        COUNT(*) FILTER (WHERE f.event_type = 'REFUND') AS refund_count
    FROM edw.fact_revenue_event f
    INNER JOIN edw.dim_platform pl ON f.platform_key = pl.platform_key
    INNER JOIN edw.dim_revenue_stream rs ON f.revenue_stream_key = rs.revenue_stream_key
    GROUP BY
        pl.platform_code, pl.platform_name, pl.platform_type,
        rs.revenue_stream_code, rs.revenue_stream_name
)
SELECT
    *,
    -(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr) AS net_leakage_idr,
    ROUND(
        CASE
            WHEN gross_sales_idr > 0
            THEN -(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr) * 100.0 / gross_sales_idr
            ELSE 0
        END,
        2
    ) AS leakage_pct
FROM agg;

CREATE OR REPLACE VIEW mart.v_fx_exposure AS
WITH monthly_fx AS (
    SELECT
        d.year,
        d.month_number,
        PRINTF('%04d-%02d', d.year, d.month_number) AS year_month,
        cu.currency_code,
        cu.currency_name,
        cu.currency_symbol,
        SUM(f.amount_orig) AS net_amount_orig,
        COALESCE(SUM(f.amount_orig) FILTER (WHERE f.event_type = 'SALE'), 0) AS gross_sales_orig,
        COALESCE(SUM(f.amount_idr) FILTER (WHERE f.event_type = 'SALE'), 0) AS gross_sales_idr,
        SUM(f.amount_idr) AS net_revenue_idr,
        ROUND(AVG(f.exchange_rate_to_idr), 4) AS avg_exchange_rate_to_idr,
        ROUND(MIN(f.exchange_rate_to_idr), 4) AS min_exchange_rate_to_idr,
        ROUND(MAX(f.exchange_rate_to_idr), 4) AS max_exchange_rate_to_idr,
        COUNT(*) AS event_count
    FROM edw.fact_revenue_event f
    INNER JOIN edw.dim_date d ON f.date_key = d.date_key
    INNER JOIN edw.dim_currency cu ON f.currency_key = cu.currency_key
    GROUP BY
        d.year, d.month_number,
        cu.currency_code, cu.currency_name, cu.currency_symbol
)
SELECT
    *,
    ROUND(
        net_revenue_idr * 100.0 / NULLIF(SUM(net_revenue_idr) OVER (PARTITION BY year_month), 0),
        2
    ) AS monthly_net_share_pct,
    ROUND(
        net_revenue_idr * 100.0 / NULLIF(SUM(net_revenue_idr) OVER (), 0),
        2
    ) AS overall_net_share_pct
FROM monthly_fx;
