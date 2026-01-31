# AI SaaS Idea Analyzer - Buyer Documentation

Welcome! This guide will help you set up and run your new AI SaaS Idea Analyzer.

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-saas-idea-analyzer.git
cd ai-saas-idea-analyzer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Your Free Groq API Key

1. Go to https://console.groq.com
2. Sign up (free)
3. Create an API key
4. Copy the key

### 4. Create Environment File

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Deployment Options

### Option A: Streamlit Cloud (Free & Recommended)

1. Push code to your GitHub repository
2. Go to https://share.streamlit.io
3. Connect your GitHub account
4. Select your repository
5. Set main file: `app.py`
6. Add secret: `GROQ_API_KEY = "your_key"`
7. Deploy!

Your app will be live at: `https://your-app-name.streamlit.app`

### Option B: Heroku

1. Create `Procfile`:
```
web: streamlit run app.py --server.port $PORT
```

2. Deploy:
```bash
heroku create your-app-name
heroku config:set GROQ_API_KEY=your_key
git push heroku main
```

### Option C: Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

```bash
docker build -t saas-analyzer .
docker run -p 8501:8501 -e GROQ_API_KEY=your_key saas-analyzer
```

---

## Project Structure

```
ai-saas-idea-analyzer/
├── app.py                    # Main Streamlit web app
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── trend_hunter/            # Core analysis engine
│   ├── config.py            # Configuration
│   ├── main.py              # Main runner
│   ├── analyzer.py          # Basic trend analyzer
│   ├── saas_analyzer.py     # AI-powered SaaS idea generator
│   ├── storage.py           # Data persistence
│   └── sources/             # Data source integrations
│       ├── google_trends.py # Google Trends parser
│       ├── reddit.py        # Reddit API client
│       ├── hackernews.py    # Hacker News API client
│       └── producthunt.py   # Product Hunt RSS parser
└── docs/                    # Research documentation
```

---

## Customization Guide

### Add New Data Sources

1. Create a new file in `trend_hunter/sources/`
2. Implement an async fetch function
3. Import it in `app.py`
4. Add UI checkbox in sidebar

Example:
```python
# trend_hunter/sources/twitter.py
async def fetch_twitter_trends():
    # Your implementation
    return [{"title": "...", "source": "twitter"}]
```

### Modify AI Prompts

Edit `trend_hunter/saas_analyzer.py`:
- `SAAS_ANALYSIS_PROMPT` - Main analysis prompt
- Adjust scoring in `score_saas_idea()`

### Change UI Theme

Edit the CSS in `app.py`:
```python
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #YOUR_COLOR 0%, #YOUR_COLOR 100%);
    }
</style>
""", unsafe_allow_html=True)
```

### Add User Authentication

Install Streamlit-Authenticator:
```bash
pip install streamlit-authenticator
```

See: https://github.com/mkhorasani/Streamlit-Authenticator

### Add Payment (Stripe)

1. Create Stripe account
2. Install: `pip install stripe`
3. Add paywall before analysis

---

## Monetization Strategies

### 1. SaaS Subscription
- Free tier: 3 analyses/month
- Pro: $29/month - Unlimited
- Enterprise: $99/month - API access

### 2. Pay-Per-Report
- $9 per analysis
- $49 for 10-pack

### 3. White-Label
- Sell to agencies for $500-2000
- They rebrand and resell

### 4. API Access
- Build REST API with FastAPI
- Charge per request

---

## API Costs (All Free Tiers)

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Groq | 14,400 requests/day | More than enough |
| Google Trends | Unlimited | RSS feed, no API key needed |
| Reddit | 100 requests/min | JSON endpoints, no auth needed |
| Hacker News | Unlimited | Firebase API, no key needed |
| Product Hunt | Unlimited | RSS feed, no key needed |

**Total monthly cost to run: $0**

---

## Support

You have 30 days of email support included with your purchase.

For questions, contact: [YOUR_EMAIL]

---

## License

Full ownership transferred. You can:
- Modify the code
- Resell the product
- Use commercially
- White-label

No attribution required.

---

Thank you for your purchase! Good luck with your SaaS venture!
