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

    async def connect(self):
        """
        Connect to the backend engine.
        """
        try:
            # We delay actual connection to stream_market_data or do it here
            # For simplicity, we just mark as ready, but connection happens in stream loop
            # or we establish it now. Let's establish it now.
            # self.ws = await websockets.connect(self.backend_url) 
            # Re-design: Strategy.start() calls connect() then stream().
            pass 
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise
        self._connected = True
        print(f"Client Initialized for {self.backend_url}")

    async def stream_market_data(self, subscribe: list[str] = None) -> AsyncIterable[Tick]:
        """
        Yields Ticks from the Backend.
        """
        if not self._connected:
            raise ConnectionError("Client not initialized")
        
        async with websockets.connect(self.backend_url) as websocket:
            self.ws = websocket
            print("Connected to Backend WebSocket.")
            
            if subscribe:
                print(f"Subscribing to: {subscribe}")
                # Send subscription message (Backend needs to handle this!)
                await websocket.send(json.dumps({"action": "subscribe", "symbols": subscribe}))
            
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
        if not self._connected:
            raise ConnectionError("Client not connected")
        print(f"Sending Order: {order}")
