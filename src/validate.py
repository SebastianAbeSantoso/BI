from __future__ import annotations

import pathlib
import sys
import duckdb
import pandas as pd

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"
VALIDATE_SQL_PATH = ROOT_DIR / "sql" / "03_validate.sql"


def run_validation(db_path: pathlib.Path = DB_PATH) -> pd.DataFrame:
    if not db_path.exists():
        raise FileNotFoundError(f"Warehouse file not found: {db_path}")
    sql_text = VALIDATE_SQL_PATH.read_text(encoding="utf-8")
    with duckdb.connect(str(db_path), read_only=True) as con:
        df = con.execute(sql_text).df()
    return df


def main() -> int:
    df = run_validation()
    print("\n=== WASAKA INTERACTIVE DW — VALIDATION SUITE (V1–V14) ===")
    for _, row in df.iterrows():
        print(
            f"[{row['status']:4s}] {row['check_id']:3s} | {row['check_name']:58s} "
            f"| Actual: {row['metric_value']:22s} | Rule: {row['expected_rule']}"
        )
        print(f"       Details: {row['details']}")

    failed = df[df["status"] == "FAIL"]
    passed = df[df["status"] == "PASS"]
    info = df[df["status"] == "INFO"]
    print(
        f"\nSummary: {len(passed)} PASS, {len(info)} INFO, {len(failed)} FAIL "
        f"(Total: {len(df)} checks)"
    )
    return 1 if not failed.empty else 0


if __name__ == "__main__":
    sys.exit(main())
