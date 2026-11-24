import pathlib
import subprocess
import sys
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
SHOT_DIR = ROOT_DIR / "report" / "screenshots"
VENV_PY = ROOT_DIR / ".venv" / "Scripts" / "python.exe"


def render_cli_evidence():
    etl_res = subprocess.run(
        [str(VENV_PY), str(ROOT_DIR / "src" / "etl.py")],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=True,
    )
    val_res = subprocess.run(
        [str(VENV_PY), str(ROOT_DIR / "src" / "validate.py")],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=True,
    )

    lines = ["$ .\\.venv\\Scripts\\python.exe src\\etl.py"]
    lines.extend(etl_res.stdout.strip().splitlines())
    lines.append("")
    lines.append("$ .\\.venv\\Scripts\\python.exe src\\validate.py")
    lines.extend(val_res.stdout.strip().splitlines())

    font_path = pathlib.Path(r"C:\Windows\Fonts\consola.ttf")
    if font_path.exists():
        font = ImageFont.truetype(str(font_path), 15)
    else:
        font = ImageFont.load_default()

    line_height = 22
    pad_x = 24
    pad_y = 22
    width = 1320
    height = pad_y * 2 + line_height * len(lines)

    img = Image.new("RGB", (width, height), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width - 1, height - 1], outline=(206, 212, 218), width=2)

    y = pad_y
    for line in lines:
        color = (33, 37, 41)
        if line.startswith("$ "):
            color = (13, 110, 253)
        elif line.startswith("[PASS]"):
            color = (25, 135, 84)
        elif line.startswith("[FAIL]"):
            color = (220, 53, 69)
        elif line.startswith("[INFO]"):
            color = (108, 117, 125)
        draw.text((pad_x, y), line, fill=color, font=font)
        y += line_height

    out_path = SHOT_DIR / "07_cli_etl_validate.png"
    img.save(out_path)
    print(f"Saved {out_path.name} ({out_path.stat().st_size} bytes)")


def wait_for_server(url, timeout_s=35):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200 and "ok" in r.text.lower():
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Streamlit did not become healthy at {url}")


def launch_browser(p):
    for ch in ["msedge", "chrome", None]:
        try:
            kwargs = {"headless": True}
            if ch:
                kwargs["channel"] = ch
            return p.chromium.launch(**kwargs)
        except Exception:
            continue
    raise RuntimeError("No Playwright Chromium/Edge/Chrome browser available")


def capture_ui_screenshots():
    port = 8512
    cmd = [
        str(VENV_PY),
        "-m",
        "streamlit",
        "run",
        str(ROOT_DIR / "app" / "app.py"),
        "--server.headless",
        "true",
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
        "--theme.base",
        "light",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_server(f"http://127.0.0.1:{port}/_stcore/health")
        with sync_playwright() as p:
            browser = launch_browser(p)
            page = browser.new_page(viewport={"width": 1440, "height": 960}, device_scale_factor=1.5)
            page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")
            page.wait_for_selector('[data-testid="stDataFrame"]', timeout=20000)
            page.wait_for_selector(".js-plotly-plot", timeout=20000)
            time.sleep(1.2)

            sql_expander = page.locator("summary", has_text="Lihat SQL yang dijalankan").first
            sql_expander.click()
            time.sleep(0.9)
            p1 = SHOT_DIR / "01_tab1_query_builder.png"
            page.screenshot(path=str(p1), full_page=True)
            print(f"Saved {p1.name} ({p1.stat().st_size} bytes)")

            page.get_by_role("tab", name="2. Empat Pertanyaan Bisnis").click()
            time.sleep(1.4)
            p2 = SHOT_DIR / "02_tab2_q1_revenue_trend.png"
            page.screenshot(path=str(p2), full_page=True)
            print(f"Saved {p2.name} ({p2.stat().st_size} bytes)")

            page.get_by_role("tab", name="Q2: Proyek & Bidang").click()
            time.sleep(1.2)
            p3 = SHOT_DIR / "03_tab2_q2_project_field.png"
            page.screenshot(path=str(p3), full_page=True)
            print(f"Saved {p3.name} ({p3.stat().st_size} bytes)")

            page.get_by_role("tab", name="Q3: Biaya & Refund").click()
            time.sleep(1.2)
            p4 = SHOT_DIR / "04_tab2_q3_fee_leakage.png"
            page.screenshot(path=str(p4), full_page=True)
            print(f"Saved {p4.name} ({p4.stat().st_size} bytes)")

            page.get_by_role("tab", name="Q4: Eksposur Kurs").click()
            time.sleep(1.2)
            p5 = SHOT_DIR / "05_tab2_q4_fx_exposure.png"
            page.screenshot(path=str(p5), full_page=True)
            print(f"Saved {p5.name} ({p5.stat().st_size} bytes)")

            page.get_by_role("tab", name="3. Arsitektur & Validasi").click()
            time.sleep(1.4)
            p6 = SHOT_DIR / "06_tab3_validation.png"
            page.screenshot(path=str(p6), full_page=True)
            print(f"Saved {p6.name} ({p6.stat().st_size} bytes)")

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main():
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    render_cli_evidence()
    capture_ui_screenshots()


if __name__ == "__main__":
    sys.exit(main())
