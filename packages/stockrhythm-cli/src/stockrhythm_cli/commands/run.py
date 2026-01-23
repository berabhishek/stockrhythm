import asyncio
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import List, Optional, Union

import typer
from stockrhythm import Strategy
from stockrhythm.models import UniverseFilterSpec


FilterInput = Union[UniverseFilterSpec, List[str], None]


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


def run_backtest(
    *,
    file: Path,
    start_at: str,
    end_at: str,
    symbols: Optional[List[str]],
    db_path: str,
    name: Optional[str],
    backend_url: Optional[str],
    interval: Optional[str],
    provider: Optional[str],
) -> None:
    module = _load_module(file)
    strategy = _resolve_strategy(module, paper_trade=True)

    run_id = asyncio.run(
        strategy.backtest(
            start_at=start_at,
            end_at=end_at,
            symbols=symbols,
            db_path=db_path,
            name=name,
            backend_url=backend_url,
            interval=interval,
            provider=provider,
        )
    )
    typer.echo(f"Backtest completed. Run ID: {run_id}")


def run(
    file: Optional[str] = typer.Option(None, "--file", "-f"),
    filter_path: Optional[str] = typer.Option(None, "--filter"),
    paper: bool = typer.Option(False, "--paper", help="Run in paper trading mode."),
    live: bool = typer.Option(False, "--live", help="Run in live trading mode."),
    backtest: bool = typer.Option(False, "--backtest", help="Run in backtest mode (supports provider fetch)."),
    start_at: Optional[str] = typer.Option(None, "--start", help="Backtest start datetime (ISO)."),
    end_at: Optional[str] = typer.Option(None, "--end", help="Backtest end datetime (ISO)."),
    symbols: Optional[List[str]] = typer.Option(None, "--symbol", help="Backtest symbol (repeatable)."),
    db_path: str = typer.Option("backtests.db", "--db-path", help="Backtest SQLite DB path."),
    name: Optional[str] = typer.Option(None, "--name", help="Backtest run name."),
    use_provider: bool = typer.Option(False, "--use-provider", help="Fetch backtest data from backend provider."),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name for backend-backed backtests."),
    backtest_url: Optional[str] = typer.Option(None, "--backtest-url", help="Backend HTTP URL for backtest data."),
    interval: Optional[str] = typer.Option(None, "--interval", help="Provider interval for historical data."),
    backend_url: Optional[str] = typer.Option(None, "--backend-url"),
):
    if backtest and (paper or live):
        raise typer.BadParameter("Use --backtest alone, without --paper or --live.")

    if backtest:
        if not file:
            file = typer.prompt("Strategy file path", default="strategies/strategy.py")
        if not start_at:
            start_at = typer.prompt("Backtest start datetime (ISO)")
        if not end_at:
            end_at = typer.prompt("Backtest end datetime (ISO)")
        if use_provider and not symbols:
            raise typer.BadParameter("Use --symbol when fetching backtest data from a provider.")

        try:
            provider_url = None
            if use_provider:
                provider_url = backtest_url or "http://127.0.0.1:8000"
            run_backtest(
                file=Path(file),
                start_at=start_at,
                end_at=end_at,
                symbols=symbols,
                db_path=db_path,
                name=name,
                backend_url=provider_url,
                interval=interval,
                provider=provider,
            )
        except KeyboardInterrupt:
            typer.echo("Backtest interrupted.")
        return

    if paper and live:
        raise typer.BadParameter("Choose either --paper or --live, not both.")

    paper_trade = True if not live else False
    if paper:
        paper_trade = True

    if not file:
        file = "strategies/strategy.py"

    try:
        run_strategy(
            file=Path(file),
            filter_path=Path(filter_path) if filter_path else None,
            paper_trade=paper_trade,
            backend_url=backend_url,
        )
    except KeyboardInterrupt:
        typer.echo("Run interrupted.")
