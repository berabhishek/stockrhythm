import sqlite3
from datetime import datetime
from stockrhythm.models import Order
import os

DB_PATH = "paper_trades.db"

class PaperEngine:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Creates the SQLite database and tables if they don't exist."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                qty INTEGER,
                side TEXT,
                type TEXT,
                limit_price REAL,
                status TEXT,
                timestamp DATETIME
            )
        """)
        
        # Trades Table (Fills)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                symbol TEXT,
                qty INTEGER,
                price REAL,
                timestamp DATETIME,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
        """)
        conn.commit()
        conn.close()

    async def execute_order(self, order: Order) -> dict:
        """
        Simulates an order execution and saves to SQLite.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Insert Order
        cursor.execute(
            "INSERT INTO orders (symbol, qty, side, type, limit_price, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (order.symbol, order.qty, order.side, order.type, order.limit_price, "FILLED", datetime.now())
        )
        order_id = cursor.lastrowid
        
        # 2. Simulate immediate Fill (Paper trading simplification)
        # Note: In a real simulation, we would wait for a tick price.
        # Here we just record it.
        cursor.execute(
            "INSERT INTO trades (order_id, symbol, qty, price, timestamp) VALUES (?, ?, ?, ?, ?)",
            (order_id, order.symbol, order.qty, order.limit_price or 0.0, datetime.now())
        )
        
        conn.commit()
        conn.close()
        
        print(f"[PaperEngine] Recorded Order #{order_id} for {order.symbol} in SQLite")
        return {"status": "success", "order_id": order_id}
