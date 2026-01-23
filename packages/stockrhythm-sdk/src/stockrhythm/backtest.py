import sqlite3
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import httpx

from .models import Order, OrderType, Tick

DateTimeInput = Union[str, datetime]


def _parse_datetime(value: DateTimeInput) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError("Expected datetime or ISO-8601 string for date/time input")


class BacktestDB:
    def __init__(self, db_path: str = "backtests.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL NOT NULL,
                timestamp TEXT NOT NULL,
                provider TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_market_ticks_ts ON market_ticks(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_market_ticks_symbol_ts ON market_ticks(symbol, timestamp)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backtest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backtest_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                qty INTEGER NOT NULL,
                side TEXT NOT NULL,
                type TEXT NOT NULL,
                limit_price REAL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES backtest_runs(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backtest_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES backtest_runs(id),
                FOREIGN KEY(order_id) REFERENCES backtest_orders(id)
            )
            """
        )

        conn.commit()
        conn.close()

    def insert_ticks(self, ticks: Iterable[Tick]) -> int:
        rows: List[Tuple[str, float, float, str, Optional[str]]] = []
        for tick in ticks:
            rows.append(
                (
                    tick.symbol,
                    tick.price,
                    tick.volume,
                    tick.timestamp.isoformat(),
                    tick.provider,
                )
            )

        if not rows:
            return 0

        conn = self._connect()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO market_ticks (symbol, price, volume, timestamp, provider)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        conn.close()
        return len(rows)

    def create_run(self, start_at: DateTimeInput, end_at: DateTimeInput, name: Optional[str]) -> int:
        start_dt = _parse_datetime(start_at)
        end_dt = _parse_datetime(end_at)
        created_at = datetime.utcnow().isoformat()

        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backtest_runs (name, start_at, end_at, created_at, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, start_dt.isoformat(), end_dt.isoformat(), created_at, "running"),
        )
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return run_id

    def finish_run(self, run_id: int, status: str = "completed") -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE backtest_runs SET status = ? WHERE id = ?",
            (status, run_id),
        )
        conn.commit()
        conn.close()

    def record_order(self, run_id: int, order: Order, status: str, created_at: datetime) -> int:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backtest_orders (
                run_id, symbol, qty, side, type, limit_price, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                order.symbol,
                order.qty,
                order.side,
                order.type,
                order.limit_price,
                status,
                created_at.isoformat(),
            ),
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def record_trade(self, run_id: int, order_id: int, symbol: str, qty: int, price: float, timestamp: datetime) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backtest_trades (run_id, order_id, symbol, qty, price, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, order_id, symbol, qty, price, timestamp.isoformat()),
        )
        conn.commit()
        conn.close()

    def count_ticks(
        self,
        start_at: DateTimeInput,
        end_at: DateTimeInput,
        symbols: Optional[Sequence[str]] = None,
    ) -> int:
        start_dt = _parse_datetime(start_at).isoformat()
        end_dt = _parse_datetime(end_at).isoformat()

        query = """
            SELECT COUNT(*)
            FROM market_ticks
            WHERE timestamp >= ? AND timestamp <= ?
        """
        params: List[object] = [start_dt, end_dt]

        if symbols:
            placeholders = ", ".join("?" for _ in symbols)
            query += f" AND symbol IN ({placeholders})"
            params.extend(symbols)

        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        count = cursor.fetchone()[0] or 0
        conn.close()
        return int(count)

    def fetch_ticks(
        self,
        start_at: DateTimeInput,
        end_at: DateTimeInput,
        symbols: Optional[Sequence[str]] = None,
    ) -> Iterable[Tick]:
        start_dt = _parse_datetime(start_at).isoformat()
        end_dt = _parse_datetime(end_at).isoformat()

        query = """
            SELECT symbol, price, volume, timestamp, provider
            FROM market_ticks
            WHERE timestamp >= ? AND timestamp <= ?
        """
        params: List[object] = [start_dt, end_dt]

        if symbols:
            placeholders = ", ".join("?" for _ in symbols)
            query += f" AND symbol IN ({placeholders})"
            params.extend(symbols)

        query += " ORDER BY timestamp ASC"

        conn = self._connect()
        cursor = conn.cursor()
        rows = list(cursor.execute(query, params))
        conn.close()

        for row in rows:
            yield Tick(
                symbol=row[0],
                price=row[1],
                volume=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                provider=row[4] or "backtest",
            )


class BacktestClient:
    def __init__(self, db: BacktestDB, run_id: int):
        self.db = db
        self.run_id = run_id
        self._last_tick: Optional[Tick] = None

    def set_last_tick(self, tick: Tick) -> None:
        self._last_tick = tick

    async def submit_order(self, order: Order) -> dict:
        now = datetime.utcnow()
        order_id = self.db.record_order(self.run_id, order, "FILLED", now)

        if order.type == OrderType.LIMIT and order.limit_price is not None:
            fill_price = order.limit_price
        elif self._last_tick and self._last_tick.symbol == order.symbol:
            fill_price = self._last_tick.price
        else:
            fill_price = order.limit_price or 0.0

        self.db.record_trade(
            self.run_id,
            order_id,
            order.symbol,
            order.qty,
            fill_price,
            now,
        )
        return {"status": "success", "order_id": order_id}


class BacktestEngine:
    def __init__(self, db_path: str = "backtests.db"):
        self.db = BacktestDB(db_path=db_path)

    async def run(
        self,
        strategy,
        start_at: DateTimeInput,
        end_at: DateTimeInput,
        symbols: Optional[Sequence[str]] = None,
        name: Optional[str] = None,
        *,
        backend_url: Optional[str] = None,
        interval: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> int:
        if backend_url:
            if not symbols:
                raise ValueError("Provider-backed backtests require symbols to be specified.")
            if self.db.count_ticks(start_at, end_at, symbols) == 0:
                print(f"Fetching ticks from backend for {symbols}...")
                ticks = await _fetch_ticks_from_backend(
                    backend_url=backend_url,
                    start_at=start_at,
                    end_at=end_at,
                    symbols=list(symbols),
                    interval=interval,
                    provider=provider,
                )
                print(f"Fetched {len(ticks)} ticks. Inserting into DB...")
                count = self.db.insert_ticks(ticks)
                print(f"Inserted {count} ticks.")

        run_id = self.db.create_run(start_at=start_at, end_at=end_at, name=name)
        client = BacktestClient(self.db, run_id)

        strategy.client = client
        strategy.paper_trade = True

        status = "completed"
        try:
            if symbols:
                await strategy.on_universe_init(list(symbols))

            for tick in self.db.fetch_ticks(start_at, end_at, symbols):
                client.set_last_tick(tick)
                await strategy.on_tick(tick)
        except Exception:
            status = "failed"
            raise
        finally:
            self.db.finish_run(run_id, status=status)

        return run_id


async def _fetch_ticks_from_backend(
    *,
    backend_url: str,
    start_at: DateTimeInput,
    end_at: DateTimeInput,
    symbols: Sequence[str],
    interval: Optional[str],
    provider: Optional[str],
) -> List[Tick]:
    url = f"{backend_url.rstrip('/')}/backtest"
    
    # Helper to format date for provider APIs (Upstox dislikes ISO time)
    def _fmt(dt_input: DateTimeInput) -> str:
        dt = _parse_datetime(dt_input)
        # If valid time is 00:00:00, send date only
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
            return dt.date().isoformat()
        return dt.isoformat()

    payload = {
        "symbols": list(symbols),
        "start": _fmt(start_at),
        "end": _fmt(end_at),
        "interval": interval,
        "provider": provider,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        raise ConnectionError(f"Backtest data fetch failed: {resp.status_code} - {resp.text}")

    data = resp.json()
    ticks_payload = data.get("ticks", [])
    if not isinstance(ticks_payload, list):
        raise ValueError("Backtest response missing ticks list.")

    return [Tick(**item) for item in ticks_payload]
