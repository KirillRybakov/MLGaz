import re
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any

# Импортируем нашу модель
from app.schemas.socialmedia import SocialMediaInfo

# Конфигурация парсеров для разных соцсетей
# Каждый парсер содержит:
# - domains: список доменов, относящихся к соцсети
# - pattern: регулярное выражение для извлечения идентификатора из пути ссылки
# - template: шаблон для формирования итогового описания
SOCIAL_MEDIA_PARSERS: List[Dict[str, Any]] = [
    {
        "platform": "Instagram",
        "domains": ["instagram.com", "www.instagram.com"],
        "pattern": re.compile(r"^/([a-zA-Z0-9_.]+)/?"),
        "template": "Instagram-профиль '{identifier}'. Анализируем посты, вовлечённость, визуал."
    },
    {
        "platform": "Telegram",
        "domains": ["t.me", "telegram.me"],
        "pattern": re.compile(r"^/([a-zA-Z0-9_]{5,})/?"),
        "template": "Telegram-канал '{identifier}'. Анализируем активность, темы постов, реакции."
    },
    {
        "platform": "VK",
        "domains": ["vk.com", "m.vk.com"],
        # Паттерн для public<id>, club<id> или кастомного имени
        "pattern": re.compile(r"^/(public\d+|club\d+|[a-zA-Z0-9_.]+)/?"),
        "template": "Сообщество VK '{identifier}'. Анализируем контент, охваты, демографию подписчиков."
    }
]


async def analyze_social(link: str) -> Optional[SocialMediaInfo]:
    """
    Анализирует ссылку на соцсеть, извлекает платформу и идентификатор.
    Возвращает структурированную информацию или None, если ссылка не распознана.
    """
    try:
        # 1. Парсим URL, чтобы надежно получить домен и путь
        parsed_url = urlparse(link)
        domain = parsed_url.netloc
        path = parsed_url.path
    except Exception:
        # Если ссылка некорректна, urlparse может выдать ошибку
        return None

    # 2. Ищем подходящий парсер по домену
    for parser in SOCIAL_MEDIA_PARSERS:
        if domain in parser["domains"]:
            # 3. Если домен совпал, применяем регулярное выражение к пути
            match = parser["pattern"].search(path)
            if match:
                # 4. Если идентификатор найден, формируем результат
                identifier = match.group(1)
                summary = parser["template"].format(identifier=identifier)
                return SocialMediaInfo(
                    platform=parser["platform"],
                    identifier=identifier,
                    analysis_summary=summary
                )

    # 5. Если ни один парсер не подошел
    return None