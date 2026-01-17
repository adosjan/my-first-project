"""
Хранилище данных - сохранение и загрузка JSON
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DATA_DIR = "trend_hunter/data"


def ensure_data_dir():
    """Создаёт папку data если её нет"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Создана папка {DATA_DIR}")


def save_daily_report(analysis: Dict, ideas: List[Dict]) -> str:
    """
    Сохраняет ежедневный отчёт

    Args:
        analysis: Результат анализа трендов
        ideas: Ранжированные бизнес-идеи

    Returns:
        Путь к сохранённому файлу
    """
    ensure_data_dir()

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{DATA_DIR}/report_{date_str}.json"

    report = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "summary": analysis.get("summary", ""),
        "top_opportunity": analysis.get("top_opportunity", ""),
        "ideas": ideas,
        "trends_count": len(analysis.get("trends", [])),
        "data_sources": analysis.get("data_sources", {})
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"Отчёт сохранён: {filename}")
    return filename


def save_raw_data(google_trends: List[Dict], reddit_posts: List[Dict]) -> str:
    """
    Сохраняет сырые данные для истории

    Args:
        google_trends: Тренды Google
        reddit_posts: Посты Reddit

    Returns:
        Путь к файлу
    """
    ensure_data_dir()

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{DATA_DIR}/raw_{date_str}.json"

    data = {
        "date": date_str,
        "fetched_at": datetime.now().isoformat(),
        "google_trends": google_trends,
        "reddit_posts": reddit_posts
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Сырые данные сохранены: {filename}")
    return filename


def load_report(date: str = None) -> Optional[Dict]:
    """
    Загружает отчёт за дату

    Args:
        date: Дата в формате YYYY-MM-DD (по умолчанию сегодня)

    Returns:
        Данные отчёта или None
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    filename = f"{DATA_DIR}/report_{date}.json"

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    return None


def get_all_reports() -> List[Dict]:
    """
    Возвращает список всех сохранённых отчётов

    Returns:
        Список отчётов (только метаданные)
    """
    ensure_data_dir()

    reports = []
    for filename in os.listdir(DATA_DIR):
        if filename.startswith("report_") and filename.endswith(".json"):
            filepath = os.path.join(DATA_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports.append({
                        "date": data.get("date"),
                        "generated_at": data.get("generated_at"),
                        "ideas_count": len(data.get("ideas", [])),
                        "top_opportunity": data.get("top_opportunity", "")[:100],
                        "filename": filename
                    })
            except Exception as e:
                logger.error(f"Ошибка чтения {filename}: {e}")

    reports.sort(key=lambda x: x["date"], reverse=True)
    return reports


def get_all_ideas(limit: int = 50) -> List[Dict]:
    """
    Собирает все идеи из всех отчётов

    Args:
        limit: Максимальное количество идей

    Returns:
        Список идей, отсортированных по скору
    """
    all_ideas = []

    reports = get_all_reports()
    for report_meta in reports:
        report = load_report(report_meta["date"])
        if report:
            for idea in report.get("ideas", []):
                idea["report_date"] = report_meta["date"]
                all_ideas.append(idea)

    # Сортируем по скору и возвращаем топ
    all_ideas.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    return all_ideas[:limit]
