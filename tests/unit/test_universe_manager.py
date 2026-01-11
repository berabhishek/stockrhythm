import asyncio

import pytest

from apps.backend.src.universe_manager import UniverseManager, UniverseResolver, _passes
from stockrhythm.models import FilterCondition, FilterOp, UniverseFilterSpec


class StubInstrumentMaster:
    def __init__(self, mapping):
        self.mapping = mapping
        self.loaded = False

    def load(self):
        self.loaded = True

    def resolve(self, symbol: str):
        return self.mapping.get(symbol)


class StubProvider:
    def __init__(self, snapshot_data=None, raise_snapshot=False):
        self.snapshot_data = snapshot_data or {}
        self.raise_snapshot = raise_snapshot
        self.subscriptions = []

    async def snapshot(self, symbols):
        if self.raise_snapshot:
            raise NotImplementedError
        return {sym: self.snapshot_data.get(sym, {}) for sym in symbols}

    async def set_subscriptions(self, symbols):
        self.subscriptions.append(list(symbols))


class SequenceResolver:
    def __init__(self, sequences):
        self.sequences = sequences
        self.index = 0

    async def resolve(self, spec, provider):
        if self.index >= len(self.sequences):
            return self.sequences[-1]
        value = self.sequences[self.index]
        self.index += 1
        return value


@pytest.mark.parametrize(
    "value,op,target,expected",
    [
        (5, FilterOp.EQ, 5, True),
        (5, FilterOp.NE, 4, True),
        (5, FilterOp.GT, 4, True),
        (5, FilterOp.GTE, 5, True),
        (5, FilterOp.LT, 6, True),
        (5, FilterOp.LTE, 5, True),
        (5, FilterOp.IN, [4, 5, 6], True),
        (5, FilterOp.NOT_IN, [1, 2, 3], True),
        (5, FilterOp.BETWEEN, (4, 6), True),
    ],
)
def test_passes_filter_ops(value, op, target, expected):
    assert _passes(value, op, target) is expected


@pytest.mark.asyncio
async def test_universe_resolver_watchlist_resolution():
    master = StubInstrumentMaster({"AAA": "nse_cm|111"})
    resolver = UniverseResolver(instrument_master=master)
    spec = UniverseFilterSpec(candidates={"type": "watchlist", "symbols": ["AAA", "BBB"]})

    resolved = await resolver.candidates(spec)

    assert resolved == ["nse_cm|111", "BBB"]
    assert master.loaded is True


@pytest.mark.asyncio
async def test_universe_resolver_dynamic_filters_and_max_symbols():
    master = StubInstrumentMaster({"AAA": "nse_cm|111", "BBB": "nse_cm|222", "CCC": "nse_cm|333"})
    resolver = UniverseResolver(instrument_master=master)
    spec = UniverseFilterSpec(
        candidates={"type": "watchlist", "symbols": ["AAA", "BBB", "CCC"]},
        max_symbols=2,
        conditions=[FilterCondition(field="last_price", op=FilterOp.GT, value=100)],
    )

    provider = StubProvider(
        snapshot_data={
            "nse_cm|111": {"last_price": 90},
            "nse_cm|222": {"last_price": 110},
            "nse_cm|333": {"last_price": 120},
        }
    )

    resolved = await resolver.resolve(spec, provider)

    assert resolved == ["nse_cm|222", "nse_cm|333"]


@pytest.mark.asyncio
async def test_universe_resolver_snapshot_not_supported_returns_base():
    master = StubInstrumentMaster({"AAA": "nse_cm|111", "BBB": "nse_cm|222"})
    resolver = UniverseResolver(instrument_master=master)
    spec = UniverseFilterSpec(
        candidates={"type": "watchlist", "symbols": ["AAA", "BBB"]},
        max_symbols=1,
        conditions=[FilterCondition(field="last_price", op=FilterOp.GT, value=100)],
    )

    provider = StubProvider(raise_snapshot=True)
    resolved = await resolver.resolve(spec, provider)

    assert resolved == ["nse_cm|111"]


@pytest.mark.asyncio
async def test_universe_manager_emits_updates_and_subscriptions():
    spec = UniverseFilterSpec(candidates={"type": "watchlist", "symbols": ["AAA", "BBB"]}, refresh_seconds=0)
    provider = StubProvider()
    resolver = SequenceResolver([["AAA", "BBB"], ["BBB"]])
    messages = []
    update_event = asyncio.Event()

    async def send_json(payload):
        messages.append(payload)
        if len(messages) >= 2:
            update_event.set()

    manager = UniverseManager(spec=spec, provider=provider, resolver=resolver, send_json=send_json)
    task = asyncio.create_task(manager.run())

    await asyncio.wait_for(update_event.wait(), timeout=1.0)
    await manager.stop()
    await asyncio.wait_for(task, timeout=1.0)

    assert provider.subscriptions == [["AAA", "BBB"], ["BBB"]]
    assert messages[0]["action"] == "universe"
    assert messages[0]["data"]["added"] == ["AAA", "BBB"]
    assert messages[0]["data"]["removed"] == []
    assert messages[1]["data"]["added"] == []
    assert messages[1]["data"]["removed"] == ["AAA"]
