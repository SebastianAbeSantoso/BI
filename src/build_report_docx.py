import json
import pathlib
import shutil

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_DOCX = ROOT_DIR.parent / "BI-Design-Template.docx"
OUT_DOCX = ROOT_DIR / "report" / "UTS_BI_Sebastian_Wasaka_DW.docx"
DIAG_DIR = ROOT_DIR / "diagrams"
SHOT_DIR = ROOT_DIR / "report" / "screenshots"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def set_cell_shading(cell, fill_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_cells = table.rows[0].cells
    for idx, text in enumerate(headers):
        hdr_cells[idx].text = text
        set_cell_shading(hdr_cells[idx], "E9ECEF")
        for p in hdr_cells[idx].paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9.5)

    for r_idx, row_vals in enumerate(rows, start=1):
        row_cells = table.rows[r_idx].cells
        for c_idx, val in enumerate(row_vals):
            row_cells[c_idx].text = str(val)
            for p in row_cells[c_idx].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)

    if col_widths:
        for row in table.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    doc.add_paragraph("")
    return table


def add_code_block(doc, code_text):
    p = doc.add_paragraph()
    p_pr = p._p.get_or_add_pPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8F9FA"/>')
    p_pr.append(shd)
    run = p.add_run(code_text.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(33, 37, 41)


def add_figure(doc, image_path, caption_text, width_in=5.8):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.add_run().add_picture(str(image_path), width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p_cap.add_run(caption_text)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(90, 98, 104)


def add_subheading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(31, 56, 100)
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Paragraph")
    p.paragraph_format.left_indent = Inches(0.25)
    p.add_run("- " + text)
    return p


def add_numbered(doc, num, text):
    p = doc.add_paragraph(style="List Paragraph")
    p.paragraph_format.left_indent = Inches(0.25)
    p.add_run(f"{num}. " + text)
    return p


def clean_front_matter_and_truncate(doc):
    body = doc.element.body
    children = list(body)

    toc_idx = None
    to_remove = []
    for idx, child in enumerate(children):
        tag = child.tag.split("}")[-1]
        if tag == "sectPr":
            continue
        if tag == "p":
            txt = "".join(t.text for t in child.findall(f".//{{{W_NS}}}t") if t.text).strip()
            if "THIS IS NOT FOR ACTUAL" in txt:
                to_remove.append(child)
            if txt == "TABLE OF CONTENT":
                toc_idx = idx
                break

    if toc_idx is None:
        raise RuntimeError("Could not locate TABLE OF CONTENT heading in template")

    for child in children[toc_idx + 1 :]:
        if child.tag.split("}")[-1] != "sectPr":
            to_remove.append(child)

    for el in to_remove:
        body.remove(el)

    prep_table = doc.tables[0]
    prep_table.rows[1].cells[2].text = "25/11/2026"

    rev_table = doc.tables[3]
    rev_row = rev_table.rows[2]
    rev_vals = [
        "1.1",
        "Sebastian Abe Santoso",
        "25 November 2026",
        "26",
        "Implementasi DW, ETL, OLAP Front End, Validasi, dan Temuan Wasaka Interactive",
        "Irham Maulani",
    ]
    for idx, val in enumerate(rev_vals):
        rev_row.cells[idx].text = val


def build_report():
    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE_DOCX, OUT_DOCX)
    doc = Document(str(OUT_DOCX))
    clean_front_matter_and_truncate(doc)

    mart = json.loads((ROOT_DIR / "report" / "mart_summary.json").read_text(encoding="utf-8"))
    etl_meta = json.loads((ROOT_DIR / "report" / "etl_last_run.json").read_text(encoding="utf-8"))

    toc_entries = [
        "1. Pendahuluan (Latar Belakang, Referensi, Definisi Teknis, Batasan)",
        "2. Konteks Organisasi dan Ruang Lingkup",
        "3. Kebutuhan Bisnis dan Tata Kelola Data",
        "4. Sumber Data (Internal dan Eksternal)",
        "5. Perancangan dan Implementasi ETL",
        "6. Arsitektur Skema dan Penyimpanan Data Warehouse",
        "7. Implementasi OLAP dan Aplikasi Antarmuka Kueri",
        "8. Implementasi Kueri Analitik",
        "9. Temuan Bisnis dan Hasil Validasi Data",
        "10. Kesimpulan dan Pengembangan Lanjutan",
    ]
    for entry in toc_entries:
        doc.add_paragraph(entry)

    doc.add_heading("1. Pendahuluan", level=1)

    add_subheading(doc, "1.1 Latar Belakang Singkat dan Alur Bisnis")
    doc.add_paragraph(
        "Wasaka Interactive adalah sebuah studio pengembangan gim independen (indie game studio) "
        "dan produksi kreatif digital yang beroperasi di Indonesia. Berbeda dengan perusahaan penerbit "
        "gim berskala besar yang hanya bergantung pada satu produk utama, proses bisnis (business flow) "
        "Wasaka Interactive bertumpu pada tiga aliran pendapatan (revenue streams) lintas disiplin produksi "
        "(full game development, 2D illustration, pixel art dan UI, 3D modeling, audio dan music, serta "
        "programming dan tech), yaitu:"
    )
    add_bullet(
        doc,
        "Penjualan Gim Video (Video Game Sales): Distribusi produk gim komersial secara langsung kepada "
        "konsumen global melalui platform digital storefront seperti Steam dan itch.io.",
    )
    add_bullet(
        doc,
        "Penjualan Aset Digital (Digital Asset Sales): Komersialisasi paket aset siap pakai (sprite sheets, "
        "UI packs, 3D low-poly models, dan audio packs) bagi sesama pengembang melalui itch.io dan VGen Shop.",
    )
    add_bullet(
        doc,
        "Komisi Klien (Client Commissions): Layanan pengerjaan proyek kustom berbasis pesanan maupun milestone "
        "(ilustrasi karakter, pembuatan custom shader, hingga aransemen musik gim) yang dipasarkan melalui "
        "VGen, Fiverr, serta transaksi langsung antar-klien melalui Direct PayPal.",
    )
    doc.add_paragraph(
        "Permasalahan utama yang dihadapi oleh studio adalah fragmentasi data pendapatan dan ketidakkonsistenan "
        "struktur pencatatan keuangan di setiap kanal distribusi. Setiap platform menghasilkan laporan transaksi "
        "dalam format yang berbeda, menerapkan struktur pemotongan biaya yang beragam (mulai dari potongan "
        "komisi platform seperti 30% pada Steam dan 20% pada Fiverr, hingga biaya pemrosesan gerbang pembayaran "
        "pada PayPal, itch.io, dan VGen), serta memiliki mekanisme pengembalian dana (refund) yang dapat "
        "terjadi di periode waktu berbeda dari tanggal transaksi awal. Selain itu, transaksi masuk tercatat dalam "
        "tujuh mata uang asing dan lokal (IDR, USD, SGD, JPY, CNY, EUR, dan GBP), sehingga menyulitkan pihak "
        "manajemen studio dalam mengevaluasi pendapatan bersih (net revenue) yang sebenarnya diterima dalam nilai Rupiah (IDR)."
    )
    doc.add_paragraph(
        "Tujuan utama dari perancangan dokumen ini adalah membangun Data Warehouse Pendapatan Studio Indie "
        "berbasis Metodologi Kimball (Star Schema) yang mengonsolidasikan seluruh catatan peristiwa keuangan "
        "(revenue events) ke dalam satu repositori analitis terpadu. Desain ini menyelesaikan permasalahan bisnis "
        "studio dengan menstandardisasi pencatatan penjualan kotor (gross sale), potongan platform (platform fee), "
        "biaya pemrosesan pembayaran (processing fee), pengembalian dana (refund), dan pembalikan biaya "
        "(fee reversal) pada tingkat granularitas peristiwa transaksi (event-level grain). Melalui integrasi data "
        "kurs mata uang historis ke dalam tabel fakta terpusat (fact_revenue_event), rancangan ini memungkinkan "
        "studio menganalisis kontribusi tiap aliran pendapatan, memantau tren bulanan dan kuartalan, mengukur kinerja "
        "tiap proyek dan bidang produksi (production field), serta mengevaluasi dampak potongan biaya platform dan "
        "fluktuasi nilai tukar secara akurat."
    )

    add_subheading(doc, "1.2 Referensi")
    refs = [
        "Kimball, R., & Ross, M. (2013). The Data Warehouse Toolkit: The Complete Guide to Dimensional Modeling (3rd ed.). John Wiley & Sons.",
        "Inmon, W. H. (2005). Building the Data Warehouse (4th ed.). John Wiley & Sons.",
        "Golfarelli, M., & Rizzi, S. (2009). Data Warehouse Design: Modern Principles and Methodologies. McGraw-Hill Education.",
        "Vaisman, A., & Zimanyi, E. (2014). Data Warehouse Systems: Design and Implementation. Springer-Verlag Berlin Heidelberg.",
        "Dokumentasi Skema Pelaporan Keuangan Platform Eksternal & API Nilai Tukar: Steamworks Financial Reporting Guide, itch.io Creator Payout Export Format, VGen Help Center Fee Structure, Fiverr Seller Terms, PayPal Indonesia Merchant Commercial Fees, dan European Central Bank Reference Rates via Frankfurter REST API.",
        "DuckDB Documentation (2026). SQL, Constraints, and Columnar Analytical Storage.",
        "Streamlit & Plotly Documentation (2026). Interactive Web Front End for Data Applications.",
    ]
    for i, r in enumerate(refs, start=1):
        add_numbered(doc, i, r)

    add_subheading(doc, "1.3 Definisi dan Istilah Teknis")
    terms_rows = [
        ["Data Warehouse (DW)", "Repositori data terpusat yang bersifat subject-oriented, integrated, time-variant, dan non-volatile untuk mendukung proses analisis dan pengambilan keputusan bisnis."],
        ["Kimball Dimensional Modeling", "Metodologi perancangan data warehouse yang berfokus pada proses bisnis dengan menyusun tabel fakta berisi metrik terukur dan tabel dimensi berisi konteks deskriptif."],
        ["Star Schema", "Struktur skema relasional dalam pemodelan dimensional di mana satu tabel fakta terpusat terhubung langsung ke beberapa tabel dimensi yang didenormalisasi."],
        ["Fact Table (fact_revenue_event)", "Tabel pusat dalam Star Schema yang menyimpan ukuran kuantitatif (amount_orig, exchange_rate_to_idr, amount_idr) beserta foreign key yang merujuk ke lima tabel dimensi."],
        ["Dimension Table (dim_*)", "Tabel pendamping yang menyimpan atribut deskriptif (dim_date, dim_project, dim_platform, dim_currency, dim_revenue_stream) untuk pemfilteran dan pengelompokan data fakta."],
        ["Grain (Granularitas)", "Definisi tingkat kedetailan paling atomik dari satu baris tabel fakta. Satu baris merepresentasikan satu peristiwa pergerakan pendapatan tunggal."],
        ["Surrogate Key (<<PK>>)", "Kunci utama buatan bertipe integer atau bigint yang dibangkitkan di warehouse agar independen dari sistem sumber."],
        ["Natural Key (<<NK>>)", "Pengidentifikasi bisnis asli yang berasal dari sistem operasional atau eksternal, seperti project_code atau kode ISO currency_code."],
        ["Degenerate Dimension (<<DD>>)", "Pengidentifikasi transaksi operasional (transaction_code) yang disimpan langsung di tabel fakta tanpa tabel dimensi tersendiri dan dijamin unik."],
        ["Lineage Key (parent_transaction_code)", "Kolom referensi operasional pada tabel fakta untuk menautkan biaya, tip, refund, dan fee reversal kembali ke transaksi SALE induknya; sengaja tidak diberi tag <<DD>>."],
        ["ETL (Extract, Transform, Load)", "Proses terstruktur untuk menarik data mentah dari sumber internal maupun eksternal, membersihkan serta menyeragamkan format, lalu memuatnya ke warehouse."],
        ["Platform Fee vs. Processing Fee", "Platform Fee adalah komisi pasar digital (Steam 30%, Fiverr 20%, itch.io 10%, VGen 5%), sedangkan Processing Fee adalah biaya gerbang pembayaran (PayPal, checkout itch.io, checkout VGen)."],
        ["Fee Reversal (FEE_REVERSAL)", "Pembalikan komisi platform yang dikembalikan kepada kreator saat terjadi refund atau pembatalan (bernilai positif), berbeda dari processing fee yang tidak dikembalikan."],
        ["Spot Exchange Rate", "Nilai tukar mata uang asing terhadap Rupiah (IDR) yang berlaku pada tanggal terjadinya suatu peristiwa transaksi keuangan (exchange_rate_to_idr)."],
        ["Staging Area (stg) & Data Mart (mart)", "Skema stg menyimpan salinan mentah sementara termasuk kolom PII sebelum pembersihan; skema mart menyediakan view siap kueri untuk tiap pertanyaan bisnis."],
        ["OLAP", "Mesin basis data berorientasi kolom dan antarmuka kueri (DuckDB dan Streamlit) untuk menjalankan agregasi cepat terhadap Star Schema."],
        ["Data Owner / Steward / Provider / Custodian", "Peran tata kelola: penanggung jawab bisnis data (Owner), penjaga kualitas dan aturan (Steward), penyedia ekspor eksternal (Provider), dan pengelola teknis warehouse (Custodian)."],
        ["Full Refresh", "Strategi pemuatan ulang penuh yang menjatuhkan dan membangun ulang tabel dimensi, fakta, serta view pada setiap eksekusi ETL agar selalu idempoten."],
    ]
    add_styled_table(doc, ["Istilah / Singkatan", "Definisi Teknis"], terms_rows, col_widths=[2.1, 4.3])

    add_subheading(doc, "1.4 Batasan Desain dan Implementasi")
    doc.add_paragraph("Kendala teknis dan operasional yang membatasi penerapan desain penuh meliputi:")
    limits = [
        "Tidak tersedianya akses API transaksi langsung pada platform distribusi kreator: Steamworks, itch.io, VGen, Fiverr, dan PayPal tidak membuka endpoint REST API penarikan riwayat keuangan secara bebas untuk akun studio indie, sehingga tahap Extract memakai berkas ekspor penyelesaian (CSV/JSON) melalui File System Reader.",
        "Ketidakteraturan pengidentifikasi proyek pada laporan platform: ekspor VGen, Fiverr, dan PayPal tidak menyertakan project_code internal melainkan teks judul pesanan bebas. Tahap Transform memakai kamus pencocokan teks (project_title_map.csv) dan mengarahkan judul yang belum terdaftar ke tabel karantina stg.etl_rejects.",
        "Kekosongan publikasi kurs pada akhir pekan dan hari libur bank internasional: Frankfurter API (kurs referensi ECB) tidak menerbitkan data pada hari Sabtu, Minggu, dan hari libur bank seperti 1 Januari. Tahap Transform menerapkan fallback ke nilai tukar hari kerja terakhir sebelumnya (last known business day).",
        "Penyederhanaan penyimpanan pada satu instance DBMS lokal: pemisahan empat basis data fisik (STG_DB, INT_DB, EDW_DB, MART_DB) disederhanakan menjadi skema logis stg, edw, dan mart dalam satu berkas DuckDB lokal (data/warehouse.duckdb), sedangkan logika integrasi (INT) dijalankan di tahap Transform Python dan view SQL.",
        "Penggunaan data transaksi sintetis: seluruh catatan penjualan, tip, biaya, dan refund pada data/raw/ (2025-01-01 sampai 2026-10-31) merupakan data sintetis yang dibangkitkan dari aturan tarif resmi masing-masing platform, dipadukan dengan data kurs historis riil ECB (474 hari kerja, 2024-12-20 sampai 2026-10-30) via Frankfurter API.",
        "Penerapan lokal satu pengguna: aplikasi antarmuka Streamlit berjalan lokal dalam mode baca-saja tanpa mekanisme login atau kontrol akses berbasis peran (RBAC), sehingga pengaturan otorisasi multi-pengguna dicatat sebagai pekerjaan lanjutan.",
    ]
    for i, lim in enumerate(limits, start=1):
        add_numbered(doc, i, lim)

    doc.add_heading("2. Konteks Organisasi dan Ruang Lingkup", level=1)

    add_subheading(doc, "2.1 Profil Organisasi, Permasalahan Pelaporan, dan Struktur Fungsi")
    doc.add_paragraph(
        "Wasaka Interactive mengoperasikan model bisnis hibrida untuk menjaga arus kas selama pengembangan "
        "gim jangka panjang melalui tiga aliran pendapatan simultan lintas enam bidang produksi (Full Game Dev, "
        "2D Illustration, Pixel Art & UI, 3D Modeling, Audio & Music, serta Programming & Tech): Penjualan Gim Video "
        "(Steam dan itch.io), Penjualan Aset Digital (itch.io dan VGen), dan Komisi Klien (VGen, Fiverr, dan Direct PayPal)."
    )
    doc.add_paragraph("Sebelum dibangun Data Warehouse, pelaporan keuangan dan evaluasi proyek mengalami tiga masalah:")
    add_bullet(doc, "Silo Data Antar-Platform: data penjualan dan komisi tersebar di lima format ekspor CSV/JSON yang berbeda struktur.")
    add_bullet(doc, "Distorsi Pendapatan Bersih (Net Revenue Blindness): rekap spreadsheet manual mencampur nilai kotor dengan nilai bersih serta mengabaikan biaya pemrosesan pembayaran yang tetap hangus saat refund.")
    add_bullet(doc, "Ketidakakuratan Konversi Multi-Mata Uang: laporan bulanan sebelumnya memakai kurs rata-rata tebakan di akhir bulan, bukan kurs historis pada tanggal transaksi.")
    doc.add_paragraph("Struktur organisasi Wasaka Interactive terdiri atas lima fungsi utama:")
    add_numbered(doc, 1, "Studio Lead / Executive Management: penentu arah strategis studio, alokasi jam kerja tim, dan evaluasi kelayakan proyek.")
    add_numbered(doc, 2, "Game & Digital Asset Production Division: tim teknis dan artistik pengembang gim serta paket aset digital.")
    add_numbered(doc, 3, "Commission & Client Relations Division: pengelola pesanan kustom, milestone komisi, dan kamus judul pesanan.")
    add_numbered(doc, 4, "Finance & Administration Division: pengelola arus kas, rekonsiliasi payout, aturan tanda akuntansi, dan pelaporan kurs.")
    add_numbered(doc, 5, "IT & Data Engineering Function: pengelola berkas DuckDB, pipa ETL, validasi kualitas data, dan aplikasi kueri.")
    doc.add_paragraph(
        "Pengembangan Data Warehouse menjadi mendesak agar manajemen studio dapat menilai apakah alokasi waktu tim "
        "lebih menguntungkan pada penjualan gim penuh, aset digital, atau komisi klien. Sebagai Data Engineer, solusi "
        "yang dihadirkan adalah Star Schema Kimball di atas DuckDB beserta pipa ETL semi-otomatis berbasis berkas ekspor "
        "dan API kurs untuk menyediakan jawaban berbasis bukti."
    )

    add_subheading(doc, "2.2 Tujuan Dokumen")
    doc.add_paragraph(
        "Dokumen ini menyediakan panduan perancangan, implementasi, validasi, dan pemeliharaan Data Warehouse pendapatan "
        "Wasaka Interactive, mencakup pendefinisian masalah bisnis, matriks kepemilikan data, arsitektur Star Schema, "
        "aturan transformasi ETL, antarmuka kueri OLAP tanpa menulis kode SQL, serta temuan dari data yang telah dimuat."
    )

    add_subheading(doc, "2.3 Ruang Lingkup Proyek")
    doc.add_paragraph(
        "Ruang lingkup proyek (In-Scope) mencakup integrasi peristiwa pendapatan dari lima platform (Steam, itch.io, VGen, "
        "Fiverr, Direct PayPal), tiga aliran pendapatan, dua belas proyek portofolio pada enam bidang produksi, tujuh "
        "mata uang (IDR, USD, SGD, JPY, CNY, EUR, GBP), pembangunan tiga skema DuckDB (stg, edw, mart), pelaksanaan "
        "14 pemeriksaan integritas (V1 sampai V14), dan pembangunan aplikasi Streamlit untuk menjawab empat pertanyaan bisnis utama."
    )
    doc.add_paragraph(
        "Hal di luar ruang lingkup (Out-of-Scope) mencakup pencatatan biaya operasional (gaji tim, sewa, pajak, langganan "
        "perangkat lunak), perhitungan laba bersih (profitability), pemrosesan streaming waktu nyata, penarikan otomatis "
        "dari API platform berbayar, peramalan machine learning, serta pengelolaan login multi-pengguna."
    )

    doc.add_heading("3. Kebutuhan Bisnis dan Tata Kelola Data", level=1)

    add_subheading(doc, "3.1 Permasalahan Bisnis dan Solusi Data Warehouse")
    prob_rows = [
        [
            "Silo data di 5 format ekspor (tanggal MM/DD/YYYY, DD/MM/YYYY, ISO; angka berformat teks dan koma desimal; JSON bertingkat; baris duplikat).",
            "Rekonsiliasi laporan lambat dan rawan salah salin manual.",
            "Pipa ETL di src/etl.py membersihkan tanggal/angka, membuang duplikat Fiverr, dan memuat seluruh peristiwa ke fact_revenue_event.",
            "Satu repositori terpadu berisi 5,911 baris peristiwa tervalidasi.",
        ],
        [
            "Pencatatan manual mencampur nilai kotor dan bersih serta gagal memisahkan fee reversal dari processing fee hangus.",
            "Manajemen melebih-lebihkan pendapatan bersih pada kanal berbiaya tinggi.",
            "Memecah setiap order ke peristiwa atomik (SALE, TIP, PLATFORM_FEE, PROCESSING_FEE, REFUND, FEE_REVERSAL) dengan constraint tanda.",
            "Menjawab Q3: mengukur persentase erosi biaya dan refund per platform.",
        ],
        [
            "Rekap bulanan menggunakan kurs tebakan akhir bulan untuk 7 mata uang.",
            "Selisih laporan internal terhadap nilai Rupiah yang cair di rekening.",
            "Mengambil kurs harian ECB (Frankfurter API) dan memakai fallback hari kerja sebelumnya untuk akhir pekan/hari libur.",
            "Menjawab Q4: memetakan eksposur valuta asing dan rentang kurs tiap bulan.",
        ],
        [
            "Sulit membandingkan kinerja bersih 12 proyek dan 6 bidang produksi lintas kanal distribusi.",
            "Alokasi tenaga kerja tim antara gim, aset, dan komisi tidak berbasis data.",
            "Menghubungkan dim_project dan dim_revenue_stream ke mart.v_project_performance dan mart.v_revenue_monthly.",
            "Menjawab Q1 dan Q2: tren pendapatan bulanan serta peringkat bersih proyek dan bidang produksi.",
        ],
        [
            "Ekspor komisi memuat judul bebas tanpa project_code dan mengandung data pribadi pembeli (email/username).",
            "Pesanan gagal dipetakan ke proyek dan berisiko mengekspos PII ke lapisan laporan.",
            "Kamus project_title_map.csv memetakan judul, baris asing dikarantina ke stg.etl_rejects, dan 5 kolom PII dihapus di staging.",
            "11 baris asing dikarantina dan 0 kolom PII ada di edw/mart (V13).",
        ],
    ]
    add_styled_table(
        doc,
        ["Permasalahan Bisnis", "Dampak Bisnis", "Solusi Data Warehouse", "Luaran & Pertanyaan Bisnis"],
        prob_rows,
        col_widths=[1.7, 1.4, 1.8, 1.5],
    )

    add_subheading(doc, "3.2 Pemangku Kepentingan dan Kepemilikan Data (Tata Kelola Data)")
    doc.add_paragraph(
        "Pembagian kepemilikan data menetapkan siapa yang bertanggung jawab penuh atas data (Data Owner), "
        "siapa yang menjaga aturan kualitas dan pemetaan (Data Steward), sistem penyedia ekspor (Data Provider), "
        "pengelola teknis basis data (Custodian), serta konsumen laporan."
    )
    gov_rows = [
        ["Penjualan gim, refund, biaya Steam", "Studio Lead", "Finance & Administration", "Valve (Steamworks export)", "IT & Data Eng", "Studio Lead, Finance", "Studio pemilik catatan penjualan; Valve sebagai provider"],
        ["Payout gim dan aset itch.io", "Studio Lead", "Finance & Administration", "itch.io (payout CSV)", "IT & Data Eng", "Studio Lead, Finance, Production", "Kolom buyer_email dibuang di staging"],
        ["Aset, komisi, tip, refund VGen", "Studio Lead", "Commission & Client Relations (+ Finance)", "VGen (JSON export)", "IT & Data Eng", "Commission, Finance", "Kolom client_username dibuang di staging"],
        ["Komisi dan tip Fiverr", "Studio Lead", "Commission & Client Relations", "Fiverr (earnings CSV)", "IT & Data Eng", "Commission, Finance", "buyer_username dibuang; baris duplikat dihapus"],
        ["Komisi langsung, tip, biaya PayPal", "Studio Lead", "Finance & Administration", "PayPal (activity CSV)", "IT & Data Eng", "Finance", "Dimodelkan sebagai platform komisi langsung; payer PII dibuang"],
        ["Kurs historis harian", "Finance & Administration", "IT & Data Eng", "ECB via Frankfurter API", "IT & Data Eng", "Finance, Studio Lead", "Fallback hari kerja sebelumnya untuk akhir pekan dan libur"],
        ["Daftar proyek & bidang produksi", "Production Division", "Production Division", "Internal projects.csv", "IT & Data Eng", "Seluruh divisi", "Menetapkan project_code dan production_field kanonik"],
        ["Kamus pemetaan judul komisi", "Commission & Client Relations", "Commission & Client Relations", "Internal project_title_map.csv", "IT & Data Eng", "ETL Pipeline", "Judul tak cocok masuk stg.etl_rejects untuk ditinjau steward"],
        ["Taksonomi stream & aturan tanda", "Finance & Administration", "Finance & Administration", "Aturan akuntansi internal", "IT & Data Eng", "Seluruh divisi", "Mengatur tanda +/-, jenis peristiwa, dan batas refund"],
        ["Warehouse DuckDB & aplikasi Streamlit", "Studio Lead", "IT & Data Eng", "Internal", "IT & Data Eng", "Seluruh divisi", "Penerapan lokal satu pengguna; RBAC adalah pengembangan lanjutan"],
    ]
    add_styled_table(
        doc,
        ["Domain Data", "Data Owner", "Data Steward", "Data Provider", "Custodian", "Konsumen", "Catatan Tata Kelola"],
        gov_rows,
        col_widths=[1.05, 0.85, 0.95, 0.9, 0.7, 0.85, 1.1],
    )
    doc.add_paragraph(
        "Kebijakan Privasi dan PII: lima kolom identitas pribadi (itch.buyer_email, vgen.client_username, "
        "fiverr.buyer_username, paypal.payer_name, dan paypal.payer_email) hanya hadir sementara pada tabel mentah "
        "skema stg dan langsung dihapus pada tahap Transform. Pemeriksaan otomatis V13 memastikan tidak ada "
        "kolom PII di skema edw maupun mart."
    )

    add_subheading(doc, "3.3 Rencana Anggaran")
    budget_rows = [
        ["Perangkat Lunak", "DuckDB, Python, pandas, Streamlit, Plotly, PlantUML", "Rp 0", "Seluruh pustaka berlisensi open-source"],
        ["API Eksternal", "Frankfurter REST API (kurs referensi ECB)", "Rp 0", "Layanan publik gratis tanpa biaya langganan"],
        ["Infrastruktur Lokal", "Laptop pengembangan milik studio", "Rp 0 (tambahan)", "Memanfaatkan perangkat keras lokal eksisting"],
        ["Hosting Opsional", "VPS ringan (hanya bila diperlukan akses daring tim)", "Rp 150.000 / bulan", "Estimasi opsional; implementasi UTS berjalan lokal"],
        ["Sumber Daya Manusia", "1 Data Engineer paruh waktu (24 jam kerja perancangan, ETL, app, laporan)", "Rp 1.800.000 - Rp 2.400.000", "Asumsi alokasi tenaga internal studio skala kecil"],
    ]
    add_styled_table(doc, ["Kategori", "Item", "Estimasi Biaya (IDR)", "Catatan"], budget_rows, col_widths=[1.3, 2.1, 1.3, 1.7])

    add_subheading(doc, "3.4 Perangkat dan Teknologi")
    tools_rows = [
        ["Python 3.10+ & pandas", "Pembangkit sumber ekspor sintetis, pembersihan data, pemetaan judul, dan pemuatan ETL"],
        ["requests + Frankfurter API", "Penarikan kurs historis harian ECB ke data/raw/fx_rates.csv"],
        ["DuckDB 2.0.1", "Data warehouse kolom satu berkas (stg, edw, mart), penegak PK/FK/UNIQUE/CHECK, dan mesin OLAP"],
        ["Streamlit 1.67.0 + Plotly", "Antarmuka web tanpa menulis kode SQL (Pembuat Kueri, 4 Pertanyaan Bisnis, Panel Validasi)"],
        ["PlantUML", "Pembuatan diagram alur ETL, struktur JSON, tunnel data, arsitektur DW, dan desain penyimpanan"],
        ["Git & python-docx", "Kontrol versi kode sumber dan penyusunan dokumen desain ini"],
    ]
    add_styled_table(doc, ["Perangkat", "Peran dalam Sistem"], tools_rows, col_widths=[2.0, 4.4])

    doc.add_heading("4. Sumber Data", level=1)

    add_subheading(doc, "4.1 Sumber Data Internal")
    doc.add_paragraph(
        "Sumber internal terdiri atas daftar master proyek (data/raw/projects.csv) sebanyak 12 proyek portofolio "
        "Wasaka Interactive di enam bidang produksi, serta kamus pemetaan judul pesanan (data/raw/project_title_map.csv) "
        "berisi 21 aturan substring tidak peka huruf besar/kecil."
    )
    proj_rows = [
        ["GAME-AMMD", "A Match Made in Dungeon", "Game", "Full Game Dev", "GAME_SALES"],
        ["GAME-RBRT", "R*bert", "Game", "Full Game Dev", "GAME_SALES"],
        ["GAME-PSPC", "Personal Space", "Game", "Full Game Dev", "GAME_SALES"],
        ["GAME-CNTG", "Canting Cloth", "Game", "Full Game Dev", "GAME_SALES"],
        ["AST-DGPX", "Dungeon Matchmaker Pixel UI & Sprite Kit", "Asset Pack", "Pixel Art & UI", "ASSET_SALES"],
        ["AST-ISOR", "Personal Space Isometric Room & Props Pack", "Asset Pack", "3D Modeling", "ASSET_SALES"],
        ["AST-RHYT", "R*bert Reactive Rhythm & SFX Stem Pack", "Asset Pack", "Audio & Music", "ASSET_SALES"],
        ["AST-BATK", "Canting NPR Batik Shader & Godot Toolkit", "Asset Pack", "Programming & Tech", "ASSET_SALES"],
        ["COM-ILLU", "Custom 2D Character & Key Visual Illustration", "Commission Service", "2D Illustration", "COMMISSION"],
        ["COM-PXUI", "Indie Game Pixel Art & HUD UI Commissions", "Commission Service", "Pixel Art & UI", "COMMISSION"],
        ["COM-SHDR", "Godot & Custom NPR Shader Commissions", "Commission Service", "Programming & Tech", "COMMISSION"],
        ["COM-MUSC", "Interactive Game BGM & SynthV Arrangement", "Commission Service", "Audio & Music", "COMMISSION"],
    ]
    add_styled_table(
        doc,
        ["project_code", "project_name", "project_type", "production_field", "Stream"],
        proj_rows,
        col_widths=[1.0, 2.1, 1.1, 1.2, 1.0],
    )

    add_subheading(doc, "4.2 Sumber Data Eksternal")
    ext_rows = [
        ["steam_sales_report.csv", "Steam (GAME_SALES)", "1.297 baris", "MM/DD/YYYY; angka titik", "Platform fee 30%; reversal saat refund", "Tidak ada"],
        ["itch_payouts.csv", "itch.io (GAME & ASSET)", "517 baris", "YYYY-MM-DD; string $ / Rp / ¥", "Share 10% kembali saat refund; proc fee hangus", "buyer_email"],
        ["vgen_export.json", "VGen (ASSET & COMM)", "257 order", "ISO-8601 UTC; JSON bertingkat tips[] & refunds[]", "Platform fee 5% kembali proporsional; proc fee 2.9%+$0.30", "client_username"],
        ["fiverr_earnings.csv", "Fiverr (COMMISSION)", "250 baris (15 duplikat)", "YYYY-MM-DD; baris terpisah ORDER/TIP/CANCEL", "Komisi 20% pada order dan tip; dibalik saat batal", "buyer_username"],
        ["paypal_activity.csv", "Direct PayPal (COMM)", "189 baris", "DD/MM/YYYY; koma desimal (~42% baris)", "Platform 0%; proc fee 3.40%/4.40%+fixed; tanpa reversal", "payer_name, payer_email"],
        ["fx_rates.csv", "Frankfurter ECB API", "3.318 baris (474 hari)", "YYYY-MM-DD; 6 desimal ke IDR", "Hari kerja ECB saja (2024-12-20 s.d. 2026-10-30)", "Tidak ada"],
    ]
    add_styled_table(
        doc,
        ["Berkas Sumber", "Platform & Stream", "Volume", "Format Tanggal & Angka", "Aturan Biaya & Refund", "PII Dihapus"],
        ext_rows,
        col_widths=[1.15, 1.0, 0.8, 1.25, 1.35, 0.85],
    )
    add_figure(
        doc,
        DIAG_DIR / "02_vgen_json_schema.png",
        "Gambar 4.1 Struktur Objek JSON Bertingkat pada Ekspor VGen (vgen_export.json).",
        width_in=5.2,
    )

    doc.add_heading("5. Perancangan dan Implementasi ETL", level=1)
    add_figure(
        doc,
        DIAG_DIR / "01_etl_flow.png",
        "Gambar 5.1 Alur Keseluruhan Extract, Transform, dan Load (src/etl.py).",
        width_in=5.6,
    )

    add_subheading(doc, "5.1 Proses Extract")
    doc.add_paragraph(
        "Tahap Extract membaca lima berkas platform dan dua berkas master internal menggunakan File System Reader "
        "serta berkas fx_rates.csv hasil tarikan API Frankfurter. Seluruh kolom dimuat apa adanya ke delapan tabel "
        "sementara pada skema stg (stg.raw_*). Array tips dan refunds pada vgen_export.json disimpan sementara "
        "sebagai kolom JSON string sebelum diurai menjadi baris kejadian terpisah di tahap Transform."
    )
    add_figure(
        doc,
        DIAG_DIR / "03_data_tunnel.png",
        "Gambar 5.2 Tunnel Aliran Data dari Catatan Sumber ke Baris Atomik fact_revenue_event.",
        width_in=6.0,
    )

    add_subheading(doc, "5.2 Penjadwalan")
    sched_rows = [
        ["steam_sales_report.csv", "Bulanan (setelah tutup buku Steamworks)", "Tanggal 2 setiap bulan", "Eksekusi manual full refresh via src/etl.py"],
        ["itch_payouts.csv", "Mingguan / per pencairan payout", "Mingguan (Senin pagi)", "Eksekusi manual full refresh via src/etl.py"],
        ["vgen_export.json, fiverr_earnings.csv, paypal_activity.csv", "Mingguan dari dasbor masing-masing", "Mingguan (Senin pagi)", "Eksekusi manual full refresh via src/etl.py"],
        ["fx_rates.csv (Frankfurter API)", "Harian (hari kerja ECB)", "Harian pukul 06:00 WITA", "Diunduh via src/fetch_fx.py dan di-cache lokal"],
    ]
    add_styled_table(
        doc,
        ["Sumber", "Frekuensi Ekspor", "Jadwal Rencana Produksi", "Realisasi UTS Saat Ini"],
        sched_rows,
        col_widths=[1.7, 1.5, 1.5, 1.7],
    )

    add_subheading(doc, "5.3 Proses Transform")
    trf_rows = [
        ["1", "Penghapusan PII", "Menghapus 5 kolom pribadi (email/username/nama pembayar) sebelum proses lanjut", "0 kolom PII masuk edw/mart (V13 PASS)"],
        ["2", "Deduplikasi Sumber", "Menghapus baris kembar persis akibat tumpang tindih rentang ekspor Fiverr", "15 baris duplikat Fiverr dibuang"],
        ["3", "Standardisasi Tanggal", "Mengurai MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, dan ISO-8601 UTC ke tipe DATE", "Seluruh baris cocok dengan dim_date"],
        ["4", "Pembersihan Angka", "Menghapus simbol $, Rp, ¥ dan mengubah koma desimal (350000,00) ke Decimal(18,2)", "Presisi nominal terjaga tanpa galat float"],
        ["5", "Pemetaan Judul & Karantina", "Mencocokkan judul komisi via project_title_map.csv; judul tak dikenal dialihkan", "11 baris masuk stg.etl_rejects; anak barisnya ikut ditahan"],
        ["6", "Ledakan Event & Aturan Tanda", "Memecah order menjadi SALE/TIP/FEE_REVERSAL (>0) dan PLATFORM_FEE/PROCESSING_FEE/REFUND (<0)", "5,911 baris atomik dimuat ke fakta"],
        ["7", "Kode Transaksi & Lineage", "Menetapkan transaction_code unik dan parent_transaction_code ke SALE induk (NULL pada SALE)", "33 order multi-tip tetap terpisah (V7 PASS)"],
        ["8", "Batas Refund & Non-Reversal", "Menjaga total refund <= nilai SALE induk; memblokir pembalikan processing fee PayPal/itch/VGen", "0 pelanggaran batas refund dan reversal (V5, V12 PASS)"],
        ["9", "Lookup FX & Fallback Akhir Pekan", "Mencari kurs pada tanggal transaksi; jika Sabtu/Minggu/libur pakai binary search hari kerja sebelumnya", "1,717 lookup fallback (termasuk 1 Jan 2025 -> 31 Des 2024)"],
        ["10", "Konversi IDR", "Menghitung amount_idr = ROUND(amount_orig * exchange_rate_to_idr, 2)", "0 selisih > Rp 0.01 (V10 PASS)"],
    ]
    add_styled_table(doc, ["No.", "Aturan", "Logika Transformasi", "Hasil Tercatat"], trf_rows, col_widths=[0.4, 1.35, 2.85, 1.8])

    add_subheading(doc, "5.4 Proses Load")
    doc.add_paragraph(
        "Pemuatan ke skema edw memakai pola Full Refresh yang idempoten di dalam sql/01_ddl_edw.sql dan src/etl.py: "
        "view pada mart dan edw dijatuhkan lebih dulu, diikuti tabel fact_revenue_event lalu kelima tabel dimensi "
        "agar kendala Foreign Key tidak dilanggar. Setelah keenam tabel dibuat ulang, dimensi diisi lebih dulu, "
        "baris fakta diurutkan secara deterministik menurut (date_key, transaction_code) sebelum diberi surrogate key "
        "revenue_event_sk 1 sampai 5911, dimuat dengan tipe DECIMAL eksak, lalu view edw.v_fact_enriched dan empat "
        "view mart dibangun kembali. Dua eksekusi berurutan terbukti menghasilkan jumlah baris identik."
    )
    add_figure(
        doc,
        SHOT_DIR / "07_cli_etl_validate.png",
        "Gambar 5.3 Bukti Eksekusi Terminal src/etl.py dan src/validate.py (5.911 Baris Fakta, 12 PASS, 2 INFO, 0 FAIL).",
        width_in=6.0,
    )

    doc.add_heading("6. Arsitektur Skema dan Penyimpanan Data Warehouse", level=1)

    add_subheading(doc, "6.1 Arsitektur Data Warehouse")
    doc.add_paragraph(
        "Proyek ini memilih arsitektur Kimball dibandingkan Inmon. Pendekatan Kimball bersifat bottom-up dan langsung "
        "membangun Star Schema di sekitar proses bisnis pendapatan studio agar kueri analitik dapat dijalankan segera "
        "tanpa membangun gudang data 3NF berskala korporasi terlebih dulu."
    )
    add_figure(
        doc,
        DIAG_DIR / "04_dw_architecture.png",
        "Gambar 6.1 Arsitektur Data Warehouse Kimball Wasaka Interactive (Sumber -> stg -> ETL -> edw -> mart -> Streamlit).",
        width_in=5.5,
    )

    add_subheading(doc, "6.2 Kode PlantUML dan Desain Star Schema")
    puml_star = """@startuml
skinparam linetype ortho
hide circle

entity "dim_date" as dim_date {
  * **date_key** : INT <<PK>>
  --
  full_date : DATE <<NK>>
  day_of_week : VARCHAR(20)
  day_of_week_number : INT
  day_of_month : INT
  day_of_year : INT
  month_name : VARCHAR(20)
  month_number : INT
  quarter : INT
  year : INT
  is_weekend : BOOLEAN
}

entity "dim_revenue_stream" as dim_revenue_stream {
  * **revenue_stream_key** : INT <<PK>>
  --
  revenue_stream_code : VARCHAR(50) <<NK>>
  revenue_stream_name : VARCHAR(100)
  description : VARCHAR(255)
}

entity "dim_currency" as dim_currency {
  * **currency_key** : INT <<PK>>
  --
  currency_code : CHAR(3) <<NK>>
  currency_name : VARCHAR(50)
  currency_symbol : VARCHAR(5)
}

entity "dim_platform" as dim_platform {
  * **platform_key** : INT <<PK>>
  --
  platform_code : VARCHAR(50) <<NK>>
  platform_name : VARCHAR(100)
  platform_type : VARCHAR(50)
}

entity "dim_project" as dim_project {
  * **project_key** : INT <<PK>>
  --
  project_code : VARCHAR(50) <<NK>>
  project_name : VARCHAR(150)
  project_type : VARCHAR(50)
  production_field : VARCHAR(100)
}

entity "fact_revenue_event" as fact_revenue_event {
  * **revenue_event_sk** : BIGINT <<PK>>
  --
  * date_key : INT <<FK>>
  * project_key : INT <<FK>>
  * platform_key : INT <<FK>>
  * currency_key : INT <<FK>>
  * revenue_stream_key : INT <<FK>>
  --
  transaction_code : VARCHAR(100) <<DD>>
  parent_transaction_code : VARCHAR(100)
  event_type : VARCHAR(30)
  amount_orig : DECIMAL(18,2)
  exchange_rate_to_idr : DECIMAL(18,6)
  amount_idr : DECIMAL(18,2)
}

dim_date           ||--o{ fact_revenue_event : "occurred on"
dim_currency       ||--o{ fact_revenue_event : "denominated in"
dim_revenue_stream ||--o{ fact_revenue_event : "classified as"
dim_platform       ||--o{ fact_revenue_event : "transacted via"
dim_project        ||--o{ fact_revenue_event : "attributed to"
@enduml"""
    add_code_block(doc, puml_star)
    doc.add_paragraph(
        "Catatan Skema: Desain memakai Kimball Star Schema dengan fact_revenue_event sebagai tabel fakta utama "
        "yang terhubung ke lima tabel dimensi (dim_date, dim_revenue_stream, dim_currency, dim_platform, dim_project). "
        "Nilai transaksi dalam mata uang asal disimpan pada kolom amount_orig dan dikonversi ke Rupiah pada kolom "
        "amount_idr memakai kurs spot di exchange_rate_to_idr. Penjualan, tip, dan pembalikan biaya bernilai positif, "
        "sedangkan refund, biaya platform, dan biaya pemrosesan bernilai negatif sehingga pendapatan bersih dihitung "
        "cukup dengan SUM(amount_idr). Kolom transaction_code bertindak sebagai Degenerate Dimension (<<DD>>) unik, "
        "sedangkan parent_transaction_code merupakan kunci garis keturunan (lineage key) operasional untuk menautkan "
        "biaya, tip, dan refund ke transaksi penjualan induknya."
    )
    add_figure(
        doc,
        DIAG_DIR / "06_star_schema_edw.png",
        "Gambar 6.2 Diagram Star Schema Terkunci (edw.fact_revenue_event dan 5 Tabel Dimensi).",
        width_in=6.0,
    )

    add_subheading(doc, "6.3 Desain Penyimpanan")
    doc.add_paragraph(
        "Ketiga skema logis berada dalam satu berkas DuckDB (data/warehouse.duckdb). DuckDB menyimpan data secara "
        "kolom (columnar) sehingga pemindaian agregasi cepat dilakukan di laptop lokal. Pada lapisan edw, database "
        "menegakkan constraint PRIMARY KEY, lima FOREIGN KEY, UNIQUE(transaction_code), serta CHECK pada nilai "
        "event_type, kesesuaian tanda positif/negatif amount_orig dan amount_idr, serta exchange_rate_to_idr > 0."
    )
    add_figure(
        doc,
        DIAG_DIR / "05_storage_design.png",
        "Gambar 6.3 Desain Penyimpanan Logis pada Berkas Tunggal DuckDB (stg, edw, dan mart).",
        width_in=6.0,
    )

    doc.add_heading("7. Implementasi OLAP dan Aplikasi Antarmuka Kueri", level=1)
    doc.add_paragraph(
        "Lapisan OLAP ditenagai oleh mesin DuckDB melalui view edw.v_fact_enriched dan empat view analitik di skema "
        "mart (mart.v_revenue_monthly, mart.v_project_performance, mart.v_fee_refund_leakage, mart.v_fx_exposure). "
        "Di atasnya berjalan aplikasi web Streamlit (app/app.py) dalam mode baca-saja dengan tiga tab:"
    )
    add_numbered(
        doc,
        1,
        "Pembuat Kueri Tanpa SQL (app/query_builder.py): Pengguna memilih 0 sampai 3 atribut pengelompokan, "
        "metrik pengukuran, filter dari tabel dimensi, urutan, dan batas baris lewat form. SQL dibangun hanya dari "
        "daftar kolom whitelist dengan nilai filter berparameter ? agar aman dari SQL injection. Metrik Nilai Mata "
        "Uang Asal dan Rata-rata Kurs hanya aktif ketika pengelompokan Mata Uang dipilih agar mata uang berbeda tidak "
        "dijumlahkan sembarangan. Tersedia expander Lihat SQL yang dijalankan serta tombol unduh CSV.",
    )
    add_numbered(
        doc,
        2,
        "Empat Pertanyaan Bisnis: Empat sub-tab siap pakai yang menjalankan kueri terhadap skema mart beserta grafik Plotly dan tabel angka.",
    )
    add_numbered(
        doc,
        3,
        "Arsitektur & Validasi: Menampilkan ringkasan eksekusi ETL terbaru, tabel hasil pemeriksaan otomatis V1 sampai V14 langsung dari sql/03_validate.sql, dan isi tabel karantina stg.etl_rejects.",
    )
    add_figure(
        doc,
        SHOT_DIR / "01_tab1_query_builder.png",
        "Gambar 7.1 Tab 1 Aplikasi Streamlit: Antarmuka Pembuat Kueri Tanpa SQL dengan Panel SQL Terbuka.",
        width_in=6.0,
    )
    add_figure(
        doc,
        SHOT_DIR / "06_tab3_validation.png",
        "Gambar 7.2 Tab 3 Aplikasi Streamlit: Monitoring Validasi V1 sampai V14 dan Log Karantina stg.etl_rejects.",
        width_in=6.0,
    )

    doc.add_heading("8. Implementasi Kueri Analitik", level=1)
    doc.add_paragraph("Empat kueri inti berikut digunakan pada Tab 2 untuk menjawab pertanyaan bisnis studio secara langsung:")

    add_subheading(doc, "8.1 Kueri Q1: Bauran dan Tren Pendapatan Bulanan")
    add_code_block(
        doc,
        """SELECT year_month, revenue_stream_name,
       SUM(gross_sales_idr) AS gross_sales_idr,
       SUM(tips_idr) AS tips_idr,
       SUM(net_revenue_idr) AS net_revenue_idr,
       SUM(event_count) AS event_count
FROM mart.v_revenue_monthly
GROUP BY year_month, revenue_stream_name
ORDER BY year_month ASC, revenue_stream_name ASC;""",
    )
    add_figure(
        doc,
        SHOT_DIR / "02_tab2_q1_revenue_trend.png",
        "Gambar 8.1 Hasil Kueri Q1: Tren Pendapatan Bersih Bulanan per Aliran Pendapatan.",
        width_in=6.0,
    )

    add_subheading(doc, "8.2 Kueri Q2: Perbandingan Kinerja Proyek dan Bidang Produksi")
    add_code_block(
        doc,
        """SELECT project_code, project_name, production_field, revenue_stream_name,
       gross_sales_idr, tips_idr, net_leakage_idr, net_revenue_idr, leakage_pct, sale_count
FROM mart.v_project_performance
ORDER BY net_revenue_idr DESC;""",
    )
    add_figure(
        doc,
        SHOT_DIR / "03_tab2_q2_project_field.png",
        "Gambar 8.2 Hasil Kueri Q2: Perbandingan Pendapatan Bersih per Proyek dan Bidang Produksi.",
        width_in=6.0,
    )

    add_subheading(doc, "8.3 Kueri Q3: Erosi Pendapatan oleh Biaya Platform, Pemrosesan, dan Refund")
    add_code_block(
        doc,
        """SELECT platform_name,
       SUM(gross_sales_idr) AS gross_sales_idr,
       SUM(tips_idr) AS tips_idr,
       SUM(platform_fees_idr) AS platform_fees_idr,
       SUM(processing_fees_idr) AS processing_fees_idr,
       SUM(refunds_idr) AS refunds_idr,
       SUM(fee_reversals_idr) AS fee_reversals_idr,
       SUM(net_leakage_idr) AS net_leakage_idr,
       SUM(net_revenue_idr) AS net_revenue_idr,
       ROUND(SUM(net_leakage_idr) * 100.0 / NULLIF(SUM(gross_sales_idr), 0), 2) AS leakage_pct
FROM mart.v_fee_refund_leakage
GROUP BY platform_name
ORDER BY leakage_pct DESC;""",
    )
    add_figure(
        doc,
        SHOT_DIR / "04_tab2_q3_fee_leakage.png",
        "Gambar 8.3 Hasil Kueri Q3: Erosi Biaya Platform, Biaya Pemrosesan, dan Refund per Platform.",
        width_in=6.0,
    )

    add_subheading(doc, "8.4 Kueri Q4: Eksposur Mata Uang Asing dan Pergerakan Kurs")
    add_code_block(
        doc,
        """SELECT currency_code, currency_name,
       SUM(net_amount_orig) AS total_net_orig,
       SUM(net_revenue_idr) AS total_net_idr,
       ROUND(AVG(avg_exchange_rate_to_idr), 2) AS mean_rate_to_idr,
       ROUND(SUM(net_revenue_idr) * 100.0 / NULLIF(SUM(SUM(net_revenue_idr)) OVER (), 0), 2) AS share_of_net_pct
FROM mart.v_fx_exposure
GROUP BY currency_code, currency_name
ORDER BY total_net_idr DESC;""",
    )
    add_figure(
        doc,
        SHOT_DIR / "05_tab2_q4_fx_exposure.png",
        "Gambar 8.4 Hasil Kueri Q4: Porsi Pendapatan per Mata Uang Asal dan Tren Kurs Bulanan.",
        width_in=6.0,
    )

    doc.add_heading("9. Temuan Bisnis dan Hasil Validasi Data", level=1)
    doc.add_paragraph(
        "Karena catatan transaksi berasal dari data sintetis berbasis tarif resmi platform yang dipadukan dengan kurs "
        "riil ECB, hasil berikut menunjukkan jenis jawaban bisnis yang dapat dihasilkan oleh Data Warehouse Wasaka "
        "Interactive pada periode simulasi 1 Januari 2025 sampai 31 Oktober 2026:"
    )

    ov = mart["overall"]
    doc.add_paragraph(
        f"Total peristiwa yang dimuat mencapai {ov['total_events']:,} baris ({ov['sale_events']:,} penjualan). "
        f"Penjualan kotor tercatat Rp {ov['gross_sales_idr']:,.2f}, tip klien Rp {ov['tips_idr']:,.2f}, "
        f"potongan biaya platform Rp {ov['platform_fees_idr']:,.2f}, biaya pemrosesan Rp {ov['processing_fees_idr']:,.2f}, "
        f"refund Rp {ov['refunds_idr']:,.2f}, dan pembalikan biaya Rp {ov['fee_reversals_idr']:,.2f}, sehingga "
        f"menghasilkan pendapatan bersih akhir Rp {ov['net_revenue_idr']:,.2f}."
    )

    stream_rows = [
        [
            s["revenue_stream_name"],
            f"Rp {s['gross_idr']:,.2f}",
            f"Rp {s['tips_idr']:,.2f}",
            f"Rp {s['net_idr']:,.2f}",
            f"{s['net_share_pct']:.2f}%",
        ]
        for s in mart["by_stream"]
    ]
    add_styled_table(doc, ["Aliran Pendapatan", "Penjualan Kotor", "Tip", "Pendapatan Bersih", "Porsi Bersih"], stream_rows, col_widths=[1.6, 1.35, 1.15, 1.35, 0.95])

    field_rows = [
        [
            f["production_field"],
            f"Rp {f['gross_idr']:,.2f}",
            f"Rp {f['net_idr']:,.2f}",
            f"Rp {f['leakage_idr']:,.2f}",
            f"{f['leakage_pct']:.2f}%",
        ]
        for f in mart["by_field"]
    ]
    add_styled_table(doc, ["Bidang Produksi", "Penjualan Kotor", "Pendapatan Bersih", "Kebocoran Bersih", "Rasio Kebocoran"], field_rows, col_widths=[1.5, 1.35, 1.35, 1.25, 0.95])

    plat_rows = [
        [
            p["platform_name"],
            f"Rp {p['gross_idr']:,.2f}",
            f"Rp {p['pfee_idr']:,.2f}",
            f"Rp {p['prcfee_idr']:,.2f}",
            f"Rp {p['ref_idr']:,.2f}",
            f"Rp {p['frev_idr']:,.2f}",
            f"Rp {p['net_idr']:,.2f}",
            f"{p['leakage_pct']:.2f}%",
        ]
        for p in mart["by_platform"]
    ]
    add_styled_table(
        doc,
        ["Platform", "Gross", "Platform Fee", "Proc Fee", "Refund", "Reversal", "Net IDR", "Leakage %"],
        plat_rows,
        col_widths=[0.85, 0.85, 0.85, 0.75, 0.8, 0.75, 0.9, 0.65],
    )

    fx_rows = [
        [
            c["currency_code"],
            f"{c['net_orig']:,.2f}",
            f"Rp {c['net_idr']:,.2f}",
            f"Rp {c['avg_fx']:,.2f}",
            f"Rp {c['min_fx']:,.2f} s.d. Rp {c['max_fx']:,.2f}",
            f"{c['share_pct']:.2f}%",
        ]
        for c in mart["by_currency"]
    ]
    add_styled_table(doc, ["Mata Uang", "Net Asal", "Net IDR", "Rata-rata Kurs", "Rentang Kurs ECB", "Porsi %"], fx_rows, col_widths=[0.75, 0.95, 1.25, 1.0, 1.65, 0.8])

    add_bullet(doc, "Temuan Q1: Komisi Klien menopang 83,01% arus kas secara merata setiap bulan, sedangkan Penjualan Gim Video (9,75%) terkonsentrasi pada musim diskon Juni, Juli, November, dan Desember.")
    add_bullet(doc, "Temuan Q2: Bidang Full Game Dev mengalami rasio kebocoran terbesar (32,17%) dibanding bidang komisi dan aset (16,29% sampai 17,75%) akibat potongan 30% di Steam.")
    add_bullet(doc, "Temuan Q3: Kebocoran di Fiverr mencapai 25,94% dibandingkan VGen (13,39%) dan Direct PayPal (9,77%). Memindahkan klien komisi berulang dari Fiverr ke VGen atau PayPal langsung menghemat sekitar 12 sampai 16 poin persentase penjualan kotor.")
    add_bullet(doc, "Temuan Q4: 95,38% pendapatan studio berdenominasi valuta asing (USD 58,42%) dengan fluktuasi USD/IDR hingga sekitar Rp 2.072 sepanjang periode ECB 2025 hingga 2026, membuktikan pentingnya pencatatan kurs per tanggal peristiwa.")

    add_subheading(doc, "Hasil Suite Validasi Otomatis (sql/03_validate.sql)")
    val_rows = [
        ["V1", "Row counts per layer", f"{etl_meta['edw_counts']['edw.fact_revenue_event']:,} fact rows", "reported", "INFO"],
        ["V2", "Orphan FKs in fact_revenue_event", "0", "= 0", "PASS"],
        ["V3", "Sign rule violations", "0", "= 0", "PASS"],
        ["V4", "Duplicate transaction_code", "0", "= 0", "PASS"],
        ["V5", "Refunds exceeding parent sale", "0", "= 0", "PASS"],
        ["V6", "Broken parent_transaction_code links", "0", "= 0", "PASS"],
        ["V7", "Multi-tip orders kept separate", "33", "> 0", "PASS"],
        ["V8", "Invalid stream and platform pair", "0", "= 0", "PASS"],
        ["V9", "Stream vs project_type mismatch", "0", "= 0", "PASS"],
        ["V10", "IDR conversion rounding check", "0", "= 0", "PASS"],
        ["V11", "Weekend FX fallback check", "1,615 rows (0 bad)", "> 0 and 0 bad", "PASS"],
        ["V12", "Processing fee reversed on refund", "0", "= 0", "PASS"],
        ["V13", "PII columns in edw or mart", "0", "= 0", "PASS"],
        ["V14", "Quarantined rows in stg.etl_rejects", f"{etl_meta['rejects_count']} rows", "reported", "INFO"],
    ]
    add_styled_table(doc, ["ID", "Pemeriksaan", "Hasil Aktual", "Aturan", "Status"], val_rows, col_widths=[0.5, 2.5, 1.4, 1.1, 0.9])

    doc.add_heading("10. Kesimpulan dan Pengembangan Lanjutan", level=1)
    doc.add_paragraph(
        "Data Warehouse pendapatan Wasaka Interactive berhasil menjawab permasalahan fragmentasi lima format sumber, "
        "distorsi nilai bersih akibat biaya pemrosesan dan refund, serta ketidakakuratan kurs akhir bulan. "
        "Seluruh rangkaian mulai dari skema Star Schema enam tabel yang terkunci, pipa ETL idempoten di DuckDB, "
        "14 validasi otomatis (12 PASS, 2 INFO, 0 FAIL), hingga aplikasi kueri Streamlit tanpa menulis SQL telah selesai "
        "dan siap didemonstrasikan pada sesi presentasi serta penilaian peer-review."
    )
    doc.add_paragraph(
        "Pengembangan lanjutan yang disiapkan untuk fase produksi meliputi pemuatan inkremental berbasis tanggal agar "
        "tidak perlu mengulang seluruh riwayat, penerapan Slowly Changing Dimension (SCD Type 2) bila kategori proyek "
        "berubah, penambahan tabel fakta pengeluaran untuk analisis laba bersih, serta pembatasan akses berbasis peran "
        "(RBAC) saat aplikasi dipasang pada server bersama. Dokumen terpisah Kesimpulan setelah peer-review akan "
        "disusun setelah sesi presentasi kelas dan masukan dari kedua reviewer selesai dikumpulkan."
    )

    doc.save(str(OUT_DOCX))
    print(f"Saved report to {OUT_DOCX} ({OUT_DOCX.stat().st_size} bytes)")


if __name__ == "__main__":
    build_report()
