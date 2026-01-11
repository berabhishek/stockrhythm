import asyncio
import sys
import os

# Ensure the packages are in path
sys.path.append(os.path.abspath("packages/stockrhythm-sdk/src"))

from stockrhythm.strategy import Strategy
from stockrhythm.models import Tick, UniverseUpdate, FilterOp
from stockrhythm.filters import UniverseFilter

class ResolveTestBot(Strategy):
    async def on_universe_init(self, symbols):
        print(f"\n[Bot] Universe Initialized with {len(symbols)} symbols: {symbols}")
        # Expectation: "nse_cm|2885" (for RELIANCE) if mapping works
        
    async def on_tick(self, tick: Tick):
        print(f"[Bot] Tick: {tick.symbol} @ {tick.price}")

async def main():
    # Strategy User says "RELIANCE"
    # Backend has instruments.csv mapping RELIANCE -> 2885
    u_filter = (
        UniverseFilter.from_watchlist(["RELIANCE", "TEST"])
        .where("last_price", FilterOp.GT, 50)
        .build()
    )

    bot = ResolveTestBot(paper_trade=True)
    # Override client URL for test isolation
    bot.client.backend_url = "ws://localhost:8001"
    
    print("Starting bot to test Symbol -> Token resolution...")
    try:
        await bot.start(subscribe=u_filter)
    except KeyboardInterrupt:
        print("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nManual token resolve test interrupted by user.")
