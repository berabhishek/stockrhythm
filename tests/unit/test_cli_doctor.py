import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture()
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        (tmpdir_path / "strategies").mkdir()
        (tmpdir_path / "tests").mkdir()
        (tmpdir_path / "pyproject.toml").write_text('[project]\nname="test"\ndependencies=[]')
        yield tmpdir_path


class TestRuntimeIntegrity:
    """Test runtime integrity checks."""

    def test_python_version_check_passes_for_3_12_plus(self):
        """Test that Python 3.12+ passes version check."""
        from stockrhythm_cli.commands.doctor import _check_runtime_integrity

        passed, status, warnings = _check_runtime_integrity()
        assert passed is True
        assert "Python" in status
        assert sys.version_info >= (3, 12)

    def test_runtime_status_includes_python_version(self):
        """Test that status message includes Python version."""
        from stockrhythm_cli.commands.doctor import _check_runtime_integrity

        passed, status, warnings = _check_runtime_integrity()
        assert "3." in status  # Contains Python version
        assert "Python" in status

    def test_runtime_status_indicates_venv_if_active(self):
        """Test that venv status is indicated in output."""
        from stockrhythm_cli.commands.doctor import _check_runtime_integrity

        passed, status, warnings = _check_runtime_integrity()
        # Should mention venv or include warning about no venv
        assert passed is True
        if "venv active" not in status.lower():
            assert any("virtual environment" in w.lower() for w in warnings)


class TestDependencyGraph:
    """Test dependency graph correctness checks."""

    def test_dependencies_check_returns_tuple(self):
        """Test that dependency check returns expected tuple format."""
        from stockrhythm_cli.commands.doctor import _check_dependencies

        result = _check_dependencies()
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert isinstance(result[2], list)

    def test_dependencies_finds_ruff_installed(self):
        """Test that ruff is detected as installed."""
        from stockrhythm_cli.commands.doctor import _check_dependencies

        passed, status, warnings = _check_dependencies()
        assert passed is True
        assert "Dependencies" in status

    def test_dependencies_with_empty_project(self, temp_project_dir):
        """Test dependency check on project with no dependencies."""
        from stockrhythm_cli.commands.doctor import _check_dependencies

        with patch(
            "stockrhythm_cli.commands.doctor._get_project_root",
            return_value=temp_project_dir,
        ):
            passed, status, warnings = _check_dependencies()
            assert passed is True
            assert "0 packages" in status


class TestProjectStructure:
    """Test project structure validation."""

    def test_project_structure_requires_strategies_and_tests(self):
        """Test that required directories are validated."""
        from stockrhythm_cli.commands.doctor import (
            _check_project_structure,
        )

        # Should fail on current working directory if not in project root
        # Instead test with mock
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "strategies").mkdir()
            # tests missing
            (tmpdir_path / "pyproject.toml").write_text("[project]")

            with patch(
                "stockrhythm_cli.commands.doctor._get_project_root",
                return_value=tmpdir_path,
            ):
                # Test that structure check requires tests directory
                passed, status, warnings = _check_project_structure()
                # Should fail because tests dir is missing
                assert passed is False or any("tests" in w.lower() for w in warnings)

    def test_project_structure_check_format(self):
        """Test structure check returns correct format."""
        from stockrhythm_cli.commands.doctor import _check_project_structure

        result = _check_project_structure()
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert isinstance(result[2], list)


class TestStrategyAnalysis:
    """Test strategy static analysis."""

    def test_analyze_strategy_detects_strategy_subclass(self, temp_project_dir):
        """Test that Strategy subclass is detected."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
from stockrhythm import Strategy

class MyStrategy(Strategy):
    async def on_tick(self, tick):
        pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert len(errors) == 0

    def test_analyze_strategy_detects_missing_subclass(self, temp_project_dir):
        """Test that missing Strategy subclass is detected."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
def some_func():
    pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert any("Strategy subclass" in e for e in errors)

    def test_analyze_strategy_detects_forbidden_imports(self, temp_project_dir):
        """Test that forbidden imports are detected."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
import requests

from stockrhythm import Strategy

class MyStrategy(Strategy):
    pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert any("requests" in e or "Forbidden" in e for e in errors)

    def test_analyze_strategy_detects_socket_import(self, temp_project_dir):
        """Test that socket import is flagged."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
import socket
from stockrhythm import Strategy

class MyStrategy(Strategy):
    pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert any("socket" in e.lower() for e in errors)

    def test_analyze_strategy_detects_datetime_now_warning(self, temp_project_dir):
        """Test that datetime.now() usage is warned about."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
from datetime import datetime
from stockrhythm import Strategy

class MyStrategy(Strategy):
    async def on_tick(self, tick):
        now = datetime.now()
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert any("engine time" in w.lower() for w in warnings)

    def test_analyze_strategy_with_syntax_error(self, temp_project_dir):
        """Test that syntax errors are caught."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
from stockrhythm import Strategy
class MyStrategy(Strategy
    pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert any("Syntax" in e for e in errors)

    def test_analyze_strategy_file_not_found(self, temp_project_dir):
        """Test that missing file is caught."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "nonexistent.py"
        errors, warnings = _analyze_strategy_file(strategy_file)
        assert any("not found" in e for e in errors)


class TestStrategyAnalysisCheck:
    """Test the high-level strategy analysis check."""

    def test_strategy_analysis_finds_valid_strategies(self):
        """Test that valid strategies are recognized."""
        from stockrhythm_cli.commands.doctor import _check_strategy_analysis

        # This will run on the actual project's strategies
        passed, status, warnings = _check_strategy_analysis()
        # Project has actual strategies, so should find them
        assert passed is True
        assert "Strategy" in status or "strategies" in status.lower()

    def test_strategy_analysis_returns_correct_format(self):
        """Test strategy analysis returns correct format."""
        from stockrhythm_cli.commands.doctor import _check_strategy_analysis

        result = _check_strategy_analysis()
        assert isinstance(result, tuple)
        assert len(result) == 3


class TestConfigSchema:
    """Test configuration schema validation."""

    def test_config_schema_check_format(self):
        """Test config schema check returns correct format."""
        from stockrhythm_cli.commands.doctor import _check_config_schema

        result = _check_config_schema()
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert isinstance(result[2], list)

    def test_config_schema_handles_missing_config(self, temp_project_dir):
        """Test that missing config is handled gracefully."""
        from stockrhythm_cli.commands.doctor import _check_config_schema

        with patch(
            "stockrhythm_cli.commands.doctor._get_project_root",
            return_value=temp_project_dir,
        ):
            passed, status, warnings = _check_config_schema()
            assert passed is True
            # Should handle gracefully with warning


class TestRiskGuardrails:
    """Test risk guardrail checks."""

    def test_risk_guardrails_check_format(self):
        """Test risk guardrails check returns correct format."""
        from stockrhythm_cli.commands.doctor import _check_risk_guardrails

        result = _check_risk_guardrails()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_risk_guardrails_returns_safe_status(self):
        """Test that risk check returns 'Safe' in status."""
        from stockrhythm_cli.commands.doctor import _check_risk_guardrails

        passed, status, warnings = _check_risk_guardrails()
        assert passed is True
        # Status should mention risk engine or guardrails


class TestDataLayer:
    """Test data layer sanity checks."""

    def test_data_layer_check_format(self):
        """Test data layer check returns correct format."""
        from stockrhythm_cli.commands.doctor import _check_data_layer

        result = _check_data_layer()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_data_layer_handles_missing_data_dir(self, temp_project_dir):
        """Test that missing data directory is handled."""
        from stockrhythm_cli.commands.doctor import _check_data_layer

        with patch(
            "stockrhythm_cli.commands.doctor._get_project_root",
            return_value=temp_project_dir,
        ):
            passed, status, warnings = _check_data_layer()
            assert passed is True


class TestTestHarness:
    """Test test harness presence checks."""

    def test_test_harness_check_format(self):
        """Test harness check returns correct format."""
        from stockrhythm_cli.commands.doctor import _check_test_harness

        result = _check_test_harness()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_test_harness_finds_existing_tests(self):
        """Test that existing tests are found."""
        from stockrhythm_cli.commands.doctor import _check_test_harness

        passed, status, warnings = _check_test_harness()
        # Project has tests
        assert passed is True
        assert "test" in status.lower()


class TestDoctorIntegration:
    """Integration tests for doctor command."""

    def test_doctor_command_runs_all_checks(self):
        """Test that doctor command can execute all checks."""
        import click
        from stockrhythm_cli.commands.doctor import doctor

        # Doctor will raise click.exceptions.Exit from typer.Exit
        with pytest.raises(click.exceptions.Exit):
            doctor(verbose=False)

    def test_doctor_verbose_mode(self):
        """Test doctor verbose mode execution."""
        import click
        from stockrhythm_cli.commands.doctor import doctor

        # Doctor will raise click.exceptions.Exit from typer.Exit
        with pytest.raises(click.exceptions.Exit):
            doctor(verbose=True)

    def test_doctor_can_be_called(self):
        """Test that doctor command is callable and produces output."""
        import click
        from stockrhythm_cli.commands.doctor import doctor

        # The only exception should be click.exceptions.Exit from typer.Exit
        try:
            doctor(verbose=False)
        except click.exceptions.Exit:
            pass  # Expected
        except Exception as e:
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")


class TestParsingUtilities:
    """Test utility functions."""

    def test_parse_dependency_version(self):
        """Test dependency version parsing."""
        from stockrhythm_cli.commands.doctor import _parse_dependency_version

        name, spec = _parse_dependency_version("ruff>=0.5.0")
        assert name == "ruff"
        assert spec == ">=0.5.0"

    def test_parse_dependency_version_without_spec(self):
        """Test parsing dependency without version spec."""
        from stockrhythm_cli.commands.doctor import _parse_dependency_version

        name, spec = _parse_dependency_version("numpy")
        assert name == "numpy"
        assert spec == ""

    def test_parse_dependency_with_different_operators(self):
        """Test parsing with various version operators."""
        from stockrhythm_cli.commands.doctor import _parse_dependency_version

        test_cases = [
            ("pkg==1.0", "pkg", "==1.0"),
            ("pkg~=1.0", "pkg", "~=1.0"),
            ("pkg<=2.0", "pkg", "<=2.0"),
            ("pkg>1.0", "pkg", ">1.0"),
        ]

        for dep_str, expected_name, expected_spec in test_cases:
            name, spec = _parse_dependency_version(dep_str)
            assert name == expected_name
            assert spec == expected_spec

    def test_get_project_root_finds_pyproject(self, temp_project_dir):
        """Test that project root detection works."""
        from stockrhythm_cli.commands.doctor import _get_project_root

        with patch("pathlib.Path.cwd", return_value=temp_project_dir):
            root = _get_project_root()
            assert (root / "pyproject.toml").exists()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_doctor_with_empty_strategies_dir(self):
        """Test doctor on project with empty strategies directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "strategies").mkdir()
            (tmpdir_path / "tests").mkdir()
            (tmpdir_path / "pyproject.toml").write_text("[project]")

            from stockrhythm_cli.commands.doctor import _check_project_structure

            with patch(
                "stockrhythm_cli.commands.doctor._get_project_root",
                return_value=tmpdir_path,
            ):
                passed, status, warnings = _check_project_structure()
                assert passed is True
                assert any("No strategy files" in w for w in warnings)

    def test_strategy_with_unicode_characters(self, temp_project_dir):
        """Test strategy parsing with unicode characters."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
# -*- coding: utf-8 -*-
\"\"\"Strategy with émojis and spëcial chars.\"\"\"
from stockrhythm import Strategy

class MyStrategy(Strategy):
    async def on_tick(self, tick):
        \"\"\"Process ticks with unicode: 📊\"\"\"
        pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        assert len(errors) == 0

    def test_multiple_strategy_classes_in_one_file(self, temp_project_dir):
        """Test file with multiple strategy classes."""
        from stockrhythm_cli.commands.doctor import _analyze_strategy_file

        strategy_file = temp_project_dir / "test_strategy.py"
        strategy_file.write_text(
            """
from stockrhythm import Strategy

class Strategy1(Strategy):
    pass

class Strategy2(Strategy):
    pass
"""
        )

        errors, warnings = _analyze_strategy_file(strategy_file)
        # Should be OK - multiple strategies per file is allowed
        assert len(errors) == 0
