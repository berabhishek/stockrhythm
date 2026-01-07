from fastapi import FastAPI, WebSocket
from .data_orchestrator import get_provider
from .paper_engine import PaperEngine
from stockrhythm.models import Order as OrderModel
import asyncio
import os
import json
from dotenv import load_dotenv

# Load .env file from root or current dir
load_dotenv()

app = FastAPI()
paper_engine = PaperEngine()

# Dynamic Config
CONFIG = {
    "active_provider": os.getenv("STOCKRHYTHM_PROVIDER", "mock"),
    "kotak_access_token": os.getenv("KOTAK_ACCESS_TOKEN")
}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    provider = get_provider(CONFIG)
    await provider.connect()
    
    is_paper_trading = True # Default
    
    async def handle_messages():
        nonlocal is_paper_trading
        try:
            async for message in websocket.iter_json():
                action = message.get("action")
                
                if action == "configure":
                    is_paper_trading = message.get("paper_trade", True)
                    symbols = message.get("subscribe", [])
                    if symbols:
                        await provider.subscribe(symbols)
                    print(f"Session Configured: Paper={is_paper_trading}, Symbols={symbols}")
                
                elif action == "order":
                    order_data = message.get("data")
                    order = OrderModel(**order_data)
                    
                    if is_paper_trading:
                        await paper_engine.execute_order(order)
                    else:
                        print(f"LIVE TRADING NOT IMPLEMENTED YET FOR {order.symbol}")
                        
        except Exception as e:
            print(f"Message Loop Error: {e}")

    # Start message handler in background
    asyncio.create_task(handle_messages())
    
    # Start streaming
    try:
        async for tick in provider.stream():
            await websocket.send_json(tick.model_dump(mode='json'))
    except Exception as e:
        print(f"Connection closed: {e}")

