import asyncio
import websockets
import json
from typing import AsyncIterable, List, Optional, Union, Callable
from .models import Tick, Order, UniverseFilterSpec, UniverseUpdate

SubscribeInput = Union[List[str], UniverseFilterSpec]

def _model_dump(obj):
    # pydantic v1/v2 compatibility
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()

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

    async def stream_market_data(
        self,
        subscribe: SubscribeInput = None,
        on_universe_update: Optional[Callable[[UniverseUpdate], "asyncio.Future"]] = None,
    ) -> AsyncIterable[Tick]:
        """
        Yields Ticks from the Backend.
        """
        if not self._connected:
            raise ConnectionError("Client not initialized")
        
        # Build configure payload
        subscribe_symbols = None
        filter_spec = None

        if isinstance(subscribe, list):
            subscribe_symbols = subscribe
        elif subscribe is not None:
            # Assume it is UniverseFilterSpec
            filter_spec = _model_dump(subscribe)
        
        handshake = {
            "action": "configure",
            "data": {
                "paper_trade": self.paper_trade,
                "protocol_version": 2,
                "subscribe": subscribe_symbols,
                "filter": filter_spec,
            }
        }

        # Backward compatibility for existing backend (if not updated yet, though we are updating both)
        # But let's stick to the new protocol structure as defined in the plan.
        # The prompt used "data" wrapper. The existing code sent flat keys. 
        # I will use the new structure but also keep top-level keys if needed for safety or stick to the plan.
        # The plan says: { action: "configure", data: { paper_trade, subscribe_symbols? , filter_spec? , protocol_version } }
        
        async with websockets.connect(self.backend_url) as websocket:
            self.ws = websocket
            print("Connected to Backend WebSocket.")
            
            await websocket.send(json.dumps(handshake))
            
            try:
                async for raw_message in websocket:
                    msg = json.loads(raw_message)
                    
                    # Backward compatibility: if backend sends bare ticks or legacy format
                    if "action" not in msg:
                        # Assumption: it's a legacy tick
                        yield Tick(**msg)
                        continue

                    action = msg.get("action")
                    data = msg.get("data", {})

                    if action == "tick":
                        yield Tick(**data)

                    elif action == "universe":
                        if on_universe_update:
                            update = UniverseUpdate(**data)
                            await on_universe_update(update)

                    elif action == "error":
                        # Decide your behavior: raise or log
                        print(f"Backend Error: {data.get('message', 'Unknown backend error')}")

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
