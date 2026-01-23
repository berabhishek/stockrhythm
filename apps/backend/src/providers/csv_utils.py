import csv
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("CsvInstrumentMaster")

class CsvInstrumentMaster:
    """
    A specialized helper for UpstoxProvider to look up ISINs from the instruments CSV.
    Maps symbol -> NSE_EQ|ISIN (or just ISIN if needed).
    """
    def __init__(self, csv_path: str = "data/instruments.csv"):
        self.csv_path = csv_path
        self._symbol_map: Dict[str, str] = {}
        self._loaded = False

    def load(self):
        """Loads the CSV into memory."""
        if self._loaded:
            return

        # Resolve path relative to apps/backend if it's relative
        # Assuming we are running from project root or similar, but safer to anchor
        # to the file location if needed. However, the app runs from root usually.
        # Let's try standard resolution.
        path = Path(self.csv_path)
        if not path.exists():
            # Try to resolve relative to apps/backend
            possible_path = Path("apps/backend") / self.csv_path
            if possible_path.exists():
                path = possible_path
            else:
                logger.warning(f"Instrument master CSV not found at {path} or {possible_path}")
                return

        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    symbol = row.get("symbol", "").upper()
                    isin = row.get("isin", "")
                    
                    # We need valid symbol and ISIN
                    if symbol and isin:
                        # Map SYMBOL -> NSE_EQ|ISIN
                        # Assuming NSE for now as per user context (NSE_EQ|...)
                        self._symbol_map[symbol] = f"NSE_EQ|{isin}"
            
            self._loaded = True
            logger.info(f"Loaded {len(self._symbol_map)} symbols from CSV.")
        except Exception as e:
            logger.error(f"Failed to load instrument CSV: {e}")

    def get_upstox_key(self, symbol: str) -> Optional[str]:
        if not self._loaded:
            self.load()
        return self._symbol_map.get(symbol.upper())
