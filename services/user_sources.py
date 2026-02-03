import json
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

SOURCES_FILE = Path(__file__).parent.parent / "user_sources.json"
DEFAULT_SOURCES = ["rbc_news"]
MAX_SOURCES = 5


def load_all_sources() -> dict:
    """Загружает все настройки источников."""
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_all_sources(data: dict):
    """Сохраняет все настройки источников."""
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_sources(user_id: int) -> list:
    """Возвращает список источников пользователя."""
    data = load_all_sources()
    return data.get(str(user_id), DEFAULT_SOURCES.copy())


def add_user_source(user_id: int, source: str) -> tuple:
    """
    Добавляет источник пользователю.
    
    Returns:
        tuple: (успех, сообщение)
    """
    # Извлекаем название канала из URL
    channel = extract_channel_name(source)
    if not channel:
        return False, "Неверный формат. Используйте: https://t.me/s/channel или @channel"
    
    data = load_all_sources()
    user_key = str(user_id)
    
    if user_key not in data:
        data[user_key] = DEFAULT_SOURCES.copy()
    
    if len(data[user_key]) >= MAX_SOURCES:
        return False, f"Максимум {MAX_SOURCES} источников. Удалите лишние через /removesource"
    
    if channel in data[user_key]:
        return False, f"Канал @{channel} уже добавлен"
    
    data[user_key].append(channel)
    save_all_sources(data)
    
    return True, f"Канал @{channel} добавлен"


def remove_user_source(user_id: int, channel: str) -> tuple:
    """Удаляет источник у пользователя."""
    data = load_all_sources()
    user_key = str(user_id)
    
    if user_key not in data:
        return False, "У вас нет настроенных источников"
    
    if channel not in data[user_key]:
        return False, f"Канал @{channel} не найден в вашем списке"
    
    data[user_key].remove(channel)
    
    # Если список пуст, возвращаем дефолт
    if not data[user_key]:
        data[user_key] = DEFAULT_SOURCES.copy()
    
    save_all_sources(data)
    return True, f"Канал @{channel} удалён"


def clear_user_sources(user_id: int) -> str:
    """Сбрасывает источники к дефолту."""
    data = load_all_sources()
    data[str(user_id)] = DEFAULT_SOURCES.copy()
    save_all_sources(data)
    return "Источники сброшены к стандартным"


def extract_channel_name(source: str):
    """
    Извлекает название канала из разных форматов.
    
    Поддерживает:
    - https://t.me/s/channel
    - https://t.me/channel
    - t.me/s/channel
    - @channel
    - channel
    """
    source = source.strip()
    
    # https://t.me/s/channel или https://t.me/channel
    match = re.search(r't\.me/(?:s/)?([a-zA-Z0-9_]+)', source)
    if match:
        return match.group(1)
    
    # @channel
    if source.startswith('@'):
        return source[1:]
    
    # Просто название канала
    if re.match(r'^[a-zA-Z0-9_]+$', source):
        return source
    
    return None


def get_channel_url(channel: str) -> str:
    """Возвращает URL для парсинга канала."""
    return f"https://t.me/s/{channel}"
