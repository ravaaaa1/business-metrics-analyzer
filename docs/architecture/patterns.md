# Паттерны проектирования

## Выбор и альтернативы
| Паттерн | Где применяется | Обоснование | Альтернативы |
|---|---|---|---|
| Repository | Сделки, пользователи, аудит | SQL скрыт за портом, можно подставить memory-реализацию | Прямой ORM проще сначала, но связывает сценарий с БД |
| Unit of Work | Публикация набора и смена прав | Данные, версия и аудит успеха фиксируются атомарно | Ручные commit в контроллерах создают частичные изменения |
| Service Layer | Auth, Import, KPI, Reports, Users | Сценарий един для HTTP и worker | Логика в роутерах усложняет повторное использование |
| Factory | Excel/PDF generators, import adapters | Выбор реализации по разрешённому типу в одном месте | if в каждом контроллере дублирует выбор |
| Strategy | Четыре формулы KPI и validation policies | Общий вход агрегатов, заменяемые алгоритмы | Одна большая функция удобна лишь для неизменного набора |
| DTO | HTTP, фоновые задания и снимки отчётов | Явная схема без ORM и утечки секретов | Передача dict без схемы переносит ошибки на runtime |
| Adapter | CSV/Excel/1С, S3 и SMTP | Внешний формат не проникает в бизнес-логику | Прямые SDK-вызовы увеличивают связанность |
| Observer | DatasetPublished и AccessChanged | Подписчики обновляют производные данные после commit | Синхронный вызов всех подписчиков увеличивает задержку |

## Покрытие функциональных областей
Для каждой области указано не менее шести паттернов. Общие паттерны реализуются один раз, не отдельным набором классов на каждый endpoint.

| Область | Применение паттернов |
|---|---|
| Аутентификация и пользователи | Repository: User; UoW: смена роли и аудит; Service Layer: Auth/UserService; DTO: login/UserDto; Adapter: JWT provider; Strategy: политика role/scope |
| Загрузка и импорт | Repository: staging; UoW: публикация версии; Service Layer: SalesImportService; DTO: ImportResult; Adapter: CSV/Excel/1С; Factory: выбор импортера; Observer: DatasetPublished |
| Расчёт KPI | Repository: агрегаты; Service Layer: KpiService; Strategy: четыре формулы; DTO: KpiInputs/KpiResult; Adapter: Redis; Observer: пересчёт после публикации |
| Дашборды | Service Layer: get_dashboard; DTO: DashboardDto; Repository: выборка в scope; Strategy: KPI; Adapter: cache; Observer: версия данных запускает обновление |
| Отчёты и экспорт | Repository: снимок отчёта; UoW: метаданные/job; Service Layer: ReportService; Factory: XLSX/PDF; DTO: ReportSnapshot; Adapter: S3/SMTP; Strategy: formatter |
| Метрики и справочники | Repository: цели/отделы; UoW: изменение и аудит; Service Layer: MetricService; DTO: TargetDto; Strategy: проверка цели; Observer: TargetChanged |
| Логирование и аудит | Repository: AuditEvent; UoW: аудит успеха вместе с изменением; Service Layer: AuditService; DTO: AuditEventDto; Adapter: структурированный logger; Observer: обработка доменных событий |

Observer реализуется через транзакционный outbox с идемпотентными подписчиками, а не обещанием exactly-once доставки. В MVP достаточно прямого пересчёта по version_id, уведомления относятся к третьему спринту. Factory для Excel/API/PDF описывает точки расширения, а не текущую поддержку этих форматов.

## Три ключевых паттерна на Python
Полный автономный пример: [patterns_demo.py](examples/patterns_demo.py). Используется SQLite из стандартной библиотеки как учебный адаптер, целевая СУБД остаётся PostgreSQL. Пример работает с агрегатами выбранного периода и разрешённого scope, не реализует загрузку CSV или веб-сервер.

### Repository и Unit of Work

```python
class SaleRepository(Protocol):
    def add(self, sale: Sale) -> None: ...
    def all(self) -> list[Sale]: ...


class SqlSaleRepository:
    def __init__(self, connection):
        self.connection = connection

    def add(self, sale):
        self.connection.execute(
            'INSERT INTO sales VALUES (?, ?, ?, ?)',
            (sale.deal_id, sale.status, str(sale.amount), str(sale.cost)),
        )

    def all(self):
        return [Sale(i, s, Decimal(a), Decimal(c)) for i, s, a, c in
                self.connection.execute('SELECT * FROM sales ORDER BY id')]


class UnitOfWork:
    """Owns a transaction, caller owns this demo's in-memory connection."""
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.execute('BEGIN')
        self.sales: SaleRepository = SqlSaleRepository(self.connection)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            self.connection.rollback()
            return False
        try:
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise
        return False


```

### Strategy

```python
class KpiStrategy(Protocol):
    def calculate(self, inputs: KpiInputs) -> Decimal | None: ...


class Revenue:
    def calculate(self, inputs):
        return inputs.revenue


class AverageCheck:
    def calculate(self, inputs):
        return inputs.revenue / inputs.won if inputs.won else None


class Conversion:
    def calculate(self, inputs):
        closed = inputs.won + inputs.lost
        return Decimal(inputs.won) / closed * 100 if closed else None


class Profitability:
    def calculate(self, inputs):
        return ((inputs.revenue - inputs.cost) / inputs.revenue * 100
                if inputs.revenue else None)


```
