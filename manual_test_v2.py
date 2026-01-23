import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to sys.path to allow imports from apps.backend
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from apps.backend.src.providers.upstox import UpstoxProvider

async def main():
    print("--- Manual Test V2: Upstox Provider ---")
    
    # Initialize provider - it will read from env vars automatically
    provider = UpstoxProvider()

    print("Checking Credentials...")
    if not provider.api_key:
         print("WARNING: UPSTOX_API_KEY is missing.")
    if not provider.access_token:
         print("WARNING: UPSTOX_ACCESS_TOKEN is missing.")
    
    if not provider.access_token and not (provider.api_key and provider.api_secret):
        print("CRITICAL: No access token and no API key/secret found. Test will likely fail.")
    else:
        print("Credentials appear to be present (or partially present).")

    symbols = ["NSE_EQ|INE848E01016"] # RELIANCE
    start_at = "2024-01-02"
    end_at = "2024-01-03"
    
    print(f"Attempting to fetch historical data for {symbols}...")
    try:
        ticks = await provider.historical(
            symbols=symbols,
            start_at=start_at,
            end_at=end_at,
            interval="day"
        )
        
        print(f"Success! Fetched {len(ticks)} ticks.")
        for tick in ticks:
            print(f"  {tick}")

    except Exception as e:
        print(f"Error fetching data: {e}")
        # Print full traceback for debugging if needed, but keeping it simple for now
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
