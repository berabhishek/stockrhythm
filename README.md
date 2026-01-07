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

Launch the backend services (Mock Provider is enabled by default):

```bash
docker-compose up -d backend
```

### 3. Create a Strategy

Use the CLI to scaffold a new strategy inside the `strategies/` directory:

```bash
# Activate the virtual environment managed by uv
source .venv/bin/activate

# Create a new bot
cd strategies
stockrhythm init my-first-bot
```

This creates a folder `my-first-bot/` with a `strategy.py` template:

```python
# my-first-bot/strategy.py
from stockrhythm import Strategy, Tick

class MyFirstStrategy(Strategy):
    async def on_tick(self, tick: Tick):
        print(f"Received: {tick}")
        if tick.price < 100:
            await self.buy(tick.symbol, 10)
```

### 4. Run Your Strategy

(Note: You can run this directly with python if the SDK is in your path, or install the requirements)

```bash
cd my-first-bot
pip install -r requirements.txt
python strategy.py
```

*The strategy will connect to the local backend, receive mock market data, and print ticks to the console.*

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

### ⚠️ AGENT INSTRUCTION: ENVIRONMENT VARIABLES
**DO NOT TOUCH, MODIFY, OR READ THE `.env` FILE DIRECTLY.** 
Sensitive credentials must be managed manually.

## 📄 License

MIT
