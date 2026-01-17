"""
Trend Hunter - Главный скрипт
Запускает сбор данных, анализ и генерацию отчёта
"""
import asyncio
import logging
import schedule
import time
from datetime import datetime

from .sources.google_trends import fetch_google_trends
from .sources.reddit import fetch_reddit_trends
from .analyzer import analyze_trends, rank_ideas
from .storage import save_daily_report, save_raw_data
from .config import SUBREDDITS, SEARCH_CATEGORIES, SCHEDULE_TIME

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def run_trend_hunt():
    """
    Основной процесс поиска трендов
    1. Собирает данные из источников
    2. Анализирует через AI
    3. Сохраняет отчёт
    """
    logger.info("=" * 50)
    logger.info("🚀 Запуск Trend Hunter...")
    logger.info("=" * 50)

    start_time = datetime.now()

    # 1. Сбор данных
    logger.info("\n📊 Сбор данных из Google Trends...")
    google_trends = await fetch_google_trends(geo="US")
    logger.info(f"   Получено {len(google_trends)} трендов")

    logger.info("\n📱 Сбор данных из Reddit...")
    reddit_posts = await fetch_reddit_trends(
        subreddits=SUBREDDITS,
        keywords=["startup idea", "business idea", "side project", "saas idea"]
    )
    logger.info(f"   Получено {len(reddit_posts)} постов")

    # 2. Сохраняем сырые данные
    raw_file = save_raw_data(google_trends, reddit_posts)
    logger.info(f"\n💾 Сырые данные: {raw_file}")

    # 3. AI-анализ
    logger.info("\n🤖 Анализ трендов через AI...")
    analysis = analyze_trends(google_trends, reddit_posts)

    if "error" in analysis:
        logger.error(f"   Ошибка анализа: {analysis['error']}")
        return None

    # 4. Ранжирование идей
    ranked_ideas = rank_ideas(analysis)
    logger.info(f"   Найдено {len(ranked_ideas)} бизнес-идей")

    # 5. Сохраняем отчёт
    report_file = save_daily_report(analysis, ranked_ideas)
    logger.info(f"\n📄 Отчёт сохранён: {report_file}")

    # Итоги
    elapsed = (datetime.now() - start_time).seconds
    logger.info("\n" + "=" * 50)
    logger.info(f"✅ Готово за {elapsed} секунд!")
    logger.info("=" * 50)

    # Выводим топ-3 идеи
    if ranked_ideas:
        logger.info("\n🏆 ТОП-3 ИДЕИ СЕГОДНЯ:\n")
        for i, idea in enumerate(ranked_ideas[:3], 1):
            logger.info(f"{i}. {idea.get('name', 'N/A')} (Score: {idea.get('final_score', 0)})")
            logger.info(f"   {idea.get('description', '')[:100]}...")
            logger.info(f"   💰 {idea.get('monetization', 'N/A')}")
            logger.info("")

    return {
        "trends_count": len(google_trends),
        "posts_count": len(reddit_posts),
        "ideas_count": len(ranked_ideas),
        "report_file": report_file,
        "top_ideas": ranked_ideas[:3]
    }


def run_scheduled():
    """Обёртка для запуска через schedule"""
    asyncio.run(run_trend_hunt())


def start_scheduler():
    """
    Запускает планировщик для ежедневного выполнения
    """
    logger.info(f"⏰ Планировщик запущен. Ежедневный запуск в {SCHEDULE_TIME}")
    logger.info("   Для ручного запуска используйте: python -m trend_hunter.main --now")

    schedule.every().day.at(SCHEDULE_TIME).do(run_scheduled)

    # Также можно добавить дополнительные запуски
    # schedule.every().day.at("15:00").do(run_scheduled)  # Дневная проверка
    # schedule.every().day.at("21:00").do(run_scheduled)  # Вечерняя проверка

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import sys

    if "--now" in sys.argv or "-n" in sys.argv:
        # Немедленный запуск
        asyncio.run(run_trend_hunt())
    elif "--daemon" in sys.argv or "-d" in sys.argv:
        # Запуск как демон с расписанием
        start_scheduler()
    else:
        # По умолчанию - немедленный запуск
        print("Использование:")
        print("  python -m trend_hunter.main --now     # Запустить сейчас")
        print("  python -m trend_hunter.main --daemon  # Запустить по расписанию")
        print("\nЗапускаю сейчас...")
        asyncio.run(run_trend_hunt())
