import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent
RAW_DIR = ROOT_DIR / "data" / "raw"
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"
SQL_DIR = ROOT_DIR / "sql"
REPORT_DIR = ROOT_DIR / "report"

RANDOM_SEED = 20261124

DIM_DATE_START = "2025-01-01"
DIM_DATE_END = "2026-12-31"

FX_FETCH_START = "2024-12-20"
TX_START = "2025-01-01"
TX_END = "2026-10-31"

FEE_SCHEDULE = {
    "STEAM": {
        "platform_fee_pct": 0.30,
        "processing_fee_pct": 0.00,
        "refund_reverses_platform_fee": True,
        "source": "Steamworks standard 30% revenue share.",
        "verified": True,
    },
    "ITCH": {
        "platform_fee_pct": 0.10,
        "processing_fee_pct": 0.029,
        "processing_fixed_usd": 0.30,
        "refund_reverses_platform_fee": True,
        "source": "itch.io default 10% creator share plus 2.9% + $0.30 checkout fee.",
        "verified": True,
    },
    "VGEN": {
        "platform_fee_pct": 0.05,
        "processing_fee_pct": 0.029,
        "processing_fixed_usd": 0.30,
        "refund_reverses_platform_fee": True,
        "source": "VGen Help Center: 5% platform fee plus 2.9% + $0.30 processing.",
        "verified": True,
    },
    "FIVERR": {
        "platform_fee_pct": 0.20,
        "processing_fee_pct": 0.00,
        "refund_reverses_platform_fee": True,
        "source": "Fiverr Seller Terms: 20% fee on orders and tips.",
        "verified": True,
    },
    "PAYPAL": {
        "platform_fee_pct": 0.00,
        "processing_fee_intl_pct": 0.044,
        "processing_fee_dom_pct": 0.034,
        "fixed_fee_by_currency": {
            "IDR": 4600.00,
            "USD": 0.30,
            "SGD": 0.50,
            "JPY": 40.00,
            "CNY": 2.50,
            "EUR": 0.35,
            "GBP": 0.20,
        },
        "refund_reverses_platform_fee": False,
        "source": "PayPal Indonesia (paypal.com/id): 3.40% + fixed fee domestic, 4.40% + fixed fee cross-border, non-refundable.",
        "verified": True,
    },
}

STATIC_STREAMS = [
    (
        1,
        "GAME_SALES",
        "Penjualan Gim Video",
        "Penjualan gim komersial Wasaka Interactive melalui Steam dan itch.io.",
    ),
    (
        2,
        "ASSET_SALES",
        "Penjualan Aset Digital",
        "Penjualan paket aset (pixel UI, 3D low-poly, audio, shader) melalui itch.io dan VGen Shop.",
    ),
    (
        3,
        "COMMISSION",
        "Komisi Klien",
        "Pengerjaan pesanan kustom melalui VGen, Fiverr, dan Direct PayPal.",
    ),
]

STATIC_PLATFORMS = [
    (1, "STEAM", "Steam", "Digital Storefront"),
    (2, "ITCH", "itch.io", "Indie Storefront & Marketplace"),
    (3, "VGEN", "VGen", "Creator Marketplace"),
    (4, "FIVERR", "Fiverr", "Freelance Marketplace"),
    (5, "PAYPAL", "Direct PayPal", "Direct Payment / Direct Commission"),
]

STATIC_CURRENCIES = [
    (1, "IDR", "Indonesian Rupiah", "Rp"),
    (2, "USD", "US Dollar", "$"),
    (3, "SGD", "Singapore Dollar", "S$"),
    (4, "JPY", "Japanese Yen", "¥"),
    (5, "CNY", "Chinese Yuan", "¥"),
    (6, "EUR", "Euro", "€"),
    (7, "GBP", "British Pound", "£"),
]

PROJECTS_CATALOG = [
    ("GAME-AMMD", "A Match Made in Dungeon", "Game", "Full Game Dev", "GAME_SALES"),
    ("GAME-RBRT", "R*bert", "Game", "Full Game Dev", "GAME_SALES"),
    ("GAME-PSPC", "Personal Space", "Game", "Full Game Dev", "GAME_SALES"),
    ("GAME-CNTG", "Canting Cloth", "Game", "Full Game Dev", "GAME_SALES"),
    ("AST-DGPX", "Dungeon Matchmaker Pixel UI & Sprite Kit", "Asset Pack", "Pixel Art & UI", "ASSET_SALES"),
    ("AST-ISOR", "Personal Space Isometric Room & Props Pack", "Asset Pack", "3D Modeling", "ASSET_SALES"),
    ("AST-RHYT", "R*bert Reactive Rhythm & SFX Stem Pack", "Asset Pack", "Audio & Music", "ASSET_SALES"),
    ("AST-BATK", "Canting NPR Batik Shader & Godot Toolkit", "Asset Pack", "Programming & Tech", "ASSET_SALES"),
    ("COM-ILLU", "Custom 2D Character & Key Visual Illustration", "Commission Service", "2D Illustration", "COMMISSION"),
    ("COM-PXUI", "Indie Game Pixel Art & HUD UI Commissions", "Commission Service", "Pixel Art & UI", "COMMISSION"),
    ("COM-SHDR", "Godot & Custom NPR Shader Commissions", "Commission Service", "Programming & Tech", "COMMISSION"),
    ("COM-MUSC", "Interactive Game BGM & SynthV Arrangement", "Commission Service", "Audio & Music", "COMMISSION"),
]

TITLE_MAP_RULES = [
    ("dungeon matchmaker", "contains", "AST-DGPX"),
    ("pixel ui kit", "contains", "AST-DGPX"),
    ("isometric room", "contains", "AST-ISOR"),
    ("low-poly props", "contains", "AST-ISOR"),
    ("rhythm stem", "contains", "AST-RHYT"),
    ("sfx pack", "contains", "AST-RHYT"),
    ("batik shader", "contains", "AST-BATK"),
    ("npr toolkit", "contains", "AST-BATK"),
    ("character illustration", "contains", "COM-ILLU"),
    ("key visual", "contains", "COM-ILLU"),
    ("oc portrait", "contains", "COM-ILLU"),
    ("splash art", "contains", "COM-ILLU"),
    ("pixel sprite", "contains", "COM-PXUI"),
    ("hud icon", "contains", "COM-PXUI"),
    ("tileset commission", "contains", "COM-PXUI"),
    ("custom shader", "contains", "COM-SHDR"),
    ("godot mechanic", "contains", "COM-SHDR"),
    ("hlsl/gdshader", "contains", "COM-SHDR"),
    ("game bgm", "contains", "COM-MUSC"),
    ("synthv vocal", "contains", "COM-MUSC"),
    ("boss theme", "contains", "COM-MUSC"),
]

ANCHOR_RATES_TO_IDR = {
    "IDR": 1.0,
    "USD": 16250.0,
    "SGD": 12100.0,
    "JPY": 107.5,
    "CNY": 2245.0,
    "EUR": 17650.0,
    "GBP": 20650.0,
}
