# Persiapan Tanya Jawab Reviewer (Bisnis & Teknis DW)

## Pertanyaan Reviewer Sisi Bisnis (Bobot 20%)

**1. Mengapa studio memodelkan tiga aliran pendapatan sekaligus dalam satu gudang data?**
Karena tim Wasaka Interactive bekerja lintas enam bidang produksi yang sama. Dengan menyatukan Penjualan Gim, Aset Digital, dan Komisi Klien dalam satu tabel fakta, pimpinan studio bisa melihat aliran mana yang menopang arus kas stabil setiap bulan dibanding gim yang hanya melonjak saat masa diskon.

**2. Keputusan bisnis nyata apa yang bisa berubah besok dari hasil DW ini?**
Pada simulasi tarif resmi platform, kanal Fiverr memotong total 25,94% dari penjualan kotor sementara VGen hanya 13,39% dan Direct PayPal 9,77%. Manajemen bisa mengarahkan klien komisi berulang agar bertransaksi lewat VGen atau invoice PayPal langsung untuk menjaga selisih 12 sampai 16 poin persentase margin kotor.

**3. Mengapa tidak cukup memakai spreadsheet Excel saja?**
Spreadsheet menuntut penyalinan manual lima format ekspor berbeda (termasuk JSON bertingkat VGen dan angka koma desimal PayPal), rentan menggandakan baris saat ekspor tanggal tumpang tindih, dan tidak menegakkan aturan tanda atau batas refund secara otomatis. DW mengotomatisasi pembersihan tersebut dan menjaga satu definisi pendapatan bersih (`SUM(amount_idr)`).

**4. Mengapa PayPal dimodelkan sebagai platform komisi di `dim_platform`, bukan sekadar gerbang pembayaran?**
Karena banyak klien langsung membayar faktur komisi melalui PayPal tanpa melewati VGen atau Fiverr. Memisahkan PayPal di `dim_platform` memungkinkan studio membandingkan kebocoran bersih komisi langsung (`9,77%`) terhadap komisi marketplace (`25,94%` di Fiverr) sekaligus melihat biaya pemrosesan yang hangus saat refund.

**5. Data transaksinya sintetis. Apakah temuan di laporan masih valid untuk dipertanggungjawabkan?**
Tujuan UTS ini adalah membuktikan arsitektur DW mampu menjawab masalah bisnis studio. Oleh karena itu saya jujur menyatakan di laporan bahwa transaksi disimulasikan, namun tarif potongannya mengacu pada ketentuan resmi platform (Steam 30%, Fiverr 20%, VGen 5%, PayPal Indonesia 3,40%/4,40%) dan seluruh kurs memakai data historis riil ECB dari Frankfurter API.

**6. Berapa biaya implementasi arsitektur ini untuk studio kecil?**
Biaya perangkat lunak dan API adalah Rp 0 karena DuckDB, Python, pandas, Streamlit, Plotly, dan Frankfurter API semuanya gratis/open-source. Sistem berjalan di laptop yang sudah dimiliki studio tanpa biaya server bulanan, dan baru butuh VPS sekitar Rp 150.000 per bulan jika nantinya ingin diakses bersama secara daring.

**7. Bagaimana data pribadi klien (email/username) ditangani?**
Ekspor itch.io, VGen, Fiverr, dan PayPal memang membawa email dan username pembeli. Kelima kolom tersebut hanya singgah di skema `stg` dan langsung dibuang pada tahap Transform sebelum memuat `edw`, sehingga tidak pernah muncul di antarmuka analitik dan dicek otomatis lewat validasi `V13`.

---

## Pertanyaan Reviewer Sisi Teknis DW (Bobot 20%)

**1. Mengapa memilih grain peristiwa atomik, bukan agregat harian per proyek/platform?**
Karena potongan biaya platform, tip tambahan, dan refund dapat terjadi beberapa hari atau minggu setelah tanggal penjualan awal, serta memakai kurs tanggal terjadinya peristiwa tersebut. Agregat harian akan mencampur peristiwa berbeda tanggal dan menghilangkan kemampuan melacak refund atau pembalikan biaya ke transaksi induknya.

**2. Mengapa `parent_transaction_code` tidak diberi label `<<DD>>` di Star Schema?**
Degenerate Dimension (`<<DD>>`) adalah pengidentifikasi unik transaksi pada tingkat baris itu sendiri, yaitu `transaction_code` (`UNIQUE`). Sedangkan `parent_transaction_code` adalah kunci relasi lineage yang nilainya `NULL` pada baris `SALE` dan berulang pada baris biaya, tip, dan refund untuk menautkannya kembali ke transaksi `SALE` induk.

**3. Bagaimana sistem mencegah refund terhitung ganda, tetapi tetap mengizinkan refund parsial dan beberapa tip dalam satu order?**
Setiap peristiwa wajib memiliki `transaction_code` unik yang dijaga oleh constraint `UNIQUE(transaction_code)` di DuckDB sehingga ekspor ulang tidak pernah menggandakan baris yang sama. Untuk mendukung milestone komisi, beberapa baris `REFUND` atau `TIP` pada satu `parent_transaction_code` diizinkan selama validasi `V5` memastikan total refund per induk tidak melebihi nilai `SALE` induknya, dan `V7` memastikan order dengan 2+ tip tetap tersimpan terpisah.

**4. Mengapa memilih DuckDB dibandingkan PostgreSQL atau MySQL?**
DuckDB adalah basis data analitik berbasis kolom (columnar OLAP) yang dirancang khusus untuk pemindaian dan agregasi Star Schema, mendukung tipe `DECIMAL(18,2)` eksak untuk uang serta `CHECK`/`FOREIGN KEY` constraint penuh, namun tetap ringkas dalam satu berkas lokal tanpa konfigurasi server terpisah.

**5. Di mana lapisan `INT_DB` yang ada di diagram template penyimpanan?**
Sesuai Batasan #4 yang sudah disetujui, seluruh pipa berjalan pada satu mesin lokal dalam satu berkas `warehouse.duckdb`. Pemisahan server fisik disederhanakan menjadi tiga skema logis (`stg`, `edw`, `mart`), di mana logika integrasi (`INT`) seperti deduplikasi, pemetaan judul, dan fallback kurs dieksekusi di skrip Transform Python sebelum dimuat ke `edw`.

**6. Bagaimana cara menangani transaksi akhir pekan atau hari libur bank yang tidak punya data kurs?**
API Frankfurter (kurs ECB) tidak menerbitkan nilai tukar pada Sabtu, Minggu, dan tanggal 1 Januari. Oleh karena itu jendela pengambilan kurs dimulai dari 20 Desember 2024, dan kelas `FXResolver` di `etl.py` memakai binary search (`bisect_right`) untuk mengambil kurs hari kerja terakhir sebelum tanggal transaksi. Validasi `V11` mengonfirmasi 1.615 transaksi valas akhir pekan berhasil terkonversi tanpa `NULL`.

**7. Apa yang terjadi jika ada judul komisi baru dari VGen/Fiverr/PayPal yang tidak cocok dengan `project_title_map.csv`?**
Baris tersebut tidak dipaksa masuk dengan `project_key` sembarangan dan juga tidak membuat ETL crash. Baris tak dikenal (termasuk baris anak yang merujuk ke order tersebut) dialihkan ke tabel karantina `stg.etl_rejects` beserta alasannya agar Data Steward dapat memperbarui kamus pemetaan sebelum menjalankan ulang ETL.

**8. Apakah proses ETL idempoten jika dijalankan berulang kali?**
Ya. `src/etl.py` memakai strategi full refresh: menjatuhkan view, menjatuhkan fakta lalu dimensi, mengisi ulang dimensi, mengurutkan baris fakta secara deterministik berdasarkan `(date_key, transaction_code)` sebelum memberi surrogate key, lalu membangun ulang view. Menjalankan `etl.py` dua kali berturut-turut terbukti menghasilkan jumlah baris yang persis sama.

**9. Bagaimana aplikasi mencegah kesalahan penjumlahan mata uang asing yang berbeda (misalnya JPY + USD)?**
Di `app/query_builder.py`, metrik `Nilai Mata Uang Asal` (`SUM(amount_orig)`) dan `Rata-rata Kurs ke IDR` ditandai `needs_currency = True`. Baik UI maupun backend menolak kedua metrik tersebut kecuali pengguna memilih `Mata Uang` di pengelompokan, sehingga nilai lintas mata uang hanya pernah dijumlahkan dalam `amount_idr`.

**10. Mengapa tidak menggunakan Slowly Changing Dimension (SCD Type 2) pada tabel dimensi?**
Dalam cakupan data 22 bulan ini, daftar proyek, bidang produksi, platform, dan mata uang bersifat statis dan tidak mengalami perubahan hierarki historis. Penerapan SCD Type 2 dicatat sebagai pengembangan lanjutan apabila ke depan nama atau kategori proyek berubah di tengah tahun berjalan.
