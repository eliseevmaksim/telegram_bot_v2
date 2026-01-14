import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from config import DEEPSEEK_API_KEY


def parse_news(url: str = "https://t.me/s/rbc_news", limit: int = 10) -> list:
    """
    Парсит последние новости из Telegram канала.
    
    Args:
        url: URL публичного канала
        limit: количество последних новостей
    
    Returns:
        list: список текстов новостей
    """
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
            # Удаляем ненужные теги
            for tag in post.find_all(['br', 'tg-emoji', 'a', 'i', 'b']):
                if tag.name in ['br']:
                    tag.replace_with(' ')
                elif tag.name in ['tg-emoji']:
                    tag.decompose()
            
            text = post.get_text(strip=True)
            # Очищаем от проблемных символов
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            if text and len(text) > 20:
                news_list.append(text)
        
        return news_list
    except Exception as e:
        print(f"Ошибка парсинга новостей: {e}")
        return []


def summarize_news(news_list: list) -> str:
    """
    Суммаризирует новости через DeepSeek API.
    
    Args:
        news_list: список текстов новостей
    
    Returns:
        str: краткая сводка новостей
    """
    if not news_list:
        return "Новости недоступны"
    
    if not DEEPSEEK_API_KEY:
        return "API ключ не настроен"
    
    news_text = "\n\n".join([f"{i+1}. {news}" for i, news in enumerate(news_list)])
    # Убеждаемся что текст в UTF-8
    news_text = news_text.encode('utf-8', errors='ignore').decode('utf-8')
    
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
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка суммаризации: {e}")
        return "Ошибка получения сводки новостей"


def get_news_summary() -> str:
    """Получает и суммаризирует новости."""
    news = parse_news()
    return summarize_news(news)
