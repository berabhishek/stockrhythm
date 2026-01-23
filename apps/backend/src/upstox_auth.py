import httpx

TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"


async def exchange_auth_code(
    *,
    api_key: str,
    api_secret: str,
    auth_code: str,
    redirect_uri: str,
) -> dict:
    data = {
        "code": auth_code,
        "client_id": api_key,
        "client_secret": api_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise ValueError(f"Upstox token exchange failed: {resp.status_code} - {resp.text}")
    return resp.json()
