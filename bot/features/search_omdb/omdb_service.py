import aiohttp
from typing import Dict, Any
from config.config import load_config

config = load_config()


class OMDbService:
    """Сервис для работы с OMDb API"""

    API_KEY = config.omdb.api_key
    BASE_URL = "https://www.omdbapi.com/"

    @staticmethod
    def get_safe_value(details: Dict[str, Any], key: str) -> Any:
        """
        Безопасное получение значения из ответа OMDB API.
        Проверяет существование ключа и что значение не равно "N/A"

        Args:
            details: Словарь с данными от OMDB API
            key: Ключ для получения значения

        Returns:
            Значение из словаря если оно существует и не равно "N/A", иначе None
        """
        if key not in details:
            return None
        value = details[key]
        return value if value != "N/A" else None

    @classmethod
    async def search_movies_series(cls, query: str, page: int = 1) -> Dict[str, Any]:
        """
        Поиск фильмов и сериалов по запросу
        """
        params = {
            "s": query,
            "page": page,
            "apikey": cls.API_KEY,
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(cls.BASE_URL, params=params) as response:
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
    async def get_item_details(cls, imdb_id: str) -> Dict[str, Any]:
        """
        Получение детальной информации о фильме/сериале по IMDb ID
        """
        params = {
            "i": imdb_id,
            "apikey": cls.API_KEY,
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(cls.BASE_URL, params=params) as response:
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
