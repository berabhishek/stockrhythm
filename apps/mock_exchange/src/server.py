from fastapi import FastAPI, WebSocket
from .engine import MatchingEngine, Order
import asyncio
import random

app = FastAPI()
engine = MatchingEngine()

@app.post("/orders")
async def create_order(order: Order):
    trades = engine.place_order(order)
    return {"status": "accepted", "fills": trades}

@app.get("/trades")
async def get_trades():
    return engine.trades

@app.websocket("/ticks")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    price = 100.0
    symbol = "AAPL"
    try:
        while True:
            # Random Walk
            change = random.uniform(-0.5, 0.5)
            price += change
            await websocket.send_json({
                "symbol": symbol,
                "price": round(price, 2),
                "timestamp": asyncio.get_event_loop().time()
            })
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Connection closed: {e}")
