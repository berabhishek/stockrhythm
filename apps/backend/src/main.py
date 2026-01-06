from fastapi import FastAPI, WebSocket
from .data_orchestrator import get_provider
import asyncio

app = FastAPI()

# Mock config
CONFIG = {
    "active_provider": "mock"
}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    provider = get_provider(CONFIG)
    await provider.connect()
    
    # Start streaming
    try:
        async for tick in provider.stream():
            # In a real app, we would serialize the tick to JSON/msgpack
            await websocket.send_json(tick.model_dump(mode='json'))
    except Exception as e:
        print(f"Connection closed: {e}")
