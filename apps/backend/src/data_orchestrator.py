from .auth_store import AuthStore
from .providers.kotak import KotakProvider
from .providers.mock import MockProvider
from .providers.upstox import UpstoxProvider


def get_provider(config: dict, provider_override: str | None = None):
    mode = (provider_override or config.get("active_provider") or "").strip()
    if mode == "upstox":
        upstox_creds = config.get("upstox_creds", {})
        auth_db_path = config.get("auth_db_path", "auth.db")
        auth_store = AuthStore(db_path=auth_db_path)
        return UpstoxProvider(
            api_key=upstox_creds.get("api_key"),
            token=upstox_creds.get("token"),
            api_secret=upstox_creds.get("api_secret"),
            auth_store=auth_store,
        )
    elif mode == "kotak":
        return KotakProvider(api_key=config.get("kotak_access_token"))
    elif mode == "mock":
        mock_config = config.get("mock", {})
        return MockProvider(
            symbols=mock_config.get("symbols"),
            base_price=mock_config.get("base_price", 100.0),
            max_deviation=mock_config.get("max_deviation", 5.0),
            volatility=mock_config.get("volatility", 0.5),
            mean_reversion=mock_config.get("mean_reversion", 0.1),
            interval_seconds=mock_config.get("interval_seconds", 0.5),
            seed=mock_config.get("seed"),
            volume_min=mock_config.get("volume_min", 100),
            volume_max=mock_config.get("volume_max", 1000),
        )
    raise ValueError(f"Unknown provider: {mode}")
