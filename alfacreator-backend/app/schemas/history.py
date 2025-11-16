from pydantic import BaseModel
from typing import Dict, Any
import datetime


# 1. Базовая схема с полями, общими для создания и чтения
class HistoryBase(BaseModel):
    request_type: str
    input_data: Dict[str, Any]


class HistoryCreate(HistoryBase):
    output_data: Dict[str, Any]


class History(HistoryBase):
    id: int
    user_id: int
    output_data: Dict[str, Any]
    created_at: datetime.datetime

    class Config:
        from_attributes = True # Для совместимости с моделями SQLAlchemy