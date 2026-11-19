from sqlalchemy import Boolean, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class MetricSetting(Base):
    __tablename__ = "metric_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(50), unique=True)
    formula: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean(create_constraint=True, name="ck_metrics_active"), server_default=true())

    values: Mapped[list["Kpi"]] = relationship(back_populates="metric", passive_deletes="all")
