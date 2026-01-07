import asyncio
import json
import logging
from pathlib import Path

import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, REPORT_HOUR, REPORT_MINUTE
from services import generate_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))

SUBSCRIBERS_FILE = Path(__file__).parent / "subscribers.json"


def load_subscribers() -> set:
    """Загружает список подписчиков из файла."""
    if SUBSCRIBERS_FILE.exists():
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_subscribers(subscribers: set):
    """Сохраняет список подписчиков в файл."""
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)


subscribers = load_subscribers()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start — подписка на рассылку."""
    chat_id = message.chat.id
    
    if chat_id in subscribers:
        await message.answer(
            "✅ Вы уже подписаны на ежедневные сводки.\n\n"
            f"📅 Рассылка в {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} МСК\n"
            "/report — получить сводку сейчас\n"
            "/stop — отписаться"
        )
    else:
        subscribers.add(chat_id)
        save_subscribers(subscribers)
        await message.answer(
            "👋 Привет! Вы подписались на ежедневные сводки.\n\n"
            f"📅 Рассылка в {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} МСК\n"
            "/report — получить сводку сейчас\n"
            "/stop — отписаться"
        )
        logger.info(f"Новый подписчик: {chat_id}")


@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    """Обработчик команды /stop — отписка от рассылки."""
    chat_id = message.chat.id
    
    if chat_id in subscribers:
        subscribers.discard(chat_id)
        save_subscribers(subscribers)
        await message.answer("🔕 Вы отписались от ежедневных сводок.\n/start — подписаться снова")
        logger.info(f"Отписка: {chat_id}")
    else:
        await message.answer("Вы не были подписаны.\n/start — подписаться")


@dp.message(Command("report"))
async def cmd_report(message: types.Message):
    """Обработчик команды /report — ручной запрос сводки."""
    await message.answer("⏳ Собираю данные...")
    
    try:
        report = generate_report()
        await message.answer(report, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {e}")
        await message.answer("❌ Ошибка при получении данных")


async def send_daily_report():
    """Отправляет ежедневный отчет всем подписчикам."""
    if not subscribers:
        logger.info("Нет подписчиков для рассылки")
        return
    
    try:
        report = generate_report()
        for chat_id in subscribers.copy():
            try:
                await bot.send_message(chat_id, report, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Ошибка отправки в {chat_id}: {e}")
        logger.info(f"Отчет отправлен {len(subscribers)} подписчикам")
    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {e}")


async def main():
    """Запуск бота."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не установлен! Задайте переменную окружения.")
    
    scheduler.add_job(
        send_daily_report,
        CronTrigger(hour=REPORT_HOUR, minute=REPORT_MINUTE),
        id="daily_report"
    )
    scheduler.start()
    logger.info(f"Планировщик запущен: отчеты в {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} МСК")
    logger.info(f"Подписчиков: {len(subscribers)}")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
