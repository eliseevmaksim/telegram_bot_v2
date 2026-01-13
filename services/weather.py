import requests


def get_weather() -> dict:
    """Получает прогноз погоды для Москвы через Open-Meteo API."""
    
    params = {
        "latitude": 55.7558,
        "longitude": 37.6173,
        "hourly": "temperature_2m",
        "timezone": "Europe/Moscow",
        "forecast_days": 1
    }
    
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
            timeout=10
        )
        data = response.json()
        
        times = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]
        
        result = {}
        for time_str, temp in zip(times, temps):
            hour = int(time_str.split("T")[1].split(":")[0])
            result[hour] = temp
        
        return result
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None


def get_temperatures(weather_data, target_hours: list = None) -> dict:
    """Возвращает температуру для указанных часов."""
    if target_hours is None:
        target_hours = [9, 12, 15, 18, 21]
    
    if weather_data is None:
        return {h: None for h in target_hours}
    
    return {h: weather_data.get(h) for h in target_hours}
