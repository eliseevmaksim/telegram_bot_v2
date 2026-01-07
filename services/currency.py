import requests


def get_currency(currency_from: str = 'RUB', currency_to: str = 'USD') -> float:
    """Получает курс валюты через API VTB."""
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    json_data = {
        'categoryId': 1,
        'categoryTypeId': 1,
        'currencyFrom': currency_from,
        'currencyTo': currency_to,
        'fromSumma': 100000,
        'toSumma': 0,
    }

    try:
        response = requests.post(
            'https://www.vtb.ru/api/currencyrates/convert',
            headers=headers,
            json=json_data,
            timeout=10
        )
        return response.json()["fromRate"]
    except Exception as e:
        print(f"Ошибка получения курса валюты: {e}")
        return None

