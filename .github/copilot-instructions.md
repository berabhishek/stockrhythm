# Copilot Instructions for StockRhythm

## Project Overview
StockRhythm is a layered, developer-centric algorithmic trading platform. It separates trading logic, broker APIs, and risk management into distinct components for safety and flexibility.

### Architecture
- **Backend Engine (`apps/backend`)**: FastAPI server for data normalization, risk checks, and provider abstraction. Key files: `main.py`, `data_orchestrator.py`, `risk_engine.py`, `providers/`.
- **SDK (`packages/stockrhythm-sdk`)**: Python library for writing strategies. Defines Pydantic models (`models.py`), the `Strategy` base class (`strategy.py`), and WebSocket client (`client.py`).
- **CLI (`packages/stockrhythm-cli`)**: Typer-based tool for scaffolding and managing strategies.
- **Strategies (`strategies/`)**: User bots inherit from `Strategy` and implement `on_tick`.
- **Dashboard (`apps/dashboard`)**: Next.js UI for monitoring and visualization.

## Key Workflows
- **Dependency Management**: Use `uv sync` at the root. Add dependencies with `uv add <package> --package <target>`.
- **Backend Startup**: `docker-compose up -d backend redis` (do not run this automatically).
- **Strategy Scaffolding**: Use `stockrhythm init <bot-name>` in `strategies/`.
- **Testing**: Unit tests in `tests/unit`, integration in `tests/integration`. Set `active_provider: "mock"` in `apps/backend/config.yaml` for local tests.

## Project-Specific Conventions
- **Never access or modify `.env` or database files**. Credentials and persistent data are managed manually.
- **Do not start/stop servers or background processes automatically**. Provide commands for the user to run.
- **All packages use `src/` layout** to avoid import ambiguity.
- **Provider abstraction**: Add new brokers by implementing `MarketDataProvider` in `apps/backend/src/providers/` and registering in `data_orchestrator.py`.
- **Contract changes**: Update Pydantic models in `models.py`, bump version in `pyproject.toml`, and re-sync dependencies.

## Examples
- **Strategy Example** (`strategies/my-bot/strategy.py`):
  ```python
  from stockrhythm import Strategy, Tick
  class MyBot(Strategy):
      async def on_tick(self, tick: Tick):
          if tick.price < 100:
              await self.buy(tick.symbol, 10)
  ```
- **Switching Providers**: Edit `apps/backend/config.yaml` and restart backend.

## References
- See `README.md` and `GEMINI.md` for detailed architecture and workflow guidance.

---
**AGENT SAFETY**: Never touch `.env`, database files, or start/stop services. Always use `uv` for Python dependencies. When in doubt, reference `GEMINI.md`.
