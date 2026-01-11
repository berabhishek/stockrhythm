from enum import Enum
from typing import Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class FilterOp(str, Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"   # value: [low, high]

class SortDir(str, Enum):
    ASC = "asc"
    DESC = "desc"

class FilterCondition(BaseModel):
    field: str                 # e.g. "last_price", "day_volume"
    op: FilterOp
    value: Any

class SortSpec(BaseModel):
    field: str
    direction: SortDir = SortDir.DESC

class UniverseFilterSpec(BaseModel):
    """
    A safe, JSON-serializable description of how to select symbols.

    candidates: describes where the initial candidate list comes from
      Examples:
        {"type": "index", "name": "NIFTY500"}
        {"type": "watchlist", "symbols": ["nse_cm|2885", ...]}
        {"type": "instrument_master", "exchange": "NSE", "segment": "CM"}
    """
    candidates: dict = Field(default_factory=dict)

    # ANDed conditions applied after candidates are expanded.
    conditions: List[FilterCondition] = Field(default_factory=list)

    # Optional ranking + trimming
    sort: List[SortSpec] = Field(default_factory=list)
    max_symbols: int = 50

    # How often backend refreshes membership
    refresh_seconds: int = 60

    # Optional: allow a short grace period before actually unsubscribing removed symbols
    grace_seconds: int = 0

class UniverseUpdate(BaseModel):
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    universe: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    timestamp: Optional[float] = None

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
