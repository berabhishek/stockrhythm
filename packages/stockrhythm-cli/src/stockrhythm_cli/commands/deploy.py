import typer

def deploy(path: str = "."):
    typer.echo(f"Deploying strategy from {path}...")
    # Logic to zip and upload would go here
    typer.echo("Deployment complete (Simulation).")
