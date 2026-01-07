import asyncio
import websockets
import json
from typing import AsyncIterable, List
from .models import Tick, Order

class EngineClient:
    """
    Handles network communication with the StockRhythm Backend.
    """
    def __init__(self, backend_url: str = "ws://localhost:8000"):
        self.backend_url = backend_url
        self._connected = False
        self.ws = None
        self.paper_trade = True

    async def connect(self, paper_trade: bool = True):
        """
        Connect to the backend engine.
        """
        self.paper_trade = paper_trade
        self._connected = True
        print(f"Client Initialized (Paper Trading: {self.paper_trade})")

    async def stream_market_data(self, subscribe: list[str] = None) -> AsyncIterable[Tick]:
        """
        Yields Ticks from the Backend.
        """
        if not self._connected:
            raise ConnectionError("Client not initialized")
        
        async with websockets.connect(self.backend_url) as websocket:
            self.ws = websocket
            print("Connected to Backend WebSocket.")
            
            # Send initial configuration handshake
            handshake = {
                "action": "configure",
                "paper_trade": self.paper_trade,
                "subscribe": subscribe
            }
            await websocket.send(json.dumps(handshake))
            
            try:
                async for message in websocket:
                    data = json.loads(message)
                    # Convert JSON to Tick
                    yield Tick(**data)
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by Backend")

    async def submit_order(self, order: Order):
        """
        Sends an order to the Backend.
        """
        if not self.ws:
            raise ConnectionError("WebSocket connection not established")
        
        # Standardize message
        payload = {
            "action": "order",
            "data": order.model_dump(mode='json')
        }
        await self.ws.send(json.dumps(payload))
        print(f"Order Submitted: {order.symbol} {order.side} {order.qty}")
