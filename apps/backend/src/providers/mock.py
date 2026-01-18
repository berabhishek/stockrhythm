from .base import MarketDataProvider
from stockrhythm.models import Tick
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import random


class MockProvider(MarketDataProvider):
    def __init__(
        self,
        *,
        symbols: Optional[List[str]] = None,
        base_price: float = 100.0,
        max_deviation: float = 5.0,
        volatility: float = 0.5,
        mean_reversion: float = 0.1,
        interval_seconds: float = 0.5,
        seed: Optional[int] = None,
        volume_min: int = 100,
        volume_max: int = 1000,
    ):
        self.base_price = base_price
        self.max_deviation = max_deviation
        self.volatility = volatility
        self.mean_reversion = mean_reversion
        self.interval_seconds = interval_seconds
        self.volume_min = volume_min
        self.volume_max = volume_max
        self._rng = random.Random(seed)
        self._subscriptions = list(symbols or ["MOCK"])
        self._prices = {symbol: base_price for symbol in self._subscriptions}

    async def connect(self):
        print("MockProvider connected.")

    async def subscribe(self, symbols: list[str]):
        self._subscriptions = list(symbols)
        for symbol in symbols:
            self._prices.setdefault(symbol, self.base_price)
        print(f"MockProvider subscribed to {symbols}")

    async def stream(self):
        print("MockProvider starting stream...")
        while True:
            await asyncio.sleep(self.interval_seconds)
            for symbol in sorted(self._subscriptions):
                current = self._prices.get(symbol, self.base_price)
                step = self._rng.uniform(-self.volatility, self.volatility)
                reversion = (self.base_price - current) * self.mean_reversion
                next_price = current + step + reversion
                floor = self.base_price - self.max_deviation
                ceiling = self.base_price + self.max_deviation
                next_price = max(floor, min(ceiling, next_price))
                self._prices[symbol] = next_price
                yield Tick(
                    symbol=symbol,
                    price=round(next_price, 4),
                    volume=self._rng.randint(self.volume_min, self.volume_max),
                    timestamp=datetime.now(),
                    provider="mock",
                )

    async def snapshot(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        result = {}
        for sym in symbols:
            last_price = self._prices.get(sym, self.base_price)
            result[sym] = {
                "last_price": last_price,
                "day_volume": self.volume_max * 100,
            }
        return result
