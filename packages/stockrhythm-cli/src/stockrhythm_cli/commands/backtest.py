from pathlib import Path
from typing import Optional

import typer

from .run import run_strategy


def backtest(
    file: str = typer.Option("strategies/strategy.py", "--file", "-f"),
    filter_path: Optional[str] = typer.Option(None, "--filter"),
    data: Optional[str] = typer.Option(None, "--data", help="Local data directory (not used yet)."),
    start: Optional[str] = typer.Option(None, "--from", help="Backtest start date (not used yet)."),
    end: Optional[str] = typer.Option(None, "--to", help="Backtest end date (not used yet)."),
    backend_url: Optional[str] = typer.Option(None, "--backend-url"),
):
    if data or start or end:
        typer.secho(
            "Backtest parameters are accepted but not used yet.",
            fg=typer.colors.YELLOW,
        )

    typer.secho(
        "Backtest mode is not implemented in the backend yet; "
        "running the strategy in paper mode against the active backend.",
        fg=typer.colors.YELLOW,
    )

    run_strategy(
        file=Path(file),
        filter_path=Path(filter_path) if filter_path else None,
        paper_trade=True,
        backend_url=backend_url,
    )
