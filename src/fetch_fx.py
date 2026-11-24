import csv
import json
import pathlib
import random
import sys
from datetime import date, datetime, timedelta

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import config

SYMBOLS = ["USD", "SGD", "JPY", "CNY", "GBP", "IDR"]


def weekdays_between(start_d, end_d):
    days = []
    cur = start_d
    while cur <= end_d:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def fetch_frankfurter():
    urls = [
        f"https://api.frankfurter.dev/v1/{config.FX_FETCH_START}..{config.TX_END}?base=EUR&symbols={','.join(SYMBOLS)}",
        f"https://api.frankfurter.app/{config.FX_FETCH_START}..{config.TX_END}?from=EUR&to={','.join(SYMBOLS)}",
    ]
    last_err = None
    for url in urls:
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            rates = resp.json().get("rates", {})
            if rates:
                return rates
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Frankfurter API unreachable: {last_err}")


def build_fx_dataset():
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(config.RANDOM_SEED + 77)

    start_d = date.fromisoformat(config.FX_FETCH_START)
    end_d = date.fromisoformat(config.TX_END)

    rows_by_date = {}
    real_dates = []
    projected_dates = []
    mode = "real_ecb"

    try:
        raw_ecb = fetch_frankfurter()
        for d_str in sorted(raw_ecb.keys()):
            day_map = raw_ecb[d_str]
            if "IDR" not in day_map:
                continue
            eur_idr = float(day_map["IDR"])
            converted = {
                "IDR": 1.000000,
                "EUR": round(eur_idr, 6),
            }
            for sym in ["USD", "SGD", "JPY", "CNY", "GBP"]:
                if sym in day_map and float(day_map[sym]) > 0:
                    converted[sym] = round(eur_idr / float(day_map[sym]), 6)
            if len(converted) == 7:
                rows_by_date[d_str] = converted
                real_dates.append(d_str)

        if not real_dates:
            raise RuntimeError("No complete 7-currency rows returned by Frankfurter.")

        last_real = date.fromisoformat(max(real_dates))
        tail_days = weekdays_between(last_real + timedelta(days=1), end_d)
        if tail_days:
            mode = "hybrid_ecb_plus_projected_tail"
            cur_rates = dict(rows_by_date[last_real.isoformat()])
            for bday in tail_days:
                for cur_code in ["USD", "SGD", "JPY", "CNY", "EUR", "GBP"]:
                    drift = rng.gauss(0.00005, 0.0022)
                    cur_rates[cur_code] = round(max(0.01, cur_rates[cur_code] * (1.0 + drift)), 6)
                cur_rates["IDR"] = 1.000000
                rows_by_date[bday.isoformat()] = dict(cur_rates)
                projected_dates.append(bday.isoformat())
    except Exception as exc:
        print(f"FX fetch failed, using simulated fallback: {exc}")
        mode = "simulated_fallback"
        cur_rates = dict(config.ANCHOR_RATES_TO_IDR)
        for bday in weekdays_between(start_d, end_d):
            for cur_code in ["USD", "SGD", "JPY", "CNY", "EUR", "GBP"]:
                drift = rng.gauss(0.00004, 0.0025)
                cur_rates[cur_code] = round(max(0.01, cur_rates[cur_code] * (1.0 + drift)), 6)
            cur_rates["IDR"] = 1.000000
            rows_by_date[bday.isoformat()] = dict(cur_rates)
            projected_dates.append(bday.isoformat())

    fx_csv_path = config.RAW_DIR / "fx_rates.csv"
    total_rows = 0
    with fx_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "currency_code", "rate_to_idr"])
        for d_str in sorted(rows_by_date.keys()):
            for cur_code in ["IDR", "USD", "SGD", "JPY", "CNY", "EUR", "GBP"]:
                writer.writerow([d_str, cur_code, f"{rows_by_date[d_str][cur_code]:.6f}"])
                total_rows += 1

    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "window_requested": f"{config.FX_FETCH_START}..{config.TX_END}",
        "real_ecb_days": len(real_dates),
        "first_real_date": min(real_dates) if real_dates else None,
        "last_real_date": max(real_dates) if real_dates else None,
        "projected_business_days": len(projected_dates),
        "total_csv_rows": total_rows,
        "weekends_omitted": True,
    }
    (config.RAW_DIR / "fx_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"fx_rates.csv: {total_rows} rows (mode={mode}, real_days={len(real_dates)}, projected={len(projected_dates)})")
    return meta


if __name__ == "__main__":
    build_fx_dataset()
