"""
AI SaaS Idea Analyzer - Streamlit Web App
Find trending SaaS ideas powered by AI
"""
import streamlit as st
import asyncio
import json
from datetime import datetime
import os

# Import our modules
from trend_hunter.sources.google_trends import fetch_google_trends
from trend_hunter.sources.reddit import fetch_reddit_trends
from trend_hunter.sources.hackernews import fetch_hackernews
from trend_hunter.sources.producthunt import fetch_producthunt
from trend_hunter.saas_analyzer import analyze_for_saas, rank_saas_ideas
from trend_hunter.storage import load_report, get_all_reports, get_all_ideas
from trend_hunter.config import SUBREDDITS

# Page config
st.set_page_config(
    page_title="AI SaaS Idea Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .idea-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-medium { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .source-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)


def run_async(coro):
    """Helper to run async functions"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def display_idea_card(idea: dict, rank: int):
    """Display a single idea as a styled card"""
    score = idea.get('final_score', 0)

    if score >= 70:
        score_class = "score-high"
        score_emoji = "🔥"
    elif score >= 50:
        score_class = "score-medium"
        score_emoji = "⭐"
    else:
        score_class = "score-low"
        score_emoji = "💡"

    complexity = idea.get('mvp_complexity', 'medium')
    complexity_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(complexity, "🟡")

    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### {rank}. {idea.get('name', 'Unnamed Idea')}")
        with col2:
            st.markdown(f"<span class='{score_class}'>{score_emoji} Score: {score}/100</span>", unsafe_allow_html=True)

        st.markdown(f"**Problem:** {idea.get('problem', 'N/A')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"👥 **Target:** {idea.get('target_audience', 'N/A')}")
        with col2:
            st.markdown(f"💰 **Price:** {idea.get('price_range', 'N/A')}")
        with col3:
            st.markdown(f"{complexity_emoji} **Complexity:** {complexity.upper()}")

        with st.expander("📋 Full Details"):
            st.markdown(f"**Pricing Model:** {idea.get('pricing_model', 'subscription')}")
            st.markdown(f"**Differentiation:** {idea.get('differentiation', 'N/A')}")
            st.markdown(f"**MVP Timeline:** {idea.get('mvp_timeline', 'N/A')}")

            if idea.get('mvp_features'):
                st.markdown("**MVP Features:**")
                for feature in idea.get('mvp_features', []):
                    st.markdown(f"  - {feature}")

            if idea.get('competitors'):
                st.markdown(f"**Competitors:** {', '.join(idea.get('competitors', []))}")

            st.markdown(f"**Why Now:** {idea.get('why_now', 'N/A')}")
            st.markdown(f"**First Users:** {idea.get('first_users', 'N/A')}")

            if idea.get('tech_stack'):
                st.markdown(f"**Tech Stack:** {', '.join(idea.get('tech_stack', []))}")

            if idea.get('risks'):
                st.markdown("**Risks:**")
                for risk in idea.get('risks', []):
                    st.markdown(f"  - ⚠️ {risk}")

        st.divider()


def main():
    # Header
    st.markdown('<p class="main-header">🚀 AI SaaS Idea Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover trending SaaS opportunities powered by AI</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/3d-fluency/94/rocket.png", width=80)
        st.title("Settings")

        st.markdown("### Data Sources")
        use_google = st.checkbox("Google Trends", value=True)
        use_reddit = st.checkbox("Reddit", value=True)
        use_hackernews = st.checkbox("Hacker News", value=True)
        use_producthunt = st.checkbox("Product Hunt", value=True)

        st.markdown("### Region")
        region = st.selectbox("Google Trends Region", ["US", "GB", "DE", "RU"])

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        **AI SaaS Idea Analyzer** finds trending topics
        and generates SaaS business ideas using AI.

        **Sources:**
        - 🔍 Google Trends
        - 💬 Reddit discussions
        - 🔶 Hacker News
        - 🚀 Product Hunt

        **AI:** Groq LLaMA 3.3 70B
        """)

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Analyze Now", "📊 Saved Reports", "💡 All Ideas"])

    # Tab 1: Analyze
    with tab1:
        st.markdown("## Find New SaaS Ideas")
        st.markdown("Click the button to scan multiple data sources and generate AI-powered SaaS ideas.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🔍</h3>
                <p>Google Trends</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>💬</h3>
                <p>Reddit</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🔶</h3>
                <p>Hacker News</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>🚀</h3>
                <p>Product Hunt</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):

            google_trends = []
            reddit_posts = []
            hackernews_data = []
            producthunt_data = []

            progress = st.progress(0, text="Starting analysis...")

            # Fetch data
            with st.spinner("Collecting data from sources..."):

                if use_google:
                    progress.progress(10, text="Fetching Google Trends...")
                    google_trends = run_async(fetch_google_trends(geo=region))
                    st.success(f"✅ Google Trends: {len(google_trends)} trends")

                if use_reddit:
                    progress.progress(30, text="Fetching Reddit posts...")
                    reddit_posts = run_async(fetch_reddit_trends(
                        subreddits=SUBREDDITS,
                        keywords=["startup idea", "business idea", "saas idea", "side project"]
                    ))
                    st.success(f"✅ Reddit: {len(reddit_posts)} posts")

                if use_hackernews:
                    progress.progress(50, text="Fetching Hacker News...")
                    hackernews_data = run_async(fetch_hackernews())
                    st.success(f"✅ Hacker News: {len(hackernews_data)} stories")

                if use_producthunt:
                    progress.progress(70, text="Fetching Product Hunt...")
                    producthunt_data = run_async(fetch_producthunt(["today", "ai", "saas"]))
                    st.success(f"✅ Product Hunt: {len(producthunt_data)} products")

            # AI Analysis
            progress.progress(85, text="🤖 AI analyzing trends...")

            with st.spinner("AI is generating SaaS ideas..."):
                analysis = analyze_for_saas(
                    google_trends=google_trends,
                    reddit_posts=reddit_posts,
                    hackernews=hackernews_data,
                    producthunt=producthunt_data
                )

            progress.progress(100, text="Done!")

            if "error" in analysis:
                st.error(f"Analysis error: {analysis['error']}")
            else:
                # Rank ideas
                ideas = rank_saas_ideas(analysis)

                # Display results
                st.markdown("---")
                st.markdown("## 🏆 Top SaaS Ideas")

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ideas Generated", len(ideas))
                with col2:
                    st.metric("Data Points Analyzed",
                             len(google_trends) + len(reddit_posts) + len(hackernews_data) + len(producthunt_data))
                with col3:
                    if ideas:
                        st.metric("Top Score", f"{ideas[0].get('final_score', 0)}/100")

                # Market insights
                if analysis.get('market_insights'):
                    st.info(f"💡 **Market Insights:** {analysis['market_insights']}")

                if analysis.get('hot_niches'):
                    st.markdown(f"🔥 **Hot Niches:** {', '.join(analysis.get('hot_niches', []))}")

                st.markdown("---")

                # Display ideas
                for i, idea in enumerate(ideas, 1):
                    display_idea_card(idea, i)

                # Save option
                if st.button("💾 Save Report"):
                    from trend_hunter.storage import save_daily_report
                    filename = save_daily_report(analysis, ideas)
                    st.success(f"Report saved: {filename}")

    # Tab 2: Reports
    with tab2:
        st.markdown("## 📊 Saved Reports")

        reports = get_all_reports()

        if not reports:
            st.info("No saved reports yet. Run an analysis first!")
        else:
            for report_meta in reports:
                with st.expander(f"📅 {report_meta['date']} - {report_meta['ideas_count']} ideas"):
                    report = load_report(report_meta['date'])
                    if report:
                        st.markdown(f"**Generated:** {report.get('generated_at', 'N/A')}")
                        st.markdown(f"**Top Opportunity:** {report.get('top_opportunity', 'N/A')}")

                        if report.get('ideas'):
                            st.markdown("### Ideas:")
                            for i, idea in enumerate(report['ideas'][:5], 1):
                                st.markdown(f"**{i}. {idea.get('name', 'N/A')}** (Score: {idea.get('final_score', 0)})")
                                st.markdown(f"   {idea.get('problem', '')[:100]}...")

    # Tab 3: All Ideas
    with tab3:
        st.markdown("## 💡 All Ideas Database")

        ideas = get_all_ideas(limit=50)

        if not ideas:
            st.info("No ideas in database. Run some analyses first!")
        else:
            # Filter
            min_score = st.slider("Minimum Score", 0, 100, 50)

            filtered = [i for i in ideas if i.get('final_score', 0) >= min_score]

            st.markdown(f"Showing **{len(filtered)}** ideas with score >= {min_score}")
            st.markdown("---")

            for i, idea in enumerate(filtered, 1):
                display_idea_card(idea, i)

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>"
        "Built with ❤️ using Streamlit | AI SaaS Idea Analyzer v1.0"
        "</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
