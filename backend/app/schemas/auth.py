from pydantic import BaseModel


class AuthStatusLoggedOut(BaseModel):
    logged: bool = False
    allowed: bool = False


class AuthStatusLoggedIn(BaseModel):
    logged: bool = True
    allowed: bool
    id: str
    username: str | None
