import asyncio
import json
import logging
from pathlib import Path

import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, REPORT_HOUR, REPORT_MINUTE
from services import generate_report
from services.news import get_news_summary
from services.user_sources import (
    get_user_sources, add_user_source, remove_user_source, 
    clear_user_sources, DEFAULT_SOURCES
)

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


def get_main_keyboard():
    """Возвращает главную клавиатуру с кнопками."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Сводка", callback_data="action_report"),
            InlineKeyboardButton(text="📰 Новости", callback_data="action_news")
        ],
        [
            InlineKeyboardButton(text="⚙️ Источники", callback_data="action_sources"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="action_help")
        ]
    ])


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start — подписка на рассылку."""
    chat_id = message.chat.id
    
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        save_subscribers(subscribers)
        logger.info(f"Новый подписчик: {chat_id}")
    
    await message.answer(
        f"👋 Привет! Я бот ежедневных сводок.\n\n"
        f"📅 Каждый день в {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} МСК отправляю:\n"
        f"• Курсы валют и крипты\n"
        f"• Биржевые котировки\n"
        f"• Погоду в Москве\n"
        f"• Персональную подборку новостей\n\n"
        f"Выберите действие:",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Показывает справку по всем командам."""
    await message.answer(
        "📚 Все команды бота:\n\n"
        
        "📊 СВОДКИ\n"
        "/report — финансы, крипта, погода\n"
        "/news — новостная сводка\n\n"
        
        "📰 НАСТРОЙКИ НОВОСТЕЙ\n"
        "/sources — мои источники\n"
        "/addsource ссылка — добавить канал\n"
        "/removesource — удалить канал\n"
        "/clearsources — сбросить к стандартным\n\n"
        
        "⚙️ ПОДПИСКА\n"
        "/start — подписаться на рассылку\n"
        "/stop — отписаться\n\n"
        
        f"📅 Ежедневная рассылка в {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} МСК"
    )


@dp.callback_query(lambda c: c.data.startswith("action_"))
async def callback_main_actions(callback: CallbackQuery):
    """Обрабатывает нажатия на главные кнопки."""
    action = callback.data.replace("action_", "")
    
    if action == "report":
        await callback.answer("Собираю данные...")
        try:
            report = generate_report()
            await callback.message.answer(report, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            await callback.message.answer("❌ Ошибка при получении данных")
    
    elif action == "news":
        await callback.answer("Собираю новости...")
        user_id = callback.from_user.id
        try:
            news = get_news_summary(user_id)
            await callback.message.answer(f"📰 Новостная сводка:\n\n{news}")
        except Exception as e:
            logger.error(f"Ошибка получения новостей: {e}")
            await callback.message.answer("❌ Ошибка при получении новостей")
    
    elif action == "sources":
        user_id = callback.from_user.id
        sources = get_user_sources(user_id)
        sources_list = "\n".join([f"  • @{s}" for s in sources])
        await callback.message.answer(
            f"📋 Ваши источники новостей:\n{sources_list}\n\n"
            f"Команды:\n"
            f"/addsource ссылка — добавить канал\n"
            f"/removesource — удалить канал\n"
            f"/clearsources — сбросить к стандартным"
        )
        await callback.answer()
    
    elif action == "help":
        await callback.message.answer(
            "📚 Все команды бота:\n\n"
            
            "📊 СВОДКИ\n"
            "/report — финансы, крипта, погода\n"
            "/news — новостная сводка\n\n"
            
            "📰 НАСТРОЙКИ НОВОСТЕЙ\n"
            "/sources — мои источники\n"
            "/addsource ссылка — добавить канал\n"
            "/removesource — удалить канал\n"
            "/clearsources — сбросить к стандартным\n\n"
            
            "⚙️ ПОДПИСКА\n"
            "/start — подписаться на рассылку\n"
            "/stop — отписаться\n\n"
            
            f"📅 Ежедневная рассылка в {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} МСК"
        )
        await callback.answer()


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


@dp.message(Command("news"))
async def cmd_news(message: types.Message):
    """Обработчик команды /news — получить новостную сводку."""
    user_id = message.from_user.id
    sources = get_user_sources(user_id)
    
    await message.answer(f"📰 Собираю новости из {len(sources)} источников...")
    
    try:
        news = get_news_summary(user_id)
        await message.answer(f"📰 *Новостная сводка:*\n\n{news}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка получения новостей: {e}")
        await message.answer("❌ Ошибка при получении новостей")


@dp.message(Command("sources"))
async def cmd_sources(message: types.Message):
    """Показывает текущие источники новостей пользователя."""
    user_id = message.from_user.id
    sources = get_user_sources(user_id)
    
    sources_list = "\n".join([f"  • @{s}" for s in sources])
    
    await message.answer(
        f"📋 Ваши источники новостей:\n{sources_list}\n\n"
        f"Команды:\n"
        f"/addsource ссылка — добавить канал\n"
        f"/removesource — удалить канал\n"
        f"/clearsources — сбросить к стандартным"
    )


@dp.message(Command("addsource"))
async def cmd_addsource(message: types.Message):
    """Добавляет источник новостей."""
    user_id = message.from_user.id
    
    # Получаем аргумент команды
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❓ Укажите канал для добавления:\n"
            "/addsource https://t.me/s/channel\n"
            "или /addsource @channel"
        )
        return
    
    source = args[1]
    success, msg = add_user_source(user_id, source)
    
    if success:
        await message.answer(f"✅ {msg}")
    else:
        await message.answer(f"❌ {msg}")


@dp.message(Command("removesource"))
async def cmd_removesource(message: types.Message):
    """Показывает кнопки для удаления источников."""
    user_id = message.from_user.id
    sources = get_user_sources(user_id)
    
    if sources == DEFAULT_SOURCES:
        await message.answer("У вас только стандартные источники.")
        return
    
    # Создаём inline кнопки
    buttons = [
        [InlineKeyboardButton(text=f"❌ @{s}", callback_data=f"remove_{s}")]
        for s in sources
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer("Выберите канал для удаления:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def callback_remove_source(callback: CallbackQuery):
    """Обрабатывает удаление источника через кнопку."""
    user_id = callback.from_user.id
    channel = callback.data.replace("remove_", "")
    
    success, msg = remove_user_source(user_id, channel)
    
    await callback.answer(msg)
    
    if success:
        # Обновляем сообщение с кнопками
        sources = get_user_sources(user_id)
        if sources == DEFAULT_SOURCES:
            await callback.message.edit_text("✅ Источники обновлены. Остались только стандартные.")
        else:
            buttons = [
                [InlineKeyboardButton(text=f"❌ @{s}", callback_data=f"remove_{s}")]
                for s in sources
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.edit_reply_markup(reply_markup=keyboard)


@dp.message(Command("clearsources"))
async def cmd_clearsources(message: types.Message):
    """Сбрасывает источники к стандартным."""
    user_id = message.from_user.id
    msg = clear_user_sources(user_id)
    await message.answer(f"✅ {msg}\n\nСтандартный источник: @{DEFAULT_SOURCES[0]}")


async def send_daily_report():
    """Отправляет ежедневный отчет с новостями всем подписчикам."""
    if not subscribers:
        logger.info("Нет подписчиков для рассылки")
        return
    
    try:
        report = generate_report()
        
        for chat_id in subscribers.copy():
            try:
                # Получаем персональные новости для каждого пользователя
                user_report = report
                try:
                    news = get_news_summary(chat_id)
                    user_report += f"\n\n📰 *Новости:*\n{news}"
                except Exception as e:
                    logger.error(f"Ошибка получения новостей для {chat_id}: {e}")
                
                await bot.send_message(chat_id, user_report, parse_mode="Markdown")
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
