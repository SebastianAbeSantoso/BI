# Raw Analytical Findings (Phase 5b Output for Phase 7 Report)

> **Important framing note for the UTS report:** Because platform transaction events are synthetic (modelled on published fee rules and real ECB exchange rates), phrase these in Section 9 (*Business Findings*) as **"Data Warehouse memungkinkan manajemen Wasaka Interactive untuk mengidentifikasi..."** rather than claiming real historical company profits.

## Overall Warehouse Totals (`2025-01-01` – `2026-10-31`)
- **Total Atomic Fact Events (`edw.fact_revenue_event`):** `5,911` rows (`2,295` `SALE`, `2,203` `PLATFORM_FEE`, `948` `PROCESSING_FEE`, `197` `TIP`, `138` `REFUND`, `130` `FEE_REVERSAL`)
- **Gross Sales (`SALE`):** `Rp 1,567,043,585.23`
- **Client & Storefront Tips (`TIP`):** `Rp 47,668,387.47`
- **Platform Fees (`PLATFORM_FEE`):** `-Rp 175,851,493.86`
- **Payment Processing Fees (`PROCESSING_FEE`):** `-Rp 38,300,522.52`
- **Refunds (`REFUND`):** `-Rp 88,002,459.66`
- **Platform Fee Reversals on Refund (`FEE_REVERSAL`):** `+Rp 10,524,992.39`
- **Total Net Revenue (`SUM(amount_idr)`):** `Rp 1,323,082,489.05`

---

## Finding 1 — Revenue Mix & Seasonality (Answers Business Question 1)
- **Observation:** Across the 22-month window, **Komisi Klien** contributes `Rp 1,098,273,990.58` (`83.01%` of net revenue) with steady monthly cashflow, **Penjualan Gim Video** contributes `Rp 128,983,832.44` (`9.75%`) concentrated heavily around mid-year (June–July) and year-end (November–December) storefront sale windows, and **Penjualan Aset Digital** contributes `Rp 95,824,666.03` (`7.24%`).
- **Decision value:** Separating recurring service cashflow (commissions + asset packs) from seasonal game storefront spikes lets Wasaka Interactive schedule full-game development sprints without misreading seasonal game troughs as studio-wide decline.

## Finding 2 — Project & Production Field Comparison After Deductions (Answers Business Question 2)
- **Observation:** Comparing all 6 production fields on *net* rather than *gross* revenue reveals sharp margin differences:
  - `Programming & Tech` (`COM-SHDR` + `AST-BATK`): `Rp 369.04M` net (`16.42%` leakage)
  - `Audio & Music` (`COM-MUSC` + `AST-RHYT`): `Rp 303.61M` net (`17.75%` leakage)
  - `2D Illustration` (`COM-ILLU`): `Rp 270.49M` net (`16.39%` leakage)
  - `Pixel Art & UI` (`COM-PXUI` + `AST-DGPX`): `Rp 224.42M` net (`16.50%` leakage)
  - `Full Game Dev` (*A Match Made in Dungeon*, *R\*bert*, *Personal Space*, *Canting Cloth*): `Rp 187.74M` gross → `Rp 128.98M` net (**`32.17%` leakage**, almost double non-game fields due to Steam's 30% cut + refunds).
  - `3D Modeling` (`AST-ISOR`): `Rp 26.54M` net (`16.29%` leakage).
- **Decision value:** Judging projects purely by gross revenue overstates `Full Game Dev` cash contribution by nearly a third relative to custom commissions and asset packs.

## Finding 3 — Platform Fee Drag & Non-Refundable Processing Fee Asymmetry (Answers Business Question 3)
- **Observation:** Total gross revenue erosion (`-(platform_fees + processing_fees + refunds + fee_reversals) / gross_sales`) varies more than **3.5×** across channels:
  1. **Steam:** `34.61%` leakage (`Rp 153.22M` gross → `Rp 100.19M` net; `-Rp 46.00M` platform fees, `-Rp 10.03M` refunds, `+Rp 3.01M` fee reversals).
  2. **Fiverr:** `25.94%` leakage (`Rp 463.08M` gross → `Rp 361.87M` net including `Rp 18.92M` tips; 20% fee applies to both orders and tips).
  3. **itch.io:** `18.29%` leakage (`Rp 108.72M` gross → `Rp 92.28M` net; 10% platform share reversed on refund, `-Rp 5.93M` checkout processing fee kept by processor).
  4. **VGen:** `13.39%` leakage (`Rp 451.36M` gross → `Rp 406.21M` net; 5% platform fee + checkout processing).
  5. **Direct PayPal:** `9.77%` leakage (`Rp 390.66M` gross → `Rp 362.53M` net; `0%` platform cut, `-Rp 17.98M` processing fees, and `Rp 0` fee reversal across `-Rp 20.17M` refunds).
- **Decision value:** Routing repeat commission clients from Fiverr (`25.94%` leakage) to **VGen** (`13.39%`) or **Direct PayPal** (`9.77%`) preserves `12–16` percentage points of gross revenue, while tracking `PROCESSING_FEE` separately exposes sunk gateway costs on refunded PayPal/VGen/itch.io orders.

## Finding 4 — Foreign-Exchange Concentration & Spot-Rate Variance (Answers Business Question 4)
- **Observation:** **`95.38%`** of studio net revenue originates in foreign currencies (`USD` `58.42%`, `SGD` `11.51%`, `EUR` `11.43%`, `JPY` `6.07%`, `GBP` `5.80%`, `CNY` `2.16%`), while domestic `IDR` accounts for only `4.62%` (`Rp 61.09M`). Across real ECB reference rates in 2025–2026:
  - `USD/IDR` ranged from `Rp 16,104.40` to `Rp 18,176.40` (a `~12.9%` swing)
  - `EUR/IDR` ranged from `Rp 16,680.99` to `Rp 21,034.06`
  - `1,615` weekend foreign-currency events were valued accurately via prior-business-day spot fallback instead of month-end guesswork.
- **Decision value:** Because over half of net cashflow is USD-denominated and >95% is non-IDR, per-event spot FX conversion eliminates month-end spreadsheet distortion and shows when holding or converting foreign balances materially affects IDR treasury.
