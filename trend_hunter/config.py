"""
Конфигурация Trend Hunter
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API ключи
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Reddit API (опционально, можно парсить без API)
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')

# Настройки поиска
SEARCH_CATEGORIES = [
    "SaaS", "AI tools", "automation", "productivity",
    "fintech", "health tech", "e-commerce", "no-code"
]

# Сабреддиты для мониторинга
SUBREDDITS = [
    "Entrepreneur",
    "SideProject",
    "startups",
    "SaaS",
    "artificial",
    "automation",
    "smallbusiness",
    "indiehackers"
]

# Пути к файлам
DATA_DIR = "trend_hunter/data"
TRENDS_FILE = f"{DATA_DIR}/trends.json"
IDEAS_FILE = f"{DATA_DIR}/business_ideas.json"

# Расписание (cron формат для ежедневного запуска)
SCHEDULE_TIME = "09:00"  # Утренняя сводка
