import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (из .env файла)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Время отправки ежедневного отчета (Москва)
REPORT_HOUR = 9
REPORT_MINUTE = 0

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
