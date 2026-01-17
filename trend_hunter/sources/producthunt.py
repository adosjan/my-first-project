"""
Парсер Product Hunt
Использует публичный RSS для бесплатного доступа
(GraphQL API требует регистрации)
"""
import asyncio
import aiohttp
from typing import List, Dict
from datetime import datetime
import xml.etree.ElementTree as ET
import logging
import re

logger = logging.getLogger(__name__)


class ProductHuntFetcher:
    """Получает данные из Product Hunt через RSS"""

    def __init__(self):
        # RSS фиды Product Hunt
        self.feeds = {
            "today": "https://www.producthunt.com/feed",
            "tech": "https://www.producthunt.com/topics/tech/feed",
            "saas": "https://www.producthunt.com/topics/software-engineering/feed",
            "ai": "https://www.producthunt.com/topics/artificial-intelligence/feed",
            "productivity": "https://www.producthunt.com/topics/productivity/feed",
        }

    async def get_products(self, category: str = "today", limit: int = 30) -> List[Dict]:
        """
        Получает продукты из RSS фида

        Args:
            category: Категория (today, tech, saas, ai, productivity)
            limit: Количество продуктов

        Returns:
            Список продуктов
        """
        products = []
        feed_url = self.feeds.get(category, self.feeds["today"])

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0 SaaS-Pipeline/1.0"}
                async with session.get(feed_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        products = self._parse_rss(content, category)[:limit]
                        logger.info(f"Получено {len(products)} продуктов из Product Hunt ({category})")
                    else:
                        logger.warning(f"Product Hunt вернул статус {response.status}")

        except Exception as e:
            logger.error(f"Ошибка получения Product Hunt: {e}")

        return products

    def _parse_rss(self, content: str, category: str) -> List[Dict]:
        """Парсит RSS фид Product Hunt"""
        products = []

        try:
            root = ET.fromstring(content)

            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                pub_date_elem = item.find('pubDate')

                if title_elem is not None:
                    # Извлекаем название и tagline из title
                    title_text = title_elem.text or ""
                    # Формат: "Product Name — Tagline"
                    parts = title_text.split(' — ')
                    name = parts[0].strip() if parts else title_text
                    tagline = parts[1].strip() if len(parts) > 1 else ""

                    # Парсим описание (убираем HTML теги)
                    description = ""
                    if description_elem is not None and description_elem.text:
                        description = re.sub(r'<[^>]+>', '', description_elem.text)[:500]

                    product = {
                        "name": name,
                        "tagline": tagline,
                        "url": link_elem.text if link_elem is not None else "",
                        "description": description,
                        "pub_date": pub_date_elem.text if pub_date_elem is not None else "",
                        "category": category,
                        "source": "producthunt",
                        "fetched_at": datetime.now().isoformat()
                    }
                    products.append(product)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга RSS: {e}")

        return products

    async def get_all_categories(self) -> List[Dict]:
        """
        Получает продукты из всех категорий

        Returns:
            Список всех продуктов
        """
        all_products = []

        for category in self.feeds.keys():
            products = await self.get_products(category, limit=20)
            all_products.extend(products)
            await asyncio.sleep(1)  # Пауза между запросами

        # Убираем дубликаты по URL
        seen_urls = set()
        unique = []
        for product in all_products:
            if product["url"] and product["url"] not in seen_urls:
                seen_urls.add(product["url"])
                unique.append(product)

        return unique


async def fetch_producthunt(categories: List[str] = None) -> List[Dict]:
    """
    Главная функция для получения продуктов из Product Hunt

    Args:
        categories: Список категорий (по умолчанию все)

    Returns:
        Список продуктов
    """
    fetcher = ProductHuntFetcher()

    if categories:
        all_products = []
        for category in categories:
            products = await fetcher.get_products(category)
            all_products.extend(products)
            await asyncio.sleep(1)

        # Дедупликация
        seen = set()
        unique = []
        for p in all_products:
            if p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        return unique
    else:
        return await fetcher.get_all_categories()


# Тест
if __name__ == "__main__":
    async def main():
        products = await fetch_producthunt(["today", "ai", "saas"])

        print(f"\nПолучено {len(products)} продуктов из Product Hunt\n")

        for i, product in enumerate(products[:10], 1):
            print(f"{i}. {product['name']}")
            if product['tagline']:
                print(f"   {product['tagline']}")
            print(f"   Категория: {product['category']}")
            print(f"   {product['url']}")
            print()

    asyncio.run(main())
