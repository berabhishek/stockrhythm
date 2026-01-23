import asyncio
import logging
import os
from datetime import datetime
from urllib.parse import quote

import httpx

from stockrhythm.models import Tick

from ..auth_store import AuthStore
from ..upstox_auth import exchange_auth_code
from .base import MarketDataProvider
from .csv_utils import CsvInstrumentMaster

logger = logging.getLogger("UpstoxProvider")


class UpstoxProvider(MarketDataProvider):
    def __init__(
        self,
        api_key: str | None = None,
        token: str | None = None,
        api_secret: str | None = None,
        auth_store: AuthStore | None = None,
    ):
        self.api_key = (api_key or os.getenv("UPSTOX_API_KEY", "")).strip()
        self.api_secret = (api_secret or os.getenv("UPSTOX_API_SECRET", "")).strip()
        self.access_token = (token or os.getenv("UPSTOX_ACCESS_TOKEN", "")).strip()
        self.auth_code = os.getenv("UPSTOX_AUTH_CODE", "").strip()
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI", "").strip()
        self.auth_store = auth_store
        
        # Helper to resolve SYMBOL -> NSE_EQ|ISIN
        self.instrument_master = CsvInstrumentMaster()

        if not self.api_key or not self.api_secret:
            logger.warning(
                "Missing Upstox credentials in environment (UPSTOX_API_KEY, UPSTOX_API_SECRET)."
            )

        self.client = httpx.AsyncClient(timeout=10.0)
        self.base_url = "https://api.upstox.com/v2"
        self.subscribed_symbols: list[str] = []

    async def connect(self):
        """
        Initializes the session by ensuring an access token is available.
        If no access token is set, tries to exchange auth code for one.
        """
        if self.access_token:
            if self.auth_store and not self.auth_store.get_valid_upstox_token():
                self.auth_store.save_upstox_token(self.access_token)
            return

        if not self.access_token and self.auth_store:
            self.access_token = self.auth_store.get_valid_upstox_token() or ""

        if not self.access_token:
            await self._exchange_auth_code()

        if not self.access_token:
            raise ValueError(
                "Missing Upstox access token. Visit /upstox/auth on the backend "
                "or set UPSTOX_ACCESS_TOKEN. You can also provide UPSTOX_AUTH_CODE "
                "and UPSTOX_REDIRECT_URI to exchange via API key/secret."
            )

        logger.info("Connected to Upstox.")

    async def subscribe(self, symbols: list[str]):
        self.subscribed_symbols = symbols
        logger.info(f"Subscribed to: {symbols}")

    async def stream(self):
        """
        Polls Upstox Market Quote endpoint for subscribed symbols.
        """
        while True:
            if not self.subscribed_symbols:
                await asyncio.sleep(0.5)
                continue

            try:
                instrument_keys = [
                    self._normalize_symbol(symbol) for symbol in self.subscribed_symbols
                ]
                query = ",".join(instrument_keys)
                quote_url = f"{self.base_url}/market-quote/ltp"

                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }

                resp = await self.client.get(
                    quote_url, headers=headers, params={"instrument_key": query}
                )

                if resp.status_code != 200:
                    logger.error(f"Upstox Quote Error: {resp.status_code} - {resp.text}")
                    await asyncio.sleep(1)
                    continue

                payload = resp.json()
                data = payload.get("data", payload)

                if not isinstance(data, dict):
                    logger.error(f"Unexpected Upstox response format: {payload}")
                    await asyncio.sleep(1)
                    continue

                for instrument_key, item in data.items():
                    if not isinstance(item, dict):
                        continue

                    price = self._parse_price(item)
                    volume = float(item.get("volume") or item.get("volume_traded") or 0.0)
                    timestamp = self._parse_timestamp(
                        item.get("exchange_timestamp")
                        or item.get("last_trade_time")
                        or item.get("timestamp")
                    )
                    symbol_name = item.get("symbol") or item.get("instrument_key") or instrument_key

                    yield Tick(
                        symbol=str(symbol_name),
                        price=price,
                        volume=volume,
                        timestamp=timestamp,
                        provider="upstox",
                    )
            except Exception as e:
                logger.error(f"Stream Loop Error: {e}")

            await asyncio.sleep(1)

    async def historical(
        self,
        symbols: list[str],
        start_at: str,
        end_at: str,
        interval: str | None = None,
    ) -> list[Tick]:
        if not self.access_token:
            await self.connect()

        # Helper to ensure YYYY-MM-DD
        def _fmt_date(d: str) -> str:
            if "T" in d:
                return d.split("T")[0]
            return d

        start_date = _fmt_date(start_at)
        end_date = _fmt_date(end_at)

        interval_segment = self._format_interval(interval)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        ticks: list[Tick] = []
        for symbol in symbols:
            # Try to resolve symbol to instrument_key using CSV master
            # e.g. "SBIN" -> "NSE_EQ|INE062A01020"
            resolved_key = self.instrument_master.get_upstox_key(symbol)
            
            if not resolved_key:
                # If lookup fails, maybe user passed "NSE_EQ|..." directly
                instrument_key = self._normalize_symbol(symbol)
            else:
                instrument_key = resolved_key

            encoded_key = quote(instrument_key, safe="")
            url = (
                f"{self.base_url}/historical-candle/"
                f"{encoded_key}/{interval_segment}/{end_date}/{start_date}"
            )
            resp = await self.client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Upstox historical error: {resp.status_code} - {resp.text}")
                continue

            payload = resp.json()
            data = payload.get("data", payload)
            candles = data.get("candles", []) if isinstance(data, dict) else []

            for candle in candles:
                if not isinstance(candle, (list, tuple)) or len(candle) < 5:
                    continue
                timestamp = self._parse_timestamp(candle[0])
                close_price = float(candle[4])
                volume = float(candle[5]) if len(candle) > 5 and candle[5] is not None else 0.0
                ticks.append(
                    Tick(
                        symbol=str(symbol),
                        price=close_price,
                        volume=volume,
                        timestamp=timestamp,
                        provider="upstox",
                    )
                )

        return ticks

    async def _exchange_auth_code(self):
        if not (self.api_key and self.api_secret and self.auth_code and self.redirect_uri):
            return

        try:
            payload = await exchange_auth_code(
                api_key=self.api_key,
                api_secret=self.api_secret,
                auth_code=self.auth_code,
                redirect_uri=self.redirect_uri,
            )
        except Exception as exc:
            logger.error(f"Upstox token exchange failed: {exc}")
            return

        self.access_token = str(payload.get("access_token", "")).strip()
        if not self.access_token:
            logger.error("Upstox token exchange succeeded but access_token is missing.")
            return

        if self.auth_store:
            self.auth_store.save_upstox_token(
                self.access_token,
                expires_in=payload.get("expires_in"),
                refresh_token=payload.get("refresh_token"),
            )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        if "|" in symbol:
            return symbol
        return f"NSE_EQ|{symbol}"

    @staticmethod
    def _parse_price(item: dict) -> float:
        for key in ("last_price", "ltp", "close", "last_traded_price"):
            if key in item and item[key] is not None:
                return float(item[key])
        return 0.0

    @staticmethod
    def _format_interval(interval: str | None) -> str:
        if not interval:
            return "1minute"
        if "/" in interval:
            unit, multiplier = interval.split("/", 1)
            unit = unit.strip().lower()
            multiplier = multiplier.strip()
            if multiplier.isdigit():
                return UpstoxProvider._format_interval(f"{multiplier}{unit[0]}")
            return interval
        value = interval.strip().lower()
        if value.endswith("m") and value[:-1].isdigit():
            return f"{value[:-1]}minute"
        if value.endswith("h") and value[:-1].isdigit():
            return f"{value[:-1]}hour"
        if value.endswith("d") and value[:-1].isdigit():
            return "day" if value[:-1] == "1" else f"{value[:-1]}day"
        if value in ("day", "week", "month"):
            return value
        return value

    @staticmethod
    def _parse_timestamp(value):
        if value is None:
            return datetime.now()
        if isinstance(value, (int, float)):
            if value > 1_000_000_000_000:
                return datetime.fromtimestamp(value / 1000)
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now()
