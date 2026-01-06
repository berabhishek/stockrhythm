import typer
from .commands import init, deploy

app = typer.Typer()

app.command()(init.init)
app.command()(deploy.deploy)

if __name__ == "__main__":
    app()
