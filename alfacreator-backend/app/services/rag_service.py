# alfacreator-backend/app/services/rag_service.py

import chromadb
from sentence_transformers import SentenceTransformer
from loguru import logger
import json
from pydantic import ValidationError

from app.core.llm_client import llm_client
from app.database import AsyncSessionLocal  # Для создания сессий БД внутри сервиса
from app.services import promo_service, document_service # Наши новые сервисы
from app.schemas import promo as promo_schema
from app.schemas import documents as document_schema

# --- Инициализация RAG (без изменений) ---
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
client = chromadb.PersistentClient(path="./chroma_db")
try:
    collection = client.get_collection(name="smm_assistant_kb")
    RAG_ENABLED = True
except Exception:
    RAG_ENABLED = False
    logger.warning("Коллекция ChromaDB 'smm_assistant_kb' не найдена. RAG будет отключен.")

# --- ОПИСАНИЕ ИНСТРУМЕНТОВ, ДОСТУПНЫХ БОТУ ---
TOOLS_PROMPT = """
У тебя есть доступ к следующим инструментам (функциям) нашего приложения:

1.  **generate_promo(product_description: str, audience: str, tone: str)**
    *   Описание: Генерирует 3 варианта рекламных постов.
    *   Когда использовать: Если пользователь просит "придумать пост", "написать рекламу", "сделать промо".
    *   ПРАВИЛО: Если из запроса НЕВОЗМОЖНО извлечь хотя бы `product_description`, НЕ ИСПОЛЬЗУЙ этот инструмент. Вместо этого используй `clarify` и спроси, о чем должен быть пост.

2.  **generate_document(template_name: str, details: dict)**
    *   Описание: Генерирует юридический или финансовый документ по шаблону.
    *   Доступные шаблоны (`template_name`): `invoice` (счет), `service_contract` (договор), `completion_act` (акт).
    *   ПРАВИЛО 1: Твоя задача — вести себя как заполнитель анкеты. Проанализируй запрос пользователя и извлеки из него МАКСИМУМ возможных данных для полей шаблона. Поля: "Номер счета", "Дата счета", "Имя клиента", "Сумма", "Ваше ИП/ООО" и т.д.
    *   ПРАВИЛО 2: Если пользователь просит "сделать документ", но НЕ УТОЧНЯЕТ КАКОЙ, используй `clarify` и спроси, какой именно документ нужен.

3.  **search_knowledge_base(query: str)**
    *   Описание: Ищет ответ на вопрос в базе знаний (SMM-курсы, регламенты).
    *   Когда использовать: Если вопрос явно теоретический (например, "что такое...", "какие обязанности...").

4.  **navigate_ui(feature_name: str)**
    *   Описание: Объясняет, как найти функцию в интерфейсе.
    *   Когда использовать: Если пользователь спрашивает "где найти", "как открыть".
"""

# --- СУПЕР-УЛУЧШЕННЫЙ СИСТЕМНЫЙ ПРОМПТ ---
SYSTEM_PROMPT_WITH_TOOLS = f"""
Ты — 'Альфа-Ассистент', умный и сверхточный помощник в приложении 'Альфа-Креатор'.

ТВОЯ ГЛАВНАЯ ЗАДАЧА: Проанализировать запрос пользователя и выбрать ОДИН правильный инструмент для его выполнения.

{TOOLS_PROMPT}

ПЛАН ДЕЙСТВИЙ:
1.  Проанализируй запрос пользователя.
2.  Выбери ЛУЧШИЙ инструмент. Строго следуй ПРАВИЛАМ для каждого инструмента.
3.  Сформируй JSON-объект с вызовом этого инструмента.

ОСОБЫЕ ПРАВИЛА:
-   Если запрос — бессмыслица или бытовой (например, "я поел пельмени"), используй инструмент `unrelated_query`.
-   Если не хватает данных для ВЫЗОВА инструмента, используй `clarify`.
-   Если пользователь просто здоровается или спрашивает "что ты умеешь?", используй `greet`.
-   Твой ответ ВСЕГДА — это ТОЛЬКО JSON.

ФОРМАТЫ JSON:
-   Для вызова инструмента: `{{ "tool_name": "...", "parameters": {{...}} }}`
-   Для уточнения: `{{ "tool_name": "clarify", "parameters": {{ "question": "..." }} }}`
-   Для приветствия: `{{ "tool_name": "greet", "parameters": {{}} }}`
-   Для нерелевантных запросов: `{{ "tool_name": "unrelated_query", "parameters": {{}} }}`
"""


# --- ГЛАВНАЯ ФУНКЦИЯ ---
async def get_bot_response(query: str, llm_client, user_id: int) -> str:
    logger.info(f"Получен запрос от пользователя ID={user_id}: '{query}'")
    
    # --- ЭТАП 1: ВЫБОР ИНСТРУМЕНТА (без изменений) ---
    tool_selection_prompt = f"{SYSTEM_PROMPT_WITH_TOOLS}\n\nЗапрос пользователя:\n---\n{query}\n---\n\nТвой JSON с выбором инструмента:"
    try:
        response_str = await llm_client.generate_json_response(tool_selection_prompt)
        json_start = response_str.find('{')
        json_end = response_str.rfind('}')
        if json_start == -1 or json_end == -1:
            raise ValueError("Не найден JSON в ответе LLM")
        clean_json_str = response_str[json_start:json_end + 1]
        tool_call = json.loads(clean_json_str)
        tool_name = tool_call.get("tool_name")
        parameters = tool_call.get("parameters", {})
    except Exception as e:
        logger.error(f"Ошибка выбора инструмента или парсинга JSON для user_id={user_id}: {e}\nОтвет LLM: {response_str}")
        return "К сожалению, я не смог понять ваш запрос. Попробуйте переформулировать."

    logger.info(f"Ассистент для пользователя ID={user_id} выбрал инструмент: {tool_name} с параметрами: {parameters}")

    # --- ЭТАП 2: ВЫПОЛНЕНИЕ ИНСТРУМЕНТА (НОВАЯ ЛОГИКА) ---
    # Создаем сессию БД, которая понадобится нашим сервисам
    async with AsyncSessionLocal() as db:
        try:
            if tool_name == "greet":
                return "Привет! Я Альфа-Ассистент. Я могу помочь вам сгенерировать промо-посты, создать документы, найти информацию в базе знаний или проанализировать данные. Что бы вы хотели сделать?"

            elif tool_name == "generate_promo":
                # 1. Валидируем параметры от LLM через Pydantic-схему
                promo_request_data = promo_schema.PromoRequest(**parameters)
                
                # 2. Вызываем сервисный слой НАПРЯМУЮ
                posts = await promo_service.generate_promo_logic(
                    request=promo_request_data,
                    db=db,
                    user_id=user_id
                )
                return "Готово! Вот несколько идей для постов:\n\n" + "\n".join([f"- {post}" for post in posts])

            elif tool_name == "generate_document":
                # 1. Валидируем параметры от LLM
                # Убедимся, что details - это словарь
                if 'details' not in parameters or not isinstance(parameters['details'], dict):
                    parameters['details'] = {}
                doc_request_data = document_schema.DocumentRequest(**parameters)
                
                # 2. Вызываем сервисный слой НАПРЯМУЮ
                doc_text = await document_service.generate_document_logic(
                    request=doc_request_data,
                    db=db,
                    user_id=user_id
                )
                return f"Документ '{parameters.get('template_name')}' готов! Текст ниже:\n\n---\n{doc_text}"

            elif tool_name == "navigate_ui":
                feature = parameters.get('feature_name', 'нужный раздел')
                return f"Чтобы найти '{feature}', просто перейдите в соответствующую вкладку в верхнем меню."

            elif tool_name == "search_knowledge_base":
                if not RAG_ENABLED:
                    return "К сожалению, моя база знаний сейчас недоступна."
                rag_query = parameters.get("query")
                if not rag_query:
                    return "Пожалуйста, уточните, что именно вы хотите найти."
                
                query_embedding = embedding_model.encode([rag_query])
                results = collection.query(query_embeddings=query_embedding, n_results=1)
                
                if not results.get('documents') or not results['documents'][0]:
                    return "К сожалению, я не нашел точной информации по вашему вопросу в базе знаний."

                context = results['documents'][0][0]
                final_prompt = f"..." # Ваш промпт для RAG без изменений
                response = await llm_client.client.generate(model=llm_client.model, prompt=final_prompt, stream=False)
                return response['response'].strip()

            elif tool_name == "unrelated_query":
                return "Я — ассистент для решения бизнес-задач. К сожалению, я не могу поддержать разговор на бытовые темы."
            
            elif tool_name == "clarify":
                return parameters.get("question", "Не могли бы вы уточнить ваш запрос?")

            else:
                logger.warning(f"Неизвестный инструмент '{tool_name}' выбран для user_id={user_id}")
                return "Я понял, что вы хотите сделать, но пока не умею выполнять такие действия."

        except ValidationError as e:
            # Ловим ошибки, если LLM сгенерировала неправильные параметры для наших схем
            logger.warning(f"Ошибка валидации параметров от LLM для инструмента '{tool_name}': {e}")
            return f"Я попытался использовать инструмент '{tool_name}', но мне не хватило данных. Не могли бы вы предоставить больше информации?"
        except Exception as e:
            logger.error(f"Ошибка выполнения инструмента '{tool_name}' для user_id={user_id}: {e}", exc_info=True)
            return f"К сожалению, при выполнении вашей команды произошла внутренняя ошибка."