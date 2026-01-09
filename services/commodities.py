import re
import json
import requests


def get_commodity_price(item: str) -> float:
    """
    Получает цену на сырьевой товар с tradingeconomics.com
    
    Args:
        item: название товара (gold, silver, urals-oil)
    
    Returns:
        float: цена или None при ошибке
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(
            f"https://tradingeconomics.com/commodity/{item}",
            headers=headers,
            timeout=10
        )
        html = response.text

        pattern = r'TEChartsMeta\s*=\s*(\[.*?\]);'
        match = re.search(pattern, html, re.DOTALL)

        if match:
            json_str = match.group(1).replace('\\/', '/')
            data = json.loads(json_str)
            last_value = data[0]['last']
            return round(last_value, 2)
        return None
        
    except Exception as e:
        print(f"Ошибка получения цены {item}: {e}")
        return None


def get_usd_rate() -> float:
    """Получает курс доллара с tradingeconomics.com/russia/currency"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(
            "https://tradingeconomics.com/russia/currency",
            headers=headers,
            timeout=10
        )
        html = response.text

        pattern = r'TEChartsMeta\s*=\s*(\[.*?\]);'
        match = re.search(pattern, html, re.DOTALL)

        if match:
            json_str = match.group(1).replace('\\/', '/')
            data = json.loads(json_str)
            last_value = data[0]['last']
            return round(last_value, 2)
        return None
        
    except Exception as e:
        print(f"Ошибка получения курса доллара: {e}")
        return None


def get_all_commodities() -> dict:
    """Получает цены на золото, серебро, нефть Brent/Urals и курс доллара."""
    result = {
        "usd": get_usd_rate(),
        "brent": get_commodity_price("brent-crude-oil"),
        "urals": get_commodity_price("urals-oil"),
        "gold": get_commodity_price("gold"),
        "silver": get_commodity_price("silver"),
    }
    return result

