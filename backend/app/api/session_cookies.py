from starlette.responses import Response

SESSION_COOKIE_NAMES = ("WC_TOKEN",)
SESSION_COOKIE_DOMAINS: tuple[str | None, ...] = (None, ".hcr2.xyz")


def clear_session_cookies(response: Response) -> None:
    for cookie_name in SESSION_COOKIE_NAMES:
        for domain in SESSION_COOKIE_DOMAINS:
            response.delete_cookie(
                cookie_name,
                path="/",
                domain=domain,
                secure=True,
                httponly=True,
                samesite="lax",
            )
