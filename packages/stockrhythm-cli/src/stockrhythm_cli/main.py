import typer

from .commands import backtest, deploy, doctor, init, lint, run

app = typer.Typer()

app.command()(init.init)
app.command()(run.run)
app.command()(backtest.backtest)
app.command()(deploy.deploy)
app.command()(doctor.doctor)
app.command()(lint.lint)

if __name__ == "__main__":
    app()
