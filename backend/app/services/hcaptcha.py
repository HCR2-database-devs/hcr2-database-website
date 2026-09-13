import httpx


def verify_hcaptcha(token: str, secret_key: str | None) -> bool:
    if not token or not secret_key:
        return False
    try:
        response = httpx.post(
            "https://hcaptcha.com/siteverify",
            data={"secret": secret_key, "response": token},
            timeout=5.0,
        )
    except httpx.HTTPError:
        return False
    if response.status_code != 200:
        return False
    payload = response.json()
    return bool(payload.get("success") is True)