from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_sale_date_id", "sale_date", "id"),
        CheckConstraint("status IN ('won', 'lost', 'open')", name="ck_sales_status"),
        CheckConstraint("revenue >= 0 AND cost >= 0", name="ck_sales_money"),
        CheckConstraint(
            "(status = 'won' AND orders_count > 0) OR "
            "(status IN ('lost', 'open') AND orders_count = 0 AND revenue = 0 AND cost = 0)",
            name="ck_sales_outcome",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[str] = mapped_column(String(50), unique=True)
    sale_date: Mapped[date] = mapped_column(Date)
    department: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(10))
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    orders_count: Mapped[int]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    product: Mapped["Product"] = relationship(back_populates="sales")
    manager: Mapped["User"] = relationship(back_populates="sales")

    @property
    def month(self) -> str:
        return self.sale_date.strftime("%Y-%m")
