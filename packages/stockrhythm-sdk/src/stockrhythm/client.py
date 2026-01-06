import asyncio
from typing import AsyncIterable
from .models import Tick, Order

class EngineClient:
    """
    Handles network communication with the StockRhythm Backend.
    """
    def __init__(self, backend_url: str = "ws://localhost:8000"):
        self.backend_url = backend_url
        self._connected = False

    async def connect(self):
        """
        Connect to the backend engine (Simulated for now).
        """
        # In a real impl, this would establish a websocket connection
        self._connected = True
        print(f"Connected to Engine at {self.backend_url}")

    async def stream_market_data(self) -> AsyncIterable[Tick]:
        """
        Yields Ticks from the Backend.
        """
        if not self._connected:
            raise ConnectionError("Client not connected")
        
        # Placeholder: Yields nothing or could yield mock data if needed for simple tests
        # The actual implementation would read from the websocket
        while False:
             yield Tick() # Unreachable, just for type hint logic if tools analyze it

    async def submit_order(self, order: Order):
        """
        Sends an order to the Backend.
        """
        if not self._connected:
            raise ConnectionError("Client not connected")
        print(f"Sending Order: {order}")
