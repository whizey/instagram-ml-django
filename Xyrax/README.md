## System Architecture

The system integrates a machine learning prediction pipeline with a Django-based backend that manages analytics processing, API communication, and historical data storage. This architecture enables engagement data to be analyzed, stored, and interpreted through a scalable analytics platform.

The backend is organized into modular components responsible for prediction, analytics computation, and API communication.

---v

### Project Structure
INSTAGRAM_REACH/
│
├── analytics/                # Core analytics app
│   ├── engine.py             # Engagement analytics & prediction logic
│   ├── models.py             # Database schema
│   ├── views.py              # API endpoints
│   └── urls.py               # Routing
│
├── instra/                   # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
│   └── index.html            # Web interface
│
├── Instagram Reach Viral Prediction.ipynb   # ML training pipeline
├── Instagram_Data.csv                       # Dataset
├── db.sqlite3                               # Database
├── manage.py                                # Django management script
└── requirements.txt                         # Dependencies

---

## Database Design

The platform uses **SQLite** as a lightweight database to store historical post analytics.

A Django model named `Post` stores both engagement inputs and computed analytics outputs.

### Stored Input Features

- likes  
- saves  
- comments  
- shares  
- profile visits  
- follows  
- caption length  
- hashtags  
- reposts  

### Stored Analytics Outputs

- predicted impressions  
- viral score  
- engagement rate  
- follow conversion rate  
- AI-generated performance label  

Storing historical analytics allows the system to perform **trend analysis and forecasting across multiple posts**.

---

## Analytics Engine

The analytics engine is implemented in `engine.py` and performs all prediction and engagement analysis tasks.

### Impression Prediction

The system estimates expected impressions using engagement signals and a weighted engagement formula. Historical post performance is used to calibrate predictions.

### Viral Score Calculation

A composite viral score between **0 and 100** is calculated based on engagement quality signals such as saves, comments, shares, and follower conversions.

### Engagement Metrics

Additional metrics are calculated to better understand audience behavior:

- engagement rate  
- follower conversion rate  
- save-to-like ratio  

### Trend Analysis

The system analyzes engagement patterns across historical posts to detect performance trends such as:

- improving performance  
- declining engagement  
- stable growth  

---

## API Endpoints

The backend exposes several API endpoints that allow the frontend interface to interact with the analytics system.

| Endpoint | Method | Description |
|--------|--------|--------|
| `/api/analyze/` | POST | Analyze a post and generate predictions |
| `/api/history/` | POST | Retrieve previous post analytics |
| `/api/clear/` | POST | Clear stored session data |
| `/api/agent/` | POST | Interact with the AI strategy assistant |

These endpoints allow engagement data to be submitted, processed, and returned as analytics insights.

---

## Prediction Workflow

The full system workflow for analyzing a post is as follows:

1. The user enters engagement metrics for a post.  
2. The frontend sends the data to the `/api/analyze/` endpoint.  
3. The Django backend processes the request.  
4. The analytics engine computes predictions and engagement metrics.  
5. Results are stored in the database.  
6. The system returns predictions and analytics insights to the user.

---

## AI Strategy Agent

The system includes an **AI-powered strategy assistant** that analyzes engagement data and provides recommendations for improving post performance.

The agent uses engagement metrics and historical post data to generate insights such as:

- optimizing hashtag usage  
- improving caption structure  
- increasing save-worthy content  
- posting during optimal time windows  

When an external model is available, the system uses **Groq Llama models** for generating insights. Otherwise, it falls back to a rule-based recommendation system.

---

## Forecasting and Trend Analysis

Using stored historical data, the system performs **multi-post forecasting** to estimate future performance.

Forecasting includes:

- engagement trend detection  
- predicted impressions for the next post  
- viral score projection  
- optimal hashtag recommendations  

These insights help creators identify whether their content performance is improving or declining over time.

---
