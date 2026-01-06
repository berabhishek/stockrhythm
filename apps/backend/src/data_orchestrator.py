from .providers.upstox import UpstoxProvider
from .providers.mock import MockProvider

def get_provider(config: dict):
    mode = config.get("active_provider")
    if mode == "upstox":
        return UpstoxProvider(config.get("upstox_creds", {}).get("api_key"), config.get("upstox_creds", {}).get("token"))
    elif mode == "mock":
        return MockProvider(csv_path="data/history.csv")
    raise ValueError(f"Unknown provider: {mode}")
