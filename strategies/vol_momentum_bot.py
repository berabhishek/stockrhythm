import asyncio
import numpy as np
from collections import deque
from stockrhythm import Strategy, Tick

class VolatilityMomentumBot(Strategy):
    """
    Advanced Strategy: Volatility-Targeted Momentum.
    
    Target: Sharpe Ratio 1.5
    Constraint: Max Drawdown < 10%
    """
    def __init__(self):
        super().__init__(paper_trade=True)
        
        # Configuration
        self.window_size = 20
        self.prices = deque(maxlen=self.window_size)
        
        # Risk Management State
        self.max_drawdown_limit = 0.10  # 10%
        self.peak_equity = 100000.0    
        self.current_equity = 100000.0
        self.position = 0              
        self.entry_price = 0.0
        
        print(f"Bot Initialized. Target MDD: {self.max_drawdown_limit*100}%")

    async def on_tick(self, tick: Tick):
        print(f"[Data] {tick.symbol} Price: {tick.price} | Time: {tick.timestamp}")
        self.prices.append(tick.price)
        
        if len(self.prices) < self.window_size:
            return

        # 1. Calculate Indicators
        prices_array = np.array(self.prices)
        momentum = (prices_array[-1] - prices_array[0]) / prices_array[0]
        volatility = np.std(prices_array) / np.mean(prices_array)
        
        # 2. Update PnL and MDD Check
        if self.position != 0:
            unrealized_pnl = self.position * (tick.price - self.entry_price)
            self.current_equity = self.peak_equity + unrealized_pnl
            
            drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
            if drawdown > self.max_drawdown_limit:
                print(f"⚠️ DRAWDOWN ALERT: {drawdown*100:.2f}%. Executing Panic Exit.")
                await self.emergency_exit(tick.symbol)
                return

        # 3. Strategy Logic
        if momentum > 0.005 and volatility < 0.02 and self.position == 0:
            qty = int(100 / (volatility * 100)) 
            qty = min(qty, 500) 
            
            print(f"📈 Signal: BUY {tick.symbol} | Qty: {qty} | Mom: {momentum:.4f} | Vol: {volatility:.4f}")
            await self.buy(tick.symbol, qty)
            self.position = qty
            self.entry_price = tick.price

        elif momentum < -0.002 and self.position > 0:
            print(f"📉 Signal: SELL {tick.symbol} | Exit: {tick.price}")
            await self.sell(tick.symbol, self.position)
            
            realized_pnl = self.position * (tick.price - self.entry_price)
            self.peak_equity += realized_pnl
            self.position = 0

    async def emergency_exit(self, symbol: str):
        if self.position > 0:
            await self.sell(symbol, self.position)
        print("🛑 STRATEGY HALTED: Risk limits reached.")
        self.position = 0

    async def sell(self, symbol: str, qty: int):
        from stockrhythm.models import Order, OrderSide, OrderType
        order = Order(symbol=symbol, qty=qty, side=OrderSide.SELL, type=OrderType.MARKET)
        await self.client.submit_order(order)

if __name__ == "__main__":
    bot = VolatilityMomentumBot()
    # Using numeric identifier for the specific instrument
    asyncio.run(bot.start(subscribe=["nse_cm|2885"]))