import asyncio
from abc import ABC, abstractmethod
from .models import Tick, Order, OrderSide, OrderType
from .client import EngineClient

class Strategy(ABC):
    def __init__(self):
        self.client = EngineClient()
        self.context = {} 

    async def start(self, subscribe: list[str] = None):
        """Internal Event Loop: Connects to Backend and routes ticks"""
        await self.client.connect()
        # The client.stream() method yields Ticks from the Backend's Data Orchestrator
        async for tick in self.client.stream_market_data(subscribe=subscribe):
            await self.on_tick(tick)

    @abstractmethod
    async def on_tick(self, tick: Tick):
        """Developer implements this logic"""
        pass

    async def buy(self, symbol: str, qty: int):
        # Wraps logic into an Order object and sends to Backend via Client
        order = Order(symbol=symbol, qty=qty, side=OrderSide.BUY, type=OrderType.MARKET)
        await self.client.submit_order(order)
