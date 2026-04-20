from pydantic import BaseModel


class HcaptchaSiteKey(BaseModel):
    sitekey: str
