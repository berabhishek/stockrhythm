from .base import MarketDataProvider
from stockrhythm.models import Tick
from datetime import datetime
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
            await asyncio.sleep(1)
            # Yield a dummy tick
            yield Tick(
                symbol="TEST",
                price=100.0,
                volume=10,
                timestamp=datetime.now(),
                provider="mock"
            )
