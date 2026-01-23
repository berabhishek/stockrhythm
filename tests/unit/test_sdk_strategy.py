from datetime import datetime

import pytest

from stockrhythm.models import Tick, UniverseUpdate
from stockrhythm.strategy import Strategy


class RecordingStrategy(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticks = []
        self.added = []
        self.removed = []
        self.updates = []
        self.inits = []

    async def on_tick(self, tick: Tick):
        self.ticks.append(tick)

    async def on_symbol_added(self, symbol: str):
        self.added.append(symbol)

    async def on_symbol_removed(self, symbol: str, reason=None):
        self.removed.append((symbol, reason))

    async def on_universe_changed(self, update: UniverseUpdate):
        self.updates.append(update)

    async def on_universe_init(self, symbols):
        self.inits.append(list(symbols))


class FakeClient:
    def __init__(self, ticks):
        self.ticks = ticks
        self.connected = None
        self.subscribe = None
        self.on_update = None

    async def connect(self, paper_trade=True):
        self.connected = paper_trade

    async def stream_market_data(self, subscribe=None, on_universe_update=None):
        self.subscribe = subscribe
        self.on_update = on_universe_update
        for tick in self.ticks:
            yield tick

    async def submit_order(self, order):
        self.last_order = order


@pytest.mark.asyncio
async def test_strategy_start_routes_ticks(monkeypatch):
    monkeypatch.setattr("sys.argv", ["strategy.py"])
    strategy = RecordingStrategy()
    now = datetime(2024, 1, 1, 12, 0, 0)
    strategy.client = FakeClient(
        ticks=[
            Tick(symbol="AAA", price=1.0, volume=1.0, timestamp=now, provider="mock")
        ]
    )

    await strategy.start(subscribe=["AAA"])

    assert strategy.client.connected is True
    assert strategy.client.subscribe == ["AAA"]
    assert [tick.symbol for tick in strategy.ticks] == ["AAA"]


@pytest.mark.asyncio
async def test_strategy_universe_hooks(monkeypatch):
    monkeypatch.setattr("sys.argv", ["strategy.py"])
    strategy = RecordingStrategy()
    update = UniverseUpdate(
        added=["AAA"],
        removed=["BBB"],
        universe=["AAA", "CCC"],
        reason="static_subscribe",
        timestamp=1.0,
    )

    await strategy._handle_universe_update(update)

    assert strategy.added == ["AAA"]
    assert strategy.removed == [("BBB", "static_subscribe")]
    assert strategy.updates == [update]
    assert strategy.inits == [["AAA", "CCC"]]


def test_strategy_cli_overrides_paper_trade(monkeypatch):
    monkeypatch.setattr("sys.argv", ["strategy.py", "--live"])
    strategy = RecordingStrategy(paper_trade=True)
    assert strategy.paper_trade is False


def test_strategy_cli_sets_paper_trade(monkeypatch):
    monkeypatch.setattr("sys.argv", ["strategy.py", "--paper"])
    strategy = RecordingStrategy(paper_trade=False)
    assert strategy.paper_trade is True


@pytest.mark.asyncio
async def test_strategy_buy_submits_order(monkeypatch):
    monkeypatch.setattr("sys.argv", ["strategy.py"])
    strategy = RecordingStrategy()
    strategy.client = FakeClient(ticks=[])

    await strategy.buy("AAPL", 5)

    assert strategy.client.last_order.symbol == "AAPL"
    assert strategy.client.last_order.qty == 5


@pytest.mark.asyncio
async def test_strategy_base_hooks_are_noops(monkeypatch):
    class NoopStrategy(Strategy):
        async def on_tick(self, tick: Tick):
            await super().on_tick(tick)

    monkeypatch.setattr("sys.argv", ["strategy.py"])
    strategy = NoopStrategy()

    await strategy.on_universe_init(["AAA"])
    await strategy.on_symbol_added("AAA")
    await strategy.on_symbol_removed("BBB", reason="static_subscribe")
    await strategy.on_universe_changed(
        UniverseUpdate(added=[], removed=[], universe=[], reason=None, timestamp=None)
    )
    await strategy.on_tick(
        Tick(symbol="AAA", price=1.0, volume=1.0, timestamp=datetime(2024, 1, 1, 0, 0, 0), provider="mock")
    )


@pytest.mark.asyncio
async def test_strategy_backtest_invokes_engine(monkeypatch, tmp_path):
    class FakeBacktestEngine:
        def __init__(self, db_path):
            self.db_path = db_path
            self.called = False

        async def run(
            self,
            strategy,
            start_at,
            end_at,
            symbols=None,
            name=None,
            backend_url=None,
            interval=None,
            provider=None,
        ):
            self.called = True
            self.strategy = strategy
            self.start_at = start_at
            self.end_at = end_at
            self.symbols = symbols
            self.name = name
            self.backend_url = backend_url
            self.interval = interval
            self.provider = provider
            return 42

    monkeypatch.setattr("stockrhythm.backtest.BacktestEngine", FakeBacktestEngine)
    monkeypatch.setattr("sys.argv", ["strategy.py"])
    strategy = RecordingStrategy()

    run_id = await strategy.backtest(
        start_at="2024-01-01T00:00:00",
        end_at="2024-01-02T00:00:00",
        symbols=["AAA"],
        db_path=str(tmp_path / "backtests.db"),
        name="demo",
        provider="upstox",
    )

    assert run_id == 42
