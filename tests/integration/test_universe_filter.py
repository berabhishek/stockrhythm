import importlib

import pytest
import dotenv
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("STOCKRHYTHM_PROVIDER", "mock")
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
    from apps.backend.src import main
    importlib.reload(main)
    return TestClient(main.app)


def test_websocket_universe_filter_update(client):
    """
    Integration: Configure a filter-based universe and verify a universe update arrives.
    """
    with client.websocket_connect("/") as websocket:
        websocket.send_json(
            {
                "action": "configure",
                "data": {
                    "paper_trade": True,
                    "protocol_version": 2,
                    "filter": {
                        "candidates": {"type": "watchlist", "symbols": ["TESTA", "TESTB"]},
                        "conditions": [{"field": "last_price", "op": "gt", "value": 1}],
                        "refresh_seconds": 0,
                        "max_symbols": 50,
                        "grace_seconds": 0,
                        "sort": [],
                    },
                },
            }
        )

        attempts = 0
        max_attempts = 20
        while attempts < max_attempts:
            attempts += 1
            message = websocket.receive_json()
            if message.get("action") == "universe":
                data = message.get("data", {})
                assert set(data.get("added", [])) == {"TESTA", "TESTB"}
                assert set(data.get("universe", [])) == {"TESTA", "TESTB"}
                return

        pytest.fail("Did not receive universe update for filter within message limit.")
