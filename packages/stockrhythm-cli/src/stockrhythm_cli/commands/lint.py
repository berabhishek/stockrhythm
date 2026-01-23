import subprocess

import typer
from rich.console import Console

console = Console()


def lint(
    fix: bool = typer.Option(False, "--fix", "-f", help="Auto-fix issues where possible"),
    path: str = typer.Option(".", "--path", "-p", help="Path to lint (default: current directory)"),
    show_stats: bool = typer.Option(False, "--stats", "-s", help="Show detailed statistics"),
):
    """
    Lint the project using ruff.

    Checks for:
    - Unused imports (F401)
    - Undefined names (F821)
    - Import sorting (I001)
    - Style issues (E, W)
    - Async/await best practices (ASYNC)
    - Datetime timezone issues (DTZ)
    - Performance anti-patterns (PERF)
    - Simplification opportunities (SIM)
    - And 15+ other rule categories

    Exit codes:
    - 0: No issues found
    - 1: Issues found (non-blocking)
    """

    args = ["uv", "run", "ruff", "check", path]

    if fix:
        args.append("--fix")
        console.print("[yellow]Running ruff with --fix...[/yellow]\n")
    else:
        console.print("[cyan]Running ruff check...[/cyan]\n")

    if show_stats:
        args.append("--statistics")

    result = subprocess.run(args)

    if result.returncode == 0:
        console.print("\n[green]✓ All checks passed![/green]")
    else:
        if fix:
            console.print(
                "\n[yellow]✓ Auto-fixes applied. Re-run without --fix to verify.[/yellow]"
            )
        else:
            console.print(
                "\n[yellow]⚠ Issues found. Run with --fix to auto-fix where possible.[/yellow]"
            )

    return result.returncode
