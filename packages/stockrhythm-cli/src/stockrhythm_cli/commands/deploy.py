from pathlib import Path
import zipfile
import typer


def deploy(
    file: str = typer.Option("strategies/strategy.py", "--file", "-f"),
    filter_path: str | None = typer.Option(None, "--filter"),
    output: str = typer.Option("strategy_bundle.zip", "--out", "-o"),
):
    strategy_path = Path(file)
    if not strategy_path.exists():
        raise typer.BadParameter(f"Strategy file not found: {strategy_path}")

    bundle_path = Path(output)
    extra_filter = Path(filter_path) if filter_path else None

    if extra_filter and not extra_filter.exists():
        raise typer.BadParameter(f"Filter file not found: {extra_filter}")

    default_filter = Path("config/filter.json")
    filter_to_include = extra_filter if extra_filter else (default_filter if default_filter.exists() else None)

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(strategy_path, arcname=strategy_path.name)
        if filter_to_include:
            archive.write(filter_to_include, arcname=filter_to_include.name)

    typer.secho(
        f"Strategy bundled for deploy: {bundle_path}",
        fg=typer.colors.GREEN,
        bold=True,
    )
