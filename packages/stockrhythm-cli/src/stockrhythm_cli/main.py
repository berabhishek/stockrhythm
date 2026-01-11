import typer
from .commands import init, deploy, run, backtest

app = typer.Typer()

app.command()(init.init)
app.command()(run.run)
app.command()(backtest.backtest)
app.command()(deploy.deploy)

if __name__ == "__main__":
    app()
