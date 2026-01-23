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
        # This basic example prints prices for verification.
        # print(f"[{tick.timestamp}] {tick.symbol}: {tick.price}")
        if tick.price < 100:
            await self.buy(tick.symbol, 1)

def get_filter():
    # Return a UniverseFilter object or a UniverseFilterSpec.
    return (
        UniverseFilter.from_watchlist(["SBIN"])
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
    "symbols": ["SBIN"]
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

NOTEBOOK_TEMPLATE = """
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Strategy Backtest\\n",
    "\\n",
    "This notebook demonstrates how to run a backtest for your strategy using the StockRhythm SDK."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import asyncio\\n",
    "import os\\n",
    "import sys\\n",
    "from pathlib import Path\\n",
    "\\n",
    "# Ensure the project root is in sys.path so we can import the strategy\\n",
    "project_root = Path(\\"..\\").resolve()\\n",
    "if str(project_root) not in sys.path:\\n",
    "    sys.path.insert(0, str(project_root))\\n",
    "\\n",
    "from stockrhythm.backtest import BacktestEngine\\n",
    "from strategies.strategy import MyStrategy"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Configuration\\n",
    "START_DATE = \\"2024-01-08\\"\\n",
    "END_DATE = \\"2024-01-10\\"\\n",
    "SYMBOLS = [\\"SBIN\\"]\\n",
    "PROVIDER = \\"upstox\\"\\n",
    "INTERVAL = \\"1minute\\"\\n",
    "BACKEND_URL = \\"http://127.0.0.1:8000\\""
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "async def run_backtest():\\n",
    "    engine = BacktestEngine(db_path=\\"../backtests.db\\")\\n",
    "    strategy = MyStrategy()\\n",
    "    \\n",
    "    print(f\\"Running backtest for {SYMBOLS} from {START_DATE} to {END_DATE}...\\")\\n",
    "    run_id = await engine.run(\\n",
    "        strategy=strategy,\\n",
    "        start_at=START_DATE,\\n",
    "        end_at=END_DATE,\\n",
    "        symbols=SYMBOLS,\\n",
    "        backend_url=BACKEND_URL,\\n",
    "        provider=PROVIDER,\\n",
    "        interval=INTERVAL\\n",
    "    )\\n",
    "    print(f\\"Backtest completed. Run ID: {run_id}\\")\\n",
    "    return run_id\\n",
    "\\n",
    "# Run in the existing loop if available (Jupyter handles this)\\n",
    "await run_backtest()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
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
Use notebooks/ for indicator research and idea exploration. 

To run the backtest notebook:
1. Ensure dependencies are installed:
   pip install -r requirements.txt

2. Launch Jupyter Lab:
   uv run --with-requirements requirements.txt jupyter lab
   # OR
   jupyter lab

3. Open `notebooks/backtest.ipynb` and run all cells.
   *Ensure the backend is running on port 8000.*

### Historical Data (Upstox)
To run the backtest notebook against Upstox historical data, start the backend
with the Upstox provider (from the StockRhythm repo root):
   uv run python -m apps.backend.src --broker upstox --port 8000
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
backtests.db
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
        "notebooks/backtest.ipynb": NOTEBOOK_TEMPLATE,
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
