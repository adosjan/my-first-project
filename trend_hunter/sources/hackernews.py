"""
Парсер HackerNews
Использует бесплатный Firebase API
"""
import asyncio
import aiohttp
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HackerNewsFetcher:
    """Получает данные из HackerNews API"""

    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"

    async def get_top_stories(self, limit: int = 50) -> List[Dict]:
        """
        Получает топ историй с HackerNews

        Args:
            limit: Количество историй

        Returns:
            Список историй
        """
        stories = []

        try:
            async with aiohttp.ClientSession() as session:
                # Получаем ID топ историй
                async with session.get(f"{self.base_url}/topstories.json") as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        story_ids = story_ids[:limit]

                        # Получаем детали каждой истории
                        tasks = [self._fetch_item(session, story_id) for story_id in story_ids]
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for result in results:
                            if isinstance(result, dict) and result:
                                stories.append(result)

                        logger.info(f"Получено {len(stories)} историй из HackerNews")

        except Exception as e:
            logger.error(f"Ошибка получения HackerNews: {e}")

        return stories

    async def get_show_hn(self, limit: int = 30) -> List[Dict]:
        """
        Получает Show HN посты (новые проекты!)
        Это золотая жила для SaaS-идей

        Args:
            limit: Количество постов

        Returns:
            Список Show HN постов
        """
        stories = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/showstories.json") as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        story_ids = story_ids[:limit]

                        tasks = [self._fetch_item(session, story_id) for story_id in story_ids]
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for result in results:
                            if isinstance(result, dict) and result:
                                result["is_show_hn"] = True
                                stories.append(result)

                        logger.info(f"Получено {len(stories)} Show HN постов")

        except Exception as e:
            logger.error(f"Ошибка получения Show HN: {e}")

        return stories

    async def get_ask_hn(self, limit: int = 20) -> List[Dict]:
        """
        Получает Ask HN посты (вопросы сообщества)
        Отличный источник для понимания проблем

        Args:
            limit: Количество постов

        Returns:
            Список Ask HN постов
        """
        stories = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/askstories.json") as response:
                    if response.status == 200:
                        story_ids = await response.json()
                        story_ids = story_ids[:limit]

                        tasks = [self._fetch_item(session, story_id) for story_id in story_ids]
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for result in results:
                            if isinstance(result, dict) and result:
                                result["is_ask_hn"] = True
                                stories.append(result)

                        logger.info(f"Получено {len(stories)} Ask HN постов")

        except Exception as e:
            logger.error(f"Ошибка получения Ask HN: {e}")

        return stories

    async def _fetch_item(self, session: aiohttp.ClientSession, item_id: int) -> Dict:
        """Получает детали одного item"""
        try:
            async with session.get(f"{self.base_url}/item/{item_id}.json") as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return {
                            "id": data.get("id"),
                            "title": data.get("title", ""),
                            "url": data.get("url", ""),
                            "hn_url": f"https://news.ycombinator.com/item?id={data.get('id')}",
                            "score": data.get("score", 0),
                            "comments": data.get("descendants", 0),
                            "author": data.get("by", ""),
                            "time": data.get("time"),
                            "text": data.get("text", "")[:500] if data.get("text") else "",
                            "type": data.get("type", "story"),
                            "source": "hackernews",
                            "fetched_at": datetime.now().isoformat()
                        }
        except Exception as e:
            logger.debug(f"Ошибка получения item {item_id}: {e}")

        return {}


async def fetch_hackernews(include_show: bool = True, include_ask: bool = True) -> List[Dict]:
    """
    Главная функция для получения данных из HackerNews

    Args:
        include_show: Включить Show HN
        include_ask: Включить Ask HN

    Returns:
        Список всех историй
    """
    fetcher = HackerNewsFetcher()
    all_stories = []

    # Top stories
    top = await fetcher.get_top_stories(limit=50)
    all_stories.extend(top)

    # Show HN — новые проекты (очень важно для SaaS!)
    if include_show:
        show = await fetcher.get_show_hn(limit=30)
        all_stories.extend(show)

    # Ask HN — вопросы (для понимания проблем)
    if include_ask:
        ask = await fetcher.get_ask_hn(limit=20)
        all_stories.extend(ask)

    # Убираем дубликаты
    seen_ids = set()
    unique = []
    for story in all_stories:
        if story.get("id") and story["id"] not in seen_ids:
            seen_ids.add(story["id"])
            unique.append(story)

    # Сортируем по score
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    return unique


# Тест
if __name__ == "__main__":
    async def main():
        stories = await fetch_hackernews()

        print(f"\nПолучено {len(stories)} историй из HackerNews\n")

        print("=== TOP STORIES ===")
        for story in stories[:5]:
            print(f"[{story['score']}] {story['title'][:60]}")
            print(f"    {story['hn_url']}")
            print()

        print("\n=== SHOW HN (новые продукты) ===")
        show_hn = [s for s in stories if s.get("is_show_hn")]
        for story in show_hn[:5]:
            print(f"[{story['score']}] {story['title'][:60]}")
            print()

    asyncio.run(main())
