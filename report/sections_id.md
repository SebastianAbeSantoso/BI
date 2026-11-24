# Naskah Lengkap Laporan UTS Data Warehouse Wasaka Interactive

Dokumen ini menjadi sumber teks berbahasa Indonesia untuk seluruh bagian pada `report/UTS_BI_Sebastian_Wasaka_DW.docx`.

## Bagian Depan (Validation Page & Revision History)

- Prepared By: Sebastian Abe Santoso, tanggal 25/11/2026
- Reviewed By: Irham Maulani
- Approved By: Irham Maulani
- Revision History baris 1.0: Irham Maulani, 24 September 2024, 15 halaman, Design Data Warehouse, Irham Maulani 24 September 2024
- Revision History baris 1.1: Sebastian Abe Santoso, 25 November 2026, Implementasi DW, ETL, OLAP Front End, dan Validasi Wasaka Interactive, Irham Maulani

## 1. Pendahuluan

### 1.1 Latar Belakang Singkat dan Alur Bisnis

Wasaka Interactive adalah sebuah studio pengembangan gim independen (indie game studio) dan produksi kreatif digital yang beroperasi di Indonesia. Berbeda dengan perusahaan penerbit gim berskala besar yang hanya bergantung pada satu produk utama, proses bisnis (business flow) Wasaka Interactive bertumpu pada tiga aliran pendapatan (revenue streams) lintas disiplin produksi (full game development, 2D illustration, pixel art dan UI, 3D modeling, audio dan music, serta programming dan tech), yaitu:

- Penjualan Gim Video (Video Game Sales): Distribusi produk gim komersial secara langsung kepada konsumen global melalui platform digital storefront seperti Steam dan itch.io.
- Penjualan Aset Digital (Digital Asset Sales): Komersialisasi paket aset siap pakai (sprite sheets, UI packs, 3D low-poly models, dan audio packs) bagi sesama pengembang melalui itch.io dan VGen Shop.
- Komisi Klien (Client Commissions): Layanan pengerjaan proyek kustom berbasis pesanan maupun milestone (ilustrasi karakter, pembuatan custom shader, hingga aransemen musik gim) yang dipasarkan melalui VGen, Fiverr, serta transaksi langsung antar-klien melalui Direct PayPal.

Permasalahan utama yang dihadapi oleh studio adalah fragmentasi data pendapatan dan ketidakkonsistenan struktur pencatatan keuangan di setiap kanal distribusi. Setiap platform menghasilkan laporan transaksi dalam format yang berbeda, menerapkan struktur pemotongan biaya yang beragam (mulai dari potongan komisi platform seperti 30% pada Steam dan 20% pada Fiverr, hingga biaya pemrosesan pembayaran pada PayPal, itch.io, dan VGen), serta memiliki mekanisme pengembalian dana (refund) yang dapat terjadi di periode waktu berbeda dari tanggal transaksi awal. Selain itu, transaksi masuk tercatat dalam tujuh mata uang asing dan lokal (IDR, USD, SGD, JPY, CNY, EUR, dan GBP), sehingga menyulitkan pihak manajemen studio dalam mengevaluasi pendapatan bersih (net revenue) yang sebenarnya diterima dalam nilai Rupiah (IDR).

Tujuan utama dari perancangan dokumen ini adalah membangun Data Warehouse Pendapatan Studio Indie berbasis metodologi Kimball (Star Schema) yang mengonsolidasikan seluruh catatan peristiwa keuangan (revenue events) ke dalam satu repositori analitis terpadu. Desain ini menyelesaikan permasalahan bisnis studio dengan menstandardisasi pencatatan penjualan kotor (gross sale), potongan platform (platform fee), biaya pemrosesan pembayaran (processing fee), pengembalian dana (refund), dan pembalikan biaya (fee reversal) pada tingkat granularitas peristiwa transaksi (event-level grain). Melalui integrasi data kurs mata uang historis ke dalam tabel fakta terpusat (`fact_revenue_event`), rancangan ini memungkinkan studio menganalisis kontribusi tiap aliran pendapatan, memantau tren bulanan dan kuartalan, mengukur kinerja tiap proyek dan bidang produksi (production field), serta mengevaluasi dampak potongan biaya platform dan fluktuasi nilai tukar secara akurat.

### 1.2 Referensi

1. Kimball, R., & Ross, M. (2013). The Data Warehouse Toolkit: The Complete Guide to Dimensional Modeling (3rd ed.). John Wiley & Sons.
2. Inmon, W. H. (2005). Building the Data Warehouse (4th ed.). John Wiley & Sons.
3. Golfarelli, M., & Rizzi, S. (2009). Data Warehouse Design: Modern Principles and Methodologies. McGraw-Hill Education.
4. Vaisman, A., & Zimanyi, E. (2014). Data Warehouse Systems: Design and Implementation. Springer-Verlag Berlin Heidelberg.
5. Dokumentasi Skema Pelaporan Keuangan Platform Eksternal & API Nilai Tukar: Steamworks Financial Reporting Guide, itch.io Creator Payout Export Format, VGen Help Center Fee Structure, Fiverr Seller Terms, PayPal Indonesia Merchant Commercial Fees, dan European Central Bank Reference Rates via Frankfurter API.
6. DuckDB Documentation (2026). SQL, Constraints, and Columnar Analytical Storage.
7. Streamlit & Plotly Documentation (2026). Interactive Web Front End for Data Applications.

### 1.3 Definisi dan Istilah Teknis

- Data Warehouse (DW): Repositori data terpusat yang bersifat subject-oriented, integrated, time-variant, dan non-volatile untuk mendukung analisis dan pengambilan keputusan bisnis.
- Kimball Dimensional Modeling: Metodologi perancangan data warehouse yang berfokus pada proses bisnis dengan menyusun tabel fakta berisi metrik terukur dan tabel dimensi berisi konteks deskriptif.
- Star Schema: Struktur skema relasional di mana satu tabel fakta terpusat terhubung langsung ke beberapa tabel dimensi yang didenormalisasi.
- Fact Table (`fact_revenue_event`): Tabel pusat dalam Star Schema yang menyimpan ukuran kuantitatif (`amount_orig`, `exchange_rate_to_idr`, `amount_idr`) beserta foreign key ke lima tabel dimensi.
- Dimension Table (`dim_*`): Tabel pendamping berisi atribut deskriptif (`dim_date`, `dim_project`, `dim_platform`, `dim_currency`, `dim_revenue_stream`) untuk pemfilteran dan pengelompokan data fakta.
- Grain (Granularitas): Tingkat detail paling atomik dari satu baris tabel fakta. Pada sistem ini, satu baris merepresentasikan satu peristiwa keuangan tunggal.
- Surrogate Key (`<<PK>>`): Kunci utama buatan bertipe integer/bigint yang dibangkitkan di warehouse agar independen dari sistem sumber.
- Natural Key (`<<NK>>`): Pengidentifikasi bisnis asli dari sumber (misalnya `project_code` atau kode ISO `currency_code`).
- Degenerate Dimension (`<<DD>>`): Pengidentifikasi transaksi operasional (`transaction_code`) yang disimpan langsung pada tabel fakta tanpa tabel dimensi tersendiri.
- Lineage Key (`parent_transaction_code`): Kunci referensi operasional yang menautkan biaya, tip, refund, dan pembalikan biaya kembali ke peristiwa `SALE` induknya; kolom ini sengaja tidak diberi tag `<<DD>>`.
- ETL (Extract, Transform, Load): Proses terstruktur untuk menarik data mentah dari sumber, membersihkan serta menyeragamkan format, lalu memuatnya ke dalam warehouse.
- Platform Fee vs. Processing Fee: Platform Fee adalah komisi bagi hasil pasar digital (Steam 30%, Fiverr 20%, itch.io 10%, VGen 5%), sedangkan Processing Fee adalah biaya gerbang pembayaran (PayPal, checkout itch.io, checkout VGen).
- Fee Reversal (`FEE_REVERSAL`): Pembalikan komisi platform yang dikembalikan ke kreator saat terjadi refund atau pembatalan order (bernilai positif), berbeda dengan processing fee yang tidak dikembalikan.
- Spot Exchange Rate: Nilai tukar mata uang asing terhadap Rupiah (IDR) pada tanggal peristiwa transaksi (`exchange_rate_to_idr`).
- Staging Area (`stg`) & Data Mart (`mart`): Skema `stg` menampung data mentah sementara termasuk kolom PII sebelum pembersihan; skema `mart` menyediakan view siap kueri per topik pertanyaan bisnis.
- OLAP (Online Analytical Processing): Mesin basis data dan antarmuka kueri berorientasi kolom (DuckDB dan Streamlit) untuk agregasi cepat terhadap Star Schema.
- Data Owner, Data Steward, Data Provider, Custodian: Pembagian peran tata kelola data: pihak penanggung jawab bisnis (Owner), penjaga kualitas dan aturan (Steward), penyedia ekspor eksternal (Provider), serta pengelola teknis sistem (Custodian).
- Full Refresh: Strategi pemuatan ulang penuh yang membangun kembali tabel dimensi, tabel fakta, dan view dari awal pada tiap eksekusi ETL agar hasil selalu konsisten dan idempoten.

### 1.4 Batasan Desain dan Implementasi

1. Tidak tersedianya akses API transaksi langsung pada platform distribusi kreator: Steamworks, VGen, Fiverr, itch.io, dan PayPal diekstrak melalui berkas ekspor penyelesaian (CSV/JSON) yang dibaca dari direktori berkas lokal (File System Reader).
2. Ketidakteraturan pengidentifikasi proyek pada laporan platform: ekspor Fiverr, VGen, dan PayPal hanya memuat judul pesanan teks bebas tanpa `project_code`, sehingga tahap Transform menggunakan kamus pencocokan teks (`project_title_map.csv`) dan mengirim judul tak dikenal ke tabel karantina `stg.etl_rejects`.
3. Keterbatasan publikasi kurs pada akhir pekan dan hari libur bank internasional: API Frankfurter (kurs referensi ECB) tidak menerbitkan kurs pada hari Sabtu, Minggu, dan hari libur bank seperti 1 Januari. Tahap Transform menerapkan fallback ke kurs hari kerja terakhir sebelumnya (`last known business day`).
4. Penyederhanaan arsitektur penyimpanan lokal: rancangan bertingkat (`STG_DB`, `INT_DB`, `EDW_DB`, `MART_DB`) dijalankan dalam satu berkas DuckDB lokal (`data/warehouse.duckdb`) menggunakan pemisahan skema logis `stg`, `edw`, dan `mart`, dengan logika integrasi (`INT`) ditempatkan di skrip Transform Python dan view SQL.
5. Keterbukaan data transaksi sintetis: seluruh catatan transaksi penjualan, tip, biaya, dan refund pada `data/raw/` (`2025-01-01` sampai `2026-10-31`) merupakan data sintetis yang dibangkitkan secara deterministik berdasarkan aturan tarif resmi platform, dipadukan dengan data kurs historis riil ECB (474 hari kerja, `2024-12-20` sampai `2026-10-30`) melalui Frankfurter API.
6. Penerapan satu pengguna lokal: aplikasi Streamlit berjalan di mesin lokal dalam mode baca-saja tanpa fitur login atau pembagian hak akses berbasis peran (RBAC); pengendalian akses multi-pengguna dicatat sebagai pengembangan lanjutan.

## 2. Konteks Organisasi dan Ruang Lingkup

### 2.1 Profil Organisasi, Permasalahan Pelaporan, dan Struktur Fungsi

Wasaka Interactive menjalankan model bisnis hibrida lintas enam bidang produksi (Full Game Dev, 2D Illustration, Pixel Art & UI, 3D Modeling, Audio & Music, serta Programming & Tech) pada tiga aliran pendapatan: penjualan gim video (Steam, itch.io), penjualan aset digital (itch.io, VGen), dan komisi klien (VGen, Fiverr, Direct PayPal).

Sebelum adanya Data Warehouse, pelaporan keuangan mengalami tiga kendala utama:
1. Silo data antar-platform karena tiap kanal ekspor memakai struktur kolom, format tanggal, dan penulisan angka yang berbeda.
2. Distorsi pendapatan bersih (Net Revenue Blindness) karena pencatatan manual mencampur nilai kotor dan bersih serta melewatkan fakta bahwa biaya pemrosesan pembayaran (processing fee) tidak kembali saat refund.
3. Ketidakakuratan konversi multi-mata uang karena rekap akhir bulan memakai kurs tebakan rata-rata bulanan alih-alih kurs historis pada tanggal transaksi.

Struktur organisasi terdiri atas lima fungsi utama:
1. Studio Lead / Executive Management: penentu strategi studio, alokasi tenaga proyek, dan evaluasi bisnis.
2. Game & Digital Asset Production Division: tim teknis dan artistik pengembang gim dan paket aset.
3. Commission & Client Relations Division: pengelola pesanan komisi kustom, milestone, dan pemetaan judul pesanan.
4. Finance & Administration Division: pengelola arus kas, aturan tanda akuntansi, rekonsiliasi payout, dan konversi mata uang.
5. IT & Data Engineering Function: pengelola berkas warehouse DuckDB, skrip ETL, validasi data, dan antarmuka kueri Streamlit.

Sebagai Data Engineer, solusi yang dibangun adalah arsitektur Data Warehouse Kimball (Star Schema) dengan pipa ETL semi-otomatis berbasis berkas ekspor dan API kurs yang mengekstraksi data internal maupun eksternal, mengubah setiap transaksi menjadi peristiwa atomik pada `fact_revenue_event`, dan menyajikannya melalui aplikasi kueri tanpa kode.

### 2.2 Tujuan Dokumen

Dokumen ini menjadi panduan teknis dan fungsional lengkap untuk perancangan, implementasi, pengujian integritas, dan pemeliharaan Data Warehouse pendapatan Wasaka Interactive, mulai dari pendefinisian masalah bisnis, tata kelola kepemilikan data, pemodelan Star Schema, implementasi pipa ETL dan DuckDB, hingga demonstrasi kueri OLAP serta temuan bisnis.

### 2.3 Ruang Lingkup Proyek

Cakupan proyek (In-Scope) meliputi pengumpulan dan integrasi data pendapatan dari lima platform eksternal (Steam, itch.io, VGen, Fiverr, Direct PayPal), tiga aliran pendapatan, 12 proyek portofolio pada enam bidang produksi, tujuh mata uang (IDR, USD, SGD, JPY, CNY, EUR, GBP), pembangunan tiga skema DuckDB (`stg`, `edw`, `mart`), pengujian otomatis 14 aturan kualitas data (V1 sampai V14), dan antarmuka kueri Streamlit tanpa menulis SQL untuk menjawab empat pertanyaan bisnis utama.

Hal di luar cakupan (Out-of-Scope) meliputi pencatatan biaya operasional studio (gaji, sewa, pajak, lisensi perangkat lunak), perhitungan laba bersih (profitability), pemrosesan streaming real-time, integrasi API berbayar ke platform tertutup, model prediksi machine learning, serta sistem login multi-pengguna.

## 3. Kebutuhan Bisnis dan Tata Kelola Data

### 3.1 Permasalahan Bisnis dan Solusi Data Warehouse

| Permasalahan Bisnis | Dampak bagi Studio | Solusi Data Warehouse | Luaran Terukur & Pertanyaan Bisnis |
|---|---|---|---|
| Data transaksi tersebar di 5 format ekspor berbeda (CSV US, CSV angka berformat teks, JSON bertingkat, CSV duplikat, CSV koma desimal). | Rekonsiliasi laporan bulanan lambat dan rawan salah salin. | Pipa ETL menyeragamkan tanggal, angka desimal, deduplikasi baris, dan memuat semua kejadian ke `fact_revenue_event`. | Satu sumber kebenaran `5,911` baris peristiwa atomik tervalidasi (`V1-V14`). |
| Pencatatan manual mencampur nilai kotor dan bersih, serta tidak memisahkan fee reversal dari processing fee yang hangus saat refund. | Manajemen melebih-lebihkan pendapatan bersih pada kanal berbiaya tinggi. | Pemecahan setiap transaksi menjadi baris `SALE`, `TIP`, `PLATFORM_FEE`, `PROCESSING_FEE`, `REFUND`, dan `FEE_REVERSAL`. | Menjawab Q3: mengukur persentase erosi biaya dan refund per platform. |
| Rekap bulanan memakai kurs tebakan akhir bulan untuk 7 mata uang. | Selisih kurs antara catatan internal dan pencairan Rupiah asli di bank. | Integrasi kurs historis harian ECB per tanggal kejadian dengan fallback hari kerja terakhir untuk akhir pekan. | Menjawab Q4: memetakan porsi eksposur mata uang asing dan rentang kurs tiap bulan. |
| Sulit membandingkan hasil bersih antar proyek dan 6 bidang produksi karena struktur fee tiap kanal berbeda. | Keputusan alokasi jam kerja tim antara proyek gim, aset, dan komisi tidak berbasis bukti. | `dim_project` dan `dim_revenue_stream` digabungkan ke `mart.v_project_performance` dan `mart.v_revenue_monthly`. | Menjawab Q1 & Q2: tren pendapatan bulanan dan peringkat bersih 12 proyek serta 6 bidang produksi. |
| Pesanan komisi memakai judul bebas tanpa `project_code` dan memuat data pribadi klien (email/username). | Baris gagal dipetakan ke proyek dan risiko kebocoran data pribadi di lapisan analitik. | Kamus `project_title_map.csv` memetakan judul ke proyek, baris asing dikarantina ke `stg.etl_rejects`, dan 5 kolom PII dibuang di staging. | 11 baris asing tertangkap di karantina dan 0 kolom PII lolos ke `edw`/`mart` (`V13`). |

### 3.2 Pemangku Kepentingan dan Kepemilikan Data (Tata Kelola Data)

Tata kelola data memastikan setiap sumber memiliki penanggung jawab bisnis (Data Owner), penjaga aturan kualitas (Data Steward), sumber penyedia (Data Provider), pengelola infrastruktur (Custodian), serta konsumen laporan yang jelas.

| Domain Data | Data Owner (Akuntabel) | Data Steward (Kualitas & Aturan) | Data Provider / Sumber | Custodian (Teknis) | Konsumen Data | Catatan Tata Kelola |
|---|---|---|---|---|---|---|
| Penjualan gim, refund, biaya Steam | Studio Lead | Finance & Administration | Valve (Steamworks export) | IT & Data Engineering | Studio Lead, Finance | Studio pemilik catatan penjualan; Valve penyedia laporan |
| Payout gim & aset itch.io | Studio Lead | Finance & Administration | itch.io (payout CSV) | IT & Data Engineering | Studio Lead, Finance, Production | Kolom `buyer_email` dihapus saat staging |
| Aset, komisi, tip, refund VGen | Studio Lead | Commission & Client Relations (+ Finance) | VGen (JSON export) | IT & Data Engineering | Commission, Finance | Kolom `client_username` dihapus saat staging |
| Komisi dan tip Fiverr | Studio Lead | Commission & Client Relations | Fiverr (earnings CSV) | IT & Data Engineering | Commission, Finance | `buyer_username` dihapus; baris ekspor ganda dideduplikasi |
| Komisi langsung, tip, biaya PayPal | Studio Lead | Finance & Administration | PayPal (activity CSV) | IT & Data Engineering | Finance | PayPal dimodelkan sebagai platform komisi langsung; `payer_name` dan `payer_email` dihapus |
| Kurs historis harian | Finance & Administration | IT & Data Engineering | ECB via Frankfurter API | IT & Data Engineering | Finance, Studio Lead | Fallback hari kerja terakhir untuk Sabtu, Minggu, dan libur bank |
| Daftar master proyek & bidang produksi | Production Division | Production Division | `data/raw/projects.csv` | IT & Data Engineering | Seluruh divisi | Penetapan `project_code` dan `production_field` resmi |
| Kamus pemetaan judul komisi | Commission & Client Relations | Commission & Client Relations | `data/raw/project_title_map.csv` | IT & Data Engineering | ETL Pipeline | Baris tak cocok masuk `stg.etl_rejects` untuk ditinjau steward |
| Taksonomi aliran pendapatan & aturan tanda | Finance & Administration | Finance & Administration | Aturan akuntansi internal | IT & Data Engineering | Seluruh divisi | Menetapkan tanda `+` / `-` dan aturan batas refund |
| Warehouse DuckDB (`stg`/`edw`/`mart`) & aplikasi | Studio Lead | IT & Data Engineering | Internal | IT & Data Engineering | Seluruh divisi | Penerapan lokal satu pengguna; RBAC dicatat sebagai pekerjaan lanjutan |

Kebijakan Data Pribadi (PII): Seluruh pengidentifikasi personal dari berkas ekspor eksternal (`buyer_email`, `client_username`, `buyer_username`, `payer_name`, dan `payer_email`) hanya tersimpan sementara di lapisan `stg` dan dihapus di tahap Transform sebelum pemuatan ke `edw` dan `mart`. Pemeriksaan otomatis `V13` memverifikasi tidak ada satu pun kolom PII pada skema `edw` dan `mart`.

### 3.3 Rencana Anggaran

Berbeda dengan sistem korporasi besar, implementasi untuk skala studio indie memanfaatkan perangkat lunak open-source dan perangkat keras yang sudah dimiliki studio.

| Kategori | Item | Estimasi Biaya (IDR) | Keterangan |
|---|---|---|---|
| Perangkat Lunak | DuckDB, Python, pandas, Streamlit, Plotly, PlantUML | Rp 0 | Lisensi open-source gratis |
| API Eksternal | Frankfurter ECB Exchange Rate API | Rp 0 | Endpoint publik gratis tanpa kunci API berbayar |
| Infrastruktur Lokal | Laptop pengembangan lokal studio | Rp 0 (biaya tambahan) | Memanfaatkan perangkat keras yang sudah tersedia |
| Infrastruktur Opsional | VPS ringan untuk akses tim jarak jauh | Rp 150.000 / bulan (estimasi opsional) | Hanya diperlukan jika aplikasi dihosting online; implementasi UTS berjalan lokal |
| Tenaga Kerja | 1 Data Engineer paruh waktu (pengembangan & dokumentasi 24 jam) | Rp 1.800.000 - Rp 2.400.000 (estimasi internal) | Alokasi internal tim TI studio (asumsi tarif paruh waktu mahasiswa/junior engineer) |

### 3.4 Perangkat dan Teknologi

| Komponen | Teknologi | Fungsi dalam Sistem |
|---|---|---|
| Bahasa Pemrograman & ETL | Python 3.10+, pandas, Decimal | Ekstraksi CSV/JSON, penghapusan PII, deduplikasi, pemetaan judul, konversi kurs, dan pemuatan DuckDB |
| Pengambilan Kurs Eksternal | requests + Frankfurter REST API | Mengunduh kurs referensi harian ECB untuk 7 mata uang ke `data/raw/fx_rates.csv` |
| Data Warehouse & Mesin OLAP | DuckDB 2.0.1 | Penyimpanan kolom satu berkas (`stg`, `edw`, `mart`), penegakan PK/FK/UNIQUE/CHECK, dan eksekusi kueri agregasi |
| Antarmuka Pengguna & Visualisasi | Streamlit 1.67.0 + Plotly | Antarmuka kueri tanpa menulis SQL, dasbor 4 pertanyaan bisnis, dan panel validasi V1 sampai V14 |
| Dokumentasi & Diagram | PlantUML + python-docx + Playwright | Pembuatan diagram arsitektur/ETL, tangkapan layar aplikasi nyata, dan penyusunan dokumen desain |
| Kontrol Versi | Git | Pencatatan perubahan skrip ETL, SQL, dan aplikasi secara terstruktur |

## 4. Sumber Data

### 4.1 Sumber Data Internal

Data internal terdiri dari dua berkas CSV master yang dikelola langsung oleh tim produksi dan divisi komisi:

1. `data/raw/projects.csv` (12 baris proyek resmi milik Production Division):

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

2. `data/raw/project_title_map.csv` (21 aturan pencocokan substring tidak peka huruf besar/kecil yang dikelola Commission Division), misalnya `"character illustration"` -> `COM-ILLU`, `"pixel sprite"` -> `COM-PXUI`, `"custom shader"` -> `COM-SHDR`, `"synthv vocal"` -> `COM-MUSC`, dan `"batik shader"` -> `AST-BATK`.

### 4.2 Sumber Data Eksternal

| Berkas Sumber | Platform & Aliran | Jumlah Baris | Format Tanggal & Angka | Aturan Biaya & Refund | Kolom PII Dihapus |
|---|---|---|---|---|---|
| `steam_sales_report.csv` | Steam (GAME_SALES) | 1.297 baris | `MM/DD/YYYY`, desimal titik | Platform fee 30%; refund membalikkan fee (`FEE_REVERSAL`) | Tidak ada |
| `itch_payouts.csv` | itch.io (GAME_SALES, ASSET_SALES) | 517 baris | `YYYY-MM-DD`, teks mata uang (`$1,240.00`, `Rp 89,000`) | Platform share 10% (dikembalikan saat refund) + processing fee 2.9% + $0.30 (hangus) | `buyer_email` |
| `vgen_export.json` | VGen (ASSET_SALES, COMMISSION) | 257 order (JSON bertingkat) | ISO-8601 UTC (`2025-07-12T11:20:00Z`), array `tips[]` & `refunds[]` | Platform fee 5% (dikembalikan proporsional saat refund parsial/penuh) + processing fee 2.9% + $0.30 | `client_username` |
| `fiverr_earnings.csv` | Fiverr (COMMISSION) | 250 baris (15 duplikat disuntikkan) | `YYYY-MM-DD`, ledger datar `ORDER`, `TIP`, `CANCELLATION_*` | Komisi 20% pada order dan tip; dibalikkan saat pembatalan parsial/penuh | `buyer_username` |
| `paypal_activity.csv` | Direct PayPal (COMMISSION) | 189 baris | `DD/MM/YYYY`, header Indonesia, koma desimal (`350000,00`) di ~42% baris | Platform fee 0%; processing fee 3.40% (IDR) / 4.40% (valas) + fixed fee; tidak kembali saat refund | `payer_name`, `payer_email` |
| `fx_rates.csv` | Frankfurter ECB API | 3.318 baris (474 hari kerja riil) | `YYYY-MM-DD`, kurs silang 6 desimal terhadap IDR | Tidak memuat Sabtu, Minggu, dan libur bank (`2024-12-20` s.d. `2026-10-30`) | Tidak ada |

## 5. Perancangan dan Implementasi ETL

### 5.1 Proses Extract dan Tunnel Data

Skrip `src/etl.py` menggunakan File System Reader untuk membaca seluruh CSV/JSON dari `data/raw/` secara mentah (as-is) ke delapan tabel di skema `stg` (`stg.raw_steam`, `stg.raw_itch`, `stg.raw_vgen` dengan array tip dan refund diserialisasi sebagai teks JSON, `stg.raw_fiverr`, `stg.raw_paypal`, `stg.raw_fx_rates`, `stg.raw_projects`, dan `stg.raw_title_map`). Lapisan `stg` bersifat sementara agar bukti sumber asli tetap dapat diaudit tanpa mencemari skema analitik `edw`.

### 5.2 Penjadwalan

| Sumber Data | Frekuensi Ekspor dari Platform | Jadwal Pipeline yang Direkomendasikan | Implementasi saat UTS |
|---|---|---|---|
| `steam_sales_report.csv` | Bulanan setelah siklus penyelesaian Steamworks | Setiap tanggal 2 awal bulan (Windows Task Scheduler) | Eksekusi manual penuh via `src/etl.py` |
| `itch_payouts.csv` | Mingguan / per pencairan payout | Mingguan setiap Senin pagi | Eksekusi manual penuh via `src/etl.py` |
| `vgen_export.json`, `fiverr_earnings.csv`, `paypal_activity.csv` | Mingguan dari dasbor masing-masing | Mingguan setiap Senin pagi | Eksekusi manual penuh via `src/etl.py` |
| `fx_rates.csv` (Frankfurter API) | Harian (hari kerja ECB) | Harian pukul 06:00 WITA (di-cache lokal ke CSV) | Diambil via `src/fetch_fx.py` lalu disimpan ke `data/raw/` |

### 5.3 Proses Transform

| No. | Aturan Transformasi | Implementasi Teknis di `src/etl.py` | Hasil Terukur pada Run Terbaru |
|---|---|---|---|
| 1 | Penghapusan Kolom PII | Membuang 5 kolom identitas pembeli/pembayar sebelum transformasi | 0 kolom PII masuk ke `edw` / `mart` (`V13` PASS) |
| 2 | Deduplikasi Baris Sumber | Menghapus baris identik pada `fiverr_earnings.csv` | 15 baris duplikat dibersihkan |
| 3 | Normalisasi Tanggal | Mengonversi `MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`, dan ISO timestamp ke tipe `date` | Seluruh event terhubung ke `dim_date.date_key` |
| 4 | Pembersihan Angka & Mata Uang | Menghapus simbol `$`, `Rp`, `¥` dan mengonversi koma desimal (`350000,00`) ke `Decimal(18,2)` (`ROUND_HALF_UP`) | Presisi uang terjaga tanpa galat floating-point |
| 5 | Pemetaan Judul & Karantina | Mencocokkan judul komisi/aset ke `project_title_map.csv`; judul asing dikirim ke `stg.etl_rejects` beserta penolakan anak transaksinya | 11 baris dikarantina (`4` VGen, `4` Fiverr, `3` PayPal) |
| 6 | Ledakan Event Atomik & Aturan Tanda | Memecah setiap order menjadi baris `SALE`/`TIP`/`FEE_REVERSAL` (`> 0`) dan `PLATFORM_FEE`/`PROCESSING_FEE`/`REFUND` (`< 0`) | `5,911` baris fakta tervalidasi |
| 7 | Penetapan Kode Transaksi & Induk | Memberi `transaction_code` unik per event (`STM-...-SALE`, `-PFEE`, `-TIP1`, `-TIP2`) dan `parent_transaction_code` merujuk ke `SALE` induk (`NULL` pada `SALE`) | 33 order multi-tip tetap terpisah (`V7` PASS) |
| 8 | Batas Refund Parsial | Memastikan akumulasi refund per induk tidak melebihi nilai `SALE` induk dan biaya pemrosesan PayPal/itch/VGen tidak dibalikkan | 0 pelanggaran batas refund (`V5`, `V12` PASS) |
| 9 | Pencarian Kurs & Fallback Akhir Pekan | Binary search (`bisect_right`) pada `fx_rates.csv` untuk mengambil kurs hari kerja terakhir sebelum tanggal libur/akhir pekan | 1,717 pencarian fallback (termasuk 1 Jan 2025 ke 31 Des 2024) |
| 10 | Konversi & Pembulatan IDR | Menghitung `amount_idr = ROUND(amount_orig * exchange_rate_to_idr, 2)` | 0 baris meleset di atas Rp 0.01 (`V10` PASS) |

### 5.4 Proses Load

Tahap Load menerapkan strategi Full Refresh yang idempoten: pertama skrip menjatuhkan seluruh view di `mart` dan `edw`, menjatuhkan `fact_revenue_event` terlebih dulu baru kelima tabel dimensi untuk menghormati kendala Foreign Key, membangun ulang keenam tabel via `sql/01_ddl_edw.sql`, mengisi lima tabel dimensi, mengurutkan baris fakta secara deterministik berdasarkan `(date_key, transaction_code)` sebelum menetapkan `revenue_event_sk`, memasukkan seluruh 5,911 baris fakta dengan casting `DECIMAL`, dan terakhir membangun ulang view `edw.v_fact_enriched` beserta empat view `mart`. Pengujian dua kali berturut-turut menghasilkan jumlah baris yang identik di setiap tabel.

## 6. Arsitektur Skema dan Penyimpanan Data Warehouse

### 6.1 Arsitektur Data Warehouse

Sistem ini memilih arsitektur Kimball (bottom-up, berorientasi proses bisnis pendapatan, langsung membentuk Star Schema dan mart analitik) dibandingkan pendekatan Inmon (top-down 3NF korporasi penuh terlebih dulu). Untuk studio indie dengan tim kecil dan fokus langsung pada empat pertanyaan bisnis keuangan, pendekatan Kimball jauh lebih cepat diimplementasikan dan lebih mudah dikueri langsung oleh alat pelaporan tanpa join 3NF yang dalam.

### 6.2 Kode PlantUML dan Desain Star Schema

Catatan perbaikan skema: kolom nilai mata uang asal pada tabel `fact_revenue_event` bernama `amount_orig` (bukan `original_amount`). Kolom `transaction_code` berperan sebagai Degenerate Dimension (`<<DD>>`) dengan batasan `UNIQUE`, sedangkan `parent_transaction_code` berperan sebagai kunci garis keturunan (lineage key) operasional untuk menautkan biaya, refund, fee reversal, dan beberapa tip ke transaksi `SALE` induknya, dan sengaja tidak diberi label `<<DD>>`.

### 6.3 Desain Penyimpanan

Seluruh lapisan `stg`, `edw`, dan `mart` disimpan dalam satu berkas `data/warehouse.duckdb`. DuckDB menggunakan penyimpanan berbasis kolom (columnar storage) sehingga operasi agregasi (`SUM`, `COUNT`, `FILTER`) pada ribuan hingga jutaan baris peristiwa berjalan sangat cepat pada perangkat keras laptop lokal tanpa memerlukan daemon server basis data terpisah. Integritas data dijamin langsung oleh engine melalui `PRIMARY KEY`, 5 `FOREIGN KEY`, `UNIQUE(transaction_code)`, serta `CHECK` constraint pada `event_type`, tanda positif/negatif `amount_orig` dan `amount_idr`, serta `exchange_rate_to_idr > 0`.

## 7. Implementasi OLAP dan Aplikasi Antarmuka Kueri

Aplikasi front end dibangun menggunakan Streamlit (`app/app.py`) yang terhubung ke `data/warehouse.duckdb` dalam mode baca-saja (`read_only=True`). Aplikasi terdiri atas tiga tab utama:

1. Pembuat Kueri (`app/query_builder.py`): Antarmuka form terpandu bagi pengguna non-teknis untuk menyusun kueri SQL terhadap `edw.v_fact_enriched` tanpa mengetik kode. Pengguna memilih 0 sampai 3 atribut pengelompokan, metrik pengukuran, filter dropdown dari tabel dimensi, urutan, dan batas baris. Seluruh pilihan kolom dipetakan dari daftar putih (whitelist) tetap dan nilai filter diikat menggunakan parameter `?` DuckDB agar bebas SQL injection. Selain itu, metrik `Nilai Mata Uang Asal` (`SUM(amount_orig)`) dan `Rata-rata Kurs ke IDR` dikunci baik di UI maupun backend kecuali pengguna memilih `Mata Uang` sebagai pengelompokan, sehingga mencegah penjumlahan lintas mata uang seperti JPY + USD. Panel `Lihat SQL yang dijalankan` menampilkan SQL asli beserta parameternya.
2. Empat Pertanyaan Bisnis: Empat sub-tab satu klik yang langsung menjalankan kueri terhadap `mart.v_revenue_monthly`, `mart.v_project_performance`, `mart.v_fee_refund_leakage`, dan `mart.v_fx_exposure` lengkap dengan grafik Plotly dan tabel terformat.
3. Arsitektur & Validasi: Menampilkan ringkasan alur data, metrik telemetri hasil run ETL terakhir (`report/etl_last_run.json`), hasil lengkap 14 pemeriksaan `sql/03_validate.sql` secara langsung, serta daftar 11 baris karantina pada `stg.etl_rejects`.

## 8. Implementasi Kueri Analitik

Keempat pertanyaan bisnis dijalankan melalui kueri SQL berikut terhadap skema `mart`:

- Kueri Q1 (`mart.v_revenue_monthly`): mengagregasi `gross_sales_idr`, `tips_idr`, `net_revenue_idr`, dan `event_count` per `year_month` dan `revenue_stream_name` untuk memisahkan lonjakan musiman penjualan gim dari arus kas komisi bulanan.
- Kueri Q2 (`mart.v_project_performance`): mengurutkan 12 proyek dan 6 bidang produksi berdasarkan `net_revenue_idr`, `gross_sales_idr`, `net_leakage_idr`, dan `leakage_pct` agar kontribusi bersih antar bidang dapat dibandingkan secara adil.
- Kueri Q3 (`mart.v_fee_refund_leakage`): menghitung `gross_sales_idr`, `platform_fees_idr`, `processing_fees_idr`, `refunds_idr`, `fee_reversals_idr`, `net_leakage_idr`, dan `leakage_pct` per platform. Karena biaya dan refund bernilai negatif sementara `fee_reversals_idr` bernilai positif, kebocoran bersih dihitung dengan rumus `-(platform_fees_idr + processing_fees_idr + refunds_idr + fee_reversals_idr)`.
- Kueri Q4 (`mart.v_fx_exposure`): menggabungkan pangsa pendapatan bersih per mata uang (`share_of_net_pct` via window function `SUM(...) OVER ()`) dengan tren rata-rata kurs bulanan (`avg_exchange_rate_to_idr`) untuk seluruh valuta asing.

## 9. Temuan Bisnis dan Hasil Validasi Data

Catatan penyajian: karena data transaksi disimulasikan dari tarif platform dengan kurs riil ECB, temuan berikut menunjukkan pola keputusan yang dapat diungkap oleh Data Warehouse Wasaka Interactive apabila diisi catatan transaksi produksi studio:

1. Ringkasan Global (`2025-01-01` s.d. `2026-10-31`, `5,911` baris fakta): Total penjualan kotor tercatat `Rp 1.567.043.585,23`, tip `Rp 47.668.387,47`, potongan platform `-Rp 175.851.493,86`, biaya pemrosesan `-Rp 38.300.522,52`, refund `-Rp 88.002.459,66`, dan pembalikan biaya `+Rp 10.524.992,39`, menghasilkan pendapatan bersih `Rp 1.323.082.489,05`.
2. Bauran Aliran Pendapatan (Q1): Komisi Klien menyumbang `Rp 1.098.273.990,58` (`83,01%`) secara stabil sepanjang tahun, Penjualan Gim Video menyumbang `Rp 128.983.832,44` (`9,75%`) yang terkonsentrasi pada periode diskon Juni, Juli, November, dan Desember, sedangkan Penjualan Aset Digital menyumbang `Rp 95.824.666,03` (`7,24%`).
3. Peringkat Bidang Produksi (Q2): Setelah dikurangi biaya dan refund, `Programming & Tech` mencatat pendapatan bersih terbesar (`Rp 369,04 juta`, kebocoran `16,42%`), diikuti `Audio & Music` (`Rp 303,61 juta`), `2D Illustration` (`Rp 270,49 juta`), `Pixel Art & UI` (`Rp 224,42 juta`), `Full Game Dev` (`Rp 128,98 juta` dari kotor `Rp 187,74 juta`, kebocoran `32,17%`), dan `3D Modeling` (`Rp 26,54 juta`).
4. Erosi Biaya dan Asimetri Refund per Platform (Q3): Steam mencatat rasio kebocoran tertinggi (`34,61%`), diikuti Fiverr (`25,94%`), itch.io (`18,29%`), VGen (`13,39%`), dan Direct PayPal (`9,77%`). Mengarahkan klien komisi berulang dari Fiverr ke VGen atau Direct PayPal berpotensi menahan sekitar 12 hingga 16 poin persentase pendapatan kotor, sementara pemisahan `PROCESSING_FEE` memperlihatkan biaya gerbang pembayaran yang tidak kembali ketika terjadi refund.
5. Eksposur Valuta Asing (Q4): `95,38%` pendapatan bersih studio berasal dari mata uang asing (`USD` `58,42%`, `SGD` `11,51%`, `EUR` `11,43%`, `JPY` `6,07%`, `GBP` `5,80%`, `CNY` `2,16%`) dan hanya `4,62%` dalam `IDR`. Pada data kurs ECB 2025 hingga 2026, `USD/IDR` bergerak antara `Rp 16.104,40` hingga `Rp 18.176,40` dan `EUR/IDR` antara `Rp 16.680,99` hingga `Rp 21.034,06`. Penilaian kurs per tanggal kejadian (dengan 1.615 transaksi akhir pekan valas diselesaikan via fallback hari kerja sebelumnya) mencegah distorsi kurs tebakan akhir bulan.

Seluruh hasil validasi otomatis (`sql/03_validate.sql`) menunjukkan **12 PASS, 2 INFO, dan 0 FAIL** (tidak ada orphan FK, 0 pelanggaran tanda, 0 duplikat `transaction_code`, 0 refund melebihi penjualan induk, 33 order multi-tip tetap terpisah, 0 pembalikan biaya PayPal, dan 0 kolom PII di `edw` maupun `mart`).

## 10. Kesimpulan dan Pengembangan Lanjutan

Implementasi Data Warehouse pendapatan Wasaka Interactive telah memenuhi rantai arsitektur yang ditetapkan: masalah fragmentasi data dan net revenue blindness dipetakan ke tata kelola kepemilikan data yang jelas, diintegrasikan melalui pipa ETL pembersih multi-format ke dalam Star Schema DuckDB enam tabel yang tervalidasi penuh, dan disajikan lewat antarmuka kueri tanpa kode yang menjawab empat pertanyaan bisnis utama.

Keterbatasan utama saat ini mencakup pemakaian data transaksi sintetis, pemuatan ulang penuh (full refresh), belum adanya pencatatan beban pengeluaran/profitabilitas, serta penempatan lokal satu pengguna tanpa autentikasi. Pengembangan lanjutan yang disarankan meliputi pemuatan inkremental berbasis watermark tanggal, penerapan Slowly Changing Dimension (SCD Type 2) pada atribut proyek apabila kategori berubah, penambahan mart biaya operasional untuk analisis laba bersih, serta penambahan autentikasi pengguna bila aplikasi dipindahkan ke server bersama. Dokumen terpisah `Kesimpulan setelah peer-review` akan disusun setelah sesi presentasi dan penilaian dua reviewer kelas selesai dilaksanakan.
