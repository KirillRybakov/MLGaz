# alfacreator-backend/app/routers/smart_analytics_router.py

import io
import json
import pandas as pd
import httpx
from fastapi import (
    APIRouter, UploadFile, Form, HTTPException, Query, File, Depends
)
from fastapi.responses import JSONResponse
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

# --- Правильные импорты ---
from app.services import social_parser  # Импортируем модуль целиком
from app.schemas.socialmedia import SocialMediaInfo
from app.core.llm_client import llm_client
from app.database import get_db
from app import crud
from app.core.dependencies import get_db, get_current_user
from app.schemas.user import User as UserSchema
from app.schemas import history as history_schema


router = APIRouter()


@router.get("/analyze/social", response_model=SocialMediaInfo)
async def get_social_analysis(link: str = Query(..., description="Ссылка на соцсеть для анализа")):
    analysis_result = await social_parser.analyze_social(link)
    if not analysis_result:
        raise HTTPException(
            status_code=400,
            detail="Не удалось распознать ссылку или соцсеть не поддерживается."
        )
    return analysis_result


@router.post("/smart")
async def analyze_business(
        db: AsyncSession = Depends(get_db),
        file: Optional[UploadFile] = File(None),
        link: Optional[str] = Form(None),
        current_user: UserSchema = Depends(get_current_user)
):
    if not file and not link:
        raise HTTPException(status_code=400, detail="Необходимо предоставить файл или ссылку.")

    # --- НОВАЯ ЛОГИКА ПРОВЕРКИ ---
    user_data_summary = None
    if file:
        contents = await file.read()
        try:
            df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith(".csv") else pd.read_excel(
                io.BytesIO(contents))
            user_data_summary = summarize_client_data(df)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка чтения файла: {e}")

    social_data_summary = None
    if link:
        social_info = await social_parser.analyze_social(link)
        if social_info:
            social_data_summary = social_info.analysis_summary

    # "ОХРАННИК": Если нет ни данных из файла, ни распознанной ссылки, возвращаем ошибку
    if not user_data_summary and not social_data_summary:
        raise HTTPException(
            status_code=400,
            detail="Не удалось получить данные. Пожалуйста, проверьте ссылку на соцсеть или загрузите корректный файл."
        )
    # ------------------------------

    try:
        trends = await get_latest_trends()

        prompt = f"""
        Ты — профессиональный SMM-стратег для российского малого бизнеса.
        Твоя задача — создать детальный и практичный контент-план на 7 дней.
        Твой ответ ДОЛЖЕН БЫТЬ ПОЛНОСТЬЮ на русском языке, включая ключи в JSON.

        Проанализируй информацию о бизнесе клиента:
        📊 Клиентские данные:
        {user_data_summary or "Не предоставлены."}

        🌐 Анализ соцсетей ({link or "Не указана"}):
        {social_data_summary or "Не предоставлены или ссылка не распознана."}

        🔥 Актуальные тренды в России:
        {trends}

        Основываясь на этих данных, выполни два шага:
        1. Сформулируй 2-3 ключевые рекомендации для быстрого улучшения.
        2. Составь пошаговый контент-план на неделю.

        ВАЖНО: Ответ должен быть СТРОГО в формате валидного JSON на русском языке. Вот структура:
        {{
        "kratkieRekomendatsii": [
            "Краткая ключевая рекомендация №1...",
            "Краткая ключевая рекомендация №2..."
        ],
        "celNaNedelyu": "Сформулируй здесь главную цель на неделю ",
        "kontentPlan": [
            {{
            "den": "Понедельник",
            "tema": "Тема дня ",
            "ideyaPosta": "Конкретная идея для поста ",
            "format": "Reels",
            "prizyvKDeystviyu": "Призыв к действию "
            }}
        ]
        }}
        """

        result_str = await llm_client.generate_json_response(prompt)
        result_data = json.loads(result_str)

        # 1. Формируем Pydantic-объект HistoryCreate
        input_data_for_history = {"link": link, "filename": file.filename if file else None}
        history_entry_data = history_schema.HistoryCreate(
            request_type="smart_analytics",
            input_data=input_data_for_history,
            output_data=result_data
        )

        await crud.create_history_entry(
            db=db,
            request_type="smart_analytics",
            user_id=current_user.id,
            entry=history_entry_data
        )

        return JSONResponse(content=result_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def summarize_client_data(df: pd.DataFrame) -> str:
    """
    Простейший анализ CSV/Excel — структура, количество записей, средние значения.
    """
    try:
        info = f"Найдено {len(df)} строк. Колонки: {', '.join(df.columns)}."
        if "amount" in df.columns and pd.api.types.is_numeric_dtype(df["amount"]):
            avg_amount = df["amount"].mean()
            info += f" Средний чек: {avg_amount:.2f}."
        return info
    except Exception:
        return "Не удалось проанализировать структуру файла."


async def get_latest_trends() -> str:
    """
    Получение трендов (пока заглушка, но можно подключить реальный API).
    """
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://trends.google.com/trending/rss?geo=RU")
            if res.status_code == 200:
                return "Google Trends: популярные темы недели."
    except:
        pass
    return "Тренды не удалось получить."
