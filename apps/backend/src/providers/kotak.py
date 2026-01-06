from .base import MarketDataProvider
from stockrhythm.models import Tick
from datetime import datetime
import os
import httpx
import pyotp
import asyncio
import logging

logger = logging.getLogger("KotakProvider")

class KotakProvider(MarketDataProvider):
    def __init__(self, api_key: str):
        # API Key is the "Access Token" from NEO Dashboard
        self.access_token = api_key
        
        # Load other secrets from Environment
        self.mobile = os.getenv("KOTAK_MOBILE")
        self.ucc = os.getenv("KOTAK_UCC") # Client Code
        self.mpin = os.getenv("KOTAK_MPIN")
        self.totp_secret = os.getenv("KOTAK_TOTP_SECRET") # Base32 Secret
        
        if not all([self.mobile, self.ucc, self.mpin, self.totp_secret]):
            logger.warning("Missing Kotak Credentials in Environment (KOTAK_MOBILE, KOTAK_UCC, KOTAK_MPIN, KOTAK_TOTP_SECRET)")

        self.client = httpx.AsyncClient(timeout=10.0)
        self.session_token = None
        self.session_sid = None
        self.base_url = "https://mis.kotaksecurities.com" # Default, updated after login
        
        self.subscribed_symbols = []

    async def connect(self):
        """
        Executes the 2-Step Auth Flow:
        1. TOTP Login -> View Token
        2. MPIN Validate -> Session Token
        """
        logger.info("Connecting to Kotak Securities...")
        
        # Step 1: Login with TOTP
        try:
            totp_now = pyotp.TOTP(self.totp_secret).now()
        except Exception as e:
            raise ValueError(f"Failed to generate TOTP. Check KOTAK_TOTP_SECRET. Error: {e}")

        login_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiLogin"
        headers_step1 = {
            "Authorization": self.access_token,
            "neo-fin-key": "neotradeapi",
            "Content-Type": "application/json"
        }
        body_step1 = {
            "mobileNumber": self.mobile,
            "ucc": self.ucc,
            "totp": totp_now
        }
        
        resp1 = await self.client.post(login_url, headers=headers_step1, json=body_step1)
        if resp1.status_code != 200:
            raise ConnectionError(f"Kotak Login Step 1 Failed: {resp1.text}")
            
        data1 = resp1.json()["data"]
        view_token = data1["token"]
        view_sid = data1["sid"]
        
        # Step 2: Validate MPIN
        validate_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate"
        headers_step2 = {
            "Authorization": self.access_token,
            "neo-fin-key": "neotradeapi",
            "sid": view_sid,
            "Auth": view_token,
            "Content-Type": "application/json"
        }
        body_step2 = {"mpin": self.mpin}
        
        resp2 = await self.client.post(validate_url, headers=headers_step2, json=body_step2)
        if resp2.status_code != 200:
            raise ConnectionError(f"Kotak Login Step 2 Failed: {resp2.text}")

        data2 = resp2.json()["data"]
        
        # Store Session Credentials
        self.session_token = data2["token"]
        self.session_sid = data2["sid"]
        self.base_url = data2.get("baseUrl", self.base_url)
        
        logger.info(f"Connected to Kotak. Base URL: {self.base_url}")

    async def subscribe(self, symbols: list[str]):
        """
        Kotak REST API doesn't have a 'subscribe' call, we just track symbols 
        to poll in the stream loop.
        """
        # Ensure symbols are formatted correctly (e.g., "nse_cm|RELIANCE-EQ")
        # If user passes just "RELIANCE", we might default to "nse_cm|RELIANCE-EQ"
        self.subscribed_symbols = symbols
        logger.info(f"Subscribed to: {symbols}")

    async def stream(self):
        """
        Polls the Quotes API for all subscribed symbols.
        """
        if not self.subscribed_symbols:
            logger.warning("No symbols subscribed.")
            while True: await asyncio.sleep(1)

        # Helper to format symbol for Query
        # Input: "RELIANCE" -> Output: "nse_cm|RELIANCE-EQ" (Naive assumption for demo)
        # Better: User should pass full format "nse_cm|RELIANCE-EQ"
        
        while True:
            try:
                # Construct Query
                # API format: nse_cm|Nifty 50,nse_cm|RELIANCE-EQ
                # We assume the user passes correct strings or we fix them simply
                query_parts = []
                for s in self.subscribed_symbols:
                    if "|" not in s:
                         query_parts.append(f"nse_cm|{s}-EQ") # Default to NSE Equity
                    else:
                        query_parts.append(s)
                
                query_string = ",".join(query_parts)
                
                # Quotes API Endpoint
                # GET <Base URL>/script-details/1.0/quotes/neosymbol/<query>
                # Headers: Authorization ONLY (Access Token)
                # The doc example: .../quotes/neosymbol/nse_cm|Nifty 50,nse_cm|Nifty Bank/all
                quote_url = f"{self.base_url}/script-details/1.0/quotes/neosymbol/{query_string}"
                
                headers = {
                    "Authorization": self.access_token,
                    "Content-Type": "application/json"
                }
                
                resp = await self.client.get(quote_url, headers=headers)
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Response is a list of quote objects
                    for item in data:
                        # Extract fields
                        price = float(item.get("ltp", 0.0))
                        volume = float(item.get("last_volume", 0.0))
                        # item['exchange_token'] might be "RELIANCE-EQ" or "1234"
                        symbol_name = item.get("display_symbol") or item.get("exchange_token")
                        
                        yield Tick(
                            symbol=symbol_name,
                            price=price,
                            volume=volume,
                            timestamp=datetime.now(),
                            provider="kotak"
                        )
                else:
                    logger.error(f"Quote Poll Error: {resp.status_code} - {resp.text}")

            except Exception as e:
                logger.error(f"Stream Loop Error: {e}")
            
            # Rate Limit Friendly (Doc says 10 req/s, we do 1s poll)
            await asyncio.sleep(1)
