from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class DimensionSpec:
    label: str
    column: str
    alias: str
    is_time: bool = False


@dataclass(frozen=True)
class MeasureSpec:
    label: str
    sql_expr: str
    alias: str
    format_kind: str  # "idr", "pct", "int", "orig", "fx"
    requires_currency_group: bool = False


DIMENSIONS: dict[str, DimensionSpec] = {
    "Tahun (Year)": DimensionSpec("Tahun (Year)", "year", "tahun", is_time=True),
    "Kuartal (Quarter)": DimensionSpec("Kuartal (Quarter)", "quarter_label", "kuartal", is_time=True),
    "Bulan (Year-Month)": DimensionSpec("Bulan (Year-Month)", "year_month", "bulan", is_time=True),
    "Aliran Pendapatan (Revenue Stream)": DimensionSpec(
        "Aliran Pendapatan (Revenue Stream)", "revenue_stream_name", "aliran_pendapatan"
    ),
    "Platform Distribusi (Platform)": DimensionSpec(
        "Platform Distribusi (Platform)", "platform_name", "platform"
    ),
    "Proyek / Produk (Project)": DimensionSpec(
        "Proyek / Produk (Project)", "project_name", "proyek"
    ),
    "Bidang Produksi (Production Field)": DimensionSpec(
        "Bidang Produksi (Production Field)", "production_field", "bidang_produksi"
    ),
    "Mata Uang (Currency)": DimensionSpec(
        "Mata Uang (Currency)", "currency_code", "mata_uang"
    ),
    "Jenis Peristiwa (Event Type)": DimensionSpec(
        "Jenis Peristiwa (Event Type)", "event_type", "jenis_peristiwa"
    ),
    "Kategori Hari (Weekend/Weekday)": DimensionSpec(
        "Kategori Hari (Weekend/Weekday)", "day_category", "kategori_hari"
    ),
}

CURRENCY_GROUP_KEY = "Mata Uang (Currency)"

MEASURES: dict[str, MeasureSpec] = {
    "Pendapatan Bersih / Net Revenue (IDR)": MeasureSpec(
        label="Pendapatan Bersih / Net Revenue (IDR)",
        sql_expr="COALESCE(SUM(amount_idr), 0)",
        alias="pendapatan_bersih_idr",
        format_kind="idr",
    ),
    "Penjualan Kotor / Gross Sales (IDR)": MeasureSpec(
        label="Penjualan Kotor / Gross Sales (IDR)",
        sql_expr="COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'SALE'), 0)",
        alias="penjualan_kotor_idr",
        format_kind="idr",
    ),
    "Tip Klien / Tips (IDR)": MeasureSpec(
        label="Tip Klien / Tips (IDR)",
        sql_expr="COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'TIP'), 0)",
        alias="tip_idr",
        format_kind="idr",
    ),
    "Potongan Platform / Platform Fees (IDR)": MeasureSpec(
        label="Potongan Platform / Platform Fees (IDR)",
        sql_expr="COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'PLATFORM_FEE'), 0)",
        alias="biaya_platform_idr",
        format_kind="idr",
    ),
    "Biaya Pemrosesan / Processing Fees (IDR)": MeasureSpec(
        label="Biaya Pemrosesan / Processing Fees (IDR)",
        sql_expr="COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'PROCESSING_FEE'), 0)",
        alias="biaya_pemrosesan_idr",
        format_kind="idr",
    ),
    "Pengembalian Dana / Refunds (IDR)": MeasureSpec(
        label="Pengembalian Dana / Refunds (IDR)",
        sql_expr="COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'REFUND'), 0)",
        alias="refund_idr",
        format_kind="idr",
    ),
    "Pembalikan Biaya / Fee Reversals (IDR)": MeasureSpec(
        label="Pembalikan Biaya / Fee Reversals (IDR)",
        sql_expr="COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'FEE_REVERSAL'), 0)",
        alias="pembalikan_biaya_idr",
        format_kind="idr",
    ),
    "Rasio Kebocoran Biaya & Refund (%)": MeasureSpec(
        label="Rasio Kebocoran Biaya & Refund (%)",
        sql_expr=(
            "ROUND(CASE WHEN COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'SALE'), 0) > 0 "
            "THEN -(COALESCE(SUM(amount_idr) FILTER (WHERE event_type IN ('PLATFORM_FEE', 'PROCESSING_FEE', 'REFUND')), 0) "
            "+ COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'FEE_REVERSAL'), 0)) * 100.0 "
            "/ (SUM(amount_idr) FILTER (WHERE event_type = 'SALE')) ELSE 0 END, 2)"
        ),
        alias="rasio_kebocoran_persen",
        format_kind="pct",
    ),
    "Jumlah Peristiwa / Event Count": MeasureSpec(
        label="Jumlah Peristiwa / Event Count",
        sql_expr="COUNT(*)",
        alias="jumlah_peristiwa",
        format_kind="int",
    ),
    "Nilai Mata Uang Asal / Original Amount": MeasureSpec(
        label="Nilai Mata Uang Asal / Original Amount",
        sql_expr="COALESCE(SUM(amount_orig), 0)",
        alias="nilai_mata_uang_asal",
        format_kind="orig",
        requires_currency_group=True,
    ),
    "Rata-rata Kurs ke IDR / Avg FX Rate": MeasureSpec(
        label="Rata-rata Kurs ke IDR / Avg FX Rate",
        sql_expr="ROUND(AVG(exchange_rate_to_idr), 4)",
        alias="rata_rata_kurs_idr",
        format_kind="fx",
        requires_currency_group=True,
    ),
}

FILTER_COLUMNS: dict[str, str] = {
    "streams": "revenue_stream_name",
    "platforms": "platform_name",
    "projects": "project_name",
    "production_fields": "production_field",
    "currencies": "currency_code",
    "event_types": "event_type",
}


def build_whitelisted_query(
    selected_measures: list[str],
    selected_dimensions: list[str],
    start_date: date | None,
    end_date: date | None,
    filters: dict[str, list[str]],
    sort_by_measure: str | None,
    sort_Descending: bool = True,
    limit_n: int = 50,
) -> tuple[str, list[Any]]:
    if not selected_measures:
        raise ValueError("Pilih minimal satu metrik pengukuran.")
    if len(selected_dimensions) > 3:
        raise ValueError("Maksimal 3 atribut pengelompokan (Group By).")

    has_currency_group = CURRENCY_GROUP_KEY in selected_dimensions

    dim_specs: list[DimensionSpec] = []
    for d_key in selected_dimensions:
        if d_key not in DIMENSIONS:
            raise ValueError(f"Dimensi tidak dikenali: {d_key}")
        dim_specs.append(DIMENSIONS[d_key])

    measure_specs: list[MeasureSpec] = []
    for m_key in selected_measures:
        if m_key not in MEASURES:
            raise ValueError(f"Metrik tidak dikenali: {m_key}")
        m_spec = MEASURES[m_key]
        if m_spec.requires_currency_group and not has_currency_group:
            raise ValueError(
                f"Metrik '{m_key}' hanya diizinkan jika dikelompokkan berdasarkan Mata Uang (Currency)."
            )
        measure_specs.append(m_spec)

    select_parts: list[str] = [f"{d.column} AS {d.alias}" for d in dim_specs]
    select_parts.extend(f"{m.sql_expr} AS {m.alias}" for m in measure_specs)

    where_clauses: list[str] = []
    params: list[Any] = []

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
            raise ValueError(f"Filter tidak dikenali: {filter_key}")
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
        group_cols = ", ".join(d.column for d in dim_specs)
        sql_lines.append(f"GROUP BY {group_cols}")

    order_alias = measure_specs[0].alias
    if sort_by_measure and sort_by_measure in MEASURES:
        candidate = MEASURES[sort_by_measure]
        if any(m.alias == candidate.alias for m in measure_specs):
            order_alias = candidate.alias

    direction = "DESC" if sort_Descending else "ASC"
    if dim_specs and all(d.is_time for d in dim_specs) and sort_by_measure is None:
        time_order = ", ".join(f"{d.alias} ASC" for d in dim_specs)
        sql_lines.append(f"ORDER BY {time_order}")
    else:
        sql_lines.append(f"ORDER BY {order_alias} {direction}")

    safe_limit = max(1, min(int(limit_n), 500))
    sql_lines.append(f"LIMIT {safe_limit};")

    return "\n".join(sql_lines), params
