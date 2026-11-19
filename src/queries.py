"""Запросы слоя доступа к данным. Область доступа вычисляет вызывающий сервис."""
import re
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from src.models import Product, Sale, User


def _month_filter(month: str):
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("Ожидается месяц в формате YYYY-MM.")
    start = date.fromisoformat(f"{month}-01")
    if start == date(9999, 12, 1):
        return Sale.sale_date >= start
    end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
    return (Sale.sale_date >= start) & (Sale.sale_date < end)


def get_sales_by_month(session: Session, month: str) -> list[Sale]:
    stmt = select(Sale).where(_month_filter(month)).order_by(Sale.sale_date, Sale.id)
    return list(session.execute(stmt).scalars())


def get_total_revenue(session: Session, month: str) -> Decimal:
    stmt = select(func.sum(Sale.revenue)).where(_month_filter(month), Sale.status == "won")
    return session.execute(stmt).scalar_one() or Decimal("0.00")


def get_sales_with_manager_and_product(session: Session, month: str):
    stmt = (
        select(Sale, User.username, Product.name)
        .join(Sale.manager)
        .join(Sale.product)
        .where(_month_filter(month))
        .order_by(Sale.sale_date, Sale.id)
    )
    return session.execute(stmt).all()


def get_kpi_dashboard(session: Session, month: str) -> dict[str, Decimal | int | None]:
    stmt = select(
        func.sum(Sale.revenue).label("revenue"),
        func.sum(Sale.cost).label("cost"),
        func.sum(Sale.orders_count).label("orders"),
        func.sum(case((Sale.status == "won", 1), else_=0)).label("won"),
        func.count().label("closed"),
    ).where(_month_filter(month), Sale.status.in_(("won", "lost")))
    row = session.execute(stmt).one()
    revenue = row.revenue or Decimal("0.00")
    cost = row.cost or Decimal("0.00")
    orders = row.orders or 0
    return {
        "total_revenue": revenue,
        "total_cost": cost,
        "total_orders": orders,
        "avg_check": revenue / orders if orders else None,
        "profitability": (revenue - cost) / revenue * 100 if revenue else None,
        "conversion": Decimal(row.won or 0) / row.closed * 100 if row.closed else None,
    }
