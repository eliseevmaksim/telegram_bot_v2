import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import logging

from config import DEEPSEEK_API_KEY
from .user_sources import get_user_sources, get_channel_url, DEFAULT_SOURCES

logger = logging.getLogger(__name__)


def parse_single_channel(channel: str, limit: int = 5) -> list:
    """Парсит новости из одного Telegram канала."""
    url = get_channel_url(channel)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Charset': 'utf-8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'html.parser')
        
        posts = soup.find_all('div', class_='tgme_widget_message_text js-message_text')
        
        news_list = []
        for post in posts[-limit:]:
            for tag in post.find_all(['br', 'tg-emoji', 'a', 'i', 'b']):
                if tag.name == 'br':
                    tag.replace_with(' ')
                elif tag.name == 'tg-emoji':
                    tag.decompose()
            
            text = post.get_text(strip=True)
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            if text and len(text) > 20:
                news_list.append({"channel": channel, "text": text})
        
        return news_list
    except Exception as e:
        logger.error(f"Ошибка парсинга @{channel}: {e}")
        return []


def parse_news(channels: list = None, limit_per_channel: int = 5) -> list:
    """
    Парсит новости из нескольких Telegram каналов.
    
    Args:
        channels: список названий каналов
        limit_per_channel: количество новостей с каждого канала
    
    Returns:
        list: список новостей
    """
    if channels is None:
        channels = DEFAULT_SOURCES
    
    all_news = []
    for channel in channels:
        news = parse_single_channel(channel, limit_per_channel)
        all_news.extend(news)
        logger.info(f"@{channel}: {len(news)} новостей")
    
    logger.info(f"Всего собрано {len(all_news)} новостей из {len(channels)} каналов")
    return all_news


def summarize_news(news_list: list) -> str:
    """Суммаризирует новости через DeepSeek API."""
    if not news_list:
        return "Новости недоступны"
    
    if not DEEPSEEK_API_KEY:
        return "API ключ не настроен"
    
    # Форматируем новости с указанием источника
    news_text = "\n\n".join([
        f"{i+1}. [{item['channel']}] {item['text']}" 
        for i, item in enumerate(news_list)
    ])
    news_text = news_text.encode('utf-8', errors='ignore').decode('utf-8')
    
    logger.info(f"Отправляю {len(news_list)} новостей в DeepSeek")
    
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Ты новостной редактор. Сделай краткую сводку главных новостей на русском языке. Выдели ключевые события и темы. Формат: короткие пункты с эмодзи. Не добавляй вступление и заключение."
                },
                {
                    "role": "user",
                    "content": f"Сделай краткую сводку этих новостей:\n\n{news_text}"
                }
            ],
            temperature=0.6
        )
        
        logger.info("Сводка получена успешно")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка DeepSeek API: {e}")
        return "Ошибка получения сводки новостей"


def get_news_summary(user_id: int = None) -> str:
    """
    Получает и суммаризирует новости для пользователя.
    
    Args:
        user_id: ID пользователя для персональных источников
    """
    if user_id:
        channels = get_user_sources(user_id)
    else:
        channels = DEFAULT_SOURCES
    
    news = parse_news(channels)
    return summarize_news(news)
