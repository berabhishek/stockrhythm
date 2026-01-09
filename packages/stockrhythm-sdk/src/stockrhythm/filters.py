from __future__ import annotations
from typing import Any, List
from stockrhythm.models import UniverseFilterSpec, FilterCondition, FilterOp, SortSpec, SortDir

class UniverseFilter:
    """
    Fluent builder that outputs UniverseFilterSpec (JSON-safe).
    """
    def __init__(
        self,
        candidates: dict,
        *,
        refresh_seconds: int = 60,
        max_symbols: int = 50,
        grace_seconds: int = 0,
    ):
        self._spec = UniverseFilterSpec(
            candidates=candidates,
            refresh_seconds=refresh_seconds,
            max_symbols=max_symbols,
            grace_seconds=grace_seconds,
        )

    @staticmethod
    def from_index(name: str, *, refresh_seconds: int = 60, max_symbols: int = 50) -> "UniverseFilter":
        return UniverseFilter(
            candidates={"type": "index", "name": name},
            refresh_seconds=refresh_seconds,
            max_symbols=max_symbols,
        )

    @staticmethod
    def from_watchlist(symbols: List[str], *, refresh_seconds: int = 60) -> "UniverseFilter":
        return UniverseFilter(
            candidates={"type": "watchlist", "symbols": symbols},
            refresh_seconds=refresh_seconds,
            max_symbols=len(symbols),
        )

    def where(self, field: str, op: FilterOp, value: Any) -> "UniverseFilter":
        self._spec.conditions.append(FilterCondition(field=field, op=op, value=value))
        return self

    def sort_by(self, field: str, direction: SortDir = SortDir.DESC) -> "UniverseFilter":
        self._spec.sort.append(SortSpec(field=field, direction=direction))
        return self

    def build(self) -> UniverseFilterSpec:
        return self._spec
