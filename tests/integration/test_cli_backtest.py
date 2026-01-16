import sqlite3
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


def test_cli_backtest_creates_run(tmp_path, monkeypatch):
    strategy_path = tmp_path / "strategy.py"
    _write_strategy(strategy_path)

    db_path = tmp_path / "backtests.db"
    db = BacktestDB(db_path=str(db_path))
    db.insert_ticks(
        [
            Tick(symbol="TEST", price=99.0, volume=10, timestamp=datetime(2024, 1, 2, 9, 30), provider="test"),
            Tick(symbol="TEST", price=100.0, volume=12, timestamp=datetime(2024, 1, 2, 9, 31), provider="test"),
        ]
    )

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run",
            "--backtest",
            "--file",
            str(strategy_path),
            "--start",
            "2024-01-02T09:30:00",
            "--end",
            "2024-01-02T09:31:00",
            "--db-path",
            str(db_path),
            "--name",
            "cli-run",
            "--symbol",
            "TEST",
        ],
    )

    assert result.exit_code == 0
    assert "Backtest completed. Run ID:" in result.stdout

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name, status FROM backtest_runs")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "cli-run"
    assert row[1] == "completed"
