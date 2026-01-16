from abc import ABC, abstractmethod
from typing import AsyncIterable, List, Dict, Any
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

    # ---- NEW: full replace subscription (default calls subscribe) ----
    async def set_subscriptions(self, symbols: List[str]):
        await self.subscribe(symbols)

    # ---- OPTIONAL: quote snapshot for filter evaluation ----
    async def snapshot(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Return dict keyed by symbol with fields like:
          { "last_price": 123.4, "day_volume": 100000, ... }
        Not required for all providers, but needed for dynamic filters.
        """
        raise NotImplementedError

    async def historical(
        self,
        symbols: List[str],
        start_at: str,
        end_at: str,
        interval: str | None = None,
    ) -> List[Tick]:
        """
        Return historical ticks between start_at and end_at for the given symbols.
        Provider implementations should normalize vendor responses into Tick objects.
        """
        raise NotImplementedError
