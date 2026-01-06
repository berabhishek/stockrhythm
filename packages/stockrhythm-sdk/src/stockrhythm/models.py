from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class Tick(BaseModel):
    """Normalized Market Data Event"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    provider: str  # e.g., "upstox", "mock"

class Order(BaseModel):
    """Standardized Order Request"""
    id: str | None = None
    symbol: str
    qty: int
    side: OrderSide
    type: OrderType
    limit_price: float | None = None
