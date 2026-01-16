import typer
from pathlib import Path

# --- Templates ---

STRATEGY_PY = """
import asyncio
from stockrhythm import Strategy, Tick
from stockrhythm.filters import UniverseFilter
from stockrhythm.models import FilterOp

class MyStrategy(Strategy):
    async def on_tick(self, tick: Tick):
        # Example signal: replace with your alpha.
        if tick.price < 100:
            await self.buy(tick.symbol, 1)

def get_filter():
    # Return a UniverseFilter object or a UniverseFilterSpec.
    return (
        UniverseFilter.from_watchlist(["RELIANCE"])
        .where("day_volume", FilterOp.GT, 1)
    )

def get_strategy(paper_trade: bool = True) -> Strategy:
    return MyStrategy(paper_trade=paper_trade)

def main():
    strategy = get_strategy()
    filter_spec = get_filter()
    if hasattr(filter_spec, "build"):
        filter_spec = filter_spec.build()
    asyncio.run(strategy.start(subscribe=filter_spec))

if __name__ == "__main__":
    main()
"""

FILTER_JSON = """
{
  "candidates": {
    "type": "watchlist",
    "symbols": ["RELIANCE"]
  },
  "conditions": [
    {
      "field": "day_volume",
      "op": "gt",
      "value": 1
    }
  ],
  "sort": [],
  "max_symbols": 50,
  "refresh_seconds": 60,
  "grace_seconds": 0
}
"""

PROJECT_README = """
# StockRhythm Strategy Project

## Layout
notebooks/        Research and experiments (Jupyter notebooks)
strategies/       Strategy code (your main strategy lives here)
config/           Optional filter specs and settings
data/             Local datasets for backtests (optional)

## Quickstart
1) Install dependencies:
   pip install -r requirements.txt

2) Start the backend (from the StockRhythm repo root):
   docker-compose up -d backend redis
   # or
   uv run uvicorn apps.backend.src.main:app --port 8000

3) Paper trade:
   stockrhythm run --paper --file strategies/strategy.py

4) Live trade:
   stockrhythm run --live --file strategies/strategy.py

## Filters and Universes
The CLI looks for `get_filter()` in your strategy file and passes it to
Strategy.start(subscribe=...). You can return either:
- UniverseFilter (builder) from stockrhythm.filters
- UniverseFilterSpec (built)
- A list of symbol strings for static subscriptions

If you prefer editing JSON instead, update config/filter.json and run:
   stockrhythm run --paper --file strategies/strategy.py --filter config/filter.json

## Notebooks
Use notebooks/ for indicator research and idea exploration. When the logic
is stable, copy it into strategies/strategy.py and wire it into on_tick.
"""

GITIGNORE = """
# Python
__pycache__/
*.py[cod]
.venv/

# Jupyter
.ipynb_checkpoints/

# Local data/artifacts
data/*
paper_trades.db
"""

# --- Init Logic ---

def init(name: str):
    root = Path(name)
    if root.exists():
        typer.echo(f"Error: Directory '{name}' already exists.")
        raise typer.Exit(code=1)

    root.mkdir()

    structure = {
        "README.md": PROJECT_README,
        "strategies/strategy.py": STRATEGY_PY,
        "strategies/__init__.py": "",
        "config/filter.json": FILTER_JSON,
        "data/.gitkeep": "",
        "notebooks/.gitkeep": "",
        ".gitignore": GITIGNORE,
    }

    for file_path, content in structure.items():
        full_path = root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.endswith(".gitkeep"):
            full_path.touch()
        else:
            full_path.write_text(content.strip() + "\n")

    current_file = Path(__file__).resolve()
    repo_packages_dir = current_file.parents[4]
    local_sdk_path = repo_packages_dir / "stockrhythm-sdk"

    req_content = "stockrhythm-sdk\njupyterlab\n"

    if local_sdk_path.exists() and (local_sdk_path / "pyproject.toml").exists():
        req_content = f"stockrhythm-sdk @ file://{local_sdk_path}\njupyterlab\n"
        typer.echo(f"Detected local SDK at: {local_sdk_path}")

    (root / "requirements.txt").write_text(req_content)

    typer.secho(f"Initialized StockRhythm project: {name}", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"  cd {name}")
    typer.echo("  pip install -r requirements.txt")
    typer.echo("  stockrhythm run --paper --file strategies/strategy.py")
