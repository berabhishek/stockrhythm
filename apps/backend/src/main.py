from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from .data_orchestrator import get_provider
from .paper_engine import PaperEngine
from . import paper_engine
from stockrhythm.models import Order as OrderModel, UniverseFilterSpec
from .universe_manager import UniverseManager, UniverseResolver
import asyncio
import os
import json
from dotenv import load_dotenv

# Load .env file from root or current dir
load_dotenv()

app = FastAPI()

# Dynamic Config
def _parse_symbols(value: str) -> list[str]:
    symbols = [item.strip() for item in value.split(",") if item.strip()]
    return symbols or ["MOCK"]


def _parse_int(value: str, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


CONFIG = {
    "active_provider": os.getenv("STOCKRHYTHM_PROVIDER", "mock"),
    "kotak_access_token": os.getenv("KOTAK_ACCESS_TOKEN"),
    "upstox_creds": {
        "api_key": os.getenv("UPSTOX_API_KEY"),
        "api_secret": os.getenv("UPSTOX_API_SECRET"),
        "token": os.getenv("UPSTOX_ACCESS_TOKEN"),
    },
    "paper_db_path": os.getenv("STOCKRHYTHM_PAPER_DB_PATH", "paper_trades.db"),
    "mock_db_path": os.getenv("STOCKRHYTHM_MOCK_DB_PATH", "mock_trades.db"),
    "mock": {
        "symbols": _parse_symbols(os.getenv("MOCK_SYMBOLS", "MOCK")),
        "base_price": _parse_float(os.getenv("MOCK_BASE_PRICE", "100"), 100.0),
        "max_deviation": _parse_float(os.getenv("MOCK_MAX_DEVIATION", "5"), 5.0),
        "volatility": _parse_float(os.getenv("MOCK_VOLATILITY", "0.5"), 0.5),
        "mean_reversion": _parse_float(os.getenv("MOCK_MEAN_REVERSION", "0.1"), 0.1),
        "interval_seconds": _parse_float(os.getenv("MOCK_INTERVAL_SECONDS", "0.5"), 0.5),
        "seed": _parse_int(os.getenv("MOCK_SEED", ""), None),
        "volume_min": _parse_int(os.getenv("MOCK_VOLUME_MIN", "100"), 100),
        "volume_max": _parse_int(os.getenv("MOCK_VOLUME_MAX", "1000"), 1000),
    },
}


def _select_paper_db(config: dict) -> str:
    db_override = getattr(paper_engine, "DB_PATH", None)
    if db_override and db_override != "paper_trades.db":
        return db_override
    if str(config.get("active_provider", "")).startswith("mock"):
        return config.get("mock_db_path", "mock_trades.db")
    return config.get("paper_db_path", "paper_trades.db")


class BacktestRequest(BaseModel):
    symbols: list[str]
    start: str
    end: str
    interval: str | None = None
    provider: str | None = None


@app.post("/backtest")
async def backtest(request: BacktestRequest):
    provider = get_provider(CONFIG, provider_override=request.provider)
    await provider.connect()
    ticks = await provider.historical(
        symbols=request.symbols,
        start_at=request.start,
        end_at=request.end,
        interval=request.interval,
    )
    return {"ticks": [tick.model_dump(mode="json") for tick in ticks]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    provider = get_provider(CONFIG)
    await provider.connect()
    paper_engine = PaperEngine(db_path=_select_paper_db(CONFIG))
    
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
