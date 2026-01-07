import typer
from pathlib import Path
import os
import textwrap

# --- Templates ---

SETTINGS_YAML = """
# Global Project Settings
market:
  timezone: "Asia/Kolkata"
  primary_exchange: "NSE"

system:
  log_level: "INFO"
"""

SECRETS_ENV = """
# Keep this file out of version control!
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
"""

STRATEGY_JSON = """
{
  "strategy_name": "mean_reversion_basic",
  "symbol": "nse_cm|2885",
  "parameters": {
    "sma_period": 20,
    "entry_threshold": 0.999,
    "profit_target": 0.002
  }
}
"""

FACTORY_PY = """
import json
import os
from pathlib import Path
from .alpha.signals import AlphaStrategy

def load_strategy(config_path: str):
    \"""
    Factory function to initialize the strategy with a specific config.
    \"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
        
    with open(path, 'r') as f:
        config = json.load(f)
        
    print(f"🏭 Factory: Loaded strategy config for {config.get('strategy_name')}")
    return AlphaStrategy(config)
"""


INDICATORS_PY = """
from collections import deque
from typing import List

def calculate_sma(prices: List[float]) -> float:
    if not prices:
        return 0.0
    return sum(prices) / len(prices)
"""

SIGNALS_PY = """
from stockrhythm import Strategy, Tick
from collections import deque
from .indicators import calculate_sma
import asyncio

class AlphaStrategy(Strategy):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.params = config.get("parameters", {})
        
        # State
        self.period = self.params.get("sma_period", 20)
        self.prices = deque(maxlen=self.period)
        self.position = 0
        self.entry_price = 0.0
        
        print(f"🧠 Alpha Initialized. Params: {self.params}")

    async def on_tick(self, tick: Tick):
        self.prices.append(tick.price)
        if len(self.prices) < self.period:
            return

        # Alpha Calculation
        sma = calculate_sma(list(self.prices))
        
        # Entry Logic
        threshold = self.params.get("entry_threshold", 0.999)
        if self.position == 0 and tick.price < sma * threshold:
            qty = 10
            print(f"🟢 Signal: Buy {tick.symbol} @ {tick.price} (SMA: {sma:.2f})")
            await self.buy(tick.symbol, qty)
            self.position = qty
            self.entry_price = tick.price

        # Exit Logic
        target = self.params.get("profit_target", 0.002)
        if self.position > 0:
            pnl_pct = (tick.price - self.entry_price) / self.entry_price
            if pnl_pct > target:
                print(f"🔴 Signal: Take Profit (+{pnl_pct*100:.2f}%)")
                await self.sell(tick.symbol, self.position)
                self.position = 0
"""

LIVE_RUNNER_PY = r"""
import sys
import os
import asyncio
import argparse

# Add the project root to sys.path so we can import from src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from src.factory import load_strategy

def main():
    parser = argparse.ArgumentParser(description="Run a StockRhythm Strategy")
    parser.add_argument("--config", default="config/strategies/mean_reversion.json", help="Path to strategy config")
    # Note: --paper / --live are handled automatically by the SDK's Strategy class
    # but we need to pass them through if we use argparse here.
    parser.add_argument("--live", action="store_true", help="Live Mode")
    parser.add_argument("--paper", action="store_true", help="Paper Mode")
    
    args, unknown = parser.parse_known_args()

    print(f"🚀 Launching Runner from: {PROJECT_ROOT}")
    
    try:
        # 1. Instantiate via Factory
        strategy = load_strategy(args.config)
        
        # 2. Get Symbol from config
        symbol = strategy.config.get("symbol", "nse_cm|2885")
        
        # 3. Start Event Loop
        asyncio.run(strategy.start(subscribe=[symbol]))
        
    except KeyboardInterrupt:
        print("\n🛑 Runner stopped by user.")
    except Exception as e:
        print(f"💥 Fatal Error: {e}")

if __name__ == "__main__":
    main()
"""

GITIGNORE = """
# Python
__pycache__/
*.py[cod]
.venv/

# Config
config/secrets.env

# Data
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
    
    # Define File Structure
    structure = {
        "config/settings.yaml": SETTINGS_YAML,
        "config/secrets.env": SECRETS_ENV,
        "config/strategies/mean_reversion.json": STRATEGY_JSON,
        "src/__init__.py": "",
        "src/factory.py": FACTORY_PY,
        "src/alpha/__init__.py": "",
        "src/alpha/indicators.py": INDICATORS_PY,
        "src/alpha/signals.py": SIGNALS_PY,
        "src/wrappers/__init__.py": "",
        "src/wrappers/data_loader.py": "# Logic to load CSV/DB data goes here\n",
        "src/wrappers/broker_proxy.py": "# Custom broker overrides go here\n",
        "src/reporting/__init__.py": "",
        "scripts/live_runner.py": LIVE_RUNNER_PY,
        "scripts/backtest_runner.py": "# Backtest logic goes here\n",
        "data/.gitkeep": "",
        "notebooks/.gitkeep": "",
        ".gitignore": GITIGNORE,
    }

    # Create Dirs and Files
    for file_path, content in structure.items():
        full_path = root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.endswith(".gitkeep"):
            full_path.touch()
        else:
            full_path.write_text(content.strip())

    # Smart SDK Path Detection
    current_file = Path(__file__).resolve()
    # Go up from: src/stockrhythm_cli/commands/init.py -> packages/stockrhythm-cli -> packages/
    repo_packages_dir = current_file.parents[4] 
    local_sdk_path = repo_packages_dir / "stockrhythm-sdk"
    
    req_content = "stockrhythm-sdk\nnumpy\n"
    
    if local_sdk_path.exists() and (local_sdk_path / "pyproject.toml").exists():
        req_content = f"stockrhythm-sdk @ file://{local_sdk_path}\nnumpy\n"
        typer.echo(f"Detected local SDK at: {local_sdk_path}")
    
    (root / "requirements.txt").write_text(req_content)
    
    typer.secho(f"✅ Initialized production-ready project: {name}", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"  cd {name}")
    typer.echo("  pip install -r requirements.txt")
    typer.echo("  python scripts/live_runner.py --paper")