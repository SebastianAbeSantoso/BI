-- Drop dependent views before rebuilding star schema tables (full-refresh idempotency)
DROP VIEW IF EXISTS mart.v_fx_exposure;
DROP VIEW IF EXISTS mart.v_fee_refund_leakage;
DROP VIEW IF EXISTS mart.v_project_performance;
DROP VIEW IF EXISTS mart.v_revenue_monthly;
DROP VIEW IF EXISTS edw.v_fact_enriched;

-- Drop fact table before dimension tables to respect FK dependencies
DROP TABLE IF EXISTS edw.fact_revenue_event;
DROP TABLE IF EXISTS edw.dim_project;
DROP TABLE IF EXISTS edw.dim_platform;
DROP TABLE IF EXISTS edw.dim_currency;
DROP TABLE IF EXISTS edw.dim_revenue_stream;
DROP TABLE IF EXISTS edw.dim_date;

CREATE TABLE edw.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_week VARCHAR(20) NOT NULL,
    day_of_week_number INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_year INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    month_number INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE edw.dim_revenue_stream (
    revenue_stream_key INTEGER PRIMARY KEY,
    revenue_stream_code VARCHAR(50) NOT NULL UNIQUE,
    revenue_stream_name VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);

CREATE TABLE edw.dim_currency (
    currency_key INTEGER PRIMARY KEY,
    currency_code CHAR(3) NOT NULL UNIQUE,
    currency_name VARCHAR(50) NOT NULL,
    currency_symbol VARCHAR(5) NOT NULL
);

CREATE TABLE edw.dim_platform (
    platform_key INTEGER PRIMARY KEY,
    platform_code VARCHAR(50) NOT NULL UNIQUE,
    platform_name VARCHAR(100) NOT NULL,
    platform_type VARCHAR(50) NOT NULL
);

CREATE TABLE edw.dim_project (
    project_key INTEGER PRIMARY KEY,
    project_code VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(150) NOT NULL,
    project_type VARCHAR(50) NOT NULL,
    production_field VARCHAR(100) NOT NULL
);

CREATE TABLE edw.fact_revenue_event (
    revenue_event_sk BIGINT PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES edw.dim_date(date_key),
    project_key INTEGER NOT NULL REFERENCES edw.dim_project(project_key),
    platform_key INTEGER NOT NULL REFERENCES edw.dim_platform(platform_key),
    currency_key INTEGER NOT NULL REFERENCES edw.dim_currency(currency_key),
    revenue_stream_key INTEGER NOT NULL REFERENCES edw.dim_revenue_stream(revenue_stream_key),
    transaction_code VARCHAR(100) NOT NULL UNIQUE,
    parent_transaction_code VARCHAR(100),
    event_type VARCHAR(30) NOT NULL,
    amount_orig DECIMAL(18,2) NOT NULL,
    exchange_rate_to_idr DECIMAL(18,6) NOT NULL,
    amount_idr DECIMAL(18,2) NOT NULL,
    CHECK (event_type IN ('SALE', 'TIP', 'REFUND', 'PLATFORM_FEE', 'PROCESSING_FEE', 'FEE_REVERSAL')),
    CHECK (
        (event_type IN ('SALE', 'TIP', 'FEE_REVERSAL') AND amount_orig > 0 AND amount_idr > 0)
        OR
        (event_type IN ('REFUND', 'PLATFORM_FEE', 'PROCESSING_FEE') AND amount_orig < 0 AND amount_idr < 0)
    ),
    CHECK (exchange_rate_to_idr > 0)
);
