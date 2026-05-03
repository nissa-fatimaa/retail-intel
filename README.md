Retail Intel - Project Reference
A standalone PyQt6 desktop application for retail demand & pricing intelligence.

Stack
Language: Python 3.10+
GUI: PyQt6
Charts: matplotlib (Qt6Agg backend)
Database: SQLite (file: data/retail_intel.db)
Seed data: Faker
External API: Open-Meteo (free, no key) for weather
Auth: PBKDF2-HMAC-SHA256 (200,000 iterations) password hashing
No machine learning libraries are used. All forecasting and pricing logic is rule-based, deterministic and reproducible.

Project layout
retail_intel/
├── main.py                     # Application entry point
├── requirements.txt
├── README.md
├── config/
│   └── settings.py             # constants, theme, role labels, demo accounts
├── database/
│   ├── schema.sql              # SQLite schema
│   ├── db_manager.py           # Connection + execute/fetch helpers
│   └── seed_data.py            # CATALOGUE + LAHORE_EVENTS + demo users
├── models/                     # Dataclasses + repositories per table
│   ├── user.py
│   ├── product.py
│   ├── sale.py
│   ├── event.py
│   └── pricing_history.py
├── services/                   # Pure business logic (no UI imports)
│   ├── auth_service.py         # PBKDF2 hash/verify, login, register
│   ├── weather_service.py      # Open-Meteo client + classification + modifiers
│   ├── events_service.py       # Local events CRUD + impact aggregation
│   ├── forecasting_service.py  # Weighted MA + seasonality + modifiers
│   └── pricing_service.py      # Tension index + elasticity + bounded recs
├── ui/
│   ├── styles.py               # Global QSS + matplotlib config
│   ├── login_window.py         # Rectangle login (980x620, glass-morphism)
│   ├── main_window.py          # Sidebar + topbar + page stack
│   ├── widgets/
│   │   ├── logo_widget.py      # SVG logo + "Retail Intel" wordmark
│   │   ├── notification.py     # Toast notifications
│   │   ├── stat_card.py        # KPI card
│   │   ├── chart_widget.py     # ChartFrame + plot helpers
│   │   └── sidebar.py          # Role-aware navigation
│   └── pages/
│       ├── dashboard_staff.py
│       ├── dashboard_visitor.py
│       ├── dashboard_executive.py
│       ├── forecasting_page.py
│       ├── pricing_page.py
│       ├── what_if_page.py     # Decision Simulator
│       ├── inventory_page.py
│       └── events_page.py
├── utils/
│   ├── helpers.py              # Formatters (PKR money, %, int), date utils
│   └── logger.py               # Single get_logger() entry point
├── assets/
│   └── logo.svg                # Brand mark
└── data/                       # SQLite DB file lives here at runtime

Demo accounts:
Role	Username	Password	Sees
Staff	staff	staff123	# Daily ops dashboard, inventory, events
Visitor	visitor	visitor123	# Public-facing store snapshot, events
Executive	executive	exec123	# Strategic KPIs, forecasting, pricing, simulator
Anyone may also register via the login window (role selectable)

Default location:
Store: Bahria Fresh Mart
City: Lahore, Pakistan
Coordinates: 31.5204 N, 74.3587 E (Asia/Karachi)
Currency: PKR (formatted Rs 1,234)
Dataset — "Bahria Fresh Mart" grocery catalogue
8 categories × 6 products = 48 SKUs, all priced in PKR with realistic Lahore market values. Each product carries a weather_sensitivity flag (hot, cold, rain, none) used by the forecasting modifier.

Category	Sample products	Sensitivity
Fresh Produce	Tomatoes, Onions, Potatoes, Spinach, Mangoes	rain
Dairy & Eggs	Milk 1L, Yogurt, Eggs (dozen), Cheese block	hot
Bakery	Naan, Sliced bread, Sweet rusks, Bran bread	cold
Beverages	Cola 1.5L, Mango juice, Mineral water 1.5L	hot
Snacks	Lays Salted, Slanty, Biscuits, Roasted peanuts	none
Pantry Staples	Basmati rice 5kg, Atta 10kg, Cooking oil, Salt	none
Frozen	Chicken nuggets, Frozen parathas, Ice cream tub	hot
Household	Detergent, Dish soap, Toilet rolls, Surface clr	none
Synthetic sales
seed_data.py generates 60 days of daily sales per product using:

Per-product mean daily volume (Faker seeded for repeatability)
Day-of-week effects (Friday/Saturday peaks, Wednesday troughs)
Random ±20% jitter
Weather-sensitive products amplified on sample hot/rainy days
Lahore-themed events (LAHORE_EVENTS)
8 events spread across the next 90 days, used by the events service and demand forecaster. Each carries an impact_factor that the forecasting engine applies as a multiplier:

Event	Category	Impact ×
Eid-ul-Fitr	religious	1.40
Eid-ul-Adha	religious	1.35
Pakistan Independence Day	national	1.20
Lahore Literary Festival	local	1.10
PSL Final at Gaddafi Stadium	local	1.18
Spring Basant Weekend	local	1.15
Heavy monsoon advisory	weather	0.85
Winter cold-snap advisory	weather	1.08
Forecasting algorithm (no ML)
For each product / future day:

Base = recency-weighted moving average of the last 14 days of unit sales (newest weighted highest, linear ramp).
Seasonality adjustment = additive day-of-week effect (mean sales for that weekday − overall mean).
Weather multiplier comes from Open-Meteo classification (Hot, Cold, Heavy Rain, etc.) and the product's sensitivity flag, applied multiplicatively.
Event multiplier = compounded impact factors of all active events for that day.
Final = round(max(0, (base + seasonality) × weather × event)).
Every day's DayForecast keeps an explanations list naming the contributing factors so any user can audit the result.

Pricing algorithm (no ML)
1. Tension index = forecast_demand_units(7d) / max(current_stock, 1)
2. Map tension band → target % demand change:
    ≥ 1.30 → reduce demand 12%
    ≥ 1.10 → reduce demand 6%
    0.90–1.10 → hold
    ≥ 0.70 → boost demand 6%
    ≥ 0.50 → boost demand 10%
    < 0.50 → boost demand 15%
3. Convert to price change via per-category elasticity (price_pct = demand_pct / elasticity).
4. Clamp to ±15% and to bounded range:
    Floor = cost_price × (1 + 10% min margin)
    Ceiling = MSRP × 1.20
5. Build a plain-language reason string explaining the decision.

The first launch creates data/retail_intel.db, seeds the catalogue and demo users, and pulls a 7-day weather forecast from Open-Meteo. Subsequent launches reuse the existing database.

INDIVIDUAL FILE DESCRIPTION:
1. assets/logo.svg --> logo image for Retail Intel
2. config/settings.py --> Centralized configuration for Retail Intel. All paths, theme colours, location defaults, and role definitions live here so the rest of the codebase has a single source of truth
3. database/db_manager.py --> SQLite database manager. Provides a thread-safe connection helper, schema initialization, and small utility methods used by services and the seed script.
    DatabaseManager: Static helpers around a single SQLite database file
        initialize(): Create the schema if it does not exist, then run lightweight migrations
        _migrate(): Idempotent ALTER TABLE migrations for older databases.
4. database/seed_data.py --> Seed the database with realistic synthetic retail data on first launch.
    Generates:
        * Demo user accounts (3 roles)
        * 8 product categories
        * ~48 grocery products
        * 60 days of historical weather (synthetic) + a forecast pull from Open-Meteo
        * 8 upcoming local events (Lahore-themed)
        * 60 days of synthetic sales transactions (with day-of-week, weather, event signals)
    seed_if_empty(): Run seeding only when the DB has no users yet.
    _seed_weather_history(): Generate 60 days of synthetic Lahore weather (hott climate)
    _seed_sales_history(): Generate 60 days of sales using base_demand + signals
    _refresh_weather_forecast(): Try to fetch a fresh forecast from Open-Meteo. Synthesise on failure
5. models/product.py -->product repo
    low_stock_items(): Return products at or below safety_stock * threshold_multiplier
6. models/sale.py --> sale repo and model
    daily_quantity_for_product(): Return [(date, qty)] for the last days (oldest first), zero-filled
7. services/auth_service.py --> Authentication service...Passwords are hashed with PBKDF2-HMAC-SHA256 + per-user salt. The hash format stored in the DB is: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
8. services/forecasting_service.py -->Demand forecasting service.

Pure rule-based pipeline (NO machine learning):
Base forecast for day t+k:
    base = weighted_moving_average(last_window_days_of_sales)
        + day_of_week_seasonality_adjustment

Adjustments:
    weather_modifier   — depends on the product's weather sensitivity
    event_modifier     — combined impact factor of all local events on date t+k

Final forecast = base * weather_modifier * event_modifier
Final forecast is non-negative integer

