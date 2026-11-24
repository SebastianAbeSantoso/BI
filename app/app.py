import json
import pathlib
import sys
from datetime import date

import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import config
from query_builder import CURRENCY_GROUP_KEY, DIMENSIONS, MEASURES, build_query

st.set_page_config(
    page_title="Wasaka Interactive Revenue DW",
    layout="wide",
)


@st.cache_resource
def get_connection():
    if not config.DB_PATH.exists():
        raise FileNotFoundError(
            f"Database belum ada di {config.DB_PATH}. Jalankan python src/etl.py terlebih dulu."
        )
    return duckdb.connect(str(config.DB_PATH), read_only=True)


def fmt_idr(value):
    sign = "-" if value < 0 else ""
    return f"{sign}Rp {abs(float(value)):,.0f}"


def load_options(con):
    min_d, max_d = con.execute(
        """
        SELECT MIN(d.full_date), MAX(d.full_date)
        FROM edw.fact_revenue_event f
        INNER JOIN edw.dim_date d ON f.date_key = d.date_key
        """
    ).fetchone()
    return {
        "min_date": min_d,
        "max_date": max_d,
        "streams": [r[0] for r in con.execute("SELECT revenue_stream_name FROM edw.dim_revenue_stream ORDER BY revenue_stream_key").fetchall()],
        "platforms": [r[0] for r in con.execute("SELECT platform_name FROM edw.dim_platform ORDER BY platform_key").fetchall()],
        "projects": [r[0] for r in con.execute("SELECT project_name FROM edw.dim_project ORDER BY project_key").fetchall()],
        "production_fields": [r[0] for r in con.execute("SELECT DISTINCT production_field FROM edw.dim_project ORDER BY production_field").fetchall()],
        "currencies": [r[0] for r in con.execute("SELECT currency_code FROM edw.dim_currency ORDER BY currency_key").fetchall()],
        "event_types": ["SALE", "TIP", "FEE_REVERSAL", "PLATFORM_FEE", "PROCESSING_FEE", "REFUND"],
    }


def main():
    st.title("Wasaka Interactive: Revenue Data Warehouse")
    st.caption(
        "DuckDB (stg, edw, mart). Data transaksi disimulasikan dari aturan biaya platform; kurs historis diambil dari ECB (Frankfurter API)."
    )

    try:
        con = get_connection()
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    with st.sidebar:
        st.header("Ringkasan DW")
        kpi_row = con.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(amount_idr) FILTER (WHERE event_type = 'SALE'), 0),
                COALESCE(SUM(amount_idr), 0)
            FROM edw.fact_revenue_event
            """
        ).fetchone()
        st.metric("Jumlah Event Fakta", f"{kpi_row[0]:,}")
        st.metric("Penjualan Kotor (IDR)", fmt_idr(kpi_row[1]))
        st.metric("Pendapatan Bersih (IDR)", fmt_idr(kpi_row[2]))
        st.divider()
        st.write("Skema: 1 tabel fakta (`fact_revenue_event`) dan 5 tabel dimensi (`date`, `revenue_stream`, `platform`, `project`, `currency`). Mode baca saja.")
        if st.button("Muat Ulang Koneksi"):
            st.cache_resource.clear()
            st.rerun()

    opts = load_options(con)

    tab_qb, tab_bq, tab_val = st.tabs([
        "1. Pembuat Kueri",
        "2. Empat Pertanyaan Bisnis",
        "3. Arsitektur & Validasi",
    ])

    with tab_qb:
        st.subheader("Pembuat Kueri Tanpa SQL")
        st.write("Pilih pengelompokan, metrik, dan filter di bawah ini. SQL dibentuk dari daftar kolom tetap dengan nilai filter berparameter.")

        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            selected_dims = st.multiselect(
                "Kelompokkan berdasarkan (0 sampai 3 atribut):",
                options=list(DIMENSIONS.keys()),
                default=["Aliran Pendapatan", "Platform"],
                max_selections=3,
            )
        has_currency = CURRENCY_GROUP_KEY in selected_dims
        with col_g2:
            if has_currency:
                st.success("Pengelompokan Mata Uang aktif. Metrik nilai mata uang asal dan rata-rata kurs bisa dipilih.")
            else:
                st.info("Pilih Mata Uang di pengelompokan jika ingin menampilkan nilai mata uang asal atau rata-rata kurs (agar mata uang berbeda tidak dijumlahkan).")

        available_measures = [
            key for key, spec in MEASURES.items()
            if (not spec["needs_currency"]) or has_currency
        ]
        default_measures = [
            "Penjualan Kotor (IDR)",
            "Pendapatan Bersih (IDR)",
            "Kebocoran Biaya & Refund (%)",
        ]
        selected_measures = st.multiselect(
            "Metrik yang dihitung:",
            options=available_measures,
            default=[m for m in default_measures if m in available_measures],
        )

        with st.expander("Filter Data (opsional)", expanded=False):
            f1, f2, f3 = st.columns(3)
            with f1:
                date_range = st.date_input(
                    "Rentang tanggal:",
                    value=(opts["min_date"], opts["max_date"]),
                    min_value=date(2025, 1, 1),
                    max_value=date(2026, 12, 31),
                )
                f_streams = st.multiselect("Aliran Pendapatan:", opts["streams"])
            with f2:
                f_platforms = st.multiselect("Platform:", opts["platforms"])
                f_fields = st.multiselect("Bidang Produksi:", opts["production_fields"])
            with f3:
                f_projects = st.multiselect("Proyek:", opts["projects"])
                f_currencies = st.multiselect("Mata Uang:", opts["currencies"])
                f_events = st.multiselect("Jenis Peristiwa:", opts["event_types"])

        s1, s2, s3 = st.columns([2, 1, 1])
        with s1:
            sort_measure = st.selectbox(
                "Urutkan menurut:",
                options=selected_measures if selected_measures else available_measures[:1],
            )
        with s2:
            sort_dir = st.radio("Urutan:", ["Menurun (DESC)", "Menaik (ASC)"], horizontal=True)
        with s3:
            limit_n = st.number_input("Batas baris:", min_value=5, max_value=500, value=50, step=5)

        if not selected_measures:
            st.warning("Pilih minimal satu metrik.")
        else:
            start_d = date_range[0] if isinstance(date_range, (list, tuple)) and len(date_range) >= 1 else opts["min_date"]
            end_d = date_range[1] if isinstance(date_range, (list, tuple)) and len(date_range) >= 2 else start_d

            sql_query, sql_params = build_query(
                selected_measures=selected_measures,
                selected_dimensions=selected_dims,
                start_date=start_d,
                end_date=end_d,
                filters={
                    "streams": f_streams,
                    "platforms": f_platforms,
                    "projects": f_projects,
                    "production_fields": f_fields,
                    "currencies": f_currencies,
                    "event_types": f_events,
                },
                sort_by_measure=sort_measure,
                sort_desc=sort_dir.startswith("Menurun"),
                limit_n=int(limit_n),
            )

            res_df = con.execute(sql_query, sql_params).df()

            if res_df.empty:
                st.warning("Tidak ada baris yang cocok dengan filter tersebut.")
            else:
                col_cfg = {}
                for m_key in selected_measures:
                    spec = MEASURES[m_key]
                    if spec["fmt"] == "idr":
                        col_cfg[spec["alias"]] = st.column_config.NumberColumn(m_key, format="Rp %.0f")
                    elif spec["fmt"] == "pct":
                        col_cfg[spec["alias"]] = st.column_config.NumberColumn(m_key, format="%.2f %%")
                    elif spec["fmt"] == "int":
                        col_cfg[spec["alias"]] = st.column_config.NumberColumn(m_key, format="%d")
                    elif spec["fmt"] == "orig":
                        col_cfg[spec["alias"]] = st.column_config.NumberColumn(m_key, format="%.2f")
                    elif spec["fmt"] == "fx":
                        col_cfg[spec["alias"]] = st.column_config.NumberColumn(m_key, format="Rp %.4f")

                st.dataframe(res_df, width="stretch", hide_index=True, column_config=col_cfg)

                if selected_dims:
                    first_dim = DIMENSIONS[selected_dims[0]]
                    primary_measure = MEASURES[selected_measures[0]]
                    color_col = DIMENSIONS[selected_dims[1]]["alias"] if len(selected_dims) >= 2 else None
                    chart_df = res_df.sort_values(first_dim["alias"]) if first_dim["is_time"] else res_df

                    if first_dim["is_time"]:
                        fig = px.line(
                            chart_df,
                            x=first_dim["alias"],
                            y=primary_measure["alias"],
                            color=color_col,
                            markers=True,
                            title=f"{selected_measures[0]} per {selected_dims[0]}",
                        )
                    else:
                        fig = px.bar(
                            chart_df,
                            x=first_dim["alias"],
                            y=primary_measure["alias"],
                            color=color_col,
                            barmode="group",
                            title=f"{selected_measures[0]} per {selected_dims[0]}",
                        )
                    st.plotly_chart(fig, width="stretch")

                st.download_button(
                    label="Unduh CSV",
                    data=res_df.to_csv(index=False).encode("utf-8"),
                    file_name="wasaka_dw_query_result.csv",
                    mime="text/csv",
                )

            with st.expander("Lihat SQL yang dijalankan"):
                st.code(sql_query, language="sql")
                if sql_params:
                    st.write(f"Parameter: `{sql_params}`")
                st.caption(
                    "`edw.v_fact_enriched` menggabungkan `edw.fact_revenue_event` dengan `dim_date`, `dim_revenue_stream`, `dim_platform`, `dim_project`, dan `dim_currency`."
                )

    with tab_bq:
        st.subheader("Empat Pertanyaan Bisnis")
        q1, q2, q3, q4 = st.tabs([
            "Q1: Bauran & Tren",
            "Q2: Proyek & Bidang",
            "Q3: Biaya & Refund",
            "Q4: Eksposur Kurs",
        ])

        with q1:
            st.markdown("#### 1. Bagaimana bauran dan tren pendapatan bersih per bulan?")
            sql_q1 = """
                SELECT
                    year_month,
                    revenue_stream_name,
                    SUM(gross_sales_idr) AS gross_sales_idr,
                    SUM(tips_idr) AS tips_idr,
                    SUM(net_revenue_idr) AS net_revenue_idr,
                    SUM(event_count) AS event_count
                FROM mart.v_revenue_monthly
                GROUP BY year_month, revenue_stream_name
                ORDER BY year_month ASC, revenue_stream_name ASC;
            """
            df_q1 = con.execute(sql_q1).df()
            fig_q1 = px.area(
                df_q1,
                x="year_month",
                y="net_revenue_idr",
                color="revenue_stream_name",
                title="Pendapatan Bersih Bulanan per Aliran Pendapatan (IDR)",
                labels={"year_month": "Bulan", "net_revenue_idr": "Pendapatan Bersih (IDR)", "revenue_stream_name": "Aliran Pendapatan"},
            )
            st.plotly_chart(fig_q1, width="stretch")
            st.caption("Penjualan gim melonjak saat periode diskon Juni, Juli, November, dan Desember, sedangkan komisi klien lebih merata tiap bulan.")
            st.dataframe(df_q1, width="stretch", hide_index=True)
            with st.expander("Lihat SQL Q1"):
                st.code(sql_q1.strip(), language="sql")

        with q2:
            st.markdown("#### 2. Bagaimana perbandingan kinerja proyek dan bidang produksi?")
            sql_q2 = """
                SELECT
                    project_code,
                    project_name,
                    production_field,
                    revenue_stream_name,
                    gross_sales_idr,
                    tips_idr,
                    net_leakage_idr,
                    net_revenue_idr,
                    leakage_pct,
                    sale_count
                FROM mart.v_project_performance
                ORDER BY net_revenue_idr DESC;
            """
            df_q2 = con.execute(sql_q2).df()
            c_left, c_right = st.columns(2)
            with c_left:
                fig_q2_proj = px.bar(
                    df_q2,
                    x="net_revenue_idr",
                    y="project_name",
                    color="production_field",
                    orientation="h",
                    title="Pendapatan Bersih per Proyek (IDR)",
                )
                fig_q2_proj.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_q2_proj, width="stretch")
            with c_right:
                df_q2_field = (
                    df_q2.groupby("production_field", as_index=False)[["gross_sales_idr", "net_revenue_idr", "net_leakage_idr"]]
                    .sum()
                    .sort_values("net_revenue_idr", ascending=False)
                )
                fig_q2_field = px.bar(
                    df_q2_field,
                    x="production_field",
                    y=["net_revenue_idr", "net_leakage_idr"],
                    barmode="group",
                    title="Pendapatan Bersih vs Potongan per Bidang Produksi (IDR)",
                )
                st.plotly_chart(fig_q2_field, width="stretch")
            st.caption("Perbandingan seluruh proyek dan 6 bidang produksi setelah potongan platform, pemrosesan, dan refund.")
            st.dataframe(df_q2, width="stretch", hide_index=True)
            with st.expander("Lihat SQL Q2"):
                st.code(sql_q2.strip(), language="sql")

        with q3:
            st.markdown("#### 3. Berapa pendapatan yang tergerus biaya platform dan refund?")
            sql_q3 = """
                SELECT
                    platform_name,
                    SUM(gross_sales_idr) AS gross_sales_idr,
                    SUM(tips_idr) AS tips_idr,
                    SUM(platform_fees_idr) AS platform_fees_idr,
                    SUM(processing_fees_idr) AS processing_fees_idr,
                    SUM(refunds_idr) AS refunds_idr,
                    SUM(fee_reversals_idr) AS fee_reversals_idr,
                    SUM(net_leakage_idr) AS net_leakage_idr,
                    SUM(net_revenue_idr) AS net_revenue_idr,
                    ROUND(
                        SUM(net_leakage_idr) * 100.0 / NULLIF(SUM(gross_sales_idr), 0),
                        2
                    ) AS leakage_pct
                FROM mart.v_fee_refund_leakage
                GROUP BY platform_name
                ORDER BY leakage_pct DESC;
            """
            df_q3 = con.execute(sql_q3).df()
            fig_q3 = go.Figure()
            fig_q3.add_trace(go.Bar(name="Penjualan Kotor", x=df_q3["platform_name"], y=df_q3["gross_sales_idr"]))
            fig_q3.add_trace(go.Bar(name="Kebocoran Bersih", x=df_q3["platform_name"], y=df_q3["net_leakage_idr"]))
            fig_q3.add_trace(go.Bar(name="Pendapatan Bersih", x=df_q3["platform_name"], y=df_q3["net_revenue_idr"]))
            fig_q3.update_layout(
                barmode="group",
                title="Penjualan Kotor, Kebocoran, dan Pendapatan Bersih per Platform (IDR)",
            )
            st.plotly_chart(fig_q3, width="stretch")
            st.caption("Steam (30%) dan Fiverr (20%) memotong porsi terbesar; pada Direct PayPal, biaya pemrosesan tidak kembali saat refund.")
            st.dataframe(df_q3, width="stretch", hide_index=True)
            with st.expander("Lihat SQL Q3"):
                st.code(sql_q3.strip(), language="sql")

        with q4:
            st.markdown("#### 4. Seberapa besar eksposur terhadap mata uang asing dan kurs?")
            sql_q4_share = """
                SELECT
                    currency_code,
                    currency_name,
                    SUM(net_amount_orig) AS total_net_orig,
                    SUM(net_revenue_idr) AS total_net_idr,
                    ROUND(AVG(avg_exchange_rate_to_idr), 2) AS mean_rate_to_idr,
                    ROUND(
                        SUM(net_revenue_idr) * 100.0 / NULLIF(SUM(SUM(net_revenue_idr)) OVER (), 0),
                        2
                    ) AS share_of_net_pct
                FROM mart.v_fx_exposure
                GROUP BY currency_code, currency_name
                ORDER BY total_net_idr DESC;
            """
            sql_q4_trend = """
                SELECT
                    year_month,
                    currency_code,
                    avg_exchange_rate_to_idr,
                    net_revenue_idr
                FROM mart.v_fx_exposure
                WHERE currency_code <> 'IDR'
                ORDER BY year_month ASC, currency_code ASC;
            """
            df_q4_share = con.execute(sql_q4_share).df()
            df_q4_trend = con.execute(sql_q4_trend).df()

            fx1, fx2 = st.columns(2)
            with fx1:
                fig_fx_pie = px.pie(
                    df_q4_share,
                    names="currency_code",
                    values="total_net_idr",
                    hole=0.4,
                    title="Porsi Pendapatan Bersih per Mata Uang Asal (IDR)",
                )
                st.plotly_chart(fig_fx_pie, width="stretch")
            with fx2:
                sel_cur = st.selectbox(
                    "Pilih mata uang asing:",
                    options=[c for c in df_q4_share["currency_code"].tolist() if c != "IDR"],
                )
                sub_fx = df_q4_trend[df_q4_trend["currency_code"] == sel_cur]
                fig_fx_line = px.line(
                    sub_fx,
                    x="year_month",
                    y="avg_exchange_rate_to_idr",
                    markers=True,
                    title=f"Rata-rata Kurs Bulanan {sel_cur} ke IDR",
                )
                st.plotly_chart(fig_fx_line, width="stretch")

            st.caption("Sebagian besar transaksi terjadi dalam mata uang asing sehingga konversi memakai kurs spot pada tanggal kejadian.")
            st.dataframe(df_q4_share, width="stretch", hide_index=True)
            with st.expander("Lihat SQL Q4"):
                st.code(sql_q4_share.strip() + "\n\n" + sql_q4_trend.strip(), language="sql")

    with tab_val:
        st.subheader("Arsitektur dan Hasil Validasi (V1 sampai V14)")
        st.write(
            "Alur data: 5 file ekspor platform + API kurs ECB masuk ke skema stg (mentah), "
            "dibersihkan di Python ETL (hapus PII, deduplikasi, pemetaan judul, konversi kurs dengan fallback hari kerja sebelumnya), "
            "dimuat ke 6 tabel star schema di skema edw, lalu dibaca lewat view di skema mart."
        )

        etl_log_path = config.REPORT_DIR / "etl_last_run.json"
        if etl_log_path.exists():
            etl_meta = json.loads(etl_log_path.read_text(encoding="utf-8"))
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Baris Fakta (edw)", f"{etl_meta['edw_counts'].get('edw.fact_revenue_event', 0):,}")
            m2.metric("Duplikat Dihapus", f"{etl_meta['duplicates_removed'].get('fiverr_earnings.csv', 0)}")
            m3.metric("Fallback Kurs Akhir Pekan", f"{etl_meta.get('fx_fallback_lookups', 0):,}")
            m4.metric("Baris Dikarantina", f"{etl_meta.get('rejects_count', 0)}")

        val_sql = (config.SQL_DIR / "03_validate.sql").read_text(encoding="utf-8")
        df_val = con.execute(val_sql).df()
        st.markdown("#### Pemeriksaan V1 sampai V14")
        st.dataframe(df_val, width="stretch", hide_index=True)

        st.markdown("#### Baris Dikarantina (`stg.etl_rejects`)")
        df_rej = con.execute("SELECT * FROM stg.etl_rejects ORDER BY source, source_id").df()
        st.dataframe(df_rej, width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
