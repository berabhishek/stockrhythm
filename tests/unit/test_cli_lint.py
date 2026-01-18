from unittest.mock import MagicMock, patch


class TestLintCommand:
    """Test the lint CLI command."""

    def test_lint_command_exists(self):
        """Test that lint command is importable."""
        from stockrhythm_cli.commands.lint import lint

        assert callable(lint)

    def test_lint_command_signature(self):
        """Test lint command has expected parameters."""
        import inspect

        from stockrhythm_cli.commands.lint import lint

        sig = inspect.signature(lint)
        params = list(sig.parameters.keys())
        assert "fix" in params
        assert "path" in params
        assert "show_stats" in params

    def test_lint_without_fix_flag(self):
        """Test lint check without fix flag."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path=".", show_stats=False)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "uv" in call_args
            assert "ruff" in call_args
            assert "check" in call_args
            assert "--fix" not in call_args

    def test_lint_with_fix_flag(self):
        """Test lint with fix flag enabled."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=True, path=".", show_stats=False)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--fix" in call_args

    def test_lint_with_stats_flag(self):
        """Test lint with statistics flag."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path=".", show_stats=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--statistics" in call_args

    def test_lint_with_custom_path(self):
        """Test lint on specific path."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path="packages/", show_stats=False)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "packages/" in call_args

    def test_lint_success_exit_code_zero(self):
        """Test lint success with exit code 0."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path=".", show_stats=False)
            assert result == 0

    def test_lint_issues_found_exit_code_one(self):
        """Test lint with issues found (exit code 1)."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = lint(fix=False, path=".", show_stats=False)
            assert result == 1

    def test_lint_combines_fix_and_stats(self):
        """Test lint with both fix and stats flags."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=True, path=".", show_stats=True)

            call_args = mock_run.call_args[0][0]
            assert "--fix" in call_args
            assert "--statistics" in call_args

    def test_lint_command_includes_uv_run(self):
        """Test that lint command uses uv run."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path=".", show_stats=False)

            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "uv"
            assert call_args[1] == "run"
            assert call_args[2] == "ruff"

    def test_lint_docstring_mentions_f401(self):
        """Test that docstring mentions unused imports."""
        from stockrhythm_cli.commands.lint import lint

        docstring = lint.__doc__
        assert "F401" in docstring
        assert "unused" in docstring.lower()

    def test_lint_docstring_mentions_i001(self):
        """Test that docstring mentions import sorting."""
        from stockrhythm_cli.commands.lint import lint

        docstring = lint.__doc__
        assert "I001" in docstring
        assert "sort" in docstring.lower()

    def test_lint_docstring_mentions_exit_codes(self):
        """Test that docstring documents exit codes."""
        from stockrhythm_cli.commands.lint import lint

        docstring = lint.__doc__
        assert "0" in docstring
        assert "1" in docstring
        assert "exit" in docstring.lower()


class TestLintIntegration:
    """Integration tests for lint command."""

    def test_lint_command_registered_in_cli(self):
        """Test that lint is registered in main CLI app."""
        from stockrhythm_cli.main import app

        # Check that lint command can be accessed through the app
        # Typer apps store commands in a different way
        assert hasattr(app, "__call__")  # App is callable
        assert app is not None  # App exists
        # We can verify lint is in the app by checking main.py imports it
        import stockrhythm_cli.main as main_module

        source = open(main_module.__file__).read()
        assert "lint" in source  # lint is imported/registered in main.py

    def test_lint_output_console_messages(self):
        """Test that lint shows console messages."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("stockrhythm_cli.commands.lint.console.print") as mock_print:
                result = lint(fix=False, path=".", show_stats=False)

                # Should print something
                assert mock_print.call_count >= 1


class TestLintEdgeCases:
    """Test edge cases for lint command."""

    def test_lint_with_empty_path(self):
        """Test lint with empty path (defaults to current dir)."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path=".", show_stats=False)

            call_args = mock_run.call_args[0][0]
            assert "." in call_args

    def test_lint_with_absolute_path(self):
        """Test lint with absolute path."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path="/absolute/path/to/code", show_stats=False)

            call_args = mock_run.call_args[0][0]
            assert "/absolute/path/to/code" in call_args

    def test_lint_subprocess_called_with_list(self):
        """Test that subprocess is called with list of args."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = lint(fix=False, path=".", show_stats=False)

            # subprocess.run should be called with list
            call_args = mock_run.call_args[0][0]
            assert isinstance(call_args, list)
            assert len(call_args) >= 3

    def test_lint_all_options_combined(self):
        """Test lint with all options enabled."""
        from stockrhythm_cli.commands.lint import lint

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = lint(fix=True, path="src/", show_stats=True)

            call_args = mock_run.call_args[0][0]
            assert "src/" in call_args
            assert "--fix" in call_args
            assert "--statistics" in call_args
            assert result == 1
