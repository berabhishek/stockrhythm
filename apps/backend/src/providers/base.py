from abc import ABC, abstractmethod
from typing import AsyncIterable
from stockrhythm.models import Tick

class MarketDataProvider(ABC):
    @abstractmethod
    async def connect(self): 
        """Perform Authentication and WebSocket Handshake"""
        pass

    @abstractmethod
    async def subscribe(self, symbols: list[str]):
        """Tell the provider which ticks we want"""
        pass

    @abstractmethod
    async def stream(self) -> AsyncIterable[Tick]:
        """
        Yields normalized Tick objects.
        Crucial: Must convert Vendor-Specific JSON to StockRhythm 'Tick' model.
        """
        pass
