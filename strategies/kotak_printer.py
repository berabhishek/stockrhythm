import asyncio
import os
from stockrhythm import Strategy, Tick

# Ensure you have set the KOTAK_... environment variables before running the backend!

class KotakPrinter(Strategy):
    def __init__(self):
        super().__init__()

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
    # Reliance NSE Token: 2885
    asyncio.run(strategy.start(subscribe=["nse_cm|2885"]))
