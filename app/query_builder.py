DIMENSIONS = {
    "Tahun": {"col": "year", "alias": "tahun", "is_time": True},
    "Kuartal": {"col": "quarter_label", "alias": "kuartal", "is_time": True},
    "Bulan": {"col": "year_month", "alias": "bulan", "is_time": True},
    "Aliran Pendapatan": {"col": "revenue_stream_name", "alias": "aliran_pendapatan", "is_time": False},
    "Platform": {"col": "platform_name", "alias": "platform", "is_time": False},
    "Proyek": {"col": "project_name", "alias": "proyek", "is_time": False},
    "Bidang Produksi": {"col": "production_field", "alias": "bidang_produksi", "is_time": False},
    "Mata Uang": {"col": "currency_code", "alias": "mata_uang", "is_time": False},
    "Jenis Peristiwa": {"col": "event_type", "alias": "jenis_peristiwa", "is_time": False},
    "Hari Kerja / Akhir Pekan": {"col": "day_category", "alias": "kategori_hari", "is_time": False},
}

CURRENCY_GROUP_KEY = "Mata Uang"

MEASURES = {
    "Pendapatan Bersih (IDR)": {
        "expr": "COALESCE(SUM(amount_idr), 0)",
        "alias": "pendapatan_bersih_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Penjualan Kotor (IDR)": {
        "expr": "COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'SALE'), 0)",
        "alias": "penjualan_kotor_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Tip (IDR)": {
        "expr": "COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'TIP'), 0)",
        "alias": "tip_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Biaya Platform (IDR)": {
        "expr": "COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'PLATFORM_FEE'), 0)",
        "alias": "biaya_platform_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Biaya Pemrosesan (IDR)": {
        "expr": "COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'PROCESSING_FEE'), 0)",
        "alias": "biaya_pemrosesan_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Refund (IDR)": {
        "expr": "COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'REFUND'), 0)",
        "alias": "refund_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Pembalikan Biaya (IDR)": {
        "expr": "COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'FEE_REVERSAL'), 0)",
        "alias": "pembalikan_biaya_idr",
        "fmt": "idr",
        "needs_currency": False,
    },
    "Kebocoran Biaya & Refund (%)": {
        "expr": (
            "ROUND(CASE WHEN COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'SALE'), 0) > 0 "
            "THEN -(COALESCE(SUM(amount_idr) FILTER (WHERE event_type IN ('PLATFORM_FEE', 'PROCESSING_FEE', 'REFUND')), 0) "
            "+ COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'FEE_REVERSAL'), 0)) * 100.0 "
            "/ (SUM(amount_idr) FILTER (WHERE event_type = 'SALE')) ELSE 0 END, 2)"
        ),
        "alias": "rasio_kebocoran_persen",
        "fmt": "pct",
        "needs_currency": False,
    },
    "Jumlah Peristiwa": {
        "expr": "COUNT(*)",
        "alias": "jumlah_peristiwa",
        "fmt": "int",
        "needs_currency": False,
    },
    "Nilai Mata Uang Asal": {
        "expr": "COALESCE(SUM(amount_orig), 0)",
        "alias": "nilai_mata_uang_asal",
        "fmt": "orig",
        "needs_currency": True,
    },
    "Rata-rata Kurs ke IDR": {
        "expr": "ROUND(AVG(exchange_rate_to_idr), 4)",
        "alias": "rata_rata_kurs_idr",
        "fmt": "fx",
        "needs_currency": True,
    },
}

FILTER_COLUMNS = {
    "streams": "revenue_stream_name",
    "platforms": "platform_name",
    "projects": "project_name",
    "production_fields": "production_field",
    "currencies": "currency_code",
    "event_types": "event_type",
}


def build_query(
    selected_measures,
    selected_dimensions,
    start_date,
    end_date,
    filters,
    sort_by_measure,
    sort_desc=True,
    limit_n=50,
):
    if not selected_measures:
        raise ValueError("Pilih minimal satu metrik.")
    if len(selected_dimensions) > 3:
        raise ValueError("Maksimal 3 atribut pengelompokan.")

    has_currency = CURRENCY_GROUP_KEY in selected_dimensions

    dim_specs = []
    for key in selected_dimensions:
        if key not in DIMENSIONS:
            raise ValueError(f"Dimensi tidak valid: {key}")
        dim_specs.append(DIMENSIONS[key])

    measure_specs = []
    for key in selected_measures:
        if key not in MEASURES:
            raise ValueError(f"Metrik tidak valid: {key}")
        spec = MEASURES[key]
        if spec["needs_currency"] and not has_currency:
            raise ValueError(f"Metrik '{key}' hanya bisa dipakai jika dikelompokkan per Mata Uang.")
        measure_specs.append(spec)

    select_parts = [f"{d['col']} AS {d['alias']}" for d in dim_specs]
    select_parts.extend(f"{m['expr']} AS {m['alias']}" for m in measure_specs)

    where_clauses = []
    params = []

    if start_date is not None:
        where_clauses.append("full_date >= ?")
        params.append(start_date.isoformat())
    if end_date is not None:
        where_clauses.append("full_date <= ?")
        params.append(end_date.isoformat())

    for filter_key, values in filters.items():
        if not values:
            continue
        if filter_key not in FILTER_COLUMNS:
            raise ValueError(f"Filter tidak valid: {filter_key}")
        col = FILTER_COLUMNS[filter_key]
        placeholders = ", ".join("?" for _ in values)
        where_clauses.append(f"{col} IN ({placeholders})")
        params.extend(values)

    sql_lines = [
        "SELECT",
        "    " + ",\n    ".join(select_parts),
        "FROM edw.v_fact_enriched",
    ]

    if where_clauses:
        sql_lines.append("WHERE " + "\n  AND ".join(where_clauses))

    if dim_specs:
        sql_lines.append("GROUP BY " + ", ".join(d["col"] for d in dim_specs))

    order_alias = measure_specs[0]["alias"]
    if sort_by_measure and sort_by_measure in MEASURES:
        candidate = MEASURES[sort_by_measure]["alias"]
        if any(m["alias"] == candidate for m in measure_specs):
            order_alias = candidate

    direction = "DESC" if sort_desc else "ASC"
    if dim_specs and all(d["is_time"] for d in dim_specs) and sort_by_measure is None:
        sql_lines.append("ORDER BY " + ", ".join(f"{d['alias']} ASC" for d in dim_specs))
    else:
        sql_lines.append(f"ORDER BY {order_alias} {direction}")

    safe_limit = max(1, min(int(limit_n), 500))
    sql_lines.append(f"LIMIT {safe_limit};")

    return "\n".join(sql_lines), params
