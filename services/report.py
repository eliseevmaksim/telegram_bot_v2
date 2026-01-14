from datetime import datetime
import pytz
import logging

from .currency import get_currency
from .crypto import get_bitcoin_rate, get_ethereum_rate
from .weather import get_weather, get_temperatures
from .commodities import get_all_commodities

logger = logging.getLogger(__name__)


def generate_report() -> str:
    """Формирует полную сводку для отправки в Telegram."""
    
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    date_str = now.strftime("%d.%m.%Y")
    
    lines = [f"📊 *Сводка на {date_str}*\n"]
    
    # Валюты
    try:
        lines.append("💱 *Курсы валют (ВТБ):*")
        usd_rate = get_currency('RUB', 'USD')
        eur_rate = get_currency('RUB', 'EUR')
        cny_rate = get_currency('RUB', 'CNY')
        if usd_rate:
            lines.append(f"  USD: {usd_rate} ₽")
        if eur_rate:
            lines.append(f"  EUR: {eur_rate} ₽")
        if cny_rate:
            lines.append(f"  CNY: {cny_rate / 10} ₽")
    except Exception as e:
        logger.error(f"Ошибка в блоке валют: {e}")
        lines.append("  Данные недоступны")
    
    # Крипта
    try:
        lines.append("\n₿ *Крипта:*")
        btc_rate = get_bitcoin_rate()
        eth_rate = get_ethereum_rate()
        if btc_rate:
            lines.append(f"  Bitcoin: ${btc_rate:,.0f}")
        if eth_rate:
            lines.append(f"  Ethereum: ${eth_rate:,.0f}")
    except Exception as e:
        logger.error(f"Ошибка в блоке крипты: {e}")
        lines.append("  Данные недоступны")
    
    # Сырье
    try:
        lines.append("\n🏦 *Биржевые котировки:*")
        commodities = get_all_commodities()
        commodity_names = {"usd": "Доллар", "brent": "Нефть Brent", "urals": "Нефть Urals", "gold": "Золото", "silver": "Серебро"}
        for key in ["usd", "brent", "urals", "gold", "silver"]:
            value = commodities.get(key)
            if value:
                unit = "₽" if key == "usd" else "$"
                lines.append(f"  {commodity_names[key]}: {value} {unit}")
    except Exception as e:
        logger.error(f"Ошибка в блоке котировок: {e}")
        lines.append("  Данные недоступны")
    
    # Погода
    try:
        lines.append(f"\n🌤 *Погода в Москве ({date_str}):*")
        weather_df = get_weather()
        if weather_df is not None and not weather_df.empty:
            temps = get_temperatures(weather_df, [9, 12, 15, 18, 21])
            for hour, temp in temps.items():
                if temp is not None:
                    lines.append(f"  {hour:02d}:00: {temp:+.1f}°C")
        else:
            lines.append("  Данные недоступны")
    except Exception as e:
        logger.error(f"Ошибка в блоке погоды: {e}")
        lines.append("  Данные недоступны")
    
    return "\n".join(lines)
