# Wasaka Interactive Data Warehouse — Human-Readable Build & Implementation Log

**Project:** Business Intelligence (Kecerdasan Bisnis) UTS — Individual Data Warehouse Case Study  
**Author / Owner:** Sebastian Abe Santoso (`2410817210002`, Teknologi Informasi — Big Data, ULM)  
**Case Study:** *Wasaka Interactive* — Indie Game & Creative Studio Multi-Revenue Analytics  
**Completed Scope:** Phases 1 through 5 of `PLAN.md` (strictly aligned with Sections 0–5)  
**Build Timestamp:** Tuesday, 24 November 2026 (WITA / UTC+8)  
**Repository Path:** `d:\Downloads\random\bi-dw-uts\`

---

## 1. Executive Summary (TL;DR)

Everything specified in **Phases 1–5** of `PLAN.md` has been built, executed end-to-end, verified for idempotency across back-to-back full refreshes, validated against all **14 automated data warehouse checks (`12 PASS`, `2 INFO`, `0 FAIL`)**, and tested headlessly in Streamlit (`0` runtime exceptions, `0` deprecation warnings).

Here is what now exists on disk and works out of the box:

1. **Verified Real-World Inputs & Portfolio Grounding:**
   - **Fee schedules verified from official platform documentation:** Steam (`30%`), Fiverr (`20%`), itch.io (`10%` open revenue share default + `2.9% + $0.30` processing), **VGen** (`5.0%` creator fee on both commissions and shop orders + `2.9% + $0.30` processing, verified via VGen Help Center), and **PayPal Indonesia** (`3.40% + fixed fee` domestic commercial / `4.40% + fixed fee` international cross-border commercial, verified via `paypal.com/id` Merchant Fees).
   - **Real ECB Historical Exchange Rates:** Fetched directly from the **Frankfurter API** (`474` real European Central Bank business days from `2024-12-20` through `2026-10-30`, producing `3,318` currency-day records across `IDR, USD, SGD, JPY, CNY, EUR, GBP` with **zero** simulated/projected days needed).
   - **Real Portfolio Projects:** Populated `projects.csv` using your actual Wasaka Games & personal portfolio projects (*A Match Made in Dungeon*, *R\*bert*, *Personal Space*, *Canting Cloth*, plus 4 companion digital asset packs and 4 commission service lines spanning all 6 production fields).
2. **Five Multi-Format Raw Source Exports (`data/raw/`):** Intentionally heterogeneous files (`MM/DD/YYYY` vs `YYYY-MM-DD` vs `DD/MM/YYYY` vs ISO-8601 JSON, `$`/`¥`/`Rp` currency strings, comma decimals like `350000,00`, nested JSON arrays for tips/refunds, `15` injected duplicate Fiverr rows, `11` unmapped out-of-scope titles, and `5` personal-data/PII columns).
3. **Single-File DuckDB Warehouse (`data/warehouse.duckdb`):** Organized into `stg` → `edw` → `mart` schemas, strictly implementing your approved 21 October 2026 Star Schema (`dim_date`, `dim_revenue_stream`, `dim_currency`, `dim_platform`, `dim_project`, `fact_revenue_event`) without adding, removing, or renaming a single column in `edw`. Loaded with **`5,911` atomic financial events**.
4. **Automated Validation Suite (`sql/03_validate.sql` + `src/validate.py`):** Checks `V1`–`V14` covering foreign keys, sign constraints, `transaction_code` uniqueness, partial-refund caps, `parent_transaction_code` lineage, multi-tip preservation (`33` multi-tip orders), domain matrices, `Rp 0.01` FX rounding precision, weekend FX fallback (`1,615` weekend foreign-currency events), non-reversible processing fees, PII stripping, and quarantine logging.
5. **Three-Tab No-Code Streamlit OLAP Front End (`app/app.py` + `app/query_builder.py`):**
   - **Tab 1:** Guided no-code SQL builder for non-technical users (whitelisted SQL expressions, `?`-parameterized filters, currency-grouping safety lock that blocks `SUM(amount_orig)` across mixed currencies, auto Plotly chart, CSV export, and *"Lihat SQL yang dijalankan"* expander). Contains **zero** Data Analytics course jargon (*no roll-up, drill-down, dice, or pivot labels*).
   - **Tab 2:** One-click presets answering your 4 settled business questions directly from `mart.*` views.
   - **Tab 3:** Architecture flow, ETL telemetry metrics, live `V1`–`V14` validation table, and `stg.etl_rejects` quarantine viewer.

---

## 2. Resolution of Open Items from `PLAN.md` (Section 10)

| # | Item from `PLAN.md` | Resolution Applied |
|---|---|---|
| **1** | VGen platform fee & PayPal processing fee | **Confirmed & documented in `config.py`:** VGen charges a flat **5.0%** platform service fee on both commissions and shop items, plus payment processing (~**2.9% + $0.30 USD** equivalent). PayPal Indonesia (`paypal.com/id`) charges **3.40% + currency fixed fee** on domestic commercial transactions and **4.40% + currency fixed fee** (`$0.30 USD`, `€0.35 EUR`, `£0.20 GBP`, `S$0.50 SGD`, `¥40 JPY`, `¥2.50 CNY`, `Rp 4,600 IDR`) on cross-border commercial transactions, with **no fee reversal on refund**. |
| **2** | Project names in `projects.csv` | **Populated from your real GitHub & portfolio (`sebastianabesantoso.github.io` / `wasakagames.itch.io`):** Uses *A Match Made in Dungeon*, *R\*bert*, *Personal Space*, and *Canting Cloth* for games, paired with matching asset packs and commission services across all 6 production fields. |
| **3** | Meaning of *"Dua penilaian peer-review"* | Marked **`TBA`** in `PLAN.md` and `README.md` as requested. |
| **4** | Exact e-learning upload cutoff | Marked **`TBA`** in `PLAN.md` and `README.md` as requested. |

---

## 3. Complete Repository Map & File Inventory

```text
d:\Downloads\random\bi-dw-uts\
├── .gitignore                   # Excludes .venv/, __pycache__/, data/warehouse.duckdb
├── PLAN.md                      # Master execution plan (Section 10 updated with resolved/TBA items)
├── README.md                    # 3-command quickstart, architecture overview, synthetic-data disclosure
├── IMPLEMENTATION_LOG.md        # This human-readable build & verification dossier
├── requirements.txt             # Pinned minimum versions (duckdb, pandas, streamlit, plotly, requests)
├── config.py                    # Central constants, verified fee schedules, static dims, portfolio catalog
├── data/
│   ├── raw/
│   │   ├── projects.csv             # Internal project master (12 projects across 6 production fields)
│   │   ├── project_title_map.csv    # 21 substring rules mapping messy commission titles -> project_code
│   │   ├── fx_rates.csv             # 3,318 rows of real ECB daily cross-rates to IDR (474 business days)
│   │   ├── fx_metadata.json         # Provenance log confirming mode="real_ecb", projected_days=0
│   │   ├── steam_sales_report.csv   # 1,297 rows (MM/DD/YYYY, 7 currencies, sale spikes, refunds)
│   │   ├── itch_payouts.csv         # 517 rows (YYYY-MM-DD, formatted "$/¥/Rp" strings, buyer_email PII)
│   │   ├── vgen_export.json         # 257 nested JSON orders (tips[], refunds[], client_username PII)
│   │   ├── fiverr_earnings.csv      # 250 rows (includes 15 exact re-export duplicates, buyer_username PII)
│   │   └── paypal_activity.csv      # 189 rows (DD/MM/YYYY, comma decimals "125,50", payer PII)
│   └── warehouse.duckdb         # Built single-file DuckDB warehouse (gitignored; rebuilt by src/etl.py)
├── sql/
│   ├── 00_schemas.sql           # CREATE SCHEMA IF NOT EXISTS stg, edw, mart
│   ├── 01_ddl_edw.sql           # Exact 6 approved Star Schema tables + PK, FK, UNIQUE, CHECK constraints
│   ├── 02_mart_views.sql        # edw.v_fact_enriched + 4 mart views (v_revenue_monthly, etc.)
│   └── 03_validate.sql          # Single-query V1–V14 automated validation suite
├── src/
│   ├── fetch_fx.py              # Fetches ECB daily reference rates from Frankfurter API & cross-computes IDR
│   ├── generate_sources.py      # Deterministic (seed=20261124) multi-format synthetic export generator
│   ├── etl.py                   # Extract (stg) -> Transform (clean/dedup/map/FX/explode) -> Load (edw/mart)
│   └── validate.py              # CLI runner for sql/03_validate.sql (exits non-zero if any FAIL)
├── app/
│   ├── query_builder.py         # Whitelisted SQL generator + parameter binding + currency-group guard
│   └── app.py                   # 3-tab Bahasa Indonesia Streamlit OLAP query application
├── diagrams/                    # Ready for Phase 6 PlantUML diagrams tomorrow
└── report/
    ├── etl_last_run.json        # Machine-readable telemetry from latest ETL run (used by App Tab 3)
    ├── mart_summary.json        # Extracted exact aggregates across all 4 marts
    ├── findings_raw.md          # Ready-to-use Indonesian/English analytical findings for Phase 7 report
    └── screenshots/             # Ready for Phase 6 app screenshots tomorrow
```

---

## 4. Phase-by-Phase Walkthrough of What Was Built & Why

### Phase 1 — Environment & Repository Setup
- Initialized Git repository inside `d:\Downloads\random\bi-dw-uts\` with `.gitignore` keeping virtual environments and binary `.duckdb` files out of version control.
- Created isolated local virtual environment (`.venv`) running **Python**, **DuckDB `2.0.1`**, **pandas `3.1.1`**, **Streamlit `1.67.0`**, **Plotly**, and **requests**.
- Centralized all configuration in `config.py` so there are zero magic numbers scattered across scripts.

### Phase 2 — Real Portfolio Master Data, Messy Platform Exports & Real ECB FX

#### 2A. Portfolio Project Catalog (`data/raw/projects.csv`)
Instead of generic dummy names, the 12 projects in `dim_project` reflect your actual body of work across all **6 production fields** described in your report's Background section:

| `project_code` | `project_name` | `project_type` | `production_field` | Stream |
|---|---|---|---|---|
| `GAME-AMMD` | A Match Made in Dungeon | Game | Full Game Dev | `GAME_SALES` |
| `GAME-RBRT` | R\*bert | Game | Full Game Dev | `GAME_SALES` |
| `GAME-PSPC` | Personal Space | Game | Full Game Dev | `GAME_SALES` |
| `GAME-CNTG` | Canting Cloth *(active from May 2026)* | Game | Full Game Dev | `GAME_SALES` |
| `AST-DGPX` | Dungeon Matchmaker Pixel UI & Sprite Kit | Asset Pack | Pixel Art & UI | `ASSET_SALES` |
| `AST-ISOR` | Personal Space Isometric Room & Props Pack | Asset Pack | 3D Modeling | `ASSET_SALES` |
| `AST-RHYT` | R\*bert Reactive Rhythm & SFX Stem Pack | Asset Pack | Audio & Music | `ASSET_SALES` |
| `AST-BATK` | Canting NPR Batik Shader & Godot Toolkit | Asset Pack | Programming & Tech | `ASSET_SALES` |
| `COM-ILLU` | Custom 2D Character & Key Visual Illustration | Commission Service | 2D Illustration | `COMMISSION` |
| `COM-PXUI` | Indie Game Pixel Art & HUD UI Commissions | Commission Service | Pixel Art & UI | `COMMISSION` |
| `COM-SHDR` | Godot & Custom NPR Shader Commissions | Commission Service | Programming & Tech | `COMMISSION` |
| `COM-MUSC` | Interactive Game BGM & SynthV Arrangement | Commission Service | Audio & Music | `COMMISSION` |

#### 2B. Why the 5 Platform Exports Look Different (`src/generate_sources.py`)
A common trap in student Data Warehouse projects is generating five clean CSVs that already look identical to the fact table—which makes the "Transform" step look fake during technical review. To make the ETL genuinely earn its keep, each synthetic export (`2025-01-01` → `2026-10-31`, deterministic seed `20261124`) mimics the quirks of its real-world platform:

1. **`steam_sales_report.csv` (`1,297` rows):**
   - Uses US date format `MM/DD/YYYY`.
   - Prices games in regional storefront currencies (`USD, EUR, GBP, JPY, CNY, SGD, IDR`) with realistic Summer Sale (late Jun–early Jul), Autumn Sale (late Nov), and Winter Sale (late Dec) volume multipliers and discounts.
   - Records refunds (`~5.8%`) 1–12 days after purchase referencing `parent_order_id`, returning Steam's `30%` cut.
2. **`itch_payouts.csv` (`517` rows):**
   - Uses ISO `YYYY-MM-DD` dates, mixes `Game` and `Asset Pack` items, includes optional pay-what-you-want tips, and formats money as messy display strings with currency symbols and thousands separators (`"$1,240.00"`, `"¥1,200"`, `"Rp 89,000"`).
   - Contains `buyer_email` (PII) and models itch.io's asymmetry on refunds: the `10%` platform share is reversed, while the `2.9% + $0.30` payment processor fee is **not** returned.
3. **`vgen_export.json` (`257` nested orders):**
   - Structured as nested JSON (`order` → `tips[]` array + `refunds[]` array) with UTC timestamps (`2025-05-14T11:20:00Z`), `SHOP_ASSET` vs `COMMISSION` orders, free-text order titles (`"Anime Key Visual Illustration #42"`), and `client_username` PII.
   - Includes **multi-tip orders** (2 separate tips on one commission) and **partial milestone refunds** (`40%`–`50%` of order value), plus **4 out-of-scope titles** (e.g., `"3D VTuber Fullbody ARKit Rigging"`, `"Live2D Cubism Physics & Toggle Setup"`) that intentionally fail title mapping so `stg.etl_rejects` can be demonstrated live.
4. **`fiverr_earnings.csv` (`250` rows):**
   - Flat ledger where `ORDER`, `TIP`, `CANCELLATION_PARTIAL`, and `CANCELLATION_FULL` appear as separate rows linked via `parent_order_id`, deducting Fiverr's `20%` commission on both orders and tips.
   - Contains `buyer_username` PII, **15 injected exact duplicate rows** (simulating overlapping date-range CSV exports by finance staff), and **4 out-of-scope titles** (e.g., `"Youtube Gaming Montage Video Editing"`).
5. **`paypal_activity.csv` (`189` rows):**
   - Indonesian/European regional export style: `DD/MM/YYYY` dates, Indonesian column headers (`tanggal`, `tipe_aktivitas`, `nilai_kotor`, `biaya_paypal`), and **comma decimals** (`"350000,00"`, `"-16500,00"`) in ~42% of rows mixed with dot decimals in the rest.
   - Models PayPal explicitly as a **direct-commission platform** (`0%` platform cut, `3.40%` domestic / `4.40%` cross-border + fixed processing fee, and **`0.00` fee reversal on refunds**). Includes `payer_name` + `payer_email` PII and **3 out-of-scope personal transfers** (`"Jasa Titip Artbook Comiket"`, etc.).

#### 2C. Real Historical Exchange Rates (`src/fetch_fx.py`)
- Queries the Frankfurter API (`https://api.frankfurter.dev/v1/2024-12-20..2026-10-31?base=EUR&symbols=USD,SGD,JPY,CNY,GBP,IDR`).
- Why start on `2024-12-20` instead of `2025-01-01`? Because **1 January 2025 is New Year's Day** (a bank holiday with no ECB publication). Pulling late December 2024 ensures that any transaction occurring on `2025-01-01` resolves cleanly to the real `2024-12-31` year-end business-day rate!
- Cross-rate math: since ECB quotes `1 EUR = R_IDR IDR` and `1 EUR = R_X X`, each currency's IDR rate is computed as `R_IDR / R_X` (rounded to 6 decimal places, `DECIMAL(18,6)`), with `EUR = R_IDR` and `IDR = 1.000000`.
- Result: **`474` real ECB business days (`3,318` rows)** written to `data/raw/fx_rates.csv`, `mode = "real_ecb"`, `projected_business_days = 0`. Weekends and ECB holidays are naturally absent, which forces the ETL's weekend fallback logic to work on real calendar gaps.

---

### Phase 3 — DuckDB Star Schema DDL, ETL Pipeline & Mart Views

#### 3A. Exact Approved Schema & Database-Enforced Integrity (`sql/01_ddl_edw.sql`)
- Every table and column name in `edw` matches your approved PlantUML ERD in `BI-Design-Template.docx` character-for-character:
  - `edw.dim_date` (`730` rows covering `2025-01-01` through `2026-12-31`, `date_key` as `YYYYMMDD` integer)
  - `edw.dim_revenue_stream` (`3` rows: `GAME_SALES`, `ASSET_SALES`, `COMMISSION`)
  - `edw.dim_currency` (`7` rows: `IDR, USD, SGD, JPY, CNY, EUR, GBP`)
  - `edw.dim_platform` (`5` rows: `STEAM, ITCH, VGEN, FIVERR, PAYPAL`)
  - `edw.dim_project` (`12` rows)
  - `edw.fact_revenue_event` (`5,911` rows)
- **Database-level constraints enforced by DuckDB:**
  - `PRIMARY KEY` on all surrogate keys and `UNIQUE` on all natural keys (`<<NK>>`) plus `UNIQUE(transaction_code)` (`<<DD>>`).
  - `FOREIGN KEY` constraints from `fact_revenue_event` to all 5 dimension tables.
  - `CHECK` constraint restricting `event_type` to the 6 valid codes (`SALE`, `TIP`, `REFUND`, `PLATFORM_FEE`, `PROCESSING_FEE`, `FEE_REVERSAL`).
  - `CHECK` constraint enforcing **strict sign symmetry** on both `amount_orig` and `amount_idr`: positive (`> 0`) for `SALE`, `TIP`, `FEE_REVERSAL`; negative (`< 0`) for `REFUND`, `PLATFORM_FEE`, `PROCESSING_FEE`.
  - `CHECK (exchange_rate_to_idr > 0)`.

#### 3B. ETL Execution Mechanics (`src/etl.py`)
1. **Extract → `stg`:** Loads all 8 raw files untouched into `stg.raw_*` tables. Personal identifiers remain in `stg` only as a transient landing zone.
2. **Transform:**
   - **Governance PII Drop:** Strips `itch.buyer_email`, `vgen.client_username`, `fiverr.buyer_username`, `paypal.payer_name`, and `paypal.payer_email` before transformation.
   - **Exact Deduplication:** Removes the `15` duplicate rows from `fiverr_earnings.csv` and records the count in `report/etl_last_run.json`.
   - **Amount & Date Normalization:** Parses `MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`, and ISO timestamps into `datetime.date`; parses `$1,240.00` and European/Indonesian comma decimals (`350000,00`) into exact two-decimal `Decimal` objects (`ROUND_HALF_UP`).
   - **Title Mapping & Quarantine:** Matches unstructured VGen, Fiverr, and PayPal titles case-insensitively against `project_title_map.csv`. All **`11` unmatched out-of-scope orders** (`4` VGen + `4` Fiverr + `3` PayPal) are routed to `stg.etl_rejects` with source, ID, and rejection reason—and any child rows referencing a quarantined parent order are prevented from becoming orphans.
   - **Atomic Event Explosion & Lineage Keys:** Explodes every transaction into individual financial events. Root sales receive `transaction_code = <PLATFORM>-<order_id>-SALE` and `parent_transaction_code = NULL`; child fees, tips, refunds, and fee reversals receive deterministic suffixes (`-PFEE`, `-PRCFEE`, `-TIP1`, `-TIP2`, `-REF`, `-FREV`) and `parent_transaction_code` pointing to their root `SALE`.
   - **Binary-Search Weekend FX Fallback (`FXResolver`):** Looks up `(tx_date, currency_code)` in `fx_rates.csv`. When a sale, tip, or refund lands on a Saturday, Sunday, or ECB bank holiday (`1,717` non-IDR event lookups across the run), `bisect_right` resolves the most recent published business day prior to `tx_date` in $O(\log N)$ time, then computes `amount_idr = ROUND(amount_orig * rate, 2)`.
3. **Full-Refresh Load → `edw` & `mart`:**
   - Drops dependent views first (`01_ddl_edw.sql`), drops `fact_revenue_event` before `dim_*`, recreates all 6 tables, loads dimensions first, sorts events deterministically by `(date_key, transaction_code)` before assigning `revenue_event_sk = 1..5911`, inserts facts, and builds `edw.v_fact_enriched` + the 4 `mart.*` views (`02_mart_views.sql`).
   - **Important Sign-Algebra Fix in `02_mart_views.sql` & `query_builder.py`:** Because `platform_fees_idr`, `processing_fees_idr`, and `refunds_idr` are stored as **negative** numbers while `fee_reversals_idr` is **positive**, net revenue erosion is computed as `-(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr)`. For example, on a `100` sale with `-30` fee, `-10` refund, and `+3` fee reversal, leakage is `-((-30) + (-10) + (+3)) = +37`, so `Gross (100) - Leakage (37) = Net ex-tips (63)` reconciles to the exact Rupiah!

---

### Phase 4 — Validation Suite Results (`V1`–`V14`)

Executed via `.\.venv\Scripts\python.exe src\validate.py` (`0` failures):

| ID | Category | Check Description | Actual Result | Expected | Status |
|---|---|---|---|---|---|
| **V1** | Informational | Row counts across `stg` / `edw` / `mart` layers | `5,911 fact rows` | Info summary | **INFO** |
| **V2** | Integrity | Orphan foreign keys in `fact_revenue_event` (all 5 dims) | `0` | `= 0` | **PASS** |
| **V3** | Business Rule | Event sign constraint violations (`+` vs `−`) | `0` | `= 0` | **PASS** |
| **V4** | Integrity | Duplicate `transaction_code` (`<<DD>>`) | `0` | `= 0` | **PASS** |
| **V5** | Business Rule | Total refunds per parent exceed root sale amount | `0` | `= 0` | **PASS** |
| **V6** | Lineage | Invalid `parent_transaction_code` (NULL on root SALE, valid SALE on children) | `0` | `= 0` | **PASS** |
| **V7** | Grain | Multi-tip orders preserved as distinct atomic rows (`>= 2` tips) | `33` parents | `> 0` | **PASS** |
| **V8** | Domain Rule | Invalid `revenue_stream × platform` combinations | `0` | `= 0` | **PASS** |
| **V9** | Domain Rule | `revenue_stream` mismatches `dim_project.project_type` | `0` | `= 0` | **PASS** |
| **V10** | Calculation | Currency conversion math (`ABS(amount_idr - ROUND(orig * fx, 2)) > 0.01`) | `0` | `= 0` | **PASS** |
| **V11** | ETL Fallback | Foreign-currency weekend events resolved via prior business day | `1,615` (`0` bad) | `> 0 & 0 bad` | **PASS** |
| **V12** | Business Rule | Payment processing fees reversed on refund (must never happen) | `0` | `= 0` | **PASS** |
| **V13** | Governance | PII columns (`email`, `username`, `payer_name`, `buyer`) in `edw` / `mart` | `0` | `= 0` | **PASS** |
| **V14** | Informational | Unmatched commission rows quarantined in `stg.etl_rejects` | `11 rows` | Info (`>0` demo) | **INFO** |

---

### Phase 5 — Streamlit No-Code OLAP Front End (`app/app.py`)

Designed for two simultaneous audiences in your classroom defense—a **Business Reviewer (20%)** who shouldn't have to write SQL, and a **Technical DW Reviewer (20%)** who wants proof that real Star Schema queries are executing underneath:

1. **Tab 1 — `Antarmuka Kueri Mandiri (Tanpa Kode)` (`app/query_builder.py`):**
   - Users pick **0–3 Group By attributes** (`Tahun`, `Kuartal`, `Bulan`, `Aliran Pendapatan`, `Platform`, `Proyek`, `Bidang Produksi`, `Mata Uang`, `Jenis Peristiwa`, `Kategori Hari Weekend/Weekday`), **1+ Measures**, optional **Filters** populated live from `edw.dim_*`, **Sort order**, and **Top N limit**.
   - **SQL Injection & Cross-Currency Safety:** Column and measure expressions come strictly from frozen Python whitelists (`DIMENSIONS` and `MEASURES`), while every user filter value is bound via DuckDB positional `?` parameters. Moreover, `Nilai Mata Uang Asal` (`SUM(amount_orig)`) and `Rata-rata Kurs ke IDR` are **locked in both the UI and backend** unless `Mata Uang (Currency)` is selected in *Group By*, making it impossible to accidentally sum Japanese Yen with US Dollars.
   - Renders formatted IDR/percentage columns, a dynamic Plotly chart (line chart when grouped by time, grouped bar chart otherwise), CSV export, and the **"Lihat SQL yang dijalankan"** expander showing both the executed SQL and bound parameters.
2. **Tab 2 — `Empat Pertanyaan Bisnis Utama`:**
   - Four one-click sub-tabs querying `mart.v_revenue_monthly`, `mart.v_project_performance`, `mart.v_fee_refund_leakage`, and `mart.v_fx_exposure` directly, complete with interactive Plotly visuals (stacked monthly area trend, project & production-field comparison bars, platform gross-vs-leakage-vs-net comparison, and currency share donut + historical FX trend selector) and collapsible SQL inspection.
3. **Tab 3 — `Arsitektur & Validasi DW`:**
   - Shows the `stg → edw → mart` pipeline summary, KPI cards from `report/etl_last_run.json`, the live `V1`–`V14` validation query output, and the live `stg.etl_rejects` table showing all 11 quarantined titles and why they were rejected.

---

## 5. Snapshot of Warehouse Numbers (Saved in `report/findings_raw.md`)

Across `5,911` atomic events (`2025-01-01` – `2026-10-31`):
- **Gross Sales:** `Rp 1,567,043,585` | **Tips:** `+Rp 47,668,387` | **Platform Fees:** `-Rp 175,851,494` | **Processing Fees:** `-Rp 38,300,523` | **Refunds:** `-Rp 88,002,460` | **Fee Reversals:** `+Rp 10,524,992` → **Net Revenue:** **`Rp 1,323,082,489`**.
- **By Stream (Net):** Komisi Klien `Rp 1,098.27M` (`83.01%`), Penjualan Gim Video `Rp 128.98M` (`9.75%`), Penjualan Aset Digital `Rp 95.82M` (`7.24%`).
- **By Platform Leakage (`% of Gross Sales eroded by fees + net refunds`):**
  - **Steam:** `34.61%` (`Rp 153.22M` gross → `Rp 100.19M` net)
  - **Fiverr:** `25.94%` (`Rp 463.08M` gross → `Rp 361.87M` net incl. tips)
  - **itch.io:** `18.29%` (`Rp 108.72M` gross → `Rp 92.28M` net)
  - **VGen:** `13.39%` (`Rp 451.36M` gross → `Rp 406.21M` net incl. tips)
  - **Direct PayPal:** `9.77%` (`Rp 390.66M` gross → `Rp 362.53M` net incl. tips; `Rp 0` fee reversal on refunds)
- **By Currency Share of Net IDR:** `USD` `58.42%`, `SGD` `11.51%`, `EUR` `11.43%`, `JPY` `6.07%`, `GBP` `5.80%`, `IDR` `4.62%`, `CNY` `2.16%` (**`95.38%` foreign-currency exposure**).

---

## 6. What Remains for Tomorrow (Wednesday, 25 Nov — Phases 6–8)

1. **Phase 6 (Diagrams & App Screenshots):** Generate the 5 PlantUML architecture/ETL/tunnel/JSON/storage diagrams in `diagrams/` and capture screenshots of the running Streamlit app into `report/screenshots/`.
2. **Phase 7 (Report Completion):** Copy `BI-Design-Template.docx` → `report/UTS_BI_Sebastian_Wasaka_DW.docx` (leaving the original untouched), delete line 2's template disclaimer banner, remove `Stripe` mentions, fix `parent_transaction_code` `<<DD>>` and `original_amount` typos, replace Bang Ham's example images/tables/Rp 10B budget, and paste the Wasaka sections + findings from `report/findings_raw.md`.
3. **Phase 8 (Demo & Reviewer Q&A Prep):** Write `report/qa_prep.md` and rehearse the 15-minute live walkthrough once.
4. **TBA Follow-ups (when lecturer announces):** Clarify *"Dua penilaian peer-review"* and exact e-learning upload deadline.
