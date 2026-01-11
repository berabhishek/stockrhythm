import asyncio
import sys
import os

# Ensure the packages are in path
sys.path.append(os.path.abspath("packages/stockrhythm-sdk/src"))

from stockrhythm.strategy import Strategy
from stockrhythm.models import Tick, UniverseUpdate, FilterOp
from stockrhythm.filters import UniverseFilter

class UniverseTestBot(Strategy):
    async def on_universe_init(self, symbols):
        print(f"\n[Bot] Universe Initialized with {len(symbols)} symbols: {symbols}")

    async def on_symbol_added(self, symbol):
        print(f"[Bot] + Symbol Added: {symbol}")

    async def on_symbol_removed(self, symbol, reason=None):
        print(f"[Bot] - Symbol Removed: {symbol} (Reason: {reason})")

    async def on_tick(self, tick: Tick):
        print(f"[Bot] Tick: {tick.symbol} @ {tick.price}")

async def main():
    # Define a universe filter
    # This filter candidates are mocks, so we expect "NSE_CM|123", "NSE_CM|456" from the index resolver stub
    # The mock provider snapshot returns last_price=100.0 for everything.
    # So if we filter > 50, both should be selected.
    
    u_filter = (
        UniverseFilter.from_index("NIFTY50", refresh_seconds=5)
        .where("last_price", FilterOp.GT, 50)
        .build()
    )

    bot = UniverseTestBot(paper_trade=True)
    # Override client URL for test isolation
    bot.client.backend_url = "ws://localhost:8001"
    print("Starting bot with dynamic universe filter...")
    try:
        await bot.start(subscribe=u_filter)
    except KeyboardInterrupt:
        print("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nManual universe test interrupted by user.")
