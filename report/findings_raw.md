# Warehouse Numbers and Draft Findings (2025-01-01 to 2026-10-31)

Transaction records in this warehouse are synthetic, generated from published platform fee rules and combined with real ECB exchange rates. In Section 9 of the UTS report, frame these numbers as examples of what the warehouse allows management to measure, not as audited historical profits of a real company.

## Totals across fact_revenue_event

The build loads 5,911 rows: 2,295 `SALE`, 2,203 `PLATFORM_FEE`, 948 `PROCESSING_FEE`, 197 `TIP`, 138 `REFUND`, and 130 `FEE_REVERSAL`.

| Metric | Total (IDR) |
|---|---|
| Gross sales (`SALE`) | 1,567,043,585.23 |
| Tips (`TIP`) | 47,668,387.47 |
| Platform fees (`PLATFORM_FEE`) | -175,851,493.86 |
| Processing fees (`PROCESSING_FEE`) | -38,300,522.52 |
| Refunds (`REFUND`) | -88,002,459.66 |
| Fee reversals (`FEE_REVERSAL`) | 10,524,992.39 |
| Net revenue (`SUM(amount_idr)`) | 1,323,082,489.05 |

## Q1: Revenue mix and monthly trend

Komisi Klien brings in Rp 1,098,273,990.58 net (83.01% of total net revenue) with relatively steady monthly inflow. Penjualan Gim Video brings in Rp 128,983,832.44 (9.75%) and clusters heavily around June, July, November, and December sale windows. Penjualan Aset Digital adds Rp 95,824,666.03 (7.24%).

Separating the three streams lets studio management see how steady commission and asset income covers quiet months between game sale periods.

## Q2: Project and production field comparison

Looking at net revenue after deductions changes how the six production fields rank compared with gross numbers:

| Production field | Gross (IDR) | Net (IDR) | Net leakage (IDR) | Leakage % |
|---|---:|---:|---:|---:|
| Programming & Tech | 427,306,223.50 | 369,038,898.40 | 70,176,683.56 | 16.42% |
| Audio & Music | 349,829,310.35 | 303,612,681.10 | 62,089,401.34 | 17.75% |
| 2D Illustration | 313,925,761.39 | 270,489,415.04 | 51,466,592.17 | 16.39% |
| Pixel Art & UI | 257,248,584.91 | 224,417,518.37 | 42,452,430.96 | 16.50% |
| Full Game Dev | 187,741,560.89 | 128,983,832.44 | 60,397,147.09 | 32.17% |
| 3D Modeling | 30,992,144.19 | 26,540,143.70 | 5,047,228.53 | 16.29% |

Full Game Dev (*A Match Made in Dungeon*, *R\*bert*, *Personal Space*, and *Canting Cloth*) loses 32.17% of gross sales to platform cuts and refunds, almost twice the rate of the other five fields.

## Q3: Fee and refund erosion by platform

Leakage percentage (`-(platform_fees + processing_fees + refunds + fee_reversals) / gross_sales`) varies widely by channel:

| Platform | Gross (IDR) | Platform fees | Processing fees | Refunds | Reversals | Net (IDR) | Leakage % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Steam | 153,217,395.68 | -46,004,389.69 | 0.00 | -10,030,834.67 | 3,012,171.58 | 100,194,342.90 | 34.61% |
| Fiverr | 463,084,388.59 | -96,400,657.47 | 0.00 | -29,675,499.65 | 5,935,107.39 | 361,866,500.21 | 25.94% |
| itch.io | 108,720,672.50 | -10,877,187.36 | -5,926,743.47 | -3,418,585.73 | 342,265.56 | 92,279,843.89 | 18.29% |
| VGen | 451,364,953.53 | -22,569,259.34 | -14,390,614.76 | -24,704,741.16 | 1,235,447.86 | 406,213,178.37 | 13.39% |
| Direct PayPal | 390,656,174.93 | 0.00 | -17,983,164.29 | -20,172,798.45 | 0.00 | 362,528,623.68 | 9.77% |

Moving repeat commission clients off Fiverr (25.94% erosion) onto VGen (13.39%) or Direct PayPal (9.77%) retains roughly 12 to 16 percentage points more of gross revenue. Separating `PROCESSING_FEE` from `PLATFORM_FEE` also shows the unrecovered gateway fees on PayPal, VGen, and itch.io refunds.

## Q4: Foreign currency exposure

Foreign currencies make up 95.38% of net revenue in IDR:

| Currency | Net original | Net IDR | Mean rate | Min rate | Max rate | Share % |
|---|---:|---:|---:|---:|---:|---:|
| USD | 45,656.25 | 772,898,125.18 | 16,927.24 | 16,104.40 | 18,176.40 | 58.42% |
| SGD | 11,521.53 | 152,316,587.65 | 13,099.17 | 11,961.57 | 14,196.31 | 11.51% |
| EUR | 7,751.34 | 151,247,125.81 | 19,344.92 | 16,680.99 | 21,034.06 | 11.43% |
| JPY | 725,332.55 | 80,253,192.43 | 110.35 | 102.43 | 118.30 | 6.07% |
| GBP | 3,454.40 | 76,696,500.39 | 22,505.83 | 19,823.56 | 24,335.68 | 5.80% |
| IDR | 61,087,618.80 | 61,087,618.80 | 1.00 | 1.00 | 1.00 | 4.62% |
| CNY | 11,550.15 | 28,583,338.79 | 2,422.68 | 2,216.22 | 2,677.33 | 2.16% |

USD/IDR moved between Rp 16,104.40 and Rp 18,176.40 across the 2025 to 2026 ECB series, and EUR/IDR moved between Rp 16,680.99 and Rp 21,034.06. Valuing each transaction at its event-date rate (with 1,615 weekend foreign-currency events resolved to the prior business day) removes the distortion of applying one guessed rate at month end.
