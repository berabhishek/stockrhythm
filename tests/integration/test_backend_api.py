import pytest
from fastapi.testclient import TestClient
from apps.backend.src.main import app

class TestBackendIntegration:
    client = TestClient(app)

    def test_health_check(self):
        """
        Integration: Ensure Backend API is reachable.
        """
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_websocket_connection(self):
        """
        Integration: Connect to the main WebSocket and receive at least one Tick.
        """
        with self.client.websocket_connect("/") as websocket:
            # The MockProvider sends a tick immediately after simulated delay
            # We wait for the first message
            data = websocket.receive_json()
            
            assert "symbol" in data
            assert "price" in data
            assert data["provider"] == "mock"
