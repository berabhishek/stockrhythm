from __future__ import annotations
import asyncio
import time
from typing import List, Set, Dict, Any, Optional

from stockrhythm.models import UniverseFilterSpec, UniverseUpdate, FilterOp
from .providers.base import MarketDataProvider
from .instrument_master import InstrumentMaster

def _passes(value, op: FilterOp, target) -> bool:
    if op == FilterOp.EQ: return value == target
    if op == FilterOp.NE: return value != target
    if op == FilterOp.GT: return value > target
    if op == FilterOp.GTE: return value >= target
    if op == FilterOp.LT: return value < target
    if op == FilterOp.LTE: return value <= target
    if op == FilterOp.IN: return value in target
    if op == FilterOp.NOT_IN: return value not in target
    if op == FilterOp.BETWEEN:
        lo, hi = target
        return lo <= value <= hi
    return False

class UniverseResolver:
    """
    Replace this with real implementations:
      - index constituents resolver
      - instrument master resolver
      - watchlist passthrough
    """
    def __init__(self, instrument_master: Optional[InstrumentMaster] = None):
        self.master = instrument_master or InstrumentMaster()
        # Ensure master is loaded
        self.master.load()

    async def candidates(self, spec: UniverseFilterSpec) -> List[str]:
        c = spec.candidates or {}
        t = c.get("type")

        if t == "watchlist":
            raw_symbols = list(c.get("symbols", []))
            resolved_tokens = []
            for sym in raw_symbols:
                # Try to map RELIANCE -> nse_cm|2885
                token = self.master.resolve(sym)
                if token:
                    resolved_tokens.append(token)
                else:
                    # Fallback: if user passed a token directly or mapping missing
                    print(f"Warning: Symbol {sym} not found in master, using as-is.")
                    resolved_tokens.append(sym)
            return resolved_tokens

        # Placeholder: you will implement real index/instrument_master sources
        if t == "index":
            # Just return dummy symbols for now to test flow
            return ["NSE_CM|123", "NSE_CM|456"]

        if t == "instrument_master":
             # Just return dummy symbols for now to test flow
            return ["NSE_CM|111", "NSE_CM|222"]

        return []

    async def resolve(self, spec: UniverseFilterSpec, provider: MarketDataProvider) -> List[str]:
        base = await self.candidates(spec)
        if not spec.conditions:
            return base[: spec.max_symbols]

        # For dynamic fields, we require provider.snapshot()
        try:
            snap = await provider.snapshot(base)
        except NotImplementedError:
            print("Warning: Provider does not support snapshot(), skipping dynamic conditions.")
            return base[: spec.max_symbols]

        selected: List[str] = []
        for sym in base:
            row = snap.get(sym, {})
            ok = True
            for cond in spec.conditions:
                v = row.get(cond.field)
                if v is None or not _passes(v, cond.op, cond.value):
                    ok = False
                    break
            if ok:
                selected.append(sym)

        # TODO: apply sorting if needed using snap fields
        return selected[: spec.max_symbols]

class UniverseManager:
    def __init__(
        self,
        *,
        spec: UniverseFilterSpec,
        provider: MarketDataProvider,
        resolver: UniverseResolver,
        send_json,  # async callable(dict)
    ):
        self.spec = spec
        self.provider = provider
        self.resolver = resolver
        self.send_json = send_json
        self._current: Set[str] = set()
        self._lock = asyncio.Lock()
        self._running = True

    async def stop(self):
        self._running = False

    async def run(self):
        while self._running:
            new_list = await self.resolver.resolve(self.spec, self.provider)
            new_set = set(new_list)

            async with self._lock:
                added = sorted(list(new_set - self._current))
                removed = sorted(list(self._current - new_set))
                changed = bool(added or removed)

                if changed:
                    self._current = new_set
                    await self.provider.set_subscriptions(sorted(list(self._current)))

                    update = UniverseUpdate(
                        added=added,
                        removed=removed,
                        universe=sorted(list(self._current)),
                        reason="filter_refresh",
                        timestamp=time.time(),
                    )
                    
                    data_dict = update.model_dump() if hasattr(update, "model_dump") else update.dict()
                    await self.send_json({"action": "universe", "data": data_dict})

            await asyncio.sleep(self.spec.refresh_seconds)
