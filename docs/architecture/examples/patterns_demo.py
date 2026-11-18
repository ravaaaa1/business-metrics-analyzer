"""Executable Repository + Unit of Work + Strategy example, Python 3.10+."""
from dataclasses import dataclass
from decimal import Decimal
import sqlite3
from typing import Protocol


@dataclass(frozen=True)
class Sale:
    deal_id: str
    status: str
    amount: Decimal
    cost: Decimal


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


@dataclass(frozen=True)
class KpiInputs:
    revenue: Decimal
    cost: Decimal
    won: int
    lost: int

    @classmethod
    def aggregate(cls, sales):
        won = [sale for sale in sales if sale.status == 'won']
        return cls(sum((s.amount for s in won), Decimal(0)),
                   sum((s.cost for s in won), Decimal(0)),
                   len(won), sum(s.status == 'lost' for s in sales))


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


def demonstrate():
    connection = sqlite3.connect(':memory:')
    try:
        connection.execute('CREATE TABLE sales '
                           '(id TEXT PRIMARY KEY, status TEXT, amount TEXT, cost TEXT)')
        with UnitOfWork(connection) as uow:
            for row in [('1', 'won', '10000', '7000'),
                        ('2', 'won', '8000', '5000'),
                        ('3', 'won', '12000', '9000'),
                        ('4', 'lost', '0', '0'), ('5', 'open', '0', '0')]:
                uow.sales.add(Sale(row[0], row[1], Decimal(row[2]), Decimal(row[3])))
        before = SqlSaleRepository(connection).all()
        try:
            with UnitOfWork(connection) as uow:
                uow.sales.add(Sale('6', 'won', Decimal(1), Decimal(0)))
                uow.sales.add(before[0])  # duplicate id, transaction must rollback
        except sqlite3.IntegrityError:
            pass
        assert SqlSaleRepository(connection).all() == before, 'rollback failed'
        inputs = KpiInputs.aggregate(before)
        strategies: list[KpiStrategy] = [Revenue(), AverageCheck(), Conversion(), Profitability()]
        actual = [s.calculate(inputs) for s in strategies]
        assert actual == [Decimal(30000), Decimal(10000), Decimal(75), Decimal(30)]
        empty = KpiInputs.aggregate([])
        assert [s.calculate(empty) for s in strategies] == [Decimal(0), None, None, None]
        assert Profitability().calculate(KpiInputs(Decimal(10), Decimal(20), 1, 0)) == -100
        print('PASS: commit, rollback, four KPI, zero denominators, negative margin')
    finally:
        connection.close()


if __name__ == '__main__':
    demonstrate()
