"""
Быстрый запуск Trend Hunter
"""
import asyncio
import sys
sys.path.insert(0, '.')

from trend_hunter.main import run_trend_hunt, start_scheduler

if __name__ == "__main__":
    if "--daemon" in sys.argv or "-d" in sys.argv:
        start_scheduler()
    else:
        asyncio.run(run_trend_hunt())
