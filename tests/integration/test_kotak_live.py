import pytest
import pytest_asyncio
import asyncio
import threading
import uvicorn
import os
from stockrhythm import Strategy, Tick
from apps.backend.src import main
from dotenv import load_dotenv

# Load env vars to ensure we have credentials
load_dotenv()

# We use a unique port for testing to avoid conflicts
TEST_PORT = 8002
TEST_WS_URL = f"ws://127.0.0.1:{TEST_PORT}"

def run_server():
    """Starts the Real Backend Engine in a background thread."""
    # Force the backend to use Kotak for this test run
    main.CONFIG["active_provider"] = "kotak"
    
    # Note: KotakProvider logic inside the backend will read the other 
    # credentials (MPIN, TOTP Secret) directly from os.environ, 
    # which are loaded by load_dotenv() above.
    
    uvicorn.run(main.app, host="127.0.0.1", port=TEST_PORT, log_level="error")

@pytest_asyncio.fixture(scope="module")
async def real_backend():
    """Fixture to spin up the real backend server."""
    access_token = os.getenv("KOTAK_ACCESS_TOKEN")
    if not access_token or access_token == "your_access_token_here":
        pytest.skip("Skipping E2E Test: Real Kotak Credentials not found in .env")

    # Start the server in a daemon thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Give it a moment to boot up
    await asyncio.sleep(2)
    yield
    # Daemon thread will be killed when test process exits

@pytest.mark.asyncio
async def test_reliance_cmp_real_e2e(real_backend):
    """
    E2E Test:
    Strategy -> SDK (Real) -> Network (Real) -> Backend (Real) -> Kotak (Real)
    
    NO MOCKS. This verifies the entire architecture stack.
    """
    
    # 1. Define a simple Strategy using the SDK
    class E2EBot(Strategy):
        def __init__(self):
            super().__init__()
            self.ticks = []
            # Point SDK to our Test Server
            self.client.backend_url = TEST_WS_URL

        async def on_tick(self, tick: Tick):
            print(f"✅ [E2E] REAL TICK RECEIVED: {tick.symbol} @ {tick.price}")
            self.ticks.append(tick)

    # 2. Run the Strategy
    bot = E2EBot()
    
    print("\n[Test] Connecting to Kotak (may take 5-10s for 2-step Auth)...")
    
    # Reliance Industries NSE Token is 2885
    symbol = "nse_cm|2885" 
    
    try:
        # We wrap the infinite loop in a timeout
        await asyncio.wait_for(bot.start(subscribe=[symbol]), timeout=20.0)
    except asyncio.TimeoutError:
        # Expected: The strategy runs forever, so we kill it after 20s
        pass
    except Exception as e:
        pytest.fail(f"Strategy crashed: {e}")

    # 3. Verify Real Data
    assert len(bot.ticks) > 0, "No ticks received from Kotak! Check credentials or market hours."
    
    tick = bot.ticks[0]
    # The returned symbol might be '2885' or 'RELIANCE-EQ'
    assert tick.price > 0
    assert tick.provider == "kotak"
    
    print("\nSUCCESS: Architecture validated with REAL KOTAK DATA.")
