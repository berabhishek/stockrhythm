import asyncio
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Optional, Union

import typer
from stockrhythm import Strategy
from stockrhythm.models import UniverseFilterSpec


FilterInput = Union[UniverseFilterSpec, list[str], None]


def _load_module(file_path: Path):
    if not file_path.exists():
        raise typer.BadParameter(f"Strategy file not found: {file_path}")

    module_name = "stockrhythm_user_strategy"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise typer.BadParameter(f"Unable to import strategy from: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    parent_dir = str(file_path.parent.resolve())
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    spec.loader.exec_module(module)
    return module


def _try_call_with_paper_trade(func, paper_trade: bool):
    try:
        return func(paper_trade=paper_trade)
    except TypeError:
        return func()


def _resolve_strategy(module, paper_trade: bool) -> Strategy:
    if hasattr(module, "get_strategy") and callable(module.get_strategy):
        strategy = _try_call_with_paper_trade(module.get_strategy, paper_trade)
        if isinstance(strategy, Strategy):
            return strategy

    for name in ("strategy", "STRATEGY"):
        if hasattr(module, name):
            candidate = getattr(module, name)
            if isinstance(candidate, Strategy):
                return candidate
            if inspect.isclass(candidate) and issubclass(candidate, Strategy):
                return _try_call_with_paper_trade(candidate, paper_trade)

    candidates = []
    for obj in module.__dict__.values():
        if inspect.isclass(obj) and issubclass(obj, Strategy) and obj is not Strategy:
            candidates.append(obj)

    if len(candidates) == 1:
        return _try_call_with_paper_trade(candidates[0], paper_trade)

    raise typer.BadParameter(
        "Could not resolve a Strategy. Define get_strategy(), "
        "or expose a Strategy instance as STRATEGY/strategy."
    )


def _load_filter_from_json(path: Path) -> UniverseFilterSpec:
    if not path.exists():
        raise typer.BadParameter(f"Filter file not found: {path}")
    data = json.loads(path.read_text())
    return UniverseFilterSpec(**data)


def _normalize_filter(filter_obj) -> FilterInput:
    if filter_obj is None:
        return None
    if hasattr(filter_obj, "build") and callable(filter_obj.build):
        filter_obj = filter_obj.build()
    if isinstance(filter_obj, UniverseFilterSpec):
        return filter_obj
    if isinstance(filter_obj, list):
        return filter_obj
    raise typer.BadParameter(
        "Filter must be a UniverseFilter/UniverseFilterSpec or a list of symbols."
    )


def _resolve_filter(module, filter_path: Optional[Path]) -> FilterInput:
    if filter_path:
        return _load_filter_from_json(filter_path)

    if hasattr(module, "get_filter") and callable(module.get_filter):
        return _normalize_filter(module.get_filter())

    for name in ("FILTER_SPEC", "FILTER"):
        if hasattr(module, name):
            return _normalize_filter(getattr(module, name))

    default_path = Path("config/filter.json")
    if default_path.exists():
        return _load_filter_from_json(default_path)

    return None


def run_strategy(
    *,
    file: Path,
    filter_path: Optional[Path],
    paper_trade: bool,
    backend_url: Optional[str],
) -> None:
    module = _load_module(file)
    strategy = _resolve_strategy(module, paper_trade)
    subscribe = _resolve_filter(module, filter_path)

    if backend_url:
        strategy.client.backend_url = backend_url

    asyncio.run(strategy.start(subscribe=subscribe))


def run(
    file: str = typer.Option("strategies/strategy.py", "--file", "-f"),
    filter_path: Optional[str] = typer.Option(None, "--filter"),
    paper: bool = typer.Option(False, "--paper", help="Run in paper trading mode."),
    live: bool = typer.Option(False, "--live", help="Run in live trading mode."),
    backend_url: Optional[str] = typer.Option(None, "--backend-url"),
):
    if paper and live:
        raise typer.BadParameter("Choose either --paper or --live, not both.")

    paper_trade = True if not live else False
    if paper:
        paper_trade = True

    try:
        run_strategy(
            file=Path(file),
            filter_path=Path(filter_path) if filter_path else None,
            paper_trade=paper_trade,
            backend_url=backend_url,
        )
    except KeyboardInterrupt:
        typer.echo("Run interrupted.")
