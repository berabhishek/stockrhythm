import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the StockRhythm backend.")
    parser.add_argument(
        "--broker",
        default=os.getenv("STOCKRHYTHM_PROVIDER", "mock"),
        choices=["mock", "kotak", "upstox"],
        help="Select data provider (mock, kotak, upstox).",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Auto-reload on code changes (development only).",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload even if STOCKRHYTHM_RELOAD is set.",
    )
    args = parser.parse_args()

    os.environ["STOCKRHYTHM_PROVIDER"] = args.broker
    reload_env = os.getenv("STOCKRHYTHM_RELOAD", "").strip().lower() in ("1", "true", "yes")
    reload_enabled = (args.reload or reload_env) and not args.no_reload
    uvicorn.run(
        "apps.backend.src.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
    )


if __name__ == "__main__":
    main()
