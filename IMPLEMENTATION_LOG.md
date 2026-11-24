# Implementation Log: Wasaka Interactive Data Warehouse (Phases 1 to 5)

Project: Kecerdasan Bisnis (BI) UTS individual Data Warehouse
Student: Sebastian Abe Santoso (2410817210002, Teknologi Informasi, ULM)
Case: Wasaka Interactive, Indie Studio Multi-Revenue Analytics
Repository: `d:\Downloads\random\bi-dw-uts\`
Date built: 24 Nov 2026

## 1. What is built and verified

Phases 1 through 5 from `PLAN.md` are finished and verified. Running the pipeline from scratch builds `data/warehouse.duckdb` with 5,911 rows in `edw.fact_revenue_event`, passes all 12 executable checks in `sql/03_validate.sql` (plus 2 informational summaries, 0 failures), produces identical row counts across back-to-back runs, and loads cleanly in Streamlit with no errors or warnings.

Three items from Section 10 of `PLAN.md` were settled before coding:

1. Fee rates were checked against public platform documentation and stored in `config.py`. VGen takes a 5% platform fee on commissions and shop orders plus payment processing (modeled at 2.9% + $0.30 USD equivalent). PayPal Indonesia (`paypal.com/id`) takes 3.40% plus a fixed fee on domestic commercial transactions and 4.40% plus a currency-specific fixed fee on cross-border transactions (`$0.30 USD`, `€0.35 EUR`, `£0.20 GBP`, `S$0.50 SGD`, `¥40 JPY`, `¥2.50 CNY`, `Rp 4,600 IDR`), and does not refund that processing fee when an order is refunded. Steam (30%), Fiverr (20%), and itch.io (10% default creator share plus 2.9% + $0.30 checkout) match the existing design doc.
2. Project names in `data/raw/projects.csv` come from Sebastian's GitHub (`github.com/SebastianAbeSantoso`) and portfolio (`sebastianabesantoso.github.io`): *A Match Made in Dungeon*, *R\*bert*, *Personal Space*, and *Canting Cloth*, paired with four asset packs and four commission lines covering all six production fields in the Background section.
3. The two administrative unknowns (what "Dua penilaian peer-review" requires and the exact e-learning upload cutoff) are marked TBA in `PLAN.md` and `README.md`.

## 2. Files created

```text
bi-dw-uts/
├── .gitignore
├── PLAN.md
├── README.md
├── IMPLEMENTATION_LOG.md
├── requirements.txt
├── config.py
├── data/
│   ├── raw/
│   │   ├── projects.csv
│   │   ├── project_title_map.csv
│   │   ├── fx_rates.csv
│   │   ├── fx_metadata.json
│   │   ├── steam_sales_report.csv
│   │   ├── itch_payouts.csv
│   │   ├── vgen_export.json
│   │   ├── fiverr_earnings.csv
│   │   └── paypal_activity.csv
│   └── warehouse.duckdb
├── sql/
│   ├── 00_schemas.sql
│   ├── 01_ddl_edw.sql
│   ├── 02_mart_views.sql
│   └── 03_validate.sql
├── src/
│   ├── fetch_fx.py
│   ├── generate_sources.py
│   ├── etl.py
│   └── validate.py
├── app/
│   ├── query_builder.py
│   └── app.py
├── diagrams/
└── report/
    ├── etl_last_run.json
    ├── mart_summary.json
    ├── findings_raw.md
    └── screenshots/
```

The virtual environment `.venv` inside the repo runs DuckDB 2.0.1, pandas 3.1.1, Streamlit 1.67.0, Plotly, and requests. Both `.venv/` and `data/warehouse.duckdb` are gitignored so the repo stays clean and rebuildable from code and raw files.

## 3. Source data and portfolio catalog (Phase 2)

### Internal master tables

`data/raw/projects.csv` lists 12 projects across all three streams and six production fields:

| project_code | project_name | project_type | production_field | stream |
|---|---|---|---|---|
| GAME-AMMD | A Match Made in Dungeon | Game | Full Game Dev | GAME_SALES |
| GAME-RBRT | R*bert | Game | Full Game Dev | GAME_SALES |
| GAME-PSPC | Personal Space | Game | Full Game Dev | GAME_SALES |
| GAME-CNTG | Canting Cloth | Game | Full Game Dev | GAME_SALES |
| AST-DGPX | Dungeon Matchmaker Pixel UI & Sprite Kit | Asset Pack | Pixel Art & UI | ASSET_SALES |
| AST-ISOR | Personal Space Isometric Room & Props Pack | Asset Pack | 3D Modeling | ASSET_SALES |
| AST-RHYT | R*bert Reactive Rhythm & SFX Stem Pack | Asset Pack | Audio & Music | ASSET_SALES |
| AST-BATK | Canting NPR Batik Shader & Godot Toolkit | Asset Pack | Programming & Tech | ASSET_SALES |
| COM-ILLU | Custom 2D Character & Key Visual Illustration | Commission Service | 2D Illustration | COMMISSION |
| COM-PXUI | Indie Game Pixel Art & HUD UI Commissions | Commission Service | Pixel Art & UI | COMMISSION |
| COM-SHDR | Godot & Custom NPR Shader Commissions | Commission Service | Programming & Tech | COMMISSION |
| COM-MUSC | Interactive Game BGM & SynthV Arrangement | Commission Service | Audio & Music | COMMISSION |

In the synthetic timeline (`2025-01-01` to `2026-10-31`), `GAME-CNTG` begins selling in May 2026 while the earlier games run across the full window.

`data/raw/project_title_map.csv` holds 21 case-insensitive substring rules that map unstructured commission and shop titles (for example `"character illustration"`, `"custom shader"`, `"synthv vocal"`) to their `project_code`.

### Five synthetic platform exports

`src/generate_sources.py` (fixed seed `20261124`) generates five source files with distinct formats and deliberate dirty-data cases:

| Source file | Rows / items | Format differences | Dirty data and governance cases |
|---|---:|---|---|
| `steam_sales_report.csv` | 1,297 rows | `MM/DD/YYYY` dates, 7 regional currencies, Steam sale spikes (Jun/Jul, Nov, Dec) | Refunds arrive 1 to 12 days after original sale via `parent_order_id` |
| `itch_payouts.csv` | 517 rows | `YYYY-MM-DD`, amounts formatted as strings (`$1,240.00`, `Rp 89,000`) | Contains `buyer_email` (dropped in ETL); refunds reverse itch share but keep processing fee |
| `vgen_export.json` | 257 orders | Nested JSON (`tips[]`, `refunds[]`), ISO timestamps, free-text titles | Contains `client_username` (dropped); multi-tip orders; partial milestone refunds; 4 unmatched titles |
| `fiverr_earnings.csv` | 250 rows | Flat ledger with `ORDER`, `TIP`, `CANCELLATION_PARTIAL`, `CANCELLATION_FULL` | Contains `buyer_username` (dropped); 15 exact duplicate rows from overlapping re-export; 4 unmatched titles |
| `paypal_activity.csv` | 189 rows | `DD/MM/YYYY`, Indonesian headers, comma decimals (`350000,00`) on ~42% of rows | Contains `payer_name` and `payer_email` (dropped); zero fee reversal on refunds; 3 unmatched titles |

### Real ECB exchange rates

`src/fetch_fx.py` calls the Frankfurter API (`base=EUR`, symbols `USD,SGD,JPY,CNY,GBP,IDR`) from `2024-12-20` to `2026-10-31` and computes `X -> IDR` cross rates as `R_IDR / R_X` rounded to 6 decimal places (`IDR = 1.000000`, `EUR = R_IDR`).

Starting on `2024-12-20` solves an edge case: `2025-01-01` is a bank holiday with no ECB rate, so transactions on New Year's Day fall back cleanly to the real `2024-12-31` rate. The fetch returned 474 real ECB business days (`3,318` rows in `data/raw/fx_rates.csv`, `mode="real_ecb"`, `projected_business_days=0`). Weekends and ECB holidays are naturally absent from the file, so the ETL fallback runs against real calendar gaps.

## 4. Schema, ETL pipeline, and mart views (Phase 3)

### Locked star schema (`sql/01_ddl_edw.sql`)

All six tables in `edw` keep the exact table and column names from the approved PlantUML ERD in `BI-Design-Template.docx`:

- `edw.dim_date`: 730 rows (`2025-01-01` through `2026-12-31`, `date_key` as `YYYYMMDD` integer)
- `edw.dim_revenue_stream`: 3 rows (`GAME_SALES`, `ASSET_SALES`, `COMMISSION`)
- `edw.dim_currency`: 7 rows (`IDR`, `USD`, `SGD`, `JPY`, `CNY`, `EUR`, `GBP`)
- `edw.dim_platform`: 5 rows (`STEAM`, `ITCH`, `VGEN`, `FIVERR`, `PAYPAL`)
- `edw.dim_project`: 12 rows
- `edw.fact_revenue_event`: 5,911 rows

DuckDB enforces primary keys, all five foreign keys, `UNIQUE(transaction_code)`, valid `event_type` values (`SALE`, `TIP`, `REFUND`, `PLATFORM_FEE`, `PROCESSING_FEE`, `FEE_REVERSAL`), `exchange_rate_to_idr > 0`, and the sign check (`SALE`/`TIP`/`FEE_REVERSAL` strictly positive, `REFUND`/`PLATFORM_FEE`/`PROCESSING_FEE` strictly negative on both `amount_orig` and `amount_idr`).

### ETL flow (`src/etl.py`)

1. Extract loads all 8 raw files untouched into `stg.raw_*`. Personal data exists only here.
2. Transform drops the 5 PII columns (`itch.buyer_email`, `vgen.client_username`, `fiverr.buyer_username`, `paypal.payer_name`, `paypal.payer_email`), removes the 15 duplicate Fiverr rows, normalizes dates and string/comma-decimal numbers into `Decimal` values (`ROUND_HALF_UP`), and maps free-text titles using `project_title_map.csv`.
3. Unmatched orders (4 VGen, 4 Fiverr, 3 PayPal, 11 total) are written to `stg.etl_rejects` with source, ID, and reason. Child records belonging to a quarantined parent are also skipped so no orphan lineage keys reach the fact table.
4. Each valid transaction is expanded into atomic event rows. Root sales get `transaction_code = <PLATFORM>-<order_id>-SALE` and `parent_transaction_code = NULL`. Child rows (fees, tips, refunds, fee reversals) carry deterministic suffixes (`-PFEE`, `-PRCFEE`, `-TIP1`, `-TIP2`, `-REF`, `-FREV`) and set `parent_transaction_code` to the root sale code.
5. `FXResolver` checks `(event_date, currency_code)` in `fx_rates.csv`. When an event falls on a weekend or holiday, binary search (`bisect_right`) selects the latest prior published business-day rate. Across the build, 1,717 lookups used this fallback.
6. Load executes a full refresh: views drop first, then `fact_revenue_event`, then the five dimensions, before inserting dimensions, sorting fact rows by `(date_key, transaction_code)`, assigning `revenue_event_sk`, inserting facts, and rebuilding views. Running `src/etl.py` twice in a row produced identical row counts across every table.

### Views (`sql/02_mart_views.sql`)

`edw.v_fact_enriched` joins `fact_revenue_event` with all five dimension tables and is the only object queried by the no-code query builder. Four views in `mart` answer the four business questions: `mart.v_revenue_monthly`, `mart.v_project_performance`, `mart.v_fee_refund_leakage`, and `mart.v_fx_exposure`.

One detail checked during SQL verification: because fees and refunds are stored as negative values while fee reversals are positive, net leakage is computed as `-(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr)`. On a 100 sale with -30 platform fee, -10 refund, and +3 fee reversal, leakage is `-(-30 - 10 + 3) = 37`, which matches `Gross (100) - Net (63) = 37`.

## 5. Validation results (Phase 4)

Output of `.\.venv\Scripts\python.exe src\validate.py` (`12 PASS, 2 INFO, 0 FAIL`):

| Check | Category | Observed | Expected | Status |
|---|---|---|---|---|
| V1 | Info | 5,911 fact rows across 5 dims and 8 stg tables | reported | INFO |
| V2 | Integrity | 0 orphan FKs across all 5 dimension keys | = 0 | PASS |
| V3 | Business Rule | 0 sign violations | = 0 | PASS |
| V4 | Integrity | 0 duplicate `transaction_code` values | = 0 | PASS |
| V5 | Business Rule | 0 parents where total refunds exceed root sale | = 0 | PASS |
| V6 | Lineage | 0 broken `parent_transaction_code` links | = 0 | PASS |
| V7 | Grain | 33 parent orders with at least 2 separate TIP rows | > 0 | PASS |
| V8 | Domain Rule | 0 invalid revenue stream and platform pairs | = 0 | PASS |
| V9 | Domain Rule | 0 stream vs `project_type` mismatches | = 0 | PASS |
| V10 | Calculation | 0 rows with `amount_idr` off by more than Rp 0.01 | = 0 | PASS |
| V11 | ETL Fallback | 1,615 non-IDR weekend events, 0 bad/null rates | > 0 and 0 bad | PASS |
| V12 | Business Rule | 0 processing fees reversed on refund | = 0 | PASS |
| V13 | Governance | 0 PII columns in `edw` or `mart` | = 0 | PASS |
| V14 | Info | 11 unmatched rows quarantined in `stg.etl_rejects` | reported | INFO |

## 6. Streamlit application (Phase 5)

`app/app.py` connects to `data/warehouse.duckdb` in read-only mode (cached via `st.cache_resource`, with a sidebar button to reload the connection after a fresh ETL run). All UI labels are in Bahasa Indonesia without Data Analytics course terms (no roll-up, drill-down, dice, or pivot labels).

- Tab 1 (`Pembuat Kueri`) uses `app/query_builder.py` to build parameterized SQL from fixed whitelists. Users pick 0 to 3 grouping attributes, one or more measures, optional filters loaded from the dimension tables, sort order, and row limit. `Nilai Mata Uang Asal` (`SUM(amount_orig)`) and `Rata-rata Kurs ke IDR` stay disabled in the UI and rejected in `build_query()` unless `Mata Uang` is selected in Group By, preventing cross-currency sums such as JPY + USD. An expander (`Lihat SQL yang dijalankan`) shows the exact SQL string and bound parameters.
- Tab 2 (`Empat Pertanyaan Bisnis`) provides one sub-tab per business question querying the four `mart` views, each with a Plotly chart, formatted table, and SQL expander.
- Tab 3 (`Arsitektur & Validasi`) displays the `stg` / `edw` / `mart` flow, metrics from `report/etl_last_run.json`, the live V1 to V14 table from `sql/03_validate.sql`, and the `stg.etl_rejects` table.

Headless verification using `streamlit.testing.v1.AppTest` passed with 0 exceptions and 0 deprecation warnings.

## 7. Report, diagrams, screenshots, and presentation prep (Phases 6 to 8)

Phases 6 through 8 are now complete and verified:

1. **Diagrams (`diagrams/` via `src/render_diagrams.py`):**
   - `01_etl_flow.puml` / `.png`: full Extract, Transform, and Load flow including PII stripping, Fiverr deduplication, title mapping, `stg.etl_rejects` quarantine, signed atomic event explosion, and weekend FX fallback.
   - `02_vgen_json_schema.puml` / `.png`: nested `vgen_export.json` object schema showing `tips[]` and `refunds[]` arrays.
   - `03_data_tunnel.puml` / `.png`: end-to-end trace of concrete Steam, VGen, and PayPal orders from raw landing tables into atomic `fact_revenue_event` rows.
   - `04_dw_architecture.puml` / `.png`: Kimball architecture flow (`Data Sources -> stg -> ETL -> edw -> mart -> Streamlit -> Studio Stakeholders`).
   - `05_storage_design.puml` / `.png`: single-file `data/warehouse.duckdb` logical layout across `stg`, `edw`, and `mart`.
   - `06_star_schema_edw.png`: extracted approved Star Schema diagram from the template.
2. **Application & CLI Screenshots (`report/screenshots/` via `src/capture_screenshots.py`):**
   - `01_tab1_query_builder.png` through `06_tab3_validation.png`: real headless Microsoft Edge captures of the running Streamlit app in light theme, including the expanded SQL box, all four business-question tabs, and the live validation/quarantine tab.
   - `07_cli_etl_validate.png`: rendered terminal output from running `src/etl.py` and `src/validate.py`.
3. **Word Report (`report/UTS_BI_Sebastian_Wasaka_DW.docx` via `src/build_report_docx.py` & `report/sections_id.md`):**
   - Built on a copy of `d:\Downloads\random\BI-Design-Template.docx` while keeping the original file byte-for-byte untouched.
   - Removed the template warning banner, Stripe references, stray copy-paste lines, Bang Ham example diagrams/tables, and the `original_amount` and `parent_transaction_code <<DD>>` typos.
   - Added complete Indonesian sections 1 through 10 with the 10-row Data Governance matrix, realistic open-source budget, embedded diagrams and screenshots, exact warehouse figures, and the V1 to V14 validation table.
4. **Presentation Prep (`report/demo_script.md` & `report/qa_prep.md`):**
   - Step-by-step 15 to 20 minute demo flow and concise answers for 7 Business Reviewer questions and 10 Technical DW Reviewer questions.

## 8. Remaining post-presentation steps

1. Record the in-person classroom presentation and peer-review Q&A session.
2. Collect the two peer-review assessments (exact format TBA).
3. Write `Kesimpulan setelah peer-review` reflecting on the reviewers' questions and feedback.
4. Upload all four deliverables to e-learning (exact cutoff TBA) and mark the Notion task Done.
