# Wasaka Interactive — Multi-Revenue Data Warehouse (BI UTS)

End-to-end Kimball Star Schema Data Warehouse, Python ETL pipeline, V1–V14 validation suite, and no-code Streamlit OLAP query interface for **Wasaka Interactive** (Indie Game & Creative Production Studio).

## Quick Start (PowerShell)

```powershell
Set-Location d:\Downloads\random\bi-dw-uts
.\.venv\Scripts\python.exe src\fetch_fx.py
.\.venv\Scripts\python.exe src\generate_sources.py
.\.venv\Scripts\python.exe src\etl.py
.\.venv\Scripts\python.exe src\validate.py
.\.venv\Scripts\streamlit.exe run app\app.py
```

## Architecture Summary

- **Engine:** Single-file **DuckDB** (`data/warehouse.duckdb`) organized into three logical schemas:
  - `stg`: Transient raw ingestion tables (`raw_steam`, `raw_itch`, `raw_vgen`, `raw_fiverr`, `raw_paypal`, `raw_fx_rates`, `raw_projects`, `raw_title_map`) plus `stg.etl_rejects` quarantine log.
  - `edw`: Locked 6-table Kimball Star Schema (`dim_date`, `dim_revenue_stream`, `dim_currency`, `dim_platform`, `dim_project`, `fact_revenue_event`) + `v_fact_enriched` wide star-join view.
  - `mart`: Analytical views answering the 4 core studio business questions (`v_revenue_monthly`, `v_project_performance`, `v_fee_refund_leakage`, `v_fx_exposure`).
- **Grain:** Atomic financial event (`SALE`, `TIP`, `FEE_REVERSAL` positive; `PLATFORM_FEE`, `PROCESSING_FEE`, `REFUND` negative). `SUM(amount_idr)` yields exact net revenue.
- **Data Governance & PII Policy:** Buyer/client personal identifiers (`buyer_email`, `client_username`, `buyer_username`, `payer_name`, `payer_email`) exist only in transient `stg` tables and are stripped prior to `edw` / `mart` loading (verified by check `V13`).

## Data Provenance & Synthetic Data Disclosure

- **Transaction Events (Synthetic):** Platform exports in `data/raw/` (`2025-01-01` to `2026-10-31`, deterministic seed `20261124`) are **synthetic**, generated from published platform fee structures and realistic multi-format export quirks (`MM/DD/YYYY` vs `DD/MM/YYYY` vs ISO timestamps, comma decimals, `$` / `¥` / `Rp` formatted strings, nested JSON arrays, re-export duplicates, and unmapped commission titles).
- **Exchange Rates (Real External Data):** Historical spot reference rates in `data/raw/fx_rates.csv` (`474` published business days, `2024-12-20` to `2026-10-30`) are **real European Central Bank (ECB) daily reference rates** fetched via the Frankfurter API and cross-computed to `IDR`. Weekend/holiday transactions resolve via last-known prior business day fallback (`V11`).
- **Fee Schedules Used (`config.py`):**
  - **Steam:** `30.0%` platform fee (reversed on refund via `FEE_REVERSAL`).
  - **itch.io:** `10.0%` creator-configured platform share (reversed on refund) + `2.9% + $0.30 USD eq.` checkout processing fee (non-refundable).
  - **VGen:** `5.0%` creator platform fee on commissions & shop orders (verified via VGen Help Center; reversed on refund) + `2.9% + $0.30 USD eq.` payment processing fee (non-refundable).
  - **Fiverr:** `20.0%` platform commission on orders and tips (reversed on cancellation/refund).
  - **Direct PayPal:** `0%` platform fee; `3.40% + fixed fee` domestic (`IDR`) and `4.40% + fixed fee` international commercial processing fee (verified via `paypal.com/id` Merchant Fees; never reversed on refund).

## Open Administrative Items

- **Peer-review form definition ("Dua penilaian peer-review"):** `TBA`
- **Exact e-learning submission cutoff:** `TBA`
