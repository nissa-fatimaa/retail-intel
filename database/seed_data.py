from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from faker import Faker

from config.settings import (
    DEFAULT_CITY,
    DEMO_ACCOUNTS,
    WEATHER_MODIFIERS,
)
from database.db_manager import DatabaseManager
from models.event import EventRepository
from models.product import ProductRepository
from models.sale import SaleRepository
from models.user import UserRepository
from services.auth_service import hash_password
from services.weather_service import DayWeather, WeatherService, _classify_condition
from utils.logger import get_logger

logger = get_logger(__name__)
fake = Faker()
Faker.seed(42)
random.seed(42)

#grocery store data
@dataclass
class SeedProduct:
    name: str
    unit: str
    cost: float
    msrp: float
    stock: int
    safety: int
    sensitivity: str      #'none' | 'hot' | 'cold' | 'rain'
    base_demand: float    #avg units sold/day in baseline conditions


CATALOGUE: dict[str, list[SeedProduct]] = {
    "Fresh Produce": [
        SeedProduct("Tomatoes", "kg", 60, 110, 80, 30, "none", 26.0),
        SeedProduct("Onions", "kg", 50, 90, 120, 40, "none", 32.0),
        SeedProduct("Potatoes", "kg", 45, 80, 150, 50, "none", 30.0),
        SeedProduct("Apples (Kashmiri)", "kg", 180, 320, 60, 20, "none", 14.0),
        SeedProduct("Bananas", "dozen", 110, 200, 50, 20, "none", 18.0),
        SeedProduct("Mangoes (Sindhri)", "kg", 220, 380, 70, 25, "hot", 22.0),
        SeedProduct("Spinach", "bunch", 30, 60, 40, 15, "rain", 12.0),
        SeedProduct("Coriander", "bunch", 15, 30, 60, 20, "none", 22.0),
    ],
    "Dairy & Eggs": [
        SeedProduct("Olper's Full Cream Milk 1L", "L", 240, 320, 90, 30, "none", 28.0),
        SeedProduct("Nestle Yogurt 500g", "tub", 150, 220, 70, 25, "hot", 18.0),
        SeedProduct("Adam's Cheese Slices 200g", "pack", 320, 480, 40, 15, "none", 7.0),
        SeedProduct("Desi Eggs (Tray of 30)", "tray", 600, 820, 30, 10, "none", 9.0),
        SeedProduct("Butter 250g", "pack", 380, 540, 35, 12, "cold", 8.0),
        SeedProduct("Lassi 500ml", "bottle", 90, 150, 60, 20, "hot", 16.0),
    ],
    "Bakery": [
        SeedProduct("Dawn White Bread", "loaf", 130, 200, 80, 30, "none", 22.0),
        SeedProduct("Brown Bread (Whole Wheat)", "loaf", 150, 230, 60, 20, "none", 16.0),
        SeedProduct("Bun Pack (6)", "pack", 140, 210, 50, 18, "none", 14.0),
        SeedProduct("Rusks (Cake Rusk)", "pack", 220, 320, 40, 15, "cold", 11.0),
        SeedProduct("Naan Khatai 250g", "box", 260, 380, 35, 12, "none", 8.0),
        SeedProduct("Pita Bread 6pc", "pack", 160, 240, 45, 15, "none", 10.0),
    ],
    "Beverages": [
        SeedProduct("Coca-Cola 1.5L", "bottle", 180, 260, 100, 35, "hot", 26.0),
        SeedProduct("Pepsi 1.5L", "bottle", 175, 255, 90, 30, "hot", 22.0),
        SeedProduct("Slice Mango Juice 1L", "carton", 200, 300, 70, 25, "hot", 18.0),
        SeedProduct("Tapal Danedar Tea 950g", "box", 1450, 1900, 35, 12, "cold", 8.0),
        SeedProduct("Lipton Yellow Label 475g", "box", 950, 1280, 30, 10, "cold", 6.0),
        SeedProduct("Nescafe Classic 200g", "jar", 1750, 2350, 25, 10, "cold", 5.0),
        SeedProduct("Mineral Water 1.5L", "bottle", 60, 110, 200, 60, "hot", 38.0),
    ],
    "Snacks": [
        SeedProduct("Lays Masala 60g", "pack", 70, 110, 150, 50, "none", 32.0),
        SeedProduct("Kurkure Chutney Chaska", "pack", 30, 50, 200, 70, "none", 42.0),
        SeedProduct("Dairy Milk Chocolate 38g", "bar", 130, 200, 90, 30, "cold", 18.0),
        SeedProduct("Peek Freans Sooper", "pack", 50, 80, 180, 60, "none", 36.0),
        SeedProduct("Knorr Noodles", "pack", 60, 100, 150, 50, "rain", 24.0),
    ],
    "Pantry Staples": [
        SeedProduct("Basmati Rice 5kg (Sella)", "bag", 1850, 2400, 35, 12, "none", 5.0),
        SeedProduct("Sunridge Atta 10kg", "bag", 1380, 1750, 40, 15, "none", 7.0),
        SeedProduct("Dalda Cooking Oil 5L", "tin", 2900, 3650, 30, 10, "none", 4.0),
        SeedProduct("Sugar 1kg", "kg", 220, 290, 120, 40, "none", 26.0),
        SeedProduct("National Salt 800g", "pack", 90, 140, 100, 30, "none", 14.0),
        SeedProduct("Shan Biryani Masala", "pack", 130, 195, 80, 25, "rain", 16.0),
        SeedProduct("Daal Chana 1kg", "kg", 380, 520, 60, 20, "none", 11.0),
    ],
    "Frozen Foods": [
        SeedProduct("K&N's Chicken Nuggets 1kg", "pack", 1100, 1500, 40, 15, "rain", 9.0),
        SeedProduct("Menu Frozen Parathas (5)", "pack", 380, 520, 50, 18, "cold", 12.0),
        SeedProduct("Walls Vanilla 1L Tub", "tub", 580, 820, 35, 12, "hot", 10.0),
        SeedProduct("Frozen Sheekh Kebabs", "pack", 750, 1050, 30, 10, "rain", 7.0),
    ],
    "Household": [
        SeedProduct("Surf Excel Detergent 1kg", "bag", 540, 740, 60, 20, "none", 9.0),
        SeedProduct("Dettol Antiseptic 250ml", "bottle", 480, 680, 45, 15, "none", 6.0),
        SeedProduct("Harpic Toilet Cleaner 1L", "bottle", 420, 580, 40, 15, "none", 5.0),
        SeedProduct("Lifebuoy Soap (4-Pack)", "pack", 380, 540, 70, 25, "none", 8.0),
    ],
}


LAHORE_EVENTS = [
    ("PSL Match - Qalandars at Gaddafi Stadium", 3, "local", 25_000, 1.18,
     "Cricket league fixture drives big snack/beverage uplift."),
    ("Food Street Festival, Old Lahore", 6, "local", 15_000, 1.22,
     "Citywide foodie weekend; bakery & beverages spike."),
    ("Eid Shopping Weekend", 9, "religious", 50_000, 1.30,
     "Eid prep so staples and dairy peak."),
    ("Wedding Season Winter", 12, "weather", 4_000, 1.10,
     "Multiple weddings drive premium produce demand."),
    ("FAST University Finals", 15, "custom", 0, 0.92,
     "Students stay in; foot traffic dips slightly."),
    ("Independence Day (14 Aug)", 18, "national", 30_000, 1.15,
     "National holiday so beverages & snacks up."),
    ("Lahore Literary Festival", 22, "local", 8_000, 1.08,
     "Cultural event in Gulberg so modest uplift."),
    ("Ramadan Iftaar Drive (Charity)", 25, "religious", 5_000, 1.12,
     "Bulk pantry purchases for community iftaar."),
]


def seed_if_empty() -> None:
    if UserRepository.count() > 0:
        return
    logger.info("Seeding fresh database...")
    _seed_users()
    category_ids = _seed_categories()
    _seed_products(category_ids)
    _seed_weather_history()
    _seed_events()
    _seed_sales_history()
    _refresh_weather_forecast()
    logger.info("Seeding complete.")


def _seed_users() -> None:
    for acc in DEMO_ACCOUNTS:
        UserRepository.create(
            username=acc["username"],
            password_hash=hash_password(acc["password"]),
            role=acc["role"],
            full_name=acc["full_name"],
            email=acc["email"],
        )
    logger.info("Created %d demo accounts", len(DEMO_ACCOUNTS))


def _seed_categories() -> dict[str, int]:
    ids: dict[str, int] = {}
    for name in CATALOGUE.keys():
        ids[name] = DatabaseManager.execute(
            "INSERT INTO categories (name) VALUES (?)", (name,)
        )
    return ids


def _seed_products(category_ids: dict[str, int]) -> None:
    sku_counter = 1000
    rows = []
    for cat_name, items in CATALOGUE.items():
        cat_id = category_ids[cat_name]
        for item in items:
            sku = f"BFM-{sku_counter}"
            sku_counter += 1
            current_price = item.msrp
            rows.append(
                (
                    sku,
                    item.name,
                    cat_id,
                    item.unit,
                    item.cost,
                    item.msrp,
                    current_price,
                    item.stock,
                    item.safety,
                    item.sensitivity,
                    1,
                )
            )
    DatabaseManager.executemany(
        """
        INSERT INTO products
            (sku, name, category_id, unit, cost_price, msrp, current_price,
             current_stock, safety_stock, weather_sensitivity, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d products across %d categories", len(rows), len(category_ids))


def _seed_weather_history() -> None:
    today = date.today()
    records: list[DayWeather] = []
    for i in range(60, 0, -1):
        d = today - timedelta(days=i)
        #lahore normally has a hot/warm temp as temps roughly 18-40°C across a year; pick a sensible range
        month = d.month
        if month in (12, 1, 2):
            tmax = random.uniform(15, 22)
            tmin = tmax - random.uniform(6, 10)
            precip = random.choices([0, 0, 0, 1.5, 6.0], weights=[6, 5, 4, 2, 1])[0]
        elif month in (3, 4, 10, 11):
            tmax = random.uniform(24, 32)
            tmin = tmax - random.uniform(8, 12)
            precip = random.choices([0, 0, 0, 1.0, 4.0], weights=[7, 5, 4, 2, 1])[0]
        elif month in (5, 6):
            tmax = random.uniform(36, 44)
            tmin = tmax - random.uniform(10, 14)
            precip = random.choices([0, 0, 0, 0, 2.0], weights=[8, 6, 4, 2, 1])[0]
        else:  #monsoon Jul/Aug/Sep
            tmax = random.uniform(30, 38)
            tmin = tmax - random.uniform(6, 10)
            precip = random.choices([0, 1.0, 5.0, 12.0, 25.0], weights=[3, 4, 4, 2, 1])[0]
        records.append(
            DayWeather(
                record_date=d.isoformat(),
                temp_max_c=round(tmax, 1),
                temp_min_c=round(tmin, 1),
                precipitation_mm=round(precip, 1),
                condition=_classify_condition(tmax, precip),
                is_forecast=False,
            )
        )
    WeatherService.persist(records, mark_as_forecast=False)
    logger.info("Seeded %d days of historical weather for %s", len(records), DEFAULT_CITY)


def _seed_events() -> None:
    today = date.today()
    for name, days_ahead, category, attendance, impact, notes in LAHORE_EVENTS:
        EventRepository.add(
            name=name,
            event_date=(today + timedelta(days=days_ahead)).isoformat(),
            category=category,
            expected_attendance=attendance,
            impact_factor=impact,
            notes=notes,
        )
    logger.info("Seeded %d local events", len(LAHORE_EVENTS))


def _seed_sales_history() -> None:
    products = ProductRepository.list_all()
    weather_by_date = {
        w.record_date: w for w in WeatherService.read_range(
            date.today() - timedelta(days=60), date.today() - timedelta(days=1)
        )
    }

    today = date.today()

    #seed-product lookup by name to recover base_demand
    base_demand_lookup: dict[str, SeedProduct] = {}
    for items in CATALOGUE.values():
        for item in items:
            base_demand_lookup[item.name] = item

    rows = []
    for product in products:
        sp = base_demand_lookup.get(product.name)
        if not sp:
            continue
        for i in range(60, 0, -1):
            d = today - timedelta(days=i)
            base = sp.base_demand
            #day-of-week effect: Sat/Sun busier
            dow = d.weekday()
            if dow == 5:
                base *= 1.30
            elif dow == 6:
                base *= 1.20
            elif dow == 4:  #friday can be considered heavy too in lahore (since its holiday nowadays)
                base *= 1.15
            elif dow == 1:
                base *= 0.92

            #weather sensitivity from history applying
            w = weather_by_date.get(d.isoformat())
            if w and sp.sensitivity != "none":
                if sp.sensitivity == "hot" and (w.temp_max_c or 0) >= WEATHER_MODIFIERS["hot_day_threshold_c"]:
                    base *= 1.20
                elif sp.sensitivity == "cold" and (w.temp_max_c or 99) <= WEATHER_MODIFIERS["cold_day_threshold_c"]:
                    base *= 1.20
                elif sp.sensitivity == "rain" and (w.precipitation_mm or 0) >= 1.0:
                    base *= 1.15
                elif w and w.condition == "Heavy Rain":
                    base *= 0.92

            #stochastic noise adding
            qty = max(0, int(round(random.gauss(base, base * 0.18))))
            if qty == 0:
                continue
            unit_price = product.current_price
            rows.append(
                (
                    product.id,
                    d.isoformat(),
                    qty,
                    unit_price,
                    round(qty * unit_price, 2),
                    w.condition if w else None,
                )
            )

    DatabaseManager.executemany(
        """
        INSERT INTO sales (product_id, sale_date, quantity, unit_price, total, weather_condition)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Seeded %d sales transactions", len(rows))


def _refresh_weather_forecast() -> None:
    try:
        WeatherService.fetch_forecast(days=10)
    except Exception:
        logger.info("Online forecast unavailable; synthesising 7-day forecast.")
        today = date.today()
        records = []
        for i in range(0, 10):
            d = today + timedelta(days=i)
            tmax = random.uniform(24, 38)
            tmin = tmax - random.uniform(8, 12)
            precip = random.choices([0, 0, 0, 1.5, 6.0], weights=[6, 5, 4, 2, 1])[0]
            records.append(
                DayWeather(
                    record_date=d.isoformat(),
                    temp_max_c=round(tmax, 1),
                    temp_min_c=round(tmin, 1),
                    precipitation_mm=round(precip, 1),
                    condition=_classify_condition(tmax, precip),
                    is_forecast=True,
                )
            )
        WeatherService.persist(records, mark_as_forecast=True)
