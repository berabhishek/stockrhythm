import json
from datetime import datetime

import pytest

import websockets
from websockets.frames import Close

from stockrhythm.client import EngineClient, _model_dump
from stockrhythm.models import Order, OrderSide, OrderType, UniverseFilterSpec


class FakeWebSocket:
    def __init__(self, messages=None):
        self._messages = list(messages or [])
        self.sent = []

    async def send(self, message):
        self.sent.append(message)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)


class FakeConnect:
    def __init__(self, websocket):
        self.websocket = websocket

    async def __aenter__(self):
        return self.websocket

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_stream_market_data_builds_handshake_and_yields_ticks(monkeypatch):
    messages = [
        json.dumps(
            {
                "symbol": "AAA",
                "price": 1.0,
                "volume": 2.0,
                "timestamp": "2024-01-01T00:00:00",
                "provider": "mock",
            }
        ),
        json.dumps(
            {
                "action": "tick",
                "data": {
                    "symbol": "BBB",
                    "price": 2.0,
                    "volume": 3.0,
                    "timestamp": "2024-01-01T00:01:00",
                    "provider": "mock",
                },
            }
        ),
        json.dumps(
            {
                "action": "universe",
                "data": {
                    "added": ["AAA"],
                    "removed": [],
                    "universe": ["AAA"],
                    "reason": "static_subscribe",
                    "timestamp": 1.0,
                },
            }
        ),
        json.dumps({"action": "error", "data": {"message": "oops"}}),
    ]
    fake_ws = FakeWebSocket(messages=messages)

    def fake_connect(_url):
        return FakeConnect(fake_ws)

    monkeypatch.setattr("stockrhythm.client.websockets.connect", fake_connect)

    client = EngineClient()
    await client.connect(paper_trade=False)

    updates = []

    async def on_update(update):
        updates.append(update)

    ticks = []
    async for tick in client.stream_market_data(
        subscribe=["AAA", "BBB"],
        on_universe_update=on_update,
    ):
        ticks.append(tick)

    assert [tick.symbol for tick in ticks] == ["AAA", "BBB"]
    assert updates[0].universe == ["AAA"]

    sent = json.loads(fake_ws.sent[0])
    assert sent["action"] == "configure"
    assert sent["data"]["paper_trade"] is False
    assert sent["data"]["subscribe"] == ["AAA", "BBB"]
    assert sent["data"]["filter"] is None


@pytest.mark.asyncio
async def test_stream_market_data_requires_connect():
    client = EngineClient()
    with pytest.raises(ConnectionError):
        await anext(client.stream_market_data())


@pytest.mark.asyncio
async def test_stream_market_data_with_filter_spec(monkeypatch):
    fake_ws = FakeWebSocket(messages=[])

    def fake_connect(_url):
        return FakeConnect(fake_ws)

    monkeypatch.setattr("stockrhythm.client.websockets.connect", fake_connect)

    client = EngineClient()
    await client.connect()

    spec = UniverseFilterSpec(candidates={"type": "index", "name": "NIFTY50"})
    async for _ in client.stream_market_data(subscribe=spec):
        pass

    sent = json.loads(fake_ws.sent[0])
    assert sent["data"]["subscribe"] is None
    assert sent["data"]["filter"]["candidates"]["name"] == "NIFTY50"


@pytest.mark.asyncio
async def test_stream_market_data_handles_disconnect(monkeypatch):
    class ClosingWebSocket(FakeWebSocket):
        async def __anext__(self):
            raise websockets.exceptions.ConnectionClosed(
                Close(1000, "closed"),
                Close(1000, "closed"),
                True,
            )

    fake_ws = ClosingWebSocket(messages=[])

    def fake_connect(_url):
        return FakeConnect(fake_ws)

    monkeypatch.setattr("stockrhythm.client.websockets.connect", fake_connect)

    client = EngineClient()
    await client.connect()

    async for _ in client.stream_market_data():
        pass


@pytest.mark.asyncio
async def test_submit_order_sends_payload():
    client = EngineClient()
    fake_ws = FakeWebSocket()
    client.ws = fake_ws

    order = Order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        limit_price=None,
    )
    await client.submit_order(order)

    payload = json.loads(fake_ws.sent[0])
    assert payload["action"] == "order"
    assert payload["data"]["symbol"] == "AAPL"


def test_model_dump_fallback_dict():
    class Dummy:
        def dict(self):
            return {"ok": True}

    assert _model_dump(Dummy()) == {"ok": True}


@pytest.mark.asyncio
async def test_submit_order_requires_websocket():
    client = EngineClient()
    order = Order(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        limit_price=None,
    )
    with pytest.raises(ConnectionError):
        await client.submit_order(order)
