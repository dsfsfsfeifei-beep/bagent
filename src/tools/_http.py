import httpx


def authed_get(base_url: str, path: str, token: str, params: dict | None = None) -> dict:
    if not base_url:
        raise RuntimeError(f"base_url not configured for path {path}")
    r = httpx.get(
        f"{base_url.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()
