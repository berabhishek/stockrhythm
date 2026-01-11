import pytest
import shutil
from pathlib import Path
from typer.testing import CliRunner
from stockrhythm_cli.main import app
from stockrhythm.strategy import Strategy, Tick
from stockrhythm.models import Order
from unittest.mock import AsyncMock, patch

runner = CliRunner()

class TestEndToEnd:
    @pytest.fixture
    def clean_env(self):
        # Setup: Remove any existing test bot
        bot_name = "e2e_test_bot"
        if Path(bot_name).exists():
            shutil.rmtree(bot_name)
        yield bot_name
        # Teardown
        if Path(bot_name).exists():
            shutil.rmtree(bot_name)

    def test_cli_init_flow(self, clean_env):
        """
        E2E Step 1: User runs 'stockrhythm init <name>'
        Expectation: Folder created with strategy.py and requirements.txt
        """
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["init", clean_env])
            assert result.exit_code == 0
            assert "Initialized StockRhythm project" in result.stdout
            assert f"cd {clean_env}" in result.stdout

            path = Path(clean_env)
            assert path.exists()
            assert (path / "strategies" / "strategy.py").exists()
            assert (path / "requirements.txt").exists()

    @pytest.mark.asyncio
    async def test_strategy_logic_flow(self):
        """
        E2E Step 2: Strategy connects, receives Tick, places Order.
        We simulate the Network Layer (EngineClient) to focus on the User Logic.
        """
        # 1. Define a user strategy (similar to what init produces)
        class MyStrategy(Strategy):
            async def on_tick(self, tick: Tick):
                if tick.price < 100:
                    await self.buy(tick.symbol, 10)

        strategy = MyStrategy()
        
        # 2. Mock the Client (Network Layer)
        strategy.client = AsyncMock()
        
        # 3. Simulate incoming Tick
        test_tick = Tick(
            symbol="AAPL", 
            price=99.0, # < 100, triggers buy
            volume=100, 
            timestamp="2023-01-01T00:00:00", 
            provider="mock"
        )

        # 4. Trigger the callback directly (Simulating the Event Loop)
        await strategy.on_tick(test_tick)

        # 5. Assert Order was submitted
        strategy.client.submit_order.assert_called_once()
        submitted_order = strategy.client.submit_order.call_args[0][0]
        
        assert isinstance(submitted_order, Order)
        assert submitted_order.symbol == "AAPL"
        assert submitted_order.qty == 10
        assert submitted_order.side == "BUY"
