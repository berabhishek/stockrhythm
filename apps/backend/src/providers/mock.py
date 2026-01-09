from .base import MarketDataProvider
from stockrhythm.models import Tick
from datetime import datetime
from typing import List, Dict, Any
import asyncio
import csv
from pathlib import Path

class MockProvider(MarketDataProvider):
    def __init__(self, csv_path: str = "data/history.csv"):
        self.csv_path = csv_path

    async def connect(self):
        print("MockProvider connected.")
        
    async def subscribe(self, symbols: list[str]):
        print(f"MockProvider subscribed to {symbols}")

    async def stream(self):
        # Simulate streaming from CSV
        # In a real impl, we would read the CSV line by line with delays
        print("MockProvider starting stream...")
        while True:
            await asyncio.sleep(0.1)
            # Yield a dummy tick
            yield Tick(
                symbol="TEST",
                price=99.0,
                volume=10,
                timestamp=datetime.now(),
                provider="mock"
            )

    async def snapshot(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        # Dummy snapshot for testing universe filters
        result = {}
        for sym in symbols:
            # Check if it matches our test cases
            if sym == "nse_cm|2885" or sym == "nse_cm|99999" or "TEST" in sym:
                result[sym] = {
                    "last_price": 100.0,
                    "day_volume": 500000,
                }
            else:
                # Default for others
                result[sym] = {
                    "last_price": 100.0,
                    "day_volume": 500000,
                }
        return result
