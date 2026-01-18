import pytest

from apps.backend.src.providers.upstox import UpstoxProvider


class DummyResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = "ok"

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, response: DummyResponse):
        self.response = response
        self.last_url = None
        self.last_headers = None

    async def get(self, url, headers=None, params=None):
        self.last_url = url
        self.last_headers = headers
        return self.response


@pytest.mark.asyncio
async def test_upstox_historical_parses_candles():
    payload = {
        "data": {
            "candles": [
                ["2025-01-01T09:15:00+05:30", 100.0, 105.0, 99.5, 102.0, 1200],
                ["2025-01-01T09:16:00+05:30", 102.0, 106.0, 101.0, 104.5, 900],
            ]
        }
    }
    response = DummyResponse(200, payload)
    client = DummyClient(response)

    provider = UpstoxProvider(api_key="key", api_secret="secret", token="token")
    provider.client = client

    ticks = await provider.historical(
        symbols=["NSE_EQ|INE848E01016"],
        start_at="2025-01-01",
        end_at="2025-01-02",
        interval="minutes/1",
    )

    assert len(ticks) == 2
    assert ticks[0].price == 102.0
    assert ticks[0].volume == 1200.0
    assert ticks[0].provider == "upstox"
    assert "NSE_EQ%7CINE848E01016/minutes/1/2025-01-02/2025-01-01" in client.last_url
