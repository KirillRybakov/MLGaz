# alfacreator-backend/app/services/promo_service.py

import json
import re
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_client import llm_client
from app.schemas.promo import PromoRequest
from app.schemas import history as history_schema
from app import crud

async def generate_promo_logic(
    request: PromoRequest, 
    db: AsyncSession, 
    user_id: int
) -> list[str]:
    """
    Основная бизнес-логика для генерации промо-материалов.
    """
    prompt = (
        "Ты — профессиональный SMM-копирайтер. Создай 3 уникальных, коротких рекламных поста.\n"
        "Информация:\n"
        f"- Продукт: {request.product_description}\n"
        f"- Целевая аудитория: {request.audience}\n"
        f"- Тональность: {request.tone}\n\n"
        "КРИТИЧЕСКИ ВАЖНО: Твой ответ должен быть СТРОГО в формате валидного JSON-массива (списка) из 3 строк. "
        "НЕ ИСПОЛЬЗУЙ никаких ключей или объектов, просто голый массив. "
        "Пример: [\"Первый текст...\", \"Второй текст...\", \"Третий текст...\"]\n\n"
        "Отвечай СТРОГО на русском языке."
    )

    try:
        response_str = await llm_client.generate_json_response(prompt)
        results = []
        try:
            # Ваша логика парсинга JSON
            start_index = response_str.find('[')
            end_index = response_str.rfind(']')
            if start_index != -1 and end_index != -1:
                json_str = response_str[start_index : end_index + 1]
                parsed_data = json.loads(json_str)
                if isinstance(parsed_data, list):
                    results = [str(item) for item in parsed_data if isinstance(item, (str, int, float))]
            else:
                 raise ValueError("JSON array markers not found")
        except Exception as e:
            logger.warning(f"Failed to parse JSON for user {user_id}, falling back to regex. Error: {e}")
            found_strings = re.findall(r'"(.*?)"', response_str)
            results = [s for s in found_strings if len(s) > 20]

        if not results:
            raise ValueError("LLM returned an empty or unparsable result")

        # Сохраняем в историю
        history_entry_data = history_schema.HistoryCreate(
            request_type="promo",
            input_data=request.model_dump(),
            output_data={"results": results}
        )
        await crud.create_history_entry(db=db, user_id=user_id, entry=history_entry_data)
        
        return results

    except Exception as e:
        logger.error(f"Error in promo generation logic for user {user_id}: {e}", exc_info=True)
        # Пробрасываем исключение выше, чтобы роутер мог его обработать
        raise