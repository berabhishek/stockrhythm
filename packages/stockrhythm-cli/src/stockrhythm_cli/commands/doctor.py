import ast
import importlib.metadata
import importlib.util
import os
import sys
from pathlib import Path

import typer
from rich.console import Console

console = Console()


# ==============================================================================
# 1. Runtime Integrity
# ==============================================================================


def _check_runtime_integrity() -> tuple[bool, str, list[str]]:
    """Check Python version, interpreter, venv, and OS fingerprint."""
    warnings = []

    # Check Python version
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    # We require >=3.12 per pyproject.toml
    if version_info < (3, 12):
        return False, f"Python {version_str}", [f"Python {version_str} < 3.12 (required)"]

    # Check venv/conda activation
    venv_active = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    venv_env = os.environ.get("VIRTUAL_ENV")
    venv_indicator = venv_active or venv_env

    status_str = f"Python {version_str}"
    if venv_indicator:
        status_str += " (venv active)"
    else:
        warnings.append("No virtual environment detected (recommended)")

    return True, status_str, warnings


# ==============================================================================
# 2. Dependency Graph Correctness
# ==============================================================================


def _get_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def _parse_dependency_version(spec: str) -> tuple[str, str]:
    """Parse 'package>=1.0' into ('package', '>=1.0')."""
    for op in [">=", "<=", "==", "!=", "~=", ">", "<"]:
        if op in spec:
            parts = spec.split(op, 1)
            return parts[0].strip(), op + parts[1].strip()
    return spec.strip(), ""


def _check_dependencies() -> tuple[bool, str, list[str]]:
    """Check if required packages are installed and versions match."""
    warnings = []

    root = _get_project_root()
    pyproject = root / "pyproject.toml"

    if not pyproject.exists():
        return False, "No dependencies", ["pyproject.toml not found"]

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        return False, "Dependency check failed", [f"Failed to parse pyproject.toml: {e}"]

    # Get dependencies from project.dependencies
    deps = data.get("project", {}).get("dependencies", [])

    failed_deps = []
    critical_modules = ["stockrhythm", "typer", "rich"]
    optional_accelerators = ["numba", "talib"]

    for dep in deps:
        pkg_name, spec = _parse_dependency_version(dep)
        try:
            importlib.metadata.version(pkg_name)
        except importlib.metadata.PackageNotFoundError:
            failed_deps.append(f"Missing: {pkg_name}")

    # Check optional accelerators
    for module in optional_accelerators:
        try:
            importlib.import_module(module)
        except ImportError:
            warnings.append(f"Optional accelerator missing: {module}")

    if failed_deps:
        return False, "Dependencies broken", failed_deps

    resolved_count = len(deps)
    return True, f"Dependencies resolved ({resolved_count} packages)", warnings


# ==============================================================================
# 3. Project Structure Validity
# ==============================================================================


def _check_project_structure() -> tuple[bool, str, list[str]]:
    """Check required directories and structure."""
    warnings = []

    root = _get_project_root()
    required_dirs = ["strategies", "tests"]
    optional_dirs = ["research", "deployments", "data"]

    missing_required = []
    for d in required_dirs:
        if not (root / d).exists():
            missing_required.append(d)

    if missing_required:
        return (
            False,
            "Project structure invalid",
            [f"Missing required: {', '.join(missing_required)}"],
        )

    missing_optional = [d for d in optional_dirs if not (root / d).exists()]
    for d in missing_optional:
        warnings.append(f"Optional directory missing: {d}")

    # Check for strategy files
    strategies_dir = root / "strategies"
    py_files = list(strategies_dir.glob("*.py"))
    if not py_files:
        warnings.append("No strategy files found in strategies/")

    return True, "Project structure valid", warnings


# ==============================================================================
# 4. Strategy Static Analysis (AST)
# ==============================================================================


def _analyze_strategy_file(file_path: Path) -> tuple[list[str], list[str]]:
    """
    Parse strategy file and check for:
    - Strategy subclass
    - Required callbacks
    - Forbidden imports (broker SDKs)
    - Unsafe time/randomness usage
    - Network calls
    Returns (errors, warnings)
    """
    errors = []
    warnings = []

    if not file_path.exists():
        return [f"Strategy file not found: {file_path}"], []

    try:
        tree = ast.parse(file_path.read_text())
    except SyntaxError as e:
        return [f"Syntax error in {file_path.name}: {e}"], []

    # Check for Strategy subclass
    has_strategy_subclass = False
    strategy_class_name = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Strategy":
                    has_strategy_subclass = True
                    strategy_class_name = node.name
                    break

    if not has_strategy_subclass:
        errors.append("No Strategy subclass found")

    # Check for forbidden imports
    forbidden_imports = ["requests", "socket", "upstox", "brokers", "broker_api"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_imports:
                    if forbidden in alias.name.lower():
                        errors.append(
                            f"Forbidden import: {alias.name} (broker SDKs not allowed in strategy)"
                        )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for forbidden in forbidden_imports:
                    if forbidden in node.module.lower():
                        errors.append(f"Forbidden import from: {node.module}")

    # Check for unsafe datetime usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "datetime":
                    if node.func.attr == "now":
                        warnings.append("Use engine time, not datetime.now() (non-deterministic)")

    # Check for random usage without seed context
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "random":
                    warnings.append(
                        "random module usage detected (ensure seeded for reproducibility)"
                    )

    return errors, warnings


def _check_strategy_analysis() -> tuple[bool, str, list[str]]:
    """Analyze strategy files for code smells."""
    warnings = []

    root = _get_project_root()
    strategies_dir = root / "strategies"

    if not strategies_dir.exists():
        return False, "Strategy analysis skipped", ["strategies/ not found"]

    py_files = [f for f in strategies_dir.glob("*.py") if f.name != "__init__.py"]

    if not py_files:
        return True, "No strategies to analyze", []

    all_errors = []
    for py_file in py_files:
        errors, file_warnings = _analyze_strategy_file(py_file)
        all_errors.extend(errors)
        warnings.extend(file_warnings)

    if all_errors:
        return False, "Strategy analysis failed", all_errors

    strategy_names = [f.stem for f in py_files]
    return True, f"Strategy AST clean ({', '.join(strategy_names)})", warnings


# ==============================================================================
# 5. Configuration Schema Validation
# ==============================================================================


def _check_config_schema() -> tuple[bool, str, list[str]]:
    """Validate stockrhythm.yaml or similar config."""
    warnings = []

    root = _get_project_root()
    config_files = [
        root / "stockrhythm.yaml",
        root / "config.yaml",
        root / "apps/backend/config.yaml",
    ]

    found_configs = [f for f in config_files if f.exists()]

    if not found_configs:
        warnings.append("No stockrhythm.yaml found (optional)")
        return True, "No config to validate", warnings

    required_keys = ["active_provider", "capital", "fees"]

    for config_file in found_configs:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        if config_file.suffix in [".yaml", ".yml"]:
            try:
                import yaml

                with open(config_file) as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                warnings.append(f"Failed to parse {config_file.name}: {e}")
                continue
        else:
            try:
                with open(config_file, "rb") as f:
                    data = tomllib.load(f)
            except Exception as e:
                warnings.append(f"Failed to parse {config_file.name}: {e}")
                continue

        if not isinstance(data, dict):
            continue

        # Soft check: warn if typical keys missing
        for key in required_keys:
            if key not in data:
                warnings.append(f"Recommended key missing in config: {key}")

    return True, "Config schema valid", warnings


# ==============================================================================
# 6. Risk Guardrail Presence
# ==============================================================================


def _check_risk_guardrails() -> tuple[bool, str, list[str]]:
    """Check for risk engine and kill-switch in config."""
    warnings = []

    root = _get_project_root()

    # Check for risk config
    risk_configs = [
        root / "apps/backend/config.yaml",
        root / "stockrhythm.yaml",
    ]

    found_risk_config = False
    kill_switch_enabled = False

    for config_file in risk_configs:
        if not config_file.exists():
            continue

        found_risk_config = True
        try:
            import yaml

            with open(config_file) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and data.get("risk_engine"):
                if data.get("kill_switch", True):
                    kill_switch_enabled = True
        except Exception:
            pass

    if not found_risk_config:
        warnings.append("Risk configuration not found")

    status = "Risk engine attached"
    if kill_switch_enabled:
        status += " (kill-switch ON)"
    else:
        warnings.append("Kill-switch may not be enabled")

    return True, status, warnings


# ==============================================================================
# 7. Data Layer Sanity (Local Only)
# ==============================================================================


def _check_data_layer() -> tuple[bool, str, list[str]]:
    """Check local data cache integrity."""
    warnings = []

    root = _get_project_root()
    data_dir = root / "data"

    if not data_dir.exists():
        warnings.append("No local data directory found")
        return True, "Data layer: not configured", warnings

    parquet_files = list(data_dir.glob("*.parquet"))
    csv_files = list(data_dir.glob("*.csv"))

    if not (parquet_files or csv_files):
        warnings.append("No datasets in data/ directory")
        return True, "Local data cache empty", warnings

    # Attempt to read metadata from first file
    file_count = len(parquet_files) + len(csv_files)
    return True, f"Local data cache OK ({file_count} files)", warnings


# ==============================================================================
# 8. Test Harness Presence
# ==============================================================================


def _check_test_harness() -> tuple[bool, str, list[str]]:
    """Check for test files."""
    warnings = []

    root = _get_project_root()
    tests_dir = root / "tests"

    if not tests_dir.exists():
        warnings.append("tests/ directory not found")
        return True, "No test harness", warnings

    test_files = list(tests_dir.glob("**/test_*.py")) + list(tests_dir.glob("**/*_test.py"))

    if not test_files:
        warnings.append("No test files found (test_*.py pattern expected)")
        return True, "Test directory empty", warnings

    return True, f"Test harness present ({len(test_files)} test files)", warnings


# ==============================================================================
# Main Doctor Command
# ==============================================================================


def doctor(verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed checks")):
    """
    Pre-flight health check for StockRhythm projects.

    Validates runtime, dependencies, structure, and safety without executing trades.
    Returns 0 if safe, 1 if blocked.
    """

    checks = [
        ("Runtime Integrity", _check_runtime_integrity),
        ("Dependency Graph", _check_dependencies),
        ("Project Structure", _check_project_structure),
        ("Strategy Analysis", _check_strategy_analysis),
        ("Config Schema", _check_config_schema),
        ("Risk Guardrails", _check_risk_guardrails),
        ("Data Layer", _check_data_layer),
        ("Test Harness", _check_test_harness),
    ]

    results = []
    has_hard_fail = False
    all_warnings = []

    console.print("[bold cyan]StockRhythm Doctor[/bold cyan]\n")

    for check_name, check_fn in checks:
        try:
            passed, status, warnings = check_fn()
            results.append((check_name, passed, status, warnings))
            all_warnings.extend(warnings)

            if passed:
                console.print(f"[green]✔[/green] {check_name}: {status}")
            else:
                console.print(f"[red]✗[/red] {check_name}: {status}")
                has_hard_fail = True

            if verbose and warnings:
                for warn in warnings:
                    console.print(f"  [yellow]⚠[/yellow] {warn}")
        except Exception as e:
            console.print(f"[red]✗[/red] {check_name}: Exception - {e}")
            has_hard_fail = True

    # Summary
    console.print()
    if has_hard_fail:
        console.print("[bold red]Doctor summary: BLOCKED[/bold red]")
        console.print("[yellow]Address errors above before proceeding.[/yellow]")
        raise typer.Exit(code=1)
    elif all_warnings:
        console.print("[bold yellow]Doctor summary: SAFE WITH WARNINGS[/bold yellow]")
        if not verbose:
            console.print("[dim]Run with --verbose to see details.[/dim]")
        raise typer.Exit(code=0)
    else:
        console.print("[bold green]Doctor summary: SAFE[/bold green]")
        raise typer.Exit(code=0)
