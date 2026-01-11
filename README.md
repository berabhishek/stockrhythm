# StockRhythm

**High-performance, developer-centric algorithmic trading platform.**

StockRhythm provides a modern, type-safe Python SDK for writing trading strategies, backed by a robust local backend that handles data normalization and risk management.

## 🚀 Features

*   **Type-Safe SDK**: Write strategies with full IDE autocomplete support using Pydantic models.
*   **Data Abstraction**: Switch between simulation (Mock), Upstox, and other brokers without changing a single line of strategy code.
*   **Local-First Development**: Develop and test locally with a simulated exchange environment.
*   **Built-in Risk Engine**: Pre-trade validation ensures you never send an invalid or dangerous order to the exchange.

## 🛠 Prerequisites

*   **Python 3.12+**
*   **uv**: An extremely fast Python package installer and resolver.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
*   **Docker**: For running the local backend engine.

## 🛠 Architecture Philosophy

StockRhythm utilizes a 4-layer stack to isolate trading logic from broker complexities:

1.  **Broker API**: Raw market data and order execution.
2.  **Backend Engine**: Handles Auth (TOTP/MPIN), Risk, and Normalization.
3.  **Python SDK**: Provides a type-safe, simple interface for developers.
4.  **Trading Strategy**: Your logic, completely abstracted from the broker.

## 🏁 Quick Start

### 1. Installation

Clone the repository and sync the workspace:

```bash
git clone https://github.com/yourusername/stockrhythm.git
cd stockrhythm
uv sync
```

### 2. Start the Engine

Launch the backend services (Mock Provider is enabled by default).

**Using Docker (Recommended):**
```bash
docker-compose up -d backend
```

**Development Mode (Directly via Python):**
```bash
uv run uvicorn apps.backend.src.main:app --port 8000
```

### 3. Install the CLI Tool (Optional but Recommended)

To create and manage strategies from anywhere on your system, install the StockRhythm CLI as a global tool:

```bash
uv tool install packages/stockrhythm-cli --editable
```

### 4. Create a Strategy

You can now scaffold a professional, production-ready trading project in any directory:

```bash
# In any directory
stockrhythm init my-cool-bot
cd my-cool-bot
```

This creates a structured project with segregated configuration, alpha logic, and execution scripts:
```text
my-cool-bot/
├── config/              # Strategy & Market configurations
├── src/                 # Proprietary Alpha & Signal logic
├── scripts/             # Execution runners (Live/Paper/Backtest)
└── requirements.txt     # Local SDK & dependencies
```

### 5. Run Your Strategy

First, install the local dependencies:
```bash
pip install -r requirements.txt
```

Then, execute your strategy using the provided runner script. The SDK automatically detects trading modes via CLI flags:

```bash
# Paper Trading (Default)
python scripts/live_runner.py

# Explicit Paper Trading
python scripts/live_runner.py --paper

# Live Trading (Requires Backend config)
python scripts/live_runner.py --live
```

*The runner loads your configuration from `config/strategies/`, initializes your alpha signals, and connects to the StockRhythm backend for execution.*

## 📚 Documentation

### The `Strategy` Class

Every bot inherits from `stockrhythm.Strategy`.

*   `async on_tick(self, tick: Tick)`: Called every time a new market data point arrives.
*   `async buy(self, symbol: str, qty: int)`: Submits a market buy order.
*   `async sell(self, symbol: str, qty: int)`: Submits a market sell order.

### Configuration

The backend configuration is located in `apps/backend/config.yaml`.

**Switching to Real Data (Upstox):**
1.  Open `apps/backend/config.yaml`.
2.  Change `active_provider` to `"upstox"`.
3.  Fill in your `api_key` and `token`.
4.  Restart the backend: `docker-compose restart backend`.

## 🤝 Contributing

We welcome contributions! Please see [GEMINI.md](GEMINI.md) for detailed architecture documentation and development guidelines.

## 📄 License

MIT
