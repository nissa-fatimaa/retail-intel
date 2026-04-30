from __future__ import annotations

from pathlib import Path

APP_NAME = "Retail Intel"
APP_TAGLINE = "Retail Intelligence Dashboards"
APP_VERSION = "1.0.0"
APP_ORG = "Retail Intel Labs"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "retail_intel.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"

DEFAULT_CITY = "Lahore"
DEFAULT_COUNTRY = "Pakistan"
DEFAULT_LATITUDE = 31.5204
DEFAULT_LONGITUDE = 74.3587
DEFAULT_TIMEZONE = "Asia/Karachi"
CURRENCY = "PKR"
CURRENCY_SYMBOL = "Rs."

ROLE_STAFF = "staff"
ROLE_VISITOR = "visitor"
ROLE_EXECUTIVE = "executive"

ROLES = (ROLE_STAFF, ROLE_VISITOR, ROLE_EXECUTIVE)

ROLE_LABELS = {
    ROLE_STAFF: "Retail Staff",
    ROLE_VISITOR: "Visitor",
    ROLE_EXECUTIVE: "Executive (CEO)",
}

ROLE_DESCRIPTIONS = {
    ROLE_STAFF: "Day-to-day inventory, sales monitoring & restock alerts",
    ROLE_VISITOR: "Public-facing store insights for what's trendy, weather & events",
    ROLE_EXECUTIVE: "Full strategic view: forecasts, pricing, KPIs & simulations",
}

DEMO_ACCOUNTS = [
    {
        "username": "staff",
        "password": "staff123",
        "role": ROLE_STAFF,
        "full_name": "Mehroz Khan",
        "email": "mehroz.khan@retailintel.demo",
    },
    {
        "username": "visitor",
        "password": "visitor123",
        "role": ROLE_VISITOR,
        "full_name": "Demo Visitor",
        "email": "visitor@retailintel.demo",
    },
    {
        "username": "executive",
        "password": "exec123",
        "role": ROLE_EXECUTIVE,
        "full_name": "Nissa Fatima",
        "email": "nissa.fatima@retailintel.demo",
    },
]

class Theme:
    BG_DEEP = "#070D1A"
    BG_BASE = "#0B1426"
    BG_SURFACE = "#0F1B33"
    BG_ELEVATED = "#152544"
    BG_OVERLAY = "rgba(20, 36, 68, 0.55)"

    BORDER = "#1E2F52"
    BORDER_STRONG = "#2A4475"

    TEXT_PRIMARY = "#E6ECF7"
    TEXT_SECONDARY = "#9BAACB"
    TEXT_MUTED = "#6A7A9A"
    TEXT_ON_ACCENT = "#FFFFFF"

    ACCENT = "#3B82F6"
    ACCENT_HOVER = "#5294F8"
    ACCENT_PRESSED = "#2C6BD8"
    ACCENT_SOFT = "rgba(59, 130, 246, 0.18)"
    CYAN = "#38BDF8"
    PURPLE = "#A78BFA"

    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    INFO = "#38BDF8"

    CHART_PALETTE = [
        "#3B82F6",
        "#38BDF8",
        "#A78BFA",
        "#22C55E",
        "#F59E0B",
        "#EF4444",
        "#EC4899",
        "#14B8A6",
    ]


FORECAST_WINDOW_DAYS = 14          #rolling history window for weighted moving average
FORECAST_HORIZON_DAYS = 7
SAFETY_STOCK_MULTIPLIER = 1.5      #forecast x 1.5 = recommended stock
MIN_MARGIN_PCT = 0.10
PRICE_CEILING_MULTIPLIER = 1.20    #ceiling = MSRP * 1.20

WEATHER_MODIFIERS = {
    "hot_day_threshold_c": 32.0,
    "cold_day_threshold_c": 12.0,
    "heavy_rain_mm": 8.0,
}

DEFAULT_CATEGORY_ELASTICITY = {
    "Fresh Produce": -1.4,
    "Dairy & Eggs": -0.8,
    "Bakery": -1.1,
    "Beverages": -1.3,
    "Snacks": -1.6,
    "Pantry Staples": -0.6,
    "Frozen Foods": -1.0,
    "Household": -0.9,
}
