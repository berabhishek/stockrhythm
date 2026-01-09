import csv
import gzip
import urllib.request
import io
import os

# Upstox Public Instrument Files
NSE_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
BSE_URL = "https://assets.upstox.com/market-quote/instruments/exchange/BSE.csv.gz"

OUTPUT_PATH = "apps/backend/data/instruments.csv"

def download_and_parse(url):
    print(f"Downloading {url}...")
    response = urllib.request.urlopen(url)
    compressed_file = io.BytesIO(response.read())
    decompressed_file = gzip.GzipFile(fileobj=compressed_file)
    content = decompressed_file.read().decode('utf-8')
    return csv.DictReader(io.StringIO(content))

def build_master():
    # 1. Load BSE Data first (to build ISIN -> BSE_CODE map)
    # We only care about active Equity instruments
    print("Processing BSE Data...")
    bse_map = {} # ISIN -> BSE_CODE
    try:
        bse_reader = download_and_parse(BSE_URL)
        for row in bse_reader:
            if row.get('instrument_type') == 'EQUITY' and row.get('isin'):
                # Upstox exchange_token for BSE is the BSE Scrip Code (e.g., 500325)
                bse_map[row['isin']] = row['exchange_token']
    except Exception as e:
        print(f"Error processing BSE data: {e}")

    # 2. Process NSE Data and Merge
    print("Processing NSE Data...")
    instruments = []
    try:
        nse_reader = download_and_parse(NSE_URL)
        for row in nse_reader:
            if row.get('instrument_type') == 'EQUITY':
                # Upstox tradingsymbol for EQ usually looks like "RELIANCE" or "RELIANCE-BE"
                # We assume series is 'EQ' if not specified, or we can try to parse.
                # Standard NSE convention in these files: "RELIANCE" -> EQ. "TCS" -> EQ.
                # If it has a suffix like "-BE", that's the series.
                
                raw_symbol = row['tradingsymbol']
                isin = row.get('isin', '')
                
                # Derive Series
                if '-' in raw_symbol:
                    parts = raw_symbol.rsplit('-', 1)
                    symbol = parts[0]
                    series = parts[1]
                else:
                    symbol = raw_symbol
                    series = "EQ"

                # Get BSE Code from map
                bse_code = bse_map.get(isin, "")

                record = {
                    'symbol': symbol,
                    'exchange': 'NSE',
                    'series': series,
                    'isin': isin,
                    'nse_scrip_code': row['exchange_token'],
                    'bse_code': bse_code
                }
                instruments.append(record)
    except Exception as e:
        print(f"Error processing NSE data: {e}")

    # 3. Write Output
    print(f"Writing {len(instruments)} records to {OUTPUT_PATH}...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    headers = ['symbol', 'exchange', 'series', 'isin', 'nse_scrip_code', 'bse_code']
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(instruments)

    print("Done.")

if __name__ == "__main__":
    build_master()
