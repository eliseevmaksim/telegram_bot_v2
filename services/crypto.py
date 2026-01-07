import requests


def get_bitcoin_rate() -> float:
    """Получает текущий курс биткоина в USD."""
    
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params=params,
            timeout=10
        )
        return response.json()["bitcoin"]["usd"]
    except Exception as e:
        print(f"Ошибка получения курса биткоина: {e}")
        return None


def get_ethereum_rate() -> float:
    """Получает текущий курс эфириума в USD."""
    
    params = {
        'ids': 'ethereum',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params=params,
            timeout=10
        )
        return response.json()["ethereum"]["usd"]
    except Exception as e:
        print(f"Ошибка получения курса эфириума: {e}")
        return None

