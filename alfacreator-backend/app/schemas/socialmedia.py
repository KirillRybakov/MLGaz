from pydantic import BaseModel
from typing import Optional

class SocialMediaInfo(BaseModel):
    platform: str
    identifier: Optional[str] = None # Имя пользователя, ID канала и т.д.
    analysis_summary: str