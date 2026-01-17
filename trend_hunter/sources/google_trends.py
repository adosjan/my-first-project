"""
Парсер Google Trends
Получает актуальные тренды и растущие поисковые запросы
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GoogleTrendsFetcher:
    """Получает данные из Google Trends"""

    def __init__(self):
        self.base_url = "https://trends.google.com/trends/api"
        self.daily_trends_url = "https://trends.google.com/trending/rss?geo=US"

    async def get_daily_trends(self, geo: str = "US") -> List[Dict]:
        """
        Получает ежедневные трендовые темы

        Args:
            geo: Код страны (US, RU, etc.)

        Returns:
            Список трендовых тем
        """
        trends = []

        try:
            # Используем RSS-фид Google Trends (не требует API)
            rss_url = f"https://trends.google.com/trending/rss?geo={geo}"

            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        trends = self._parse_rss(content)
                        logger.info(f"Получено {len(trends)} трендов из Google Trends ({geo})")
                    else:
                        logger.warning(f"Google Trends вернул статус {response.status}")

        except Exception as e:
            logger.error(f"Ошибка получения Google Trends: {e}")

        return trends

    def _parse_rss(self, content: str) -> List[Dict]:
        """Парсит RSS-фид Google Trends"""
        import xml.etree.ElementTree as ET

        trends = []
        try:
            root = ET.fromstring(content)

            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                traffic = item.find('{https://trends.google.com/trending/rss}approx_traffic')

                if title is not None:
                    trend = {
                        "title": title.text,
                        "link": link.text if link is not None else None,
                        "traffic": traffic.text if traffic is not None else "N/A",
                        "source": "google_trends",
                        "fetched_at": datetime.now().isoformat()
                    }
                    trends.append(trend)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга RSS: {e}")

        return trends

    async def search_trend(self, keyword: str, geo: str = "US") -> Dict:
        """
        Получает данные по конкретному ключевому слову

        Args:
            keyword: Ключевое слово для анализа
            geo: Код страны

        Returns:
            Данные о тренде
        """
        # Примечание: для полного API нужен pytrends
        # Здесь упрощённая версия через веб-скрапинг

        return {
            "keyword": keyword,
            "geo": geo,
            "interest_over_time": None,  # Требует pytrends
            "related_queries": None,
            "source": "google_trends",
            "fetched_at": datetime.now().isoformat()
        }


async def fetch_google_trends(categories: List[str] = None, geo: str = "US") -> List[Dict]:
    """
    Главная функция для получения трендов

    Args:
        categories: Список категорий для фильтрации (опционально)
        geo: Код страны

    Returns:
        Список всех найденных трендов
    """
    fetcher = GoogleTrendsFetcher()

    # Получаем ежедневные тренды
    trends = await fetcher.get_daily_trends(geo)

    # Также получаем тренды для других регионов
    for region in ["GB", "DE"]:  # UK, Germany - tech-хабы
        region_trends = await fetcher.get_daily_trends(region)
        trends.extend(region_trends)
        await asyncio.sleep(1)  # Пауза между запросами

    # Убираем дубликаты по названию
    seen = set()
    unique_trends = []
    for trend in trends:
        if trend["title"] not in seen:
            seen.add(trend["title"])
            unique_trends.append(trend)

    return unique_trends


# Тест
if __name__ == "__main__":
    async def main():
        trends = await fetch_google_trends()
        print(f"\nНайдено {len(trends)} уникальных трендов:\n")
        for i, trend in enumerate(trends[:10], 1):
            print(f"{i}. {trend['title']} ({trend['traffic']})")

    asyncio.run(main())
