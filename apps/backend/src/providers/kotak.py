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
        self.access_token = api_key.strip() if api_key else ""
        
        # Load other secrets from Environment
        self.mobile = os.getenv("KOTAK_MOBILE", "").strip()
        self.ucc = os.getenv("KOTAK_UCC", "").strip()
        self.mpin = os.getenv("KOTAK_MPIN", "").strip()
        self.totp_secret = os.getenv("KOTAK_TOTP_SECRET", "").strip()
        
        # Auto-format mobile: ensure it starts with +91 if it's a 10-digit Indian number
        if len(self.mobile) == 10 and self.mobile.isdigit():
            self.mobile = f"+91{self.mobile}"
            logger.info(f"Auto-formatted mobile number to {self.mobile}")
        
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
        while True:
            if not self.subscribed_symbols:
                # Wait for symbols to be subscribed via the WebSocket 'configure' action
                await asyncio.sleep(0.5)
                continue

            try:
                # Construct Query
                query_parts = []
                for s in self.subscribed_symbols:
                    # If it's a canonical token (has pipe) or user-constructed string, pass it
                    if "|" in s:
                        query_parts.append(s)
                    # Fallback for raw symbols without pipe -> legacy construction
                    else:
                        query_parts.append(f"nse_cm|{s}-EQ")
                
                query_string = ",".join(query_parts)
                
                # Quotes API Endpoint
                # GET <Base URL>/script-details/1.0/quotes/neosymbol/<query>[,<query>][/<filter_name>]
                # We append '/all' filter as seen in documentation examples
                quote_url = f"{self.base_url}/script-details/1.0/quotes/neosymbol/{query_string}/all"
                
                logger.info(f"Looking up Kotak symbols: {query_string}")
                logger.debug(f"Polling Kotak Quotes: {quote_url}")
                
                headers = {
                    "Authorization": self.access_token,
                    "Content-Type": "application/json"
                }
                
                resp = await self.client.get(quote_url, headers=headers)
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Kotak returns a list of objects. If it returns a dict with 'stat': 'Not_Ok', handle it.
                    if isinstance(data, dict) and data.get("stat") == "Not_Ok":
                        logger.error(f"Kotak API Error: {data.get('emsg')}")
                        continue

                    if not isinstance(data, list):
                        logger.error(f"Unexpected Kotak response format: {data}")
                        continue

                    for item in data:
                        if not isinstance(item, dict):
                            continue
                            
                        # Extract fields safely
                        price = float(item.get("ltp", 0.0))
                        volume = float(item.get("last_volume", 0.0))
                        symbol_name = item.get("display_symbol") or item.get("exchange_token")
                        
                        yield Tick(
                            symbol=str(symbol_name),
                            price=price,
                            volume=volume,
                            timestamp=datetime.now(),
                            provider="kotak"
                        )
                else:
                    logger.error(f"Quote Poll HTTP Error: {resp.status_code} - {resp.text}")

            except Exception as e:
                logger.error(f"Stream Loop Error: {e}")
            
            # Rate Limit Friendly (Doc says 10 req/s, we do 1s poll)
            await asyncio.sleep(1)

    async def historical(
        self,
        symbols: list[str],
        start_at: str,
        end_at: str,
        interval: str | None = None,
    ) -> list[Tick]:
        raise NotImplementedError("Kotak provider does not support historical data for backtesting.")

    @staticmethod
    def _parse_timestamp(value):
        if value is None:
            return datetime.now()
        if isinstance(value, (int, float)):
            # Heuristic: ms vs seconds
            if value > 1_000_000_000_000:
                return datetime.fromtimestamp(value / 1000)
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now()
