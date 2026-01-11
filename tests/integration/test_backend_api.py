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

class TestBackendIntegration:
    def test_health_check(self, client):
        """
        Integration: Ensure Backend API is reachable.
        """
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_websocket_connection(self, client):
        """
        Integration: Connect to the main WebSocket and receive at least one Tick.
        """
        with client.websocket_connect("/") as websocket:
            # Protocol v2 requires a configure message to start streaming
            websocket.send_json(
                {
                    "action": "configure",
                    "data": {
                        "paper_trade": True,
                        "subscribe": ["TEST"],
                        "protocol_version": 2,
                    },
                }
            )

            # The MockProvider sends a tick immediately after simulated delay
            # We wait for the first message
            # Backend might send universe init first, then tick
            # We loop until we get a tick, but limit attempts to avoid infinite loop
            attempts = 0
            max_attempts = 10
            while attempts < max_attempts:
                attempts += 1
                data = websocket.receive_json()
                action = data.get("action")
                payload = data.get("data", {})

                if action == "tick":
                    assert "symbol" in payload
                    assert "price" in payload
                    assert payload["provider"] == "mock"
                    return  # Success

            pytest.fail(f"Did not receive 'tick' action within {max_attempts} messages.")
