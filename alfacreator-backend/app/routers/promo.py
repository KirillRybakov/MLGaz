from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
from loguru import logger
import re
from app.schemas.promo import PromoRequest, PromoResponse
from app.core.llm_client import llm_client
from app.core.dependencies import get_db, get_current_user
from app.schemas import history as history_schema
from app.schemas import user as user_schema
from app import crud

router = APIRouter()

@router.post("/generate", response_model=PromoResponse)
async def generate_promo(
    request: PromoRequest, 
    db: AsyncSession = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
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
            # Simplified and more robust JSON parsing logic
            # Find the start of the JSON array '[' and the end ']'
            start_index = response_str.find('[')
            end_index = response_str.rfind(']')
            
            if start_index != -1 and end_index != -1:
                json_str = response_str[start_index : end_index + 1]
                parsed_data = json.loads(json_str)
                if isinstance(parsed_data, list):
                    results = [str(item) for item in parsed_data if isinstance(item, (str, int, float))]
            else:
                 raise ValueError("JSON array markers not found in LLM response")

        except Exception as e:
            logger.warning(f"Failed to parse JSON cleanly, attempting regex fallback. Error: {e}")
            # Fallback to regex if JSON parsing fails
            found_strings = re.findall(r'"(.*?)"', response_str)
            results = [s for s in found_strings if len(s) > 20]

        if not results:
            logger.warning(f"Could not extract any valid results from LLM response: {response_str}")
            raise ValueError("LLM returned an empty or unparsable result")

        # 4.1. Create a Pydantic HistoryCreate object
        history_entry_data = history_schema.HistoryCreate(
            request_type="promo",
            input_data=request.model_dump(),
            output_data={"results": results}
        )
        
        # 4.2. Call the CRUD function with the correct arguments
        await crud.create_history_entry(
            db=db,
            user_id=current_user.id, # Pass the current user's ID
            entry=history_entry_data   # Pass the Pydantic object
        )

        return PromoResponse(results=results)

    except Exception as e:
        logger.error(f"Critical error in promo endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"A critical backend error occurred: {str(e)}")