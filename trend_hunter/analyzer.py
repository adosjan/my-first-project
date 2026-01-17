"""
AI-анализатор трендов
Использует Groq (бесплатно) для анализа и генерации бизнес-идей
"""
import json
import logging
from typing import List, Dict
from datetime import datetime
from groq import Groq
from .config import GROQ_API_KEY

logger = logging.getLogger(__name__)

# Инициализация Groq
client = Groq(api_key=GROQ_API_KEY)


ANALYSIS_PROMPT = """Ты эксперт по стартапам и бизнес-трендам. Проанализируй данные и найди бизнес-возможности.

ДАННЫЕ ДЛЯ АНАЛИЗА:
{data}

ТВОЯ ЗАДАЧА:
1. Выдели 5-10 самых перспективных трендов/тем
2. Для каждого тренда предложи конкретную бизнес-идею
3. Оцени потенциал каждой идеи

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "trends": [
    {{
      "name": "Название тренда",
      "description": "Краткое описание (1-2 предложения)",
      "business_idea": {{
        "name": "Название продукта/сервиса",
        "description": "Что это и как работает",
        "target_audience": "Для кого",
        "monetization": "Как зарабатывать",
        "mvp_complexity": "low/medium/high",
        "potential_score": 1-10
      }},
      "why_now": "Почему сейчас хороший момент",
      "risks": "Основные риски"
    }}
  ],
  "summary": "Общий вывод о текущих трендах (2-3 предложения)",
  "top_opportunity": "Самая перспективная идея и почему"
}}

Отвечай ТОЛЬКО валидным JSON, без markdown и пояснений."""


def analyze_trends(google_trends: List[Dict], reddit_posts: List[Dict]) -> Dict:
    """
    Анализирует собранные данные и генерирует бизнес-идеи

    Args:
        google_trends: Тренды из Google
        reddit_posts: Посты из Reddit

    Returns:
        Структурированный анализ с бизнес-идеями
    """

    # Готовим данные для AI
    data_summary = {
        "google_trends": [
            {"title": t["title"], "traffic": t.get("traffic", "N/A")}
            for t in google_trends[:20]
        ],
        "reddit_hot_topics": [
            {
                "title": p["title"],
                "subreddit": p["subreddit"],
                "score": p["score"],
                "comments": p["num_comments"],
                "preview": p.get("selftext", "")[:200]
            }
            for p in reddit_posts[:30]
        ]
    }

    prompt = ANALYSIS_PROMPT.format(data=json.dumps(data_summary, ensure_ascii=False, indent=2))

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты аналитик трендов. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )

        result_text = response.choices[0].message.content

        # Пытаемся распарсить JSON
        # Иногда модель добавляет ```json в начале
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        analysis = json.loads(result_text.strip())
        analysis["analyzed_at"] = datetime.now().isoformat()
        analysis["data_sources"] = {
            "google_trends_count": len(google_trends),
            "reddit_posts_count": len(reddit_posts)
        }

        logger.info(f"Анализ завершён: найдено {len(analysis.get('trends', []))} трендов")
        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON от AI: {e}")
        logger.debug(f"Ответ AI: {result_text[:500]}")
        return {
            "error": "JSON parse error",
            "raw_response": result_text[:1000],
            "analyzed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        return {
            "error": str(e),
            "analyzed_at": datetime.now().isoformat()
        }


def score_idea(idea: Dict) -> float:
    """
    Рассчитывает итоговый скор бизнес-идеи

    Args:
        idea: Данные бизнес-идеи

    Returns:
        Числовой скор от 0 до 100
    """
    score = 0

    # Базовый потенциал от AI (0-10 -> 0-40)
    potential = idea.get("potential_score", 5)
    score += potential * 4

    # Бонус за низкую сложность MVP
    complexity = idea.get("mvp_complexity", "medium")
    if complexity == "low":
        score += 30
    elif complexity == "medium":
        score += 15

    # Бонус за понятную монетизацию
    if idea.get("monetization") and len(idea["monetization"]) > 10:
        score += 15

    # Бонус за конкретную целевую аудиторию
    if idea.get("target_audience") and len(idea["target_audience"]) > 10:
        score += 15

    return min(score, 100)


def rank_ideas(analysis: Dict) -> List[Dict]:
    """
    Ранжирует все идеи по скору

    Args:
        analysis: Результат analyze_trends

    Returns:
        Список идей, отсортированный по скору
    """
    ranked = []

    for trend in analysis.get("trends", []):
        idea = trend.get("business_idea", {})
        if idea:
            idea["trend_name"] = trend.get("name")
            idea["why_now"] = trend.get("why_now")
            idea["risks"] = trend.get("risks")
            idea["final_score"] = score_idea(idea)
            ranked.append(idea)

    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked
