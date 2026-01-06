import asyncio
import os
from stockrhythm import Strategy, Tick

# Ensure you have set the KOTAK_... environment variables before running the backend!

class KotakPrinter(Strategy):
    async def on_tick(self, tick: Tick):
        # Simply print the received tick
        print(f"[{tick.timestamp}] {tick.symbol} CMP: {tick.price}")

if __name__ == "__main__":
    # Note: This strategy connects to the Backend.
    # The Backend must be running with 'active_provider: kotak'
    # and valid credentials in the environment.
    
    strategy = KotakPrinter()
    print("Starting Kotak Printer Strategy...")
    print("Make sure your Backend is running with Kotak Provider enabled!")
    asyncio.run(strategy.start(subscribe=["nse_cm|RELIANCE-EQ"]))
