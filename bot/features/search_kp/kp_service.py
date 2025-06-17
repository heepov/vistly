import aiohttp
from typing import Dict, Any
from config.config import load_config

config = load_config()


class KpService:
    """Сервис для работы с Kinopoisk.dev API"""

    API_KEY = config.kp.api_key
    BASE_URL = "https://api.kinopoisk.dev/v1.4/"

    @staticmethod
    def get_safe_value(details: dict, key: str, default=None) -> Any:
        keys = key.split(".")
        value = details
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value if value not in (None, "N/A") else default

    @classmethod
    async def search_movies_series(cls, query: str, page: int = 1) -> Dict[str, Any]:
        """
        Поиск фильмов и сериалов по названию
        """
        url = cls.BASE_URL + "movie/search"
        params = {
            "query": query,
            "page": page,
            "limit": 10,  # Можно изменить лимит по необходимости
        }
        headers = {"X-API-KEY": cls.API_KEY}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "Response": "False",
                            "Error": f"API request failed with status {response.status}",
                        }
            except Exception as e:
                return {
                    "Response": "False",
                    "Error": f"Error during API request: {str(e)}",
                }

    @classmethod
    async def get_item_details(cls, kp_id: str) -> Dict[str, Any]:
        """
        Получение детальной информации о фильме/сериале по Kinopoisk ID
        """
        url = cls.BASE_URL + f"movie/{kp_id}"
        headers = {"X-API-KEY": cls.API_KEY}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "Response": "False",
                            "Error": f"API request failed with status {response.status}",
                        }
            except Exception as e:
                return {
                    "Response": "False",
                    "Error": f"Error during API request: {str(e)}",
                }
