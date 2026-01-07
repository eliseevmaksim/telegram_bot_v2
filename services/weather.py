from datetime import datetime, timedelta
import meteostat as ms
from meteostat import Point
from meteostat import Hourly
import pytz


def get_weather() -> dict:
    """Получает прогноз погоды для Москвы на сегодня."""
    
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)

    moscow = ms.Point(55.7558, 37.6173, 150)
    
    try:
        data = Hourly(moscow, start, end)
        df = data.fetch().reset_index()
        return df
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None


def get_temperatures(df, target_hours: list = None) -> dict:
    """
    Возвращает температуру для указанных часов.
    
    Args:
        df: DataFrame с колонками 'time' и 'temp'
        target_hours: список часов (по умолчанию [9, 12, 15, 18, 21])
    
    Returns:
        dict: {hour: temperature}
    """
    if target_hours is None:
        target_hours = [9, 12, 15, 18, 21]
    
    result = {}
    for hour in target_hours:
        try:
            temp = df.loc[df['time'].dt.hour == hour, 'temp'].iloc[0]
            result[hour] = temp
        except (IndexError, KeyError):
            result[hour] = None
    
    return result