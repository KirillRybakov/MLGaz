# alfacreator-backend/app/schemas/analytics.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union

# Модель для успешного результата
class AnalyticsSuccessResult(BaseModel):
    insights: str
    chart_data: Dict[str, Any]

# Модель для результата с ошибкой
class AnalyticsErrorResult(BaseModel):
    error_message: str

# Главная модель статуса, которая может содержать один из трех вариантов
class TaskStatusResponse(BaseModel):
    status: str = Field(..., example="complete")
    # Поле result теперь может быть одним из трех типов
    result: Optional[Union[AnalyticsSuccessResult, AnalyticsErrorResult]] = None