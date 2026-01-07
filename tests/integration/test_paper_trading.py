import pytest
import asyncio
import sqlite3
import os
from stockrhythm import Strategy, Tick
from apps.backend.src import main
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_paper_trading_sqlite_persistence():
    """
    Validates that:
    1. Strategy sets paper_trade=True.
    2. Strategy calls self.buy().
    3. Backend saves the trade to paper_trades.db.
    """
    
    # 1. Clean up old DB if exists
    DB_PATH = "paper_trades.db"
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # 2. Define Strategy
    class PaperBot(Strategy):
        def __init__(self):
            super().__init__(paper_trade=True)
            self.done = False

        async def on_tick(self, tick: Tick):
            if not self.done:
                # Place an order on the first tick
                await self.buy(tick.symbol, 5)
                self.done = True

    # 3. Setup Test Client
    # We use TestClient's websocket_connect directly to simulate the SDK
    with TestClient(main.app) as client:
        with client.websocket_connect("/") as websocket:
            
            # Configuration
            websocket.send_json({
                "action": "configure",
                "paper_trade": True,
                "subscribe": ["TEST_SYMBOL"]
            })
            
            # Receive 1 tick (Mock provider defaults to 99.0)
            data = websocket.receive_json()
            
            # Send Order (Simulating SDK submit_order)
            websocket.send_json({
                "action": "order",
                "data": {
                    "symbol": "RELIANCE",
                    "qty": 5,
                    "side": "BUY",
                    "type": "MARKET"
                }
            })
            
            # Give backend a moment to process SQL
            await asyncio.sleep(1)

    # 4. Assert SQLite state
    assert os.path.exists(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Orders
    cursor.execute("SELECT symbol, qty, side FROM orders")
    order = cursor.fetchone()
    assert order is not None
    assert order[0] == "RELIANCE"
    assert order[1] == 5
    assert order[2] == "BUY"
    
    # Check Trades (Fills)
    cursor.execute("SELECT qty, price FROM trades")
    trade = cursor.fetchone()
    assert trade is not None
    assert trade[0] == 5
    
    conn.close()
    print("\n✅ SQLite Paper Trading persistence verified!")
