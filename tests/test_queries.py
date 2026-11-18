from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import Base, make_engine
from src.models import Product, Sale, User
from src.queries import (
    get_kpi_dashboard, get_sales_by_month, get_sales_with_manager_and_product, get_total_revenue,
)


@pytest.fixture
def session():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            manager = User(username="manager1", email="m@example.test", password_hash="!", role="manager")
            product = Product(name="Товар 1", category="A", price=100)
            session.add_all([manager, product])
            session.flush()
            cases = [(15, "won", 1000, 700, 5), (1, "won", 100, 50, 1),
                     (2, "lost", 0, 0, 0), (3, "open", 0, 0, 0)]
            for day, status, revenue, cost, count in cases:
                session.add(Sale(deal_id=f"deal-{day}", sale_date=date(2026, 1, day),
                                 department="D1", status=status, revenue=revenue, cost=cost,
                                 orders_count=count, manager=manager, product=product))
            session.add(Sale(deal_id="next-month", sale_date=date(2026, 2, 1), department="D1",
                             status="won", revenue=99, cost=110, orders_count=1,
                             manager=manager, product=product))
            session.commit()
            yield session
    finally:
        engine.dispose()


def test_get_sales_by_month(session):
    assert [item.sale_date.day for item in get_sales_by_month(session, "2026-01")] == [1, 2, 3, 15]
    assert get_sales_by_month(session, "2026-03") == []


def test_get_total_revenue(session):
    assert get_total_revenue(session, "2026-01") == Decimal("1100.00")
    assert get_total_revenue(session, "2026-03") == Decimal("0.00")


def test_get_sales_with_manager_and_product(session):
    rows = get_sales_with_manager_and_product(session, "2026-02")
    assert [(sale.deal_id, manager, product) for sale, manager, product in rows] == [
        ("next-month", "manager1", "Товар 1")
    ]


def test_get_kpi_dashboard(session):
    assert get_kpi_dashboard(session, "2026-01") == {
        "total_revenue": Decimal(1100), "total_cost": Decimal(750),
        "total_orders": 6, "avg_check": Decimal(1100) / 6,
        "profitability": Decimal(350) / 1100 * 100, "conversion": Decimal(2) / 3 * 100,
    }
    assert get_kpi_dashboard(session, "2026-02")["profitability"] < 0


def test_empty_dashboard(session):
    assert get_kpi_dashboard(session, "2026-03") == {
        "total_revenue": Decimal(0), "total_cost": Decimal(0), "total_orders": 0,
        "avg_check": None, "profitability": None, "conversion": None,
    }


def test_invalid_period(session):
    with pytest.raises(ValueError):
        get_total_revenue(session, "2026-13")


def test_foreign_key_is_enforced(session):
    sale = get_sales_by_month(session, "2026-01")[0]
    sale.product_id = 99999
    with pytest.raises(IntegrityError):
        session.flush()
