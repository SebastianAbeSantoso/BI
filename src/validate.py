import pathlib
import sys
import duckdb

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"
VALIDATE_SQL_PATH = ROOT_DIR / "sql" / "03_validate.sql"


def run_validation(db_path=DB_PATH):
    if not db_path.exists():
        raise FileNotFoundError(f"Warehouse file not found: {db_path}")
    sql_text = VALIDATE_SQL_PATH.read_text(encoding="utf-8")
    with duckdb.connect(str(db_path), read_only=True) as con:
        return con.execute(sql_text).df()


def main():
    df = run_validation()
    for _, row in df.iterrows():
        print(f"[{row['status']:4s}] {row['check_id']:3s} {row['check_name']} | {row['metric_value']} (expected {row['expected_rule']})")
        print(f"       {row['details']}")

    failed = df[df["status"] == "FAIL"]
    passed = df[df["status"] == "PASS"]
    info = df[df["status"] == "INFO"]
    print(f"\nResult: {len(passed)} PASS, {len(info)} INFO, {len(failed)} FAIL")
    return 1 if not failed.empty else 0


if __name__ == "__main__":
    sys.exit(main())
