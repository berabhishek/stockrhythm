from datetime import datetime
from typer.testing import CliRunner

from stockrhythm import BacktestDB, Tick
from stockrhythm_cli.main import app


def _write_strategy(path):
    path.write_text(
        "\n".join(
            [
                "from stockrhythm import Strategy, Tick",
                "",
                "class MyStrategy(Strategy):",
                "    def __init__(self, paper_trade=True):",
                "        super().__init__(paper_trade=paper_trade)",
                "        self.seen = 0",
                "",
                "    async def on_tick(self, tick: Tick):",
                "        self.seen += 1",
                "",
                "def get_strategy(paper_trade: bool = True):",
                "    return MyStrategy(paper_trade=paper_trade)",
                "",
            ]
        )
        + "\n"
    )


def _seed_ticks(db_path):
    db = BacktestDB(db_path=str(db_path))
    db.insert_ticks(
        [
            Tick(symbol="TEST", price=99.0, volume=10, timestamp=datetime(2024, 1, 2, 9, 30), provider="test"),
            Tick(symbol="TEST", price=100.0, volume=12, timestamp=datetime(2024, 1, 2, 9, 31), provider="test"),
        ]
    )


def test_run_backtest_prompts_for_missing_args(tmp_path, monkeypatch):
    strategy_path = tmp_path / "strategy.py"
    _write_strategy(strategy_path)
    _seed_ticks(tmp_path / "backtests.db")

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    input_text = "\n".join(
        [
            str(strategy_path),
            "2024-01-02T09:30:00",
            "2024-01-02T09:31:00",
            "",
        ]
    )
    result = runner.invoke(app, ["run", "--backtest"], input=input_text)

    assert result.exit_code == 0
    assert "Backtest completed. Run ID:" in result.stdout
