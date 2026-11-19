"""Очистка только локальной учебной SQLite через --yes."""
import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete

from src.database import SessionLocal, engine
from src.models import Kpi, MetricSetting, Product, Report, Sale, User


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Подтвердить удаление строк")
    args = parser.parse_args()
    if not args.yes:
        parser.error("Требуется --yes.")
    if engine.url.get_backend_name() != "sqlite":
        parser.error("Очистка поддерживается только для локальной SQLite.")
    with SessionLocal.begin() as session:
        for model in (Kpi, Report, Sale, MetricSetting, Product, User):
            session.execute(delete(model))
    print("Tables cleared. Schema and Alembic revision retained.")


if __name__ == "__main__":
    main()
