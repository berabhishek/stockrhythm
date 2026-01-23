import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path to allow imports from apps.backend
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from apps.backend.src.providers.upstox import UpstoxProvider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    print("Initializing UpstoxProvider...")
    # UpstoxProvider reads from env vars by default: UPSTOX_API_KEY, UPSTOX_ACCESS_TOKEN
    provider = UpstoxProvider()

    print("Checking for credentials...")
    if not provider.access_token:
        print("ERROR: UPSTOX_ACCESS_TOKEN is not set in environment.")
        print("Please set UPSTOX_API_KEY, UPSTOX_API_SECRET, UPSTOX_AUTH_CODE, UPSTOX_REDIRECT_URI or UPSTOX_ACCESS_TOKEN.")
        return

    print("Credentials found (or at least token is present).")
    
    symbols = ["RELIANCE", "TCS"]
    start_at = "2024-01-01"
    end_at = "2024-01-02"
    
    print(f"Fetching historical data for {symbols} from {start_at} to {end_at}...")
    try:
        ticks = await provider.historical(
            symbols=symbols,
            start_at=start_at,
            end_at=end_at,
            interval="day"
        )
        
        print(f"Successfully fetched {len(ticks)} ticks.")
        for tick in ticks[:5]:
            print(f"  {tick}")
        if len(ticks) > 5:
            print("  ...")

    except Exception as e:
        print(f"Failed to fetch historical data: {e}")

if __name__ == "__main__":
    asyncio.run(main())
