from pydantic import BaseModel, HttpUrl, Field


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    expires_in: int | None = None


class URLResponse(BaseModel):
    short_code: str
    short_url: str