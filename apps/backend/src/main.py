from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .data_orchestrator import get_provider
from .paper_engine import PaperEngine
from stockrhythm.models import Order as OrderModel, UniverseFilterSpec
from .universe_manager import UniverseManager, UniverseResolver
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
    protocol_version = 1
    universe_task = None
    tick_task = None

    async def send_json(obj: dict):
        # Helper to send JSON messages
        await websocket.send_text(json.dumps(obj))

    async def tick_stream_loop():
        try:
            async for tick in provider.stream():
                # Protocol V2: Wrap in { action: "tick", data: ... }
                # Protocol V1: Raw Tick JSON
                tick_dict = tick.model_dump(mode='json')
                
                if protocol_version >= 2:
                    await send_json({"action": "tick", "data": tick_dict})
                else:
                    await websocket.send_json(tick_dict)
        except Exception as e:
            print(f"Tick Stream Error: {e}")

    try:
        async for raw_message in websocket.iter_text():
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            action = message.get("action")
            data = message.get("data", {}) # Protocol V2 wraps content in 'data'
            
            # Legacy/V1 support where top-level keys were used directly in configure
            if action == "configure":
                # Check structure
                if "data" in message and isinstance(message["data"], dict):
                    # V2 structure
                    config_data = message["data"]
                    protocol_version = config_data.get("protocol_version", 1)
                    is_paper_trading = config_data.get("paper_trade", True)
                    subscribe_symbols = config_data.get("subscribe")
                    filter_payload = config_data.get("filter")
                else:
                    # V1 structure
                    config_data = message
                    protocol_version = 1
                    is_paper_trading = config_data.get("paper_trade", True)
                    subscribe_symbols = config_data.get("subscribe")
                    filter_payload = None

                print(f"Session Configured: Protocol={protocol_version}, Paper={is_paper_trading}")

                if filter_payload:
                    spec = UniverseFilterSpec(**filter_payload)
                    resolver = UniverseResolver()
                    manager = UniverseManager(spec=spec, provider=provider, resolver=resolver, send_json=send_json)
                    # Stop existing if any
                    if universe_task:
                        universe_task.cancel()
                    universe_task = asyncio.create_task(manager.run())
                elif subscribe_symbols:
                    await provider.set_subscriptions(subscribe_symbols)
                    if protocol_version >= 2:
                        # Send initial universe snapshot for static subscribe
                        await send_json({
                            "action": "universe", 
                            "data": {
                                "added": subscribe_symbols, 
                                "removed": [], 
                                "universe": subscribe_symbols, 
                                "reason": "static_subscribe"
                            }
                        })

                # Start tick stream if not running
                if not tick_task:
                    tick_task = asyncio.create_task(tick_stream_loop())
            
            elif action == "order":
                # Handle both V1 (flat) and V2 (nested data)
                if "data" in message and isinstance(message["data"], dict):
                    order_data = message["data"]
                else:
                    order_data = message.get("data") # fallback if mixed

                if not order_data and "symbol" in message: 
                     # fallback to flat message if 'data' key missing but fields present
                     order_data = message
                
                if order_data:
                    order = OrderModel(**order_data)
                    if is_paper_trading:
                        await paper_engine.execute_order(order)
                    else:
                        print(f"LIVE TRADING NOT IMPLEMENTED YET FOR {order.symbol}")

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Message Loop Error: {e}")
    finally:
        if universe_task:
            universe_task.cancel()
        if tick_task:
            tick_task.cancel()

