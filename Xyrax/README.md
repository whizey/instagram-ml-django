# Instra — Instagram Analytics Django App

A full-stack Django app powering the Instra Instagram analytics dashboard.

## Features
- **Predict** — Enter post metrics, get predicted impressions + viral score
- **Analytics** — Charts, engagement breakdown, trend forecasting
- **History** — SQLite-backed per-session post history
- **Agent** — AI strategy chat (uses Claude via Anthropic API, or falls back to rule-based responses)

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run migrations
```bash
python manage.py migrate
```

### 3. (Optional) Set your Anthropic API key
The AI agent works without an API key using smart rule-based responses.
To enable Claude-powered answers:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

Or edit `instra/settings.py` and set `ANTHROPIC_API_KEY = 'your-key-here'`.

### 4. Start the server
```bash
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/analyze/` | Analyze a post, returns predictions + AI strategy |
| POST | `/api/history/` | Get session post history |
| POST | `/api/clear/` | Clear session history |
| POST | `/api/agent/` | Chat with the AI strategy agent |

### Example: Analyze a post
```bash
curl -X POST http://127.0.0.1:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_key": "my-session",
    "likes": 151, "saves": 109, "comments": 6,
    "shares": 6, "follows": 8, "profile_visits": 23,
    "caption_length": 150, "hashtags": 20, "reposts": 0
  }'
```

## Project Structure
```
instra/
├── manage.py
├── requirements.txt
├── instra/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── analytics/            # Main app
│   ├── models.py         # Post model (SQLite)
│   ├── views.py          # API endpoints + index view
│   ├── engine.py         # Prediction & analytics logic
│   └── urls.py
└── templates/
    └── index.html        # The SPA frontend
```

## CSV Upload Format
The frontend accepts CSV files with these columns (all optional except at least 3):
```
likes, saves, comments, shares, follows, profile_visits, caption_length, hashtags, reposts
```
