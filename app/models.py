from datetime import datetime
from pydantic import BaseModel


class URLModel(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime