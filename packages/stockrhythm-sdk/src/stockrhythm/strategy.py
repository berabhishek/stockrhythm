import asyncio
import sys
import argparse
from abc import ABC, abstractmethod
from typing import List, Union, Optional
from .models import Tick, Order, OrderSide, OrderType, UniverseFilterSpec, UniverseUpdate
from .client import EngineClient

SubscribeInput = Union[List[str], UniverseFilterSpec]

class Strategy(ABC):
    def __init__(self, paper_trade: bool = True):
        """
        Initialize the strategy. CLI arguments --live/--paper take precedence
        over the constructor's paper_trade argument.
        """
        # 1. Parse CLI arguments using argparse for robustness
        # add_help=False ensures we don't interfere if the user handles -h/--help
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--live', action='store_true', help='Run in live trading mode')
        parser.add_argument('--paper', action='store_true', help='Run in paper trading mode')
        
        # parse_known_args only consumes the flags we defined, leaving others untouched
        args, _ = parser.parse_known_args()

        # 2. Determine mode with priority: CLI > Constructor > Default
        if args.live:
            self.paper_trade = False
        elif args.paper:
            self.paper_trade = True
        else:
            # Fallback to constructor argument
            self.paper_trade = paper_trade

        self.client = EngineClient()
        self.context = {} 
        
        mode_str = "PAPER TRADING" if self.paper_trade else "LIVE TRADING"
        print(f"Strategy Initialized in {mode_str} mode.")

    # ---- NEW HOOKS (default no-op) ----
    async def on_universe_init(self, symbols: List[str]):
        return

    async def on_symbol_added(self, symbol: str):
        return

    async def on_symbol_removed(self, symbol: str, reason: Optional[str] = None):
        return

    async def on_universe_changed(self, update: UniverseUpdate):
        return

    async def _handle_universe_update(self, update: UniverseUpdate):
        # call granular hooks first
        for s in update.added:
            await self.on_symbol_added(s)
        for s in update.removed:
            await self.on_symbol_removed(s, update.reason)

        # then the aggregate hook
        await self.on_universe_changed(update)

        # init hook: if this is the first message containing a full universe snapshot
        if update.universe and update.reason == "static_subscribe" or update.reason == "filter_refresh":
            # For simplicity, we might just call it if universe is present.
            # But usually init is only once. The caller logic (universe manager) might need to flag it.
            # Or we can just let on_universe_changed handle it. 
            # The prompt suggested: "if update.universe: await self.on_universe_init(update.universe)"
            pass 
        
        # Wait, the prompt code says:
        # if update.universe:
        #    await self.on_universe_init(update.universe)
        # However, that would call init on every refresh if the full universe is sent. 
        # But let's follow the prompt's suggested implementation for now.
        if update.universe:
             await self.on_universe_init(update.universe)

    async def start(self, subscribe: SubscribeInput = None):
        """Internal Event Loop: Connects to Backend and routes ticks"""
        # We pass the paper_trade preference to the client
        await self.client.connect(paper_trade=self.paper_trade)
        # The client.stream() method yields Ticks from the Backend's Data Orchestrator
        async for tick in self.client.stream_market_data(
            subscribe=subscribe,
            on_universe_update=self._handle_universe_update
        ):
            await self.on_tick(tick)

    @abstractmethod
    async def on_tick(self, tick: Tick):
        """Developer implements this logic"""
        pass

    async def buy(self, symbol: str, qty: int):
        # Wraps logic into an Order object and sends to Backend via Client
        order = Order(symbol=symbol, qty=qty, side=OrderSide.BUY, type=OrderType.MARKET)
        await self.client.submit_order(order)

    async def backtest(
        self,
        start_at,
        end_at,
        *,
        symbols: Optional[List[str]] = None,
        db_path: str = "backtests.db",
        name: Optional[str] = None,
        backend_url: Optional[str] = None,
        interval: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> int:
        from .backtest import BacktestEngine

        engine = BacktestEngine(db_path=db_path)
        return await engine.run(
            self,
            start_at=start_at,
            end_at=end_at,
            symbols=symbols,
            name=name,
            backend_url=backend_url,
            interval=interval,
            provider=provider,
        )
