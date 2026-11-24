import pathlib
import sys
import zipfile
import zlib
import requests

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DIAG_DIR = ROOT_DIR / "diagrams"
TEMPLATE_DOCX = ROOT_DIR.parent / "BI-Design-Template.docx"

PLANTUML_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def encode_plantuml(text):
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    out = []
    for i in range(0, len(compressed), 3):
        b1 = compressed[i]
        b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
        b3 = compressed[i + 2] if i + 2 < len(compressed) else 0
        out.append(PLANTUML_ALPHABET[b1 >> 2])
        out.append(PLANTUML_ALPHABET[((b1 & 0x3) << 4) | (b2 >> 4)])
        out.append(PLANTUML_ALPHABET[((b2 & 0xF) << 2) | (b3 >> 6)])
        out.append(PLANTUML_ALPHABET[b3 & 0x3F])
    return "".join(out)


def render_puml_file(puml_path):
    text = puml_path.read_text(encoding="utf-8")
    encoded = encode_plantuml(text)
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    if resp.content[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Non-PNG response for {puml_path.name}")
    out_png = puml_path.with_suffix(".png")
    out_png.write_bytes(resp.content)
    print(f"Rendered {out_png.name} ({len(resp.content)} bytes)")


def extract_approved_erd():
    out_png = DIAG_DIR / "06_star_schema_edw.png"
    with zipfile.ZipFile(TEMPLATE_DOCX) as z:
        data = z.read("word/media/image5.png")
    out_png.write_bytes(data)
    print(f"Extracted {out_png.name} ({len(data)} bytes)")


def main():
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    puml_files = sorted(DIAG_DIR.glob("*.puml"))
    for puml in puml_files:
        render_puml_file(puml)
    extract_approved_erd()


if __name__ == "__main__":
    sys.exit(main())
