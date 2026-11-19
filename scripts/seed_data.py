"""Запуск из корня: python -m scripts.seed_data."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from random import Random
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faker import Faker
from sqlalchemy import select

from src.database import SessionLocal
from src.models import Kpi, MetricSetting, Product, Report, Sale, User
from src.queries import get_kpi_dashboard

MODELS = (User, Product, Sale, MetricSetting, Kpi, Report)
METRICS = {
    "revenue": ("SUM(revenue)", "total_revenue"),
    "profitability": ("(SUM(revenue) - SUM(cost)) / SUM(revenue) * 100", "profitability"),
    "avg_check": ("SUM(revenue) / SUM(orders_count)", "avg_check"),
    "conversion": ("won_deals / closed_deals * 100", "conversion"),
}


def seed(session):
    if any(session.scalar(select(model.id).limit(1)) is not None for model in MODELS):
        raise ValueError("Таблицы уже содержат данные. Используйте отдельную учебную БД или reset_db.")
    fake = Faker("ru_RU")
    fake.seed_instance(42)
    rng = Random(42)
    stamp = datetime(2026, 7, 1, 9)
    roles = ("director", "analyst", "admin", *("manager",) * 7)
    users = []
    for i, role in enumerate(roles, 1):
        login = f"{fake.user_name()[:32]}_{i}"
        users.append(User(
            username=login, email=f"{login}@example.test", role=role, created_at=stamp,
            password_hash="!disabled:" + sha256(login.encode()).hexdigest(),
        ))
    products = []
    catalog = {
        "Электроника": ["Наушники", "Клавиатура", "Мышь", "Зарядное устройство"],
        "Одежда": ["Футболка", "Куртка", "Брюки", "Шарф"],
        "Продукты": ["Кофе", "Чай", "Печенье", "Шоколад"],
        "Бытовая химия": ["Гель для стирки", "Мыло", "Средство для посуды", "Кондиционер"],
        "Книги": ["Атлас", "Роман", "Словарь", "Сборник рассказов"],
    }
    for category, names in catalog.items():
        for name in names:
            products.append(Product(name=name, category=category,
                                    price=Decimal(rng.randint(10000, 500000)) / 100,
                                    description=fake.sentence(nb_words=8)))
    settings = [MetricSetting(metric_name=name, formula=formula, is_active=True)
                for name, (formula, _) in METRICS.items()]
    session.add_all([*users, *products, *settings])
    session.flush()
    for i in range(1, 501):
        manager_index = rng.randrange(7)
        product = rng.choice(products)
        status = rng.choices(("won", "lost", "open"), (75, 17, 8))[0]
        orders = rng.randint(1, 20) if status == "won" else 0
        revenue = product.price * orders
        cost = (revenue * Decimal(rng.randint(45, 85)) / 100).quantize(Decimal(".01"))
        session.add(Sale(
            deal_id=f"DEMO-{i:04}", sale_date=date(2026, 1, 1) + timedelta(days=rng.randrange(181)),
            manager_id=users[3 + manager_index].id, product_id=product.id,
            department=("Розница", "Онлайн", "Опт")[manager_index % 3], status=status,
            revenue=revenue, cost=cost, orders_count=orders,
        ))
    session.flush()
    for month in range(1, 7):
        period = f"2026-{month:02}"
        kpis = get_kpi_dashboard(session, period)
        for name, (_, field) in METRICS.items():
            value = kpis[field]
            session.add(Kpi(period=period, metric_name=name, calculated_at=stamp,
                            value=value.quantize(Decimal(".0001")) if value is not None else None))
    # Синтетические ссылки на объекты для проверки FK, без генерации файлов отчётов.
    session.add_all(Report(report_type="xlsx", period=f"2026-0{i}",
                           file_path=f"demo/reports/2026-0{i}.xlsx",
                           created_by=users[1].id, created_at=stamp)
                    for i in range(1, 4))


if __name__ == "__main__":
    try:
        with SessionLocal.begin() as session:
            seed(session)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print("Created: 10 users, 20 products, 500 sales, 4 metric settings, 24 KPI, 3 report records.")
