from fastapi import FastAPI, WebSocket
from .data_orchestrator import get_provider
import asyncio
import os
from dotenv import load_dotenv

# Load .env file from root or current dir
load_dotenv()

app = FastAPI()

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
    
    # Wait for subscription message
    try:
        data = await websocket.receive_json()
        if data.get("action") == "subscribe":
            symbols = data.get("symbols", [])
            await provider.subscribe(symbols)
            print(f"Client subscribed to: {symbols}")
    except Exception as e:
        print(f"Error receiving subscription: {e}")
    
    # Start streaming
    try:
        async for tick in provider.stream():
            # In a real app, we would serialize the tick to JSON/msgpack
            await websocket.send_json(tick.model_dump(mode='json'))
    except Exception as e:
        print(f"Connection closed: {e}")
