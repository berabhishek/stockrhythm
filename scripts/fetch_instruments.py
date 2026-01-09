import csv
import urllib.request
import io
import os

URL = "https://api.kite.trade/instruments"
OUTPUT_PATH = "apps/backend/data/instruments.csv"

def fetch_and_process():
    print(f"Downloading instruments from {URL}...")
    try:
        with urllib.request.urlopen(URL) as response:
            data = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to download: {e}")
        return

    print("Processing data...")
    csv_file = io.StringIO(data)
    reader = csv.DictReader(csv_file)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    count = 0
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['symbol', 'exchange', 'segment', 'token', 'name']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            # Filter for NSE Equity
            if row['exchange'] == 'NSE' and row['segment'] == 'NSE':
                # Map Zerodha format to StockRhythm format
                # Zerodha 'segment'='NSE' implies Cash Market (CM) for us
                
                # Check instrument_type is EQ (Equity) to be safe, or just take all NSE segment
                # Zerodha 'NSE' segment includes EQ, BE, etc.
                
                writer.writerow({
                    'symbol': row['tradingsymbol'],
                    'exchange': 'NSE',
                    'segment': 'CM',
                    'token': row['exchange_token'],
                    'name': row['name']
                })
                count += 1

            # Optional: Add BSE if needed later
            # if row['exchange'] == 'BSE' ...

    print(f"Successfully wrote {count} instruments to {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_and_process()
