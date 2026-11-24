from __future__ import annotations

import csv
import json
import pathlib
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import config  # noqa: E402

# Regional base prices in local currency for natural storefront pricing
GAME_PRICES = {
    "GAME-AMMD": {"USD": 9.99, "EUR": 9.79, "GBP": 8.50, "JPY": 1200.0, "CNY": 42.0, "SGD": 10.50, "IDR": 89000.0},
    "GAME-RBRT": {"USD": 6.99, "EUR": 6.89, "GBP": 5.79, "JPY": 820.0, "CNY": 28.0, "SGD": 7.50, "IDR": 64000.0},
    "GAME-PSPC": {"USD": 4.99, "EUR": 4.99, "GBP": 4.29, "JPY": 580.0, "CNY": 22.0, "SGD": 5.50, "IDR": 45000.0},
    "GAME-CNTG": {"USD": 11.99, "EUR": 11.79, "GBP": 9.99, "JPY": 1450.0, "CNY": 48.0, "SGD": 12.50, "IDR": 109000.0},
}

ASSET_PRICES_USD = {
    "AST-DGPX": 14.00,
    "AST-ISOR": 18.00,
    "AST-RHYT": 12.00,
    "AST-BATK": 22.00,
}

USD_TO_CUR_APPROX = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "SGD": 1.34,
    "JPY": 152.0,
    "CNY": 7.20,
    "IDR": 16200.0,
}

COMMISSION_TEMPLATES = [
    ("COM-ILLU", ["Fullbody Character Illustration + BG", "Anime Key Visual Illustration", "OC Portrait Render High-Res", "Game Splash Art Illustration"], (85.0, 260.0)),
    ("COM-PXUI", ["Retro Pixel Sprite Animation Sheet", "RPG HUD Icon & Frame Pack", "Isometric Tileset Commission 64x64"], (60.0, 190.0)),
    ("COM-SHDR", ["Godot Mechanic & State Controller", "Custom Shader Toon Outline Setup", "HLSL/GDShader Stylized Water"], (95.0, 310.0)),
    ("COM-MUSC", ["Looping Indie Game BGM Track", "SynthV Vocal Ending Song Arrangement", "Dynamic Boss Theme Chiptune/Orchestral"], (80.0, 240.0)),
]

UNMATCHED_TITLES_VGEN = [
    "3D VTuber Fullbody ARKit Rigging",
    "Live2D Cubism Physics & Toggle Setup",
    "VRChat Custom Avatar Retopology",
    "Spine2D Chibi Idle Animation Rig",
]

UNMATCHED_TITLES_FIVERR = [
    "Translate English Steam Page to Indonesian",
    "Youtube Gaming Montage Video Editing",
    "Discord Bot Moderation Script Hosting",
    "Podcast Audio Noise Cleanup & Mastering",
]

UNMATCHED_TITLES_PAYPAL = [
    "Jasa Titip Artbook Comiket",
    "Reimbursement Server Hosting Kost",
    "Patungan Lisensi Plugin Kelas",
]


def _all_dates(start_s: str, end_s: str) -> list[date]:
    s = date.fromisoformat(start_s)
    e = date.fromisoformat(end_s)
    out = []
    cur = s
    while cur <= e:
        out.append(cur)
        cur += timedelta(days=1)
    return out


def _is_sale_season(d: date) -> bool:
    if d.month == 6 and d.day >= 25:
        return True
    if d.month == 7 and d.day <= 10:
        return True
    if d.month == 11 and d.day >= 22:
        return True
    if d.month == 12 and d.day >= 19:
        return True
    return False


def _fmt_currency_messy(amount: float, cur: str) -> str:
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "SGD": "S$", "JPY": "¥", "CNY": "¥", "IDR": "Rp "}
    sym = symbols[cur]
    if cur in ("JPY", "IDR"):
        return f"{sym}{amount:,.0f}"
    return f"{sym}{amount:,.2f}"


def _convert_from_usd(usd_amt: float, cur: str) -> float:
    raw = usd_amt * USD_TO_CUR_APPROX[cur]
    if cur in ("JPY", "IDR"):
        return float(round(raw, -2 if cur == "IDR" else 0))
    return round(raw, 2)


def write_internal_masters() -> None:
    projects_path = config.RAW_DIR / "projects.csv"
    with projects_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["project_code", "project_name", "project_type", "production_field", "stream"])
        for row in config.PROJECTS_CATALOG:
            w.writerow(row)

    map_path = config.RAW_DIR / "project_title_map.csv"
    with map_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pattern", "match_type", "project_code"])
        for row in config.TITLE_MAP_RULES:
            w.writerow(row)


def generate_steam_csv(rng: random.Random, dates: list[date], max_date: date) -> int:
    path = config.RAW_DIR / "steam_sales_report.csv"
    currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "SGD", "IDR"]
    cur_weights = [0.38, 0.18, 0.11, 0.13, 0.09, 0.05, 0.06]
    games = [p for p in config.PROJECTS_CATALOG if p[4] == "GAME_SALES"]
    game_weights = [0.38, 0.27, 0.17, 0.18]

    rows: list[list] = []
    seq = 100000
    for d in dates:
        # Canting Cloth launches mid-2026 in synthetic scenario; earlier games active throughout
        avail_games = games if d >= date(2026, 5, 1) else games[:3]
        avail_weights = game_weights if d >= date(2026, 5, 1) else [0.46, 0.33, 0.21]

        lam = 2.6 if _is_sale_season(d) else (1.15 if d.weekday() >= 5 else 0.75)
        n_sales = rng.choices([0, 1, 2, 3, 4, 5], weights=[0.22, 0.34, 0.22, 0.12, 0.07, 0.03])[0]
        if _is_sale_season(d):
            n_sales += rng.randint(1, 3)
        elif lam > 1.0 and rng.random() < 0.35:
            n_sales += 1

        for _ in range(n_sales):
            seq += 1
            order_id = f"STM-{seq}"
            g_code, g_name, _, _, _ = rng.choices(avail_games, weights=avail_weights, k=1)[0]
            cur = rng.choices(currencies, weights=cur_weights, k=1)[0]
            discount = rng.choice([1.0, 0.85, 0.80, 0.75]) if _is_sale_season(d) else 1.0
            base_price = GAME_PRICES[g_code][cur] * discount
            gross = round(base_price, 0 if cur in ("JPY", "IDR") else 2)
            steam_fee = round(gross * config.FEE_SCHEDULE["STEAM"]["platform_fee_pct"], 2)
            country = {"USD": "US", "EUR": "DE", "GBP": "GB", "JPY": "JP", "CNY": "CN", "SGD": "SG", "IDR": "ID"}[cur]

            rows.append([
                order_id,
                d.strftime("%m/%d/%Y"),
                "SALE",
                g_code,
                g_name,
                cur,
                f"{gross:.2f}",
                f"{-steam_fee:.2f}",
                "",
                country,
            ])

            if rng.random() < 0.058:
                ref_date = min(max_date, d + timedelta(days=rng.randint(1, 12)))
                rows.append([
                    f"{order_id}-RF",
                    ref_date.strftime("%m/%d/%Y"),
                    "REFUND",
                    g_code,
                    g_name,
                    cur,
                    f"{-gross:.2f}",
                    f"{steam_fee:.2f}",
                    order_id,
                    country,
                ])

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "order_id", "tx_date", "record_type", "game_code", "game_title",
            "buyer_currency", "gross_amount", "steam_fee_amount", "parent_order_id", "country_code",
        ])
        w.writerows(rows)
    return len(rows)


def generate_itch_csv(rng: random.Random, dates: list[date], max_date: date) -> int:
    path = config.RAW_DIR / "itch_payouts.csv"
    currencies = ["USD", "EUR", "GBP", "SGD", "JPY", "IDR"]
    cur_weights = [0.52, 0.17, 0.11, 0.08, 0.06, 0.06]
    items = [p for p in config.PROJECTS_CATALOG if p[4] in ("GAME_SALES", "ASSET_SALES")]

    rows: list[list] = []
    seq = 20000
    for d in dates:
        n_orders = rng.choices([0, 1, 2, 3], weights=[0.48, 0.33, 0.14, 0.05])[0]
        if _is_sale_season(d):
            n_orders += rng.randint(0, 2)
        for _ in range(n_orders):
            seq += 1
            tx_id = f"ITCH-{seq}"
            p_code, p_name, p_type, _, stream = rng.choice(items)
            if p_code == "GAME-CNTG" and d < date(2026, 5, 1):
                p_code, p_name, p_type, _, stream = items[0]
            cur = rng.choices(currencies, weights=cur_weights, k=1)[0]
            if stream == "GAME_SALES":
                gross = GAME_PRICES[p_code][cur]
            else:
                gross = _convert_from_usd(ASSET_PRICES_USD[p_code], cur)
            # Occasional tip/bonus on itch.io pay-what-you-want
            extra_tip = _convert_from_usd(rng.choice([2.0, 5.0]), cur) if rng.random() < 0.14 else 0.0
            itch_share = round(gross * config.FEE_SCHEDULE["ITCH"]["platform_fee_pct"], 2)
            fixed_fee_cur = _convert_from_usd(config.FEE_SCHEDULE["ITCH"]["processing_fixed_usd"], cur)
            proc_fee = round((gross + extra_tip) * config.FEE_SCHEDULE["ITCH"]["processing_fee_pct"] + fixed_fee_cur, 2)

            is_ref = rng.random() < 0.04
            ref_date_s = min(max_date, d + timedelta(days=rng.randint(1, 9))).isoformat() if is_ref else ""

            rows.append([
                tx_id,
                d.isoformat(),
                p_type,
                p_code,
                p_name,
                cur,
                _fmt_currency_messy(gross, cur),
                _fmt_currency_messy(extra_tip, cur) if extra_tip > 0 else "$0.00",
                _fmt_currency_messy(itch_share, cur),
                _fmt_currency_messy(proc_fee, cur),
                "yes" if is_ref else "no",
                ref_date_s,
                f"indie_buyer_{seq}@example.org",
            ])

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "itch_tx_id", "payout_date", "item_category", "item_code", "item_title",
            "currency", "gross_str", "tip_str", "itch_share_str", "processor_fee_str",
            "is_refunded", "refund_date", "buyer_email",
        ])
        w.writerows(rows)
    return len(rows)


def generate_vgen_json(rng: random.Random, dates: list[date], max_date: date) -> int:
    path = config.RAW_DIR / "vgen_export.json"
    asset_titles = [
        ("Dungeon Matchmaker Pixel UI Kit Commercial", "AST-DGPX"),
        ("Personal Space Isometric Room Low-Poly Props", "AST-ISOR"),
        ("R*bert Rhythm Stem & SFX Pack", "AST-RHYT"),
        ("Canting Batik Shader & NPR Toolkit", "AST-BATK"),
    ]
    currencies = ["USD", "SGD", "EUR", "JPY", "GBP"]
    cur_weights = [0.64, 0.11, 0.10, 0.09, 0.06]

    orders: list[dict] = []
    seq = 5000
    for d in dates:
        if rng.random() > 0.34:
            continue
        n_ord = rng.choices([1, 2], weights=[0.8, 0.2])[0]
        for _ in range(n_ord):
            seq += 1
            oid = f"VGN-{seq}"
            cur = rng.choices(currencies, weights=cur_weights, k=1)[0]
            is_shop = rng.random() < 0.42

            if is_shop:
                title, p_code = rng.choice(asset_titles)
                gross_usd = ASSET_PRICES_USD[p_code] * rng.choice([1.0, 1.5])
                service_kind = "SHOP_ASSET"
            else:
                _, titles, (lo, hi) = rng.choice(COMMISSION_TEMPLATES)
                title = f"{rng.choice(titles)} #{seq % 97}"
                gross_usd = round(rng.uniform(lo, hi), 2)
                service_kind = "COMMISSION"

            gross = _convert_from_usd(gross_usd, cur)
            vgen_fee = round(gross * config.FEE_SCHEDULE["VGEN"]["platform_fee_pct"], 2)
            proc_fee = round(
                gross * config.FEE_SCHEDULE["VGEN"]["processing_fee_pct"]
                + _convert_from_usd(config.FEE_SCHEDULE["VGEN"]["processing_fixed_usd"], cur),
                2,
            )

            tips = []
            if not is_shop and rng.random() < 0.28:
                n_tips = 2 if rng.random() < 0.35 else 1  # Multi-tip orders for V7
                for t_idx in range(1, n_tips + 1):
                    t_date = min(max_date, d + timedelta(days=rng.randint(0, 7)))
                    t_amt = _convert_from_usd(rng.choice([10.0, 15.0, 25.0]), cur)
                    tips.append({
                        "tip_id": f"{oid}-T{t_idx}",
                        "paid_at": f"{t_date.isoformat()}T14:15:00Z",
                        "amount": t_amt,
                    })

            refunds = []
            if rng.random() < 0.055:
                r_date = min(max_date, d + timedelta(days=rng.randint(2, 14)))
                ratio = rng.choice([0.4, 0.5]) if (not is_shop and rng.random() < 0.45) else 1.0
                r_amt = round(gross * ratio, 2)
                r_fee_rev = round(vgen_fee * ratio, 2)
                refunds.append({
                    "refund_id": f"{oid}-R1",
                    "refunded_at": f"{r_date.isoformat()}T09:30:00Z",
                    "amount": r_amt,
                    "vgen_fee_returned": r_fee_rev,
                })

            orders.append({
                "order_id": oid,
                "created_at": f"{d.isoformat()}T11:20:00Z",
                "service_kind": service_kind,
                "title": title,
                "client_username": f"@vgen_client_{seq}",
                "currency": cur,
                "gross_amount": gross,
                "vgen_fee": vgen_fee,
                "payment_proc_fee": proc_fee,
                "tips": tips,
                "refunds": refunds,
            })

    # Inject 4 unmatched commission titles to exercise quarantine (stg.etl_rejects)
    for idx, bad_title in enumerate(UNMATCHED_TITLES_VGEN, start=1):
        seq += 1
        d_bad = date(2025, 4 + idx, 12)
        orders.append({
            "order_id": f"VGN-UNM-{idx}",
            "created_at": f"{d_bad.isoformat()}T10:00:00Z",
            "service_kind": "COMMISSION",
            "title": bad_title,
            "client_username": f"@unmatched_vgen_{idx}",
            "currency": "USD",
            "gross_amount": 150.00,
            "vgen_fee": 7.50,
            "payment_proc_fee": 4.65,
            "tips": [],
            "refunds": [],
        })

    path.write_text(json.dumps(orders, indent=2), encoding="utf-8")
    return len(orders)


def generate_fiverr_csv(rng: random.Random, dates: list[date], max_date: date) -> tuple[int, int]:
    path = config.RAW_DIR / "fiverr_earnings.csv"
    currencies = ["USD", "EUR", "GBP", "SGD"]
    cur_weights = [0.76, 0.10, 0.08, 0.06]

    rows: list[list] = []
    seq = 7000
    for d in dates:
        if rng.random() > 0.24:
            continue
        seq += 1
        oid = f"FO-{seq}"
        _, titles, (lo, hi) = rng.choice(COMMISSION_TEMPLATES)
        title = f"{rng.choice(titles)} [Tier {rng.choice(['Basic', 'Standard', 'Pro'])}]"
        cur = rng.choices(currencies, weights=cur_weights, k=1)[0]
        gross = _convert_from_usd(round(rng.uniform(lo, hi), 2), cur)
        fee = round(gross * config.FEE_SCHEDULE["FIVERR"]["platform_fee_pct"], 2)
        buyer = f"fiverr_user_{seq}"

        rows.append([d.isoformat(), oid, "ORDER", title, buyer, cur, f"{gross:.2f}", f"{-fee:.2f}", ""])

        if rng.random() < 0.24:
            n_tips = 2 if rng.random() < 0.30 else 1
            for t_i in range(1, n_tips + 1):
                t_date = min(max_date, d + timedelta(days=rng.randint(0, 5)))
                tip_amt = _convert_from_usd(rng.choice([10.0, 20.0, 30.0]), cur)
                tip_fee = round(tip_amt * config.FEE_SCHEDULE["FIVERR"]["platform_fee_pct"], 2)
                rows.append([
                    t_date.isoformat(), f"{oid}-TIP{t_i}", "TIP", title, buyer, cur,
                    f"{tip_amt:.2f}", f"{-tip_fee:.2f}", oid,
                ])

        if rng.random() < 0.065:
            r_date = min(max_date, d + timedelta(days=rng.randint(2, 15)))
            partial = rng.random() < 0.35
            ratio = 0.5 if partial else 1.0
            r_amt = round(gross * ratio, 2)
            r_fee_rev = round(fee * ratio, 2)
            kind = "CANCELLATION_PARTIAL" if partial else "CANCELLATION_FULL"
            rows.append([
                r_date.isoformat(), f"{oid}-REF", kind, title, buyer, cur,
                f"{-r_amt:.2f}", f"{r_fee_rev:.2f}", oid,
            ])

    # Inject 4 unmatched Fiverr rows
    for idx, bad_title in enumerate(UNMATCHED_TITLES_FIVERR, start=1):
        d_bad = date(2025, 7 + idx, 18)
        rows.append([
            d_bad.isoformat(), f"FO-UNM-{idx}", "ORDER", bad_title,
            f"fiverr_unm_{idx}", "USD", "75.00", "-15.00", "",
        ])

    # Inject 15 exact duplicate rows (simulating overlapping date-range CSV re-exports)
    dup_samples = rng.sample(rows[:60], k=15)
    rows.extend(dup_samples)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "clearing_date", "fiverr_order_id", "row_kind", "order_title",
            "buyer_username", "currency", "gross_amount", "fiverr_commission", "parent_order_id",
        ])
        w.writerows(rows)
    return len(rows), len(dup_samples)


def generate_paypal_csv(rng: random.Random, dates: list[date], max_date: date) -> int:
    path = config.RAW_DIR / "paypal_activity.csv"
    currencies = ["USD", "SGD", "IDR", "EUR", "JPY", "CNY", "GBP"]
    cur_weights = [0.40, 0.16, 0.16, 0.10, 0.08, 0.05, 0.05]

    def fmt_num(val: float, use_comma: bool) -> str:
        s = f"{val:.2f}"
        return s.replace(".", ",") if use_comma else s

    rows: list[list] = []
    seq = 9000
    for d in dates:
        if rng.random() > 0.21:
            continue
        seq += 1
        pid = f"PP-{seq}"
        _, titles, (lo, hi) = rng.choice(COMMISSION_TEMPLATES)
        title = f"Direct Invoice - {rng.choice(titles)}"
        cur = rng.choices(currencies, weights=cur_weights, k=1)[0]
        gross = _convert_from_usd(round(rng.uniform(lo, hi), 2), cur)

        pct = (
            config.FEE_SCHEDULE["PAYPAL"]["processing_fee_dom_pct"]
            if cur == "IDR"
            else config.FEE_SCHEDULE["PAYPAL"]["processing_fee_intl_pct"]
        )
        fixed = config.FEE_SCHEDULE["PAYPAL"]["fixed_fee_by_currency"][cur]
        proc_fee = round(gross * pct + fixed, 2)
        comma_mode = rng.random() < 0.42
        payer_name = f"Client #{seq}"
        payer_email = f"client_{seq}@mail-sample.test"

        rows.append([
            d.strftime("%d/%m/%Y"), pid, "", "Direct Commission", title,
            payer_name, payer_email, cur,
            fmt_num(gross, comma_mode), fmt_num(-proc_fee, comma_mode),
        ])

        if rng.random() < 0.22:
            n_tips = 2 if rng.random() < 0.35 else 1
            for t_i in range(1, n_tips + 1):
                t_date = min(max_date, d + timedelta(days=rng.randint(0, 6)))
                tip_amt = _convert_from_usd(rng.choice([8.0, 15.0, 25.0]), cur)
                tip_fee = round(tip_amt * pct + fixed, 2)
                rows.append([
                    t_date.strftime("%d/%m/%Y"), f"{pid}-TIP{t_i}", pid, "Client Tip", title,
                    payer_name, payer_email, cur,
                    fmt_num(tip_amt, comma_mode), fmt_num(-tip_fee, comma_mode),
                ])

        if rng.random() < 0.055:
            r_date = min(max_date, d + timedelta(days=rng.randint(1, 10)))
            ratio = 0.5 if rng.random() < 0.35 else 1.0
            r_amt = round(gross * ratio, 2)
            # PayPal keeps processing fee on refund -> biaya_paypal = 0.00
            rows.append([
                r_date.strftime("%d/%m/%Y"), f"{pid}-REF", pid, "Refund", title,
                payer_name, payer_email, cur,
                fmt_num(-r_amt, comma_mode), fmt_num(0.0, comma_mode),
            ])

    # Inject 3 unmatched PayPal rows for quarantine test
    for idx, bad_title in enumerate(UNMATCHED_TITLES_PAYPAL, start=1):
        d_bad = date(2026, 2 + idx, 9)
        rows.append([
            d_bad.strftime("%d/%m/%Y"), f"PP-UNM-{idx}", "", "Direct Commission", bad_title,
            f"Unmatched {idx}", f"unm_{idx}@mail-sample.test", "IDR", "350000,00", "-16500,00",
        ])

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tanggal", "paypal_txn_id", "ref_txn_id", "tipe_aktivitas", "judul_pembayaran",
            "payer_name", "payer_email", "mata_uang", "nilai_kotor", "biaya_paypal",
        ])
        w.writerows(rows)
    return len(rows)


def main() -> None:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(config.RANDOM_SEED)
    dates = _all_dates(config.TX_START, config.TX_END)
    max_d = date.fromisoformat(config.TX_END)

    write_internal_masters()
    n_steam = generate_steam_csv(rng, dates, max_d)
    n_itch = generate_itch_csv(rng, dates, max_d)
    n_vgen = generate_vgen_json(rng, dates, max_d)
    n_fiverr, n_dups = generate_fiverr_csv(rng, dates, max_d)
    n_paypal = generate_paypal_csv(rng, dates, max_d)

    print(
        f"[SOURCES] Generated raw files in {config.RAW_DIR}:\n"
        f"  - steam_sales_report.csv : {n_steam} rows\n"
        f"  - itch_payouts.csv       : {n_itch} rows\n"
        f"  - vgen_export.json       : {n_vgen} orders\n"
        f"  - fiverr_earnings.csv    : {n_fiverr} rows (includes {n_dups} injected duplicates)\n"
        f"  - paypal_activity.csv    : {n_paypal} rows"
    )


if __name__ == "__main__":
    main()
