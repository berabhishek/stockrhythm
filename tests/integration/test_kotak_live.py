import pytest
from fastapi.testclient import TestClient
from apps.backend.src import main
from dotenv import load_dotenv
import os

# Load environment to ensure the backend starts with the correct config (e.g. STOCKRHYTHM_PROVIDER=kotak)
load_dotenv()

def test_get_reliance_cmp_blackbox():
    """
    Black-box Integration Test.
    
    Scenario:
    1. A Client (Strategy) connects to the Backend.
    2. Client requests market data for 'RELIANCE'.
    3. Backend (Abstract Layer) handles all Kotak Auth/Polling internally.
    4. Client receives a normalized Tick with the price.
    
    This confirms the Backend correctly abstracts the 'Kotak Auth Lifecycle' 
    and 'Data Streaming' from the trading logic.
    """
    
    # We expect the .env file to be set up by the user as per previous instructions.
    # If STOCKRHYTHM_PROVIDER is not 'kotak', this test might run against Mock,
    # which is also valid for testing the *abstraction*, but strictly we want to see Kotak data here.
    
    with TestClient(main.app) as client:
        # 1. Connect (Triggers Backend -> Kotak Auth Flow)
        with client.websocket_connect("/") as websocket:
            
            # 2. Subscribe (Client asks for data)
            # The backend normalizes this request to the provider's specific format if needed
            requested_symbol = "nse_cm|RELIANCE-EQ"
            websocket.send_json({
                "action": "subscribe", 
                "symbols": [requested_symbol]
            })
            
            # 3. Receive Data (Client receives normalized Tick)
            # We assume the first message is the tick. In a real scenario, we might skip status messages.
            data = websocket.receive_json()
            
            # 4. Verify Behavior (Trading Logic)
            # The strategy only cares that it got a price for the symbol it asked for.
            print(f"\n✅ [TEST OUTPUT] CMP of {data['symbol']}: {data['price']}")
            
            assert "RELIANCE" in data["symbol"], "Backend returned wrong symbol"
            assert data["price"] > 0, "Backend returned invalid price (0 or negative)"
            assert isinstance(data["price"], float), "Price should be a float"
