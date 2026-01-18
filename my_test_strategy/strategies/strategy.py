import asyncio
from stockrhythm import Strategy, Tick
from stockrhythm.filters import UniverseFilter
from stockrhythm.models import FilterOp

class MyStrategy(Strategy):
    async def on_tick(self, tick: Tick):
        # Example signal: replace with your alpha.
        if tick.price < 100:
            await self.buy(tick.symbol, 1)

def get_filter():
    # Return a UniverseFilter object or a UniverseFilterSpec.
    return (
        UniverseFilter.from_watchlist(["RELIANCE"])
        .where("day_volume", FilterOp.GT, 1)
    )

def get_strategy(paper_trade: bool = True) -> Strategy:
    return MyStrategy(paper_trade=paper_trade)

def main():
    strategy = get_strategy()
    filter_spec = get_filter()
    if hasattr(filter_spec, "build"):
        filter_spec = filter_spec.build()
    asyncio.run(strategy.start(subscribe=filter_spec))

if __name__ == "__main__":
    main()
