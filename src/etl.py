import bisect
import json
import pathlib
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import duckdb
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import config

TWO_DP = Decimal("0.01")
SIX_DP = Decimal("0.000001")


def d2(val):
    return Decimal(str(val)).quantize(TWO_DP, rounding=ROUND_HALF_UP)


def d6(val):
    return Decimal(str(val)).quantize(SIX_DP, rounding=ROUND_HALF_UP)


def parse_amount(raw):
    cleaned = re.sub(r"[^0-9,.\-]", "", str(raw).strip())
    if not cleaned:
        return Decimal("0.00")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." not in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        else:
            cleaned = cleaned.replace(",", "")
    return d2(cleaned)


class FXResolver:
    def __init__(self, fx_df):
        self.by_currency = {}
        self.exact = {}
        self.fallback_hits = 0

        for cur_code, grp in fx_df.groupby("currency_code"):
            sorted_grp = grp.sort_values("date")
            d_list = [date.fromisoformat(str(x)[:10]) for x in sorted_grp["date"]]
            r_list = [d6(x) for x in sorted_grp["rate_to_idr"]]
            self.by_currency[str(cur_code)] = (d_list, r_list)
            for dt_obj, rt_obj in zip(d_list, r_list):
                self.exact[(dt_obj, str(cur_code))] = rt_obj

    def get_rate(self, tx_date, currency_code):
        cur = currency_code.upper().strip()
        if cur == "IDR":
            return Decimal("1.000000")
        key = (tx_date, cur)
        if key in self.exact:
            return self.exact[key]
        d_list, r_list = self.by_currency[cur]
        idx = bisect.bisect_right(d_list, tx_date) - 1
        if idx < 0:
            idx = 0
        self.fallback_hits += 1
        return r_list[idx]


def build_dim_date():
    start_d = date.fromisoformat(config.DIM_DATE_START)
    end_d = date.fromisoformat(config.DIM_DATE_END)
    rows = []
    cur = start_d
    while cur <= end_d:
        iso_dow = cur.isoweekday()
        rows.append({
            "date_key": int(cur.strftime("%Y%m%d")),
            "full_date": cur,
            "day_of_week": cur.strftime("%A"),
            "day_of_week_number": iso_dow,
            "day_of_month": cur.day,
            "day_of_year": cur.timetuple().tm_yday,
            "month_name": cur.strftime("%B"),
            "month_number": cur.month,
            "quarter": (cur.month - 1) // 3 + 1,
            "year": cur.year,
            "is_weekend": iso_dow >= 6,
        })
        cur += timedelta(days=1)
    return pd.DataFrame(rows)


def match_project(title, rules):
    norm = str(title).lower().strip()
    for pattern, match_type, proj_code in rules:
        pat = pattern.lower().strip()
        if match_type == "exact" and norm == pat:
            return proj_code
        if pat in norm:
            return proj_code
    return None


def run_etl():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)

    stats = {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "stg_counts": {},
        "pii_columns_dropped": [],
        "duplicates_removed": {},
        "rejects_count": 0,
        "fx_fallback_lookups": 0,
        "edw_counts": {},
    }

    with duckdb.connect(str(config.DB_PATH)) as con:
        con.execute((config.SQL_DIR / "00_schemas.sql").read_text(encoding="utf-8"))

        df_projects_raw = pd.read_csv(config.RAW_DIR / "projects.csv", dtype=str)
        df_title_map_raw = pd.read_csv(config.RAW_DIR / "project_title_map.csv", dtype=str)
        df_fx_raw = pd.read_csv(config.RAW_DIR / "fx_rates.csv", dtype=str)
        df_steam_raw = pd.read_csv(config.RAW_DIR / "steam_sales_report.csv", dtype=str).fillna("")
        df_itch_raw = pd.read_csv(config.RAW_DIR / "itch_payouts.csv", dtype=str).fillna("")
        df_fiverr_raw = pd.read_csv(config.RAW_DIR / "fiverr_earnings.csv", dtype=str).fillna("")
        df_paypal_raw = pd.read_csv(config.RAW_DIR / "paypal_activity.csv", dtype=str).fillna("")

        vgen_orders = json.loads((config.RAW_DIR / "vgen_export.json").read_text(encoding="utf-8"))
        df_vgen_raw = pd.DataFrame([
            {
                "order_id": o["order_id"],
                "created_at": o["created_at"],
                "service_kind": o["service_kind"],
                "title": o["title"],
                "client_username": o.get("client_username", ""),
                "currency": o["currency"],
                "gross_amount": str(o["gross_amount"]),
                "vgen_fee": str(o["vgen_fee"]),
                "payment_proc_fee": str(o["payment_proc_fee"]),
                "tips_json": json.dumps(o.get("tips", [])),
                "refunds_json": json.dumps(o.get("refunds", [])),
            }
            for o in vgen_orders
        ])

        stg_tables = {
            "raw_projects": df_projects_raw,
            "raw_title_map": df_title_map_raw,
            "raw_fx_rates": df_fx_raw,
            "raw_steam": df_steam_raw,
            "raw_itch": df_itch_raw,
            "raw_vgen": df_vgen_raw,
            "raw_fiverr": df_fiverr_raw,
            "raw_paypal": df_paypal_raw,
        }
        for tbl_name, df_obj in stg_tables.items():
            con.register("tmp_df", df_obj)
            con.execute(f"CREATE OR REPLACE TABLE stg.{tbl_name} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
            stats["stg_counts"][f"stg.{tbl_name}"] = len(df_obj)

        pii_dropped = [
            "itch.buyer_email",
            "vgen.client_username",
            "fiverr.buyer_username",
            "paypal.payer_name",
            "paypal.payer_email",
        ]
        stats["pii_columns_dropped"] = pii_dropped
        df_itch = df_itch_raw.drop(columns=["buyer_email"])
        df_fiverr_clean = df_fiverr_raw.drop(columns=["buyer_username"])
        df_paypal = df_paypal_raw.drop(columns=["payer_name", "payer_email"])

        before_fiverr = len(df_fiverr_clean)
        df_fiverr = df_fiverr_clean.drop_duplicates().reset_index(drop=True)
        stats["duplicates_removed"]["fiverr_earnings.csv"] = int(before_fiverr - len(df_fiverr))

        dim_date_df = build_dim_date()
        dim_stream_df = pd.DataFrame(
            config.STATIC_STREAMS,
            columns=["revenue_stream_key", "revenue_stream_code", "revenue_stream_name", "description"],
        )
        dim_platform_df = pd.DataFrame(
            config.STATIC_PLATFORMS,
            columns=["platform_key", "platform_code", "platform_name", "platform_type"],
        )
        dim_currency_df = pd.DataFrame(
            config.STATIC_CURRENCIES,
            columns=["currency_key", "currency_code", "currency_name", "currency_symbol"],
        )
        dim_project_df = df_projects_raw[["project_code", "project_name", "project_type", "production_field"]].copy()
        dim_project_df.insert(0, "project_key", range(1, len(dim_project_df) + 1))

        stream_sk = dict(zip(dim_stream_df["revenue_stream_code"], dim_stream_df["revenue_stream_key"]))
        platform_sk = dict(zip(dim_platform_df["platform_code"], dim_platform_df["platform_key"]))
        currency_sk = dict(zip(dim_currency_df["currency_code"], dim_currency_df["currency_key"]))
        project_sk = dict(zip(dim_project_df["project_code"], dim_project_df["project_key"]))
        project_stream = dict(zip(df_projects_raw["project_code"], df_projects_raw["stream"]))

        rules = [
            (str(r["pattern"]), str(r["match_type"]), str(r["project_code"]))
            for _, r in df_title_map_raw.iterrows()
        ]
        fx = FXResolver(df_fx_raw)

        events = []
        rejects = []

        def emit_event(ev_date, proj_code, plat_code, cur_code, tx_code, parent_tx_code, ev_type, signed_orig):
            if signed_orig == Decimal("0.00"):
                return
            cur_norm = cur_code.upper().strip()
            rate = fx.get_rate(ev_date, cur_norm)
            amt_idr = d2(signed_orig * rate)
            stream_code = project_stream[proj_code]
            events.append({
                "date_key": int(ev_date.strftime("%Y%m%d")),
                "project_key": project_sk[proj_code],
                "platform_key": platform_sk[plat_code],
                "currency_key": currency_sk[cur_norm],
                "revenue_stream_key": stream_sk[stream_code],
                "transaction_code": tx_code,
                "parent_transaction_code": parent_tx_code,
                "event_type": ev_type,
                "amount_orig": signed_orig,
                "exchange_rate_to_idr": rate,
                "amount_idr": amt_idr,
            })

        for _, r in df_steam_raw.iterrows():
            tx_d = datetime.strptime(r["tx_date"], "%m/%d/%Y").date()
            p_code = r["game_code"].strip()
            if p_code not in project_sk:
                rejects.append({"source": "STEAM", "source_id": r["order_id"], "reason": f"Unknown game_code: {p_code}"})
                continue
            cur = r["buyer_currency"].upper().strip()
            gross_val = d2(r["gross_amount"])
            fee_val = d2(r["steam_fee_amount"])
            oid = r["order_id"].strip()

            if r["record_type"] == "SALE":
                root_code = f"STM-{oid}-SALE"
                emit_event(tx_d, p_code, "STEAM", cur, root_code, None, "SALE", abs(gross_val))
                emit_event(tx_d, p_code, "STEAM", cur, f"STM-{oid}-PFEE", root_code, "PLATFORM_FEE", -abs(fee_val))
            elif r["record_type"] == "REFUND":
                parent_oid = r["parent_order_id"].strip()
                root_code = f"STM-{parent_oid}-SALE"
                emit_event(tx_d, p_code, "STEAM", cur, f"STM-{oid}-REF", root_code, "REFUND", -abs(gross_val))
                emit_event(tx_d, p_code, "STEAM", cur, f"STM-{oid}-FREV", root_code, "FEE_REVERSAL", abs(fee_val))

        for _, r in df_itch.iterrows():
            tx_d = date.fromisoformat(r["payout_date"].strip())
            p_code = r["item_code"].strip()
            if p_code not in project_sk:
                rejects.append({"source": "ITCH", "source_id": r["itch_tx_id"], "reason": f"Unknown item_code: {p_code}"})
                continue
            cur = r["currency"].upper().strip()
            oid = r["itch_tx_id"].strip()
            gross = abs(parse_amount(r["gross_str"]))
            tip = abs(parse_amount(r["tip_str"]))
            itch_fee = abs(parse_amount(r["itch_share_str"]))
            proc_fee = abs(parse_amount(r["processor_fee_str"]))

            root_code = f"{oid}-SALE"
            emit_event(tx_d, p_code, "ITCH", cur, root_code, None, "SALE", gross)
            if tip > Decimal("0.00"):
                emit_event(tx_d, p_code, "ITCH", cur, f"{oid}-TIP1", root_code, "TIP", tip)
            emit_event(tx_d, p_code, "ITCH", cur, f"{oid}-PFEE", root_code, "PLATFORM_FEE", -itch_fee)
            emit_event(tx_d, p_code, "ITCH", cur, f"{oid}-PRCFEE", root_code, "PROCESSING_FEE", -proc_fee)

            if r["is_refunded"].strip().lower() == "yes" and r["refund_date"].strip():
                ref_d = date.fromisoformat(r["refund_date"].strip())
                emit_event(ref_d, p_code, "ITCH", cur, f"{oid}-REF", root_code, "REFUND", -gross)
                emit_event(ref_d, p_code, "ITCH", cur, f"{oid}-FREV", root_code, "FEE_REVERSAL", itch_fee)

        for o in vgen_orders:
            oid = str(o["order_id"]).strip()
            p_code = match_project(o["title"], rules)
            if p_code is None:
                rejects.append({
                    "source": "VGEN",
                    "source_id": oid,
                    "reason": f"Unmatched title: {o['title']}",
                })
                continue
            tx_d = date.fromisoformat(str(o["created_at"])[:10])
            cur = str(o["currency"]).upper().strip()
            gross = abs(d2(o["gross_amount"]))
            v_fee = abs(d2(o["vgen_fee"]))
            pr_fee = abs(d2(o["payment_proc_fee"]))

            root_code = f"{oid}-SALE"
            emit_event(tx_d, p_code, "VGEN", cur, root_code, None, "SALE", gross)
            emit_event(tx_d, p_code, "VGEN", cur, f"{oid}-PFEE", root_code, "PLATFORM_FEE", -v_fee)
            emit_event(tx_d, p_code, "VGEN", cur, f"{oid}-PRCFEE", root_code, "PROCESSING_FEE", -pr_fee)

            for idx_t, tip_obj in enumerate(o.get("tips", []), start=1):
                td = date.fromisoformat(str(tip_obj["paid_at"])[:10])
                t_amt = abs(d2(tip_obj["amount"]))
                emit_event(td, p_code, "VGEN", cur, f"{oid}-TIP{idx_t}", root_code, "TIP", t_amt)

            for idx_r, ref_obj in enumerate(o.get("refunds", []), start=1):
                rd = date.fromisoformat(str(ref_obj["refunded_at"])[:10])
                r_amt = min(gross, abs(d2(ref_obj["amount"])))
                r_frev = min(v_fee, abs(d2(ref_obj.get("vgen_fee_returned", 0))))
                emit_event(rd, p_code, "VGEN", cur, f"{oid}-REF{idx_r}", root_code, "REFUND", -r_amt)
                emit_event(rd, p_code, "VGEN", cur, f"{oid}-FREV{idx_r}", root_code, "FEE_REVERSAL", r_frev)

        valid_fiverr = {}
        for _, r in df_fiverr[df_fiverr["row_kind"] == "ORDER"].iterrows():
            oid = r["fiverr_order_id"].strip()
            p_code = match_project(r["order_title"], rules)
            if p_code is None:
                rejects.append({
                    "source": "FIVERR",
                    "source_id": oid,
                    "reason": f"Unmatched title: {r['order_title']}",
                })
                continue
            valid_fiverr[oid] = p_code
            tx_d = date.fromisoformat(r["clearing_date"].strip())
            cur = r["currency"].upper().strip()
            gross = abs(d2(r["gross_amount"]))
            fee = abs(d2(r["fiverr_commission"]))
            root_code = f"FVR-{oid}-SALE"
            emit_event(tx_d, p_code, "FIVERR", cur, root_code, None, "SALE", gross)
            emit_event(tx_d, p_code, "FIVERR", cur, f"FVR-{oid}-PFEE", root_code, "PLATFORM_FEE", -fee)

        for _, r in df_fiverr[df_fiverr["row_kind"] != "ORDER"].iterrows():
            oid = r["fiverr_order_id"].strip()
            parent_oid = r["parent_order_id"].strip()
            if parent_oid not in valid_fiverr:
                rejects.append({
                    "source": "FIVERR",
                    "source_id": oid,
                    "reason": f"Missing parent order: {parent_oid}",
                })
                continue
            p_code = valid_fiverr[parent_oid]
            root_code = f"FVR-{parent_oid}-SALE"
            tx_d = date.fromisoformat(r["clearing_date"].strip())
            cur = r["currency"].upper().strip()
            amt = abs(d2(r["gross_amount"]))
            fee = abs(d2(r["fiverr_commission"]))

            if r["row_kind"] == "TIP":
                emit_event(tx_d, p_code, "FIVERR", cur, f"FVR-{oid}", root_code, "TIP", amt)
                emit_event(tx_d, p_code, "FIVERR", cur, f"FVR-{oid}-PFEE", root_code, "PLATFORM_FEE", -fee)
            elif r["row_kind"].startswith("CANCELLATION"):
                emit_event(tx_d, p_code, "FIVERR", cur, f"FVR-{oid}-REF", root_code, "REFUND", -amt)
                emit_event(tx_d, p_code, "FIVERR", cur, f"FVR-{oid}-FREV", root_code, "FEE_REVERSAL", fee)

        valid_paypal = {}
        for _, r in df_paypal[df_paypal["tipe_aktivitas"] == "Direct Commission"].iterrows():
            pid = r["paypal_txn_id"].strip()
            p_code = match_project(r["judul_pembayaran"], rules)
            if p_code is None:
                rejects.append({
                    "source": "PAYPAL",
                    "source_id": pid,
                    "reason": f"Unmatched title: {r['judul_pembayaran']}",
                })
                continue
            valid_paypal[pid] = p_code
            tx_d = datetime.strptime(r["tanggal"].strip(), "%d/%m/%Y").date()
            cur = r["mata_uang"].upper().strip()
            gross = abs(parse_amount(r["nilai_kotor"]))
            pr_fee = abs(parse_amount(r["biaya_paypal"]))
            root_code = f"{pid}-SALE"
            emit_event(tx_d, p_code, "PAYPAL", cur, root_code, None, "SALE", gross)
            emit_event(tx_d, p_code, "PAYPAL", cur, f"{pid}-PRCFEE", root_code, "PROCESSING_FEE", -pr_fee)

        for _, r in df_paypal[df_paypal["tipe_aktivitas"] != "Direct Commission"].iterrows():
            pid = r["paypal_txn_id"].strip()
            parent_pid = r["ref_txn_id"].strip()
            if parent_pid not in valid_paypal:
                rejects.append({
                    "source": "PAYPAL",
                    "source_id": pid,
                    "reason": f"Missing parent txn: {parent_pid}",
                })
                continue
            p_code = valid_paypal[parent_pid]
            root_code = f"{parent_pid}-SALE"
            tx_d = datetime.strptime(r["tanggal"].strip(), "%d/%m/%Y").date()
            cur = r["mata_uang"].upper().strip()
            amt = abs(parse_amount(r["nilai_kotor"]))
            pr_fee = abs(parse_amount(r["biaya_paypal"]))

            if r["tipe_aktivitas"] == "Client Tip":
                emit_event(tx_d, p_code, "PAYPAL", cur, pid, root_code, "TIP", amt)
                emit_event(tx_d, p_code, "PAYPAL", cur, f"{pid}-PRCFEE", root_code, "PROCESSING_FEE", -pr_fee)
            elif r["tipe_aktivitas"] == "Refund":
                emit_event(tx_d, p_code, "PAYPAL", cur, pid, root_code, "REFUND", -amt)

        df_rejects = pd.DataFrame(rejects, columns=["source", "source_id", "reason"])
        con.register("tmp_rej", df_rejects)
        con.execute("CREATE OR REPLACE TABLE stg.etl_rejects AS SELECT * FROM tmp_rej")
        con.unregister("tmp_rej")

        fact_df = pd.DataFrame(events)
        fact_df = fact_df.sort_values(["date_key", "transaction_code"]).reset_index(drop=True)
        fact_df.insert(0, "revenue_event_sk", range(1, len(fact_df) + 1))

        con.execute((config.SQL_DIR / "01_ddl_edw.sql").read_text(encoding="utf-8"))

        dim_loads = [
            ("dim_date", dim_date_df),
            ("dim_revenue_stream", dim_stream_df),
            ("dim_currency", dim_currency_df),
            ("dim_platform", dim_platform_df),
            ("dim_project", dim_project_df),
        ]
        for tbl_name, df_dim in dim_loads:
            con.register("tmp_dim", df_dim)
            con.execute(f"INSERT INTO edw.{tbl_name} SELECT * FROM tmp_dim")
            con.unregister("tmp_dim")
            stats["edw_counts"][f"edw.{tbl_name}"] = len(df_dim)

        con.register("tmp_fact", fact_df)
        con.execute(
            """
            INSERT INTO edw.fact_revenue_event (
                revenue_event_sk, date_key, project_key, platform_key, currency_key,
                revenue_stream_key, transaction_code, parent_transaction_code,
                event_type, amount_orig, exchange_rate_to_idr, amount_idr
            )
            SELECT
                revenue_event_sk, date_key, project_key, platform_key, currency_key,
                revenue_stream_key, transaction_code, parent_transaction_code,
                event_type,
                CAST(amount_orig AS DECIMAL(18,2)),
                CAST(exchange_rate_to_idr AS DECIMAL(18,6)),
                CAST(amount_idr AS DECIMAL(18,2))
            FROM tmp_fact
            """
        )
        con.unregister("tmp_fact")
        stats["edw_counts"]["edw.fact_revenue_event"] = len(fact_df)

        con.execute((config.SQL_DIR / "02_mart_views.sql").read_text(encoding="utf-8"))

        stats["rejects_count"] = len(df_rejects)
        stats["fx_fallback_lookups"] = fx.fallback_hits
        stats["event_breakdown"] = fact_df["event_type"].value_counts().sort_index().to_dict()

    (config.REPORT_DIR / "etl_last_run.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print("ETL finished")
    print("stg:", stats["stg_counts"])
    print("duplicates removed:", stats["duplicates_removed"])
    print("rejects:", stats["rejects_count"])
    print("fx fallbacks:", stats["fx_fallback_lookups"])
    print("edw:", stats["edw_counts"])
    print("events:", stats["event_breakdown"])
    return stats


if __name__ == "__main__":
    run_etl()
