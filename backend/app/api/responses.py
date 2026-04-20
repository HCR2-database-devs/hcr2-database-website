from fastapi.responses import JSONResponse
from psycopg import Error as PsycopgError

from app.db.session import DatabaseNotConfigured


def error_response(message: str, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content={"error": message}, status_code=status_code)


def database_error_response(exc: Exception) -> JSONResponse:
    return error_response("Database error", status_code=500)


DATABASE_ERROR_TYPES = (DatabaseNotConfigured, PsycopgError)
