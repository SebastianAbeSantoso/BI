# Panduan Demo Presentasi Live (15 sampai 20 Menit)

## Persiapan Sebelum Maju ke Depan Kelas

1. Buka PowerShell dan jalankan aplikasi Streamlit lebih dulu agar browser langsung terbuka:
   ```powershell
   cd d:\Downloads\random\bi-dw-uts
   .\.venv\Scripts\python.exe -m streamlit run app\app.py
   ```
2. Siapkan satu terminal terpisah di folder yang sama untuk menunjukkan eksekusi `src\etl.py` dan `src\validate.py` secara langsung.
3. Siapkan `report\screenshots\` sebagai cadangan jika proyektor atau jaringan bermasalah.
4. Siapkan perekam video (ponsel dengan baterai penuh dan ruang kosong memadai, letakkan cukup dekat agar suara pertanyaan kedua reviewer terekam jelas).

## Urutan Penyampaian (Target 15 sampai 20 Menit)

1. **Menit 0-2 | Masalah Bisnis:** Jelaskan profil singkat Wasaka Interactive (3 aliran pendapatan: Game Sales, Asset Sales, Commissions; 5 platform: Steam, itch.io, VGen, Fiverr, Direct PayPal; 7 mata uang). Tekankan 3 masalah nyata: format ekspor berbeda-beda, kebingungan gross vs net (termasuk processing fee yang hangus saat refund), dan kurs tebakan akhir bulan.
2. **Menit 2-4 | Tata Kelola Data ("Siapa yang Punya Data Apa"):** Tunjukkan matriks tata kelola di laporan Section 3.2. Bedakan Data Owner (Studio Lead / studio pemilik catatan), Data Provider (Valve, itch.io, VGen, Fiverr, PayPal, ECB), dan Data Steward (Finance / Production / Commission). Jelaskan kebijakan PII: email dan username pembeli dibuang di `stg` dan tidak pernah masuk ke `edw`.
3. **Menit 4-7 | Star Schema, Grain, dan Keputusan Desain:** Tunjukkan diagram Star Schema (`06_star_schema_edw.png`) dan alur penyimpanan (`05_storage_design.png`). Jelaskan bahwa grain adalah satu baris per peristiwa keuangan atomik (bukan rekap harian), `transaction_code` adalah `<<DD>>`, sedangkan `parent_transaction_code` sengaja bukan `<<DD>>` karena berfungsi sebagai lineage key untuk menautkan refund parsial, fee reversal, dan multi-tip ke order induk.
4. **Menit 7-9 | Bukti Pipeline & Validasi di Terminal:** Jalankan `.\.venv\Scripts\python.exe src\etl.py` lalu `.\.venv\Scripts\python.exe src\validate.py`. Tunjukkan 5,911 baris fakta terbangun, 15 duplikat Fiverr dibuang, 11 judul asing dikarantina ke `stg.etl_rejects`, 1,717 lookup kurs fallback akhir pekan, dan hasil `12 PASS, 2 INFO, 0 FAIL`.
5. **Menit 9-13 | Aplikasi Tab 2 (4 Pertanyaan Bisnis):** Buka tab `2. Empat Pertanyaan Bisnis`. Jelaskan sekilas masing-masing Q1 (tren bulanan dan lonjakan sale gim), Q2 (perbandingan 12 proyek dan 6 bidang produksi), Q3 (kebocoran Steam 34,61% vs Fiverr 25,94% vs VGen 13,39% vs PayPal 9,77% beserta asimetri fee reversal), dan Q4 (95,38% valas dengan kurs riil ECB).
6. **Menit 13-17 | Aplikasi Tab 1 (Kueri Mandiri Tanpa SQL + Tantangan Live):** Buka tab `1. Pembuat Kueri`. Persilakan reviewer bisnis atau teknis meminta kombinasi pengelompokan dan filter secara acak (misalnya: hanya platform VGen dan Direct PayPal untuk kuartal tertentu, atau dikelompokkan per `Mata Uang` untuk melihat pembukaan kunci metrik nilai asli). Buka expander `Lihat SQL yang dijalankan` untuk membuktikan kueri Star Schema berparameter berjalan langsung di DuckDB.
7. **Menit 17-19 | Aplikasi Tab 3 & Keterbatasan:** Buka tab `3. Arsitektur & Validasi` untuk menunjukkan daftar `stg.etl_rejects` secara live. Tutup dengan jujur menyebut keterbatasan: transaksi bersifat sintetis berbasis tarif resmi (kurs riil ECB), pemuatan masih full refresh, dan aplikasi berjalan lokal satu pengguna.
