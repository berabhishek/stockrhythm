import csv
import os
from pathlib import Path
from typing import Dict, Optional

class InstrumentMaster:
    def __init__(self, csv_path: str = "data/instruments.csv"):
        self.csv_path = csv_path
        self._symbol_map: Dict[str, str] = {}
        self._loaded = False

import csv
import os
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("InstrumentMaster")

class InstrumentMaster:
    def __init__(self, csv_path: str = "data/instruments.csv"):
        self.csv_path = csv_path
        self._symbol_map: Dict[str, str] = {}
        self._loaded = False

    def load(self):
        """Loads the CSV into memory."""
        if self._loaded:
            return

        path = Path(self.csv_path)
        if not path.is_absolute():
            # Resolve relative to the app root (apps/backend)
            # Assuming this code is in apps/backend/src, we go up one level
            base_dir = Path(__file__).parent.parent
            path = base_dir / self.csv_path

        if not path.exists():
            logger.warning(f"Instrument master not found at {path}")
            return

        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    symbol = row.get("symbol", "").upper()
                    
                    # New Schema: symbol,exchange,series,isin,nse_scrip_code,bse_code
                    token = row.get("nse_scrip_code")
                    exchange = row.get("exchange", "NSE").lower()
                    
                    # Infer segment from series or default to cm
                    # In new CSV, we are primarily dealing with Equity
                    segment = "cm" 
                    
                    if symbol and token:
                        # Construct the canonical token ID used by Kotak Provider
                        # Format: "exchange_segment|token" e.g. "nse_cm|2885"
                        canonical_id = f"{exchange}_{segment}|{token}"
                        self._symbol_map[symbol] = canonical_id
            
            self._loaded = True
            logger.info(f"Instrument Master loaded {len(self._symbol_map)} symbols.")
        except Exception as e:
            logger.error(f"Failed to load instrument master: {e}")

    def resolve(self, symbol: str) -> Optional[str]:
        """
        Returns the canonical token for a given symbol name.
        e.g. "RELIANCE" -> "nse_cm|2885"
        """
        if not self._loaded:
            self.load()
        return self._symbol_map.get(symbol.upper())
