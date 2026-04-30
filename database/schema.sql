-- Retail Intel database schema (SQLite)
-- All money fields stored as REAL in PKR.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('staff', 'visitor', 'executive')),
    full_name       TEXT NOT NULL,
    email           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

CREATE TABLE IF NOT EXISTS categories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    category_id     INTEGER NOT NULL,
    unit            TEXT NOT NULL DEFAULT 'pcs',
    cost_price      REAL NOT NULL,
    msrp            REAL NOT NULL,
    current_price   REAL NOT NULL,
    current_stock   INTEGER NOT NULL DEFAULT 0,
    safety_stock    INTEGER NOT NULL DEFAULT 0,
    weather_sensitivity TEXT NOT NULL DEFAULT 'none', -- none|hot|cold|rain
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products (category_id);

CREATE TABLE IF NOT EXISTS sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL,
    sale_date       TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    unit_price      REAL NOT NULL,
    total           REAL NOT NULL,
    weather_condition TEXT,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales (product_id);

CREATE TABLE IF NOT EXISTS weather_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date     TEXT NOT NULL UNIQUE,
    temp_max_c      REAL,
    temp_min_c      REAL,
    precipitation_mm REAL,
    condition       TEXT,
    is_forecast     INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_records (record_date);

CREATE TABLE IF NOT EXISTS local_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    event_date          TEXT NOT NULL,
    category            TEXT NOT NULL,             -- sports|festival|cultural|wedding|exam|public-holiday
    expected_attendance INTEGER NOT NULL DEFAULT 0,
    impact_factor       REAL NOT NULL DEFAULT 1.0, -- multiplier on baseline demand (e.g, 1.15 = +15%)
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_events_date ON local_events (event_date);

CREATE TABLE IF NOT EXISTS pricing_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL,
    old_price       REAL NOT NULL,
    new_price       REAL NOT NULL,
    change_pct      REAL NOT NULL,
    reason          TEXT NOT NULL,
    recommended_at  TEXT NOT NULL DEFAULT (datetime('now')),
    applied         INTEGER NOT NULL DEFAULT 0,
    applied_at      TEXT,
    reverted        INTEGER NOT NULL DEFAULT 0,
    reverted_at     TEXT,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE INDEX IF NOT EXISTS idx_pricing_history_product ON pricing_history (product_id);
