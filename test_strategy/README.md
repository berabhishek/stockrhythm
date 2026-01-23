# StockRhythm Strategy Project

## Layout
notebooks/        Research and experiments (Jupyter notebooks)
strategies/       Strategy code (your main strategy lives here)
config/           Optional filter specs and settings
data/             Local datasets for backtests (optional)

## Quickstart
1) Install dependencies:
   pip install -r requirements.txt

2) Start the backend (from the StockRhythm repo root):
   docker-compose up -d backend redis
   # or
   uv run uvicorn apps.backend.src.main:app --port 8000

3) Paper trade:
   stockrhythm run --paper --file strategies/strategy.py

4) Live trade:
   stockrhythm run --live --file strategies/strategy.py

## Filters and Universes
The CLI looks for `get_filter()` in your strategy file and passes it to
Strategy.start(subscribe=...). You can return either:
- UniverseFilter (builder) from stockrhythm.filters
- UniverseFilterSpec (built)
- A list of symbol strings for static subscriptions

If you prefer editing JSON instead, update config/filter.json and run:
   stockrhythm run --paper --file strategies/strategy.py --filter config/filter.json

## Notebooks
Use notebooks/ for indicator research and idea exploration. When the logic
is stable, copy it into strategies/strategy.py and wire it into on_tick.
