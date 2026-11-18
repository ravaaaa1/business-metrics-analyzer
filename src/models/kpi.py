from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Kpi(Base):
    __tablename__ = "kpi"
    __table_args__ = (UniqueConstraint("period", "metric_name", name="uq_kpi_period_metric"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    period: Mapped[str] = mapped_column(String(7))
    metric_name: Mapped[str] = mapped_column(ForeignKey("metric_settings.metric_name"), index=True)
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    metric: Mapped["MetricSetting"] = relationship(back_populates="values")
