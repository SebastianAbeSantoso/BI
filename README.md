# Wasaka Interactive Revenue Data Warehouse

Kimball star schema data warehouse, Python ETL pipeline, validation checks, and Streamlit query app for the Kecerdasan Bisnis (BI) midterm project.

## Running locally (PowerShell)

```powershell
Set-Location d:\Downloads\random\bi-dw-uts
.\.venv\Scripts\python.exe src\fetch_fx.py
.\.venv\Scripts\python.exe src\generate_sources.py
.\.venv\Scripts\python.exe src\etl.py
.\.venv\Scripts\python.exe src\validate.py
.\.venv\Scripts\streamlit.exe run app\app.py
```

## Layout and schemas

All data lives in a single DuckDB file (`data/warehouse.duckdb`) split across three schemas:

- `stg` holds the raw files as loaded (`raw_steam`, `raw_itch`, `raw_vgen`, `raw_fiverr`, `raw_paypal`, `raw_fx_rates`, `raw_projects`, `raw_title_map`) plus `stg.etl_rejects` for rows that fail title mapping.
- `edw` holds the 6 approved star schema tables (`dim_date`, `dim_revenue_stream`, `dim_currency`, `dim_platform`, `dim_project`, `fact_revenue_event`) and the helper view `edw.v_fact_enriched`.
- `mart` holds four query views (`v_revenue_monthly`, `v_project_performance`, `v_fee_refund_leakage`, `v_fx_exposure`) backing the business questions in the app.

Each row in `fact_revenue_event` is a single financial event. Sales, tips, and fee reversals are stored as positive numbers; refunds, platform fees, and processing fees are stored as negative numbers. Summing `amount_idr` gives net revenue.

Personal fields from raw exports (`buyer_email`, `client_username`, `buyer_username`, `payer_name`, `payer_email`) stay in `stg` and are dropped before loading `edw`. Check `V13` verifies that none of those columns exist in `edw` or `mart`.

## Data notes and fee rates

Transaction records in `data/raw/` (covering `2025-01-01` to `2026-10-31`, seed `20261124`) are synthetic. Each platform export uses its own file shape, date style, and number formatting so the ETL has real cleaning work to do.

Exchange rates in `data/raw/fx_rates.csv` come from the European Central Bank through the Frankfurter API (`474` business days from `2024-12-20` to `2026-10-30`, cross-computed to IDR). Because the ECB does not publish rates on weekends or bank holidays, `src/etl.py` looks up the most recent earlier business day.

Fee assumptions set in `config.py`:

| Platform | Platform cut | Processing fee | Refund behavior | Source |
|---|---|---|---|---|
| Steam | 30% | none | Platform cut reversed | Steamworks standard tier |
| itch.io | 10% | 2.9% + $0.30 USD eq. | Platform cut reversed, processing kept | itch.io open revenue share default |
| VGen | 5% | 2.9% + $0.30 USD eq. | Platform cut reversed, processing kept | VGen Help Center |
| Fiverr | 20% | none | Platform cut reversed (applies to orders and tips) | Fiverr Seller Terms |
| Direct PayPal | 0% | 3.40% domestic / 4.40% cross-border + fixed fee | Processing fee kept | PayPal Indonesia merchant fees |

## Remaining admin items

- Definition of "Dua penilaian peer-review": TBA
- Exact e-learning upload cutoff: TBA
