import asyncio
import sys
import argparse
from abc import ABC, abstractmethod
from .models import Tick, Order, OrderSide, OrderType
from .client import EngineClient

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

    async def start(self, subscribe: list[str] = None):
        """Internal Event Loop: Connects to Backend and routes ticks"""
        # We pass the paper_trade preference to the client
        await self.client.connect(paper_trade=self.paper_trade)
        # The client.stream() method yields Ticks from the Backend's Data Orchestrator
        async for tick in self.client.stream_market_data(subscribe=subscribe):
            await self.on_tick(tick)

    @abstractmethod
    async def on_tick(self, tick: Tick):
        """Developer implements this logic"""
        pass

    async def buy(self, symbol: str, qty: int):
        # Wraps logic into an Order object and sends to Backend via Client
        order = Order(symbol=symbol, qty=qty, side=OrderSide.BUY, type=OrderType.MARKET)
        await self.client.submit_order(order)
