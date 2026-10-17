import httpx

HCAPTCHA_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


def verify_hcaptcha(
    token: str,
    secret_key: str | None,
    site_key: str | None = None,
    remote_ip: str | None = None,
) -> bool:
    if not token or not secret_key:
        return False
    data = {"secret": secret_key, "response": token}
    if site_key:
        data["sitekey"] = site_key
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        response = httpx.post(
            HCAPTCHA_VERIFY_URL,
            data=data,
            timeout=5.0,
        )
    except (httpx.HTTPError, OSError):
        return False
    if response.status_code != 200:
        return False
    try:
        payload = response.json()
    except (ValueError, TypeError):
        return False
    return isinstance(payload, dict) and payload.get("success") is True
