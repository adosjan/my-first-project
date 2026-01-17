"""
SaaS Ideas Analyzer
Специализированный анализатор для поиска SaaS-идей
Использует Groq (бесплатно) или Claude API
"""
import json
import logging
import os
from typing import List, Dict
from datetime import datetime
from groq import Groq
from .config import GROQ_API_KEY

logger = logging.getLogger(__name__)

# Инициализация Groq (бесплатно)
client = Groq(api_key=GROQ_API_KEY)


SAAS_ANALYSIS_PROMPT = """Ты эксперт по SaaS-бизнесам и стартапам. Проанализируй данные и найди перспективные SaaS-идеи.

ДАННЫЕ:
{data}

ТВОЯ ЗАДАЧА:
Найди 5-10 конкретных SaaS-идей на основе:
1. Проблем, которые люди обсуждают
2. Инструментов, которые люди ищут
3. Новых продуктов, которые набирают популярность
4. Технологических трендов

ДЛЯ КАЖДОЙ ИДЕИ ДОПОЛНИ:

{{
  "saas_ideas": [
    {{
      "name": "Название продукта (конкретное, не generic)",
      "problem": "Какую конкретную проблему решает",
      "target_audience": "Кто будет платить (конкретно)",
      "pricing_model": "Модель: freemium/subscription/usage-based/hybrid",
      "price_range": "$X-Y/месяц",
      "competitors": ["Конкурент 1", "Конкурент 2"],
      "differentiation": "Чем отличается от конкурентов",
      "mvp_features": ["Фича 1", "Фича 2", "Фича 3"],
      "mvp_complexity": "low/medium/high",
      "mvp_timeline": "X недель для MVP",
      "tech_stack": ["Python", "React", "etc"],
      "potential_score": 1-10,
      "market_size": "small/medium/large",
      "why_now": "Почему сейчас хороший момент",
      "risks": ["Риск 1", "Риск 2"],
      "first_users": "Где найти первых пользователей"
    }}
  ],
  "market_insights": "Общие инсайты о рынке (2-3 предложения)",
  "hot_niches": ["Ниша 1", "Ниша 2", "Ниша 3"],
  "avoid": ["Что НЕ стоит делать и почему"]
}}

ВАЖНО:
- Фокус на B2B SaaS (бизнесы платят больше)
- Идеи должны быть реализуемы одним человеком
- Приоритет: low complexity + high potential
- Конкретика! Не "AI tool for business", а "AI tool for X that does Y"

Отвечай ТОЛЬКО валидным JSON."""


def analyze_for_saas(
    google_trends: List[Dict] = None,
    reddit_posts: List[Dict] = None,
    hackernews: List[Dict] = None,
    producthunt: List[Dict] = None
) -> Dict:
    """
    Анализирует данные для поиска SaaS-идей

    Args:
        google_trends: Тренды из Google
        reddit_posts: Посты из Reddit
        hackernews: Истории из HackerNews
        producthunt: Продукты из Product Hunt

    Returns:
        Структурированный анализ с SaaS-идеями
    """

    # Собираем данные для анализа
    data_summary = {}

    if google_trends:
        data_summary["search_trends"] = [
            {"term": t.get("title"), "traffic": t.get("traffic")}
            for t in google_trends[:15]
        ]

    if reddit_posts:
        # Фокус на SaaS-релевантных постах
        saas_keywords = ["saas", "tool", "app", "software", "automate", "api", "startup", "mvp", "product"]
        relevant_posts = [
            p for p in reddit_posts
            if any(kw in p.get("title", "").lower() for kw in saas_keywords)
        ][:20]

        data_summary["reddit_discussions"] = [
            {
                "title": p.get("title"),
                "subreddit": p.get("subreddit"),
                "score": p.get("score"),
                "preview": p.get("selftext", "")[:150]
            }
            for p in (relevant_posts if relevant_posts else reddit_posts[:20])
        ]

    if hackernews:
        # Show HN особенно ценен
        show_hn = [h for h in hackernews if h.get("is_show_hn")]
        top_stories = [h for h in hackernews if not h.get("is_show_hn")][:10]

        data_summary["hackernews_products"] = [
            {"title": h.get("title"), "score": h.get("score"), "type": "Show HN"}
            for h in show_hn[:15]
        ]
        data_summary["hackernews_trending"] = [
            {"title": h.get("title"), "score": h.get("score")}
            for h in top_stories
        ]

    if producthunt:
        data_summary["new_products"] = [
            {
                "name": p.get("name"),
                "tagline": p.get("tagline"),
                "category": p.get("category")
            }
            for p in producthunt[:20]
        ]

    # Формируем промпт
    prompt = SAAS_ANALYSIS_PROMPT.format(
        data=json.dumps(data_summary, ensure_ascii=False, indent=2)
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты эксперт по SaaS. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )

        result_text = response.choices[0].message.content

        # Парсим JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]

        analysis = json.loads(result_text.strip())
        analysis["analyzed_at"] = datetime.now().isoformat()
        analysis["sources"] = {
            "google_trends": len(google_trends or []),
            "reddit": len(reddit_posts or []),
            "hackernews": len(hackernews or []),
            "producthunt": len(producthunt or [])
        }

        logger.info(f"Найдено {len(analysis.get('saas_ideas', []))} SaaS-идей")
        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return {"error": "JSON parse error", "raw": result_text[:1000]}

    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        return {"error": str(e)}


def score_saas_idea(idea: Dict) -> float:
    """
    Рассчитывает финальный скор SaaS-идеи

    Формула:
    - Потенциал (0-40)
    - Сложность MVP (0-30)
    - Размер рынка (0-15)
    - Дифференциация (0-15)
    """
    score = 0

    # Потенциал от AI (1-10 → 0-40)
    potential = idea.get("potential_score", 5)
    score += potential * 4

    # Сложность MVP
    complexity = idea.get("mvp_complexity", "medium")
    if complexity == "low":
        score += 30
    elif complexity == "medium":
        score += 15

    # Размер рынка
    market = idea.get("market_size", "medium")
    if market == "large":
        score += 15
    elif market == "medium":
        score += 10
    else:
        score += 5

    # Дифференциация (есть ли уникальность)
    if idea.get("differentiation") and len(idea["differentiation"]) > 20:
        score += 15

    return min(score, 100)


def rank_saas_ideas(analysis: Dict) -> List[Dict]:
    """
    Ранжирует SaaS-идеи по скору

    Returns:
        Отсортированный список идей
    """
    ideas = analysis.get("saas_ideas", [])

    for idea in ideas:
        idea["final_score"] = score_saas_idea(idea)

    ideas.sort(key=lambda x: x["final_score"], reverse=True)
    return ideas


def format_idea_for_telegram(idea: Dict, rank: int) -> str:
    """Форматирует идею для Telegram"""
    return f"""
*{rank}. {idea.get('name', 'N/A')}* (Score: {idea.get('final_score', 0)})

💡 *Проблема:* {idea.get('problem', 'N/A')}

👥 *Аудитория:* {idea.get('target_audience', 'N/A')}

💰 *Цена:* {idea.get('price_range', 'N/A')} ({idea.get('pricing_model', 'subscription')})

⚙️ *MVP:* {idea.get('mvp_complexity', 'medium')} сложность, ~{idea.get('mvp_timeline', 'N/A')}

🎯 *Отличие:* {idea.get('differentiation', 'N/A')}

🚀 *Первые юзеры:* {idea.get('first_users', 'N/A')}
"""
