"""Настройка SQLAlchemy для приложения и Alembic."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./business_metrics.db")


class Base(DeclarativeBase):
    pass


def make_engine(url: str = DATABASE_URL):
    parsed = make_url(url)
    options = {"echo": os.getenv("SQL_ECHO") == "1"}
    if parsed.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False}
        if parsed.database in (None, "", ":memory:"):
            options["poolclass"] = StaticPool
    engine = create_engine(parsed, **options)
    if parsed.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()
    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False)
