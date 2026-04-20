from dataclasses import dataclass


@dataclass(slots=True)
class ApiError(Exception):
    message: str
    status_code: int = 400


def legacy_error(message: str) -> dict[str, str]:
    return {"error": message}

