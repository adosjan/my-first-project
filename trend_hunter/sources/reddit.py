"""
Парсер Reddit
Получает горячие посты из бизнес/стартап сабреддитов
"""
import asyncio
import aiohttp
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedditFetcher:
    """Получает посты из Reddit без API (через JSON endpoints)"""

    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            "User-Agent": "TrendHunter/1.0 (Business Ideas Research Bot)"
        }

    async def get_subreddit_hot(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """
        Получает горячие посты из сабреддита

        Args:
            subreddit: Название сабреддита (без r/)
            limit: Количество постов

        Returns:
            Список постов
        """
        posts = []
        url = f"{self.base_url}/r/{subreddit}/hot.json?limit={limit}"

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = self._parse_posts(data, subreddit)
                        logger.info(f"Получено {len(posts)} постов из r/{subreddit}")
                    elif response.status == 429:
                        logger.warning(f"Reddit rate limit для r/{subreddit}, ждём...")
                        await asyncio.sleep(60)
                    else:
                        logger.warning(f"Reddit r/{subreddit}: статус {response.status}")

        except Exception as e:
            logger.error(f"Ошибка получения r/{subreddit}: {e}")

        return posts

    def _parse_posts(self, data: Dict, subreddit: str) -> List[Dict]:
        """Парсит JSON-ответ Reddit"""
        posts = []

        try:
            children = data.get("data", {}).get("children", [])

            for child in children:
                post_data = child.get("data", {})

                # Пропускаем закреплённые посты
                if post_data.get("stickied"):
                    continue

                post = {
                    "id": post_data.get("id"),
                    "title": post_data.get("title"),
                    "subreddit": subreddit,
                    "score": post_data.get("score", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "selftext": post_data.get("selftext", "")[:500],  # Первые 500 символов
                    "created_utc": post_data.get("created_utc"),
                    "author": post_data.get("author"),
                    "source": "reddit",
                    "fetched_at": datetime.now().isoformat()
                }

                # Вычисляем "горячесть" - насколько пост набирает обороты
                if post["score"] > 10 and post["num_comments"] > 5:
                    post["engagement_score"] = post["score"] * post["upvote_ratio"] + post["num_comments"] * 2
                else:
                    post["engagement_score"] = 0

                posts.append(post)

        except Exception as e:
            logger.error(f"Ошибка парсинга постов: {e}")

        return posts

    async def search_posts(self, query: str, subreddit: str = None, limit: int = 25) -> List[Dict]:
        """
        Поиск постов по ключевому слову

        Args:
            query: Поисковый запрос
            subreddit: Сабреддит для поиска (опционально)
            limit: Количество результатов

        Returns:
            Список найденных постов
        """
        posts = []

        if subreddit:
            url = f"{self.base_url}/r/{subreddit}/search.json?q={query}&restrict_sr=1&limit={limit}&sort=hot"
        else:
            url = f"{self.base_url}/search.json?q={query}&limit={limit}&sort=hot"

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = self._parse_posts(data, subreddit or "search")
                        logger.info(f"Найдено {len(posts)} постов по запросу '{query}'")

        except Exception as e:
            logger.error(f"Ошибка поиска '{query}': {e}")

        return posts


async def fetch_reddit_trends(subreddits: List[str], keywords: List[str] = None) -> List[Dict]:
    """
    Главная функция для получения трендов с Reddit

    Args:
        subreddits: Список сабреддитов для мониторинга
        keywords: Дополнительные ключевые слова для поиска

    Returns:
        Список всех найденных постов, отсортированных по engagement
    """
    fetcher = RedditFetcher()
    all_posts = []

    # Получаем горячие посты из каждого сабреддита
    for subreddit in subreddits:
        posts = await fetcher.get_subreddit_hot(subreddit, limit=20)
        all_posts.extend(posts)
        await asyncio.sleep(2)  # Пауза между запросами (Reddit rate limit)

    # Дополнительный поиск по ключевым словам
    if keywords:
        for keyword in keywords:
            posts = await fetcher.search_posts(keyword, limit=15)
            all_posts.extend(posts)
            await asyncio.sleep(2)

    # Убираем дубликаты по ID
    seen_ids = set()
    unique_posts = []
    for post in all_posts:
        if post["id"] not in seen_ids:
            seen_ids.add(post["id"])
            unique_posts.append(post)

    # Сортируем по engagement_score
    unique_posts.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)

    return unique_posts


# Тест
if __name__ == "__main__":
    async def main():
        subreddits = ["Entrepreneur", "SideProject", "startups", "SaaS"]
        keywords = ["business idea", "startup idea", "side project"]

        posts = await fetch_reddit_trends(subreddits, keywords)

        print(f"\nНайдено {len(posts)} уникальных постов:\n")
        for i, post in enumerate(posts[:15], 1):
            print(f"{i}. [{post['subreddit']}] {post['title'][:60]}...")
            print(f"   Score: {post['score']} | Comments: {post['num_comments']} | Engagement: {post['engagement_score']:.0f}")
            print()

    asyncio.run(main())
