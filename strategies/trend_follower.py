import asyncio
from stockrhythm import Strategy, Tick

class TrendFollower(Strategy):
    async def on_tick(self, tick: Tick):
        print(f"[Strategy] Received Tick: {tick.symbol} @ {tick.price}")
        
        # Simple Logic: Buy if price is low
        if tick.price < 100:
            print(f"[Strategy] Price {tick.price} < 100. BUYING!")
            await self.buy(tick.symbol, 10)

if __name__ == "__main__":
    # Boilerplate to run the strategy
    strategy = TrendFollower()
    # Explicitly subscribe to a symbol to receive ticks from the provider
    asyncio.run(strategy.start(subscribe=["nse_cm|2885"]))
