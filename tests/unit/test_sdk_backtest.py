import sqlite3
from datetime import datetime

import pytest

from stockrhythm.backtest import BacktestClient, BacktestDB, BacktestEngine, _parse_datetime
from stockrhythm.models import Order, OrderSide, OrderType, Tick


def test_parse_datetime_accepts_datetime():
    now = datetime(2024, 1, 1, 12, 0, 0)
    assert _parse_datetime(now) is now


def test_parse_datetime_parses_string():
    value = "2024-01-01T12:00:00"
    parsed = _parse_datetime(value)
    assert parsed == datetime(2024, 1, 1, 12, 0, 0)


def test_parse_datetime_rejects_other_types():
    with pytest.raises(TypeError):
        _parse_datetime(123)


def test_backtest_db_roundtrip(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))

    now = datetime(2024, 1, 1, 12, 0, 0)
    ticks = [
        Tick(symbol="AAPL", price=190.0, volume=10.0, timestamp=now, provider="mock")
    ]

    assert db.insert_ticks([]) == 0
    assert db.insert_ticks(ticks) == 1

    run_id = db.create_run(start_at=now, end_at=now, name="unit")
    order = Order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        limit_price=None,
    )
    order_id = db.record_order(run_id, order, status="filled", created_at=now)
    db.record_trade(run_id, order_id, "AAPL", 1, 190.0, now)
    db.finish_run(run_id, status="completed")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM backtest_runs WHERE id = ?", (run_id,))
    assert cursor.fetchone()[0] == "completed"
    cursor.execute("SELECT COUNT(*) FROM market_ticks")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM backtest_orders")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM backtest_trades")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_backtest_db_fetch_ticks_with_symbols(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    now = datetime(2024, 1, 1, 12, 0, 0)

    db.insert_ticks(
        [
            Tick(symbol="AAA", price=1.0, volume=1.0, timestamp=now, provider="mock"),
            Tick(symbol="BBB", price=2.0, volume=2.0, timestamp=now, provider="mock"),
        ]
    )

    ticks = list(db.fetch_ticks(start_at=now, end_at=now, symbols=["BBB"]))
    assert [tick.symbol for tick in ticks] == ["BBB"]


@pytest.mark.asyncio
async def test_backtest_client_submit_order_uses_limit_price(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    run_id = db.create_run(start_at="2024-01-01T00:00:00", end_at="2024-01-01T00:01:00", name=None)
    client = BacktestClient(db, run_id)

    order = Order(
        symbol="AAA",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        limit_price=101.0,
    )
    result = await client.submit_order(order)

    assert result["status"] == "success"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM backtest_trades")
    assert cursor.fetchone()[0] == 101.0
    conn.close()


@pytest.mark.asyncio
async def test_backtest_client_submit_order_uses_last_tick(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    run_id = db.create_run(start_at="2024-01-01T00:00:00", end_at="2024-01-01T00:01:00", name=None)
    client = BacktestClient(db, run_id)

    now = datetime(2024, 1, 1, 0, 0, 0)
    client.set_last_tick(
        Tick(symbol="AAA", price=123.0, volume=1.0, timestamp=now, provider="mock")
    )
    order = Order(
        symbol="AAA",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        limit_price=None,
    )
    await client.submit_order(order)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM backtest_trades")
    assert cursor.fetchone()[0] == 123.0
    conn.close()


@pytest.mark.asyncio
async def test_backtest_engine_fetches_provider_ticks_when_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "backtests.db"
    engine = BacktestEngine(db_path=str(db_path))

    fetched = [
        Tick(symbol="TEST", price=101.0, volume=5.0, timestamp=datetime(2024, 1, 1, 9, 30), provider="upstox")
    ]

    async def fake_fetch(**kwargs):
        assert kwargs.get("provider") == "upstox"
        return fetched

    monkeypatch.setattr("stockrhythm.backtest._fetch_ticks_from_backend", fake_fetch)

    class DummyStrategy:
        async def on_tick(self, tick: Tick):
            return None

        async def on_universe_init(self, symbols):
            return None

    run_id = await engine.run(
        DummyStrategy(),
        start_at="2024-01-01T09:30:00",
        end_at="2024-01-01T09:31:00",
        symbols=["TEST"],
        backend_url="http://localhost:8000",
        provider="upstox",
    )

    assert run_id == 1
    assert engine.db.count_ticks("2024-01-01T09:30:00", "2024-01-01T09:31:00", ["TEST"]) == 1


@pytest.mark.asyncio
async def test_backtest_client_submit_order_falls_back_to_zero(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    run_id = db.create_run(start_at="2024-01-01T00:00:00", end_at="2024-01-01T00:01:00", name=None)
    client = BacktestClient(db, run_id)

    order = Order(
        symbol="AAA",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        limit_price=None,
    )
    await client.submit_order(order)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM backtest_trades")
    assert cursor.fetchone()[0] == 0.0
    conn.close()


@pytest.mark.asyncio
async def test_backtest_engine_runs_strategy(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    now = datetime(2024, 1, 1, 12, 0, 0)
    db.insert_ticks(
        [
            Tick(symbol="AAA", price=1.0, volume=1.0, timestamp=now, provider="mock"),
            Tick(symbol="BBB", price=2.0, volume=2.0, timestamp=now, provider="mock"),
        ]
    )

    class StubStrategy:
        def __init__(self):
            self.ticks = []
            self.inits = []
            self.client = None
            self.paper_trade = False

        async def on_universe_init(self, symbols):
            self.inits.append(list(symbols))

        async def on_tick(self, tick):
            self.ticks.append(tick)

    engine = BacktestEngine(db_path=str(db_path))
    strategy = StubStrategy()
    run_id = await engine.run(
        strategy,
        start_at=now,
        end_at=now,
        symbols=["AAA", "BBB"],
        name="unit",
    )

    assert run_id == 1
    assert [tick.symbol for tick in strategy.ticks] == ["AAA", "BBB"]
    assert strategy.inits == [["AAA", "BBB"]]


@pytest.mark.asyncio
async def test_backtest_engine_marks_failed_on_error(tmp_path):
    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    now = datetime(2024, 1, 1, 12, 0, 0)
    db.insert_ticks(
        [Tick(symbol="AAA", price=1.0, volume=1.0, timestamp=now, provider="mock")]
    )

    class FailingStrategy:
        def __init__(self):
            self.client = None
            self.paper_trade = False

        async def on_universe_init(self, symbols):
            return

        async def on_tick(self, tick):
            raise RuntimeError("boom")

    engine = BacktestEngine(db_path=str(db_path))
    strategy = FailingStrategy()

    with pytest.raises(RuntimeError):
        await engine.run(
            strategy,
            start_at=now,
            end_at=now,
            symbols=None,
            name="fail",
        )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM backtest_runs WHERE id = 1")
    assert cursor.fetchone()[0] == "failed"
    conn.close()
