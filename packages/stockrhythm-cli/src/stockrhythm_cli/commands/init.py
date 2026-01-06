import typer
from pathlib import Path

# The template imports from the SDK we just defined
TEMPLATE = """
from stockrhythm import Strategy, Tick

class MyFirstStrategy(Strategy):
    async def on_tick(self, tick: Tick):
        if tick.price < 100:
            await self.buy(tick.symbol, 10)
"""

def init(name: str):
    path = Path(name)
    if path.exists():
        typer.echo(f"Error: Directory '{name}' already exists.")
        raise typer.Exit(code=1)
        
    path.mkdir()
    (path / "strategy.py").write_text(TEMPLATE)
    # The requirements file allows the user to pip install the SDK
    (path / "requirements.txt").write_text("stockrhythm-sdk")
    typer.echo(f"Initialized new strategy in directory: {name}")
