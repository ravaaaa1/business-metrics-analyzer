# ПЗ № 5. Проектирование и создание базы данных

Business Metrics Analyzer · Ровинский Роман Олегович, Корякин Никита Иванович · Б1123-38.03.05ба(1)

| Задание | Результат |
|---|---|
| 1. ER-модель и 3НФ | [Диаграмма PNG](er_diagram.png), [атрибуты, ограничения и индексы](schema.md) |
| 2. Подключение | [create_engine, SessionLocal и SQLite FK](../../src/database.py), [шаблон настроек](../../.env.example) |
| 3. Модели | [Шесть моделей SQLAlchemy 2.0](../../src/models/) |
| 4. Миграции | [Ревизии 0001 и 0002](../../migrations/versions/), [конфигурация](../../alembic.ini) |
| 5. Запросы | [Четыре запроса](../../src/queries.py), [семь тестов](../../tests/test_queries.py) |
| 6. Faker | [Наполнение](../../scripts/seed_data.py), [очистка](../../scripts/reset_db.py) |
| 7. Защита | [Презентация PDF](presentation.pdf), [PowerPoint](presentation.pptx), [сценарий и вопросы](defense.md) |

## Запуск

Из корня репозитория в активированном виртуальном окружении Python 3.10+:

```text
python -m pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` (PowerShell: `Copy-Item .env.example .env`). SQLite создаётся локально при подключении. ORM и Alembic используют один `DATABASE_URL`. Для PostgreSQL потребуется установить `psycopg2-binary` и задать URL с драйвером `postgresql+psycopg2`. Проверки ниже выполнены на SQLite.

```text
python -c "from sqlalchemy import text; from src.database import engine; c=engine.connect(); print(c.scalar(text('SELECT 1'))); c.close()"
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python scripts/seed_data.py
python -m pytest -q
```

На пустой учебной БД цикл отката и повторного применения: `python -m alembic downgrade -1`, затем `python -m alembic upgrade head`. Для воспроизведения данных на учебной SQLite после наполнения: `python scripts/reset_db.py --yes`, затем `python scripts/seed_data.py`. Команда с `--yes` удаляет строки всех шести таблиц. Схема и номер ревизии сохраняются. Скрипт наполнения отказывается работать на заполненной базе и выполняет вставки одной транзакцией.

```python
from src.database import SessionLocal
from src.queries import (get_sales_by_month, get_total_revenue,
                         get_sales_with_manager_and_product, get_kpi_dashboard)

with SessionLocal() as session:
    period = "2026-01"
    print(len(get_sales_by_month(session, period)))
    print(get_total_revenue(session, period))
    sale, manager, product = get_sales_with_manager_and_product(session, period)[0]
    print(sale.deal_id, manager, product)
    print(get_kpi_dashboard(session, period))
```

## Контрольный прогон

Подключение вернуло 1, внешний ключ SQLite включён, активная ревизия 0002. После `upgrade head → downgrade -1 → upgrade head` команда `alembic check` подтвердила соответствие таблиц моделям. Семь тестов прошли. После очистки и повторного наполнения совпал SHA-256 канонического снимка всех строк, включая связи и даты: `6f0f19addede5e866ea611d750dcba2740e1902b44f35cb8cf7cad041c833ab9`.

| Данные | Результат |
|---|---|
| Объём базы | 10 пользователей, 20 товаров, 500 сделок, 4 настройки метрик, 24 результата KPI, 3 записи отчётов |
| Выборка и JOIN за январь 2026 | 74 записи. Первая — DEMO-0062, hariton1988_9, Мыло |
| Выручка и затраты | 1 571 424,36 ₽ и 1 007 868,37 ₽ |
| Заказы и средний чек | 613 и 2 563,50 ₽ |
| Рентабельность и конверсия | 35,86% и 85,07% |

Данные синтетические. Строки отчётов демонстрируют связи с авторами и ключи хранилища.
