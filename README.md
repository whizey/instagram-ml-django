# Social Media Engagement Forecasting

A machine learning and analytics platform that predicts Instagram post reach and analyzes engagement behavior using regression models and a Django-based analytics backend.

The system estimates the number of **impressions a post may receive** based on engagement signals such as likes, saves, comments, shares, profile visits, and follows. It also computes additional engagement metrics such as viral score, engagement rate, and follower conversion rate to provide deeper insights into content performance.

The project combines a **machine learning prediction pipeline with a production-style analytics platform**, allowing engagement data to be analyzed, stored, and interpreted through a Django-based backend.

---

## Project Overview

Content creators often publish posts without knowing in advance which content will perform well. Most rely on intuition or vanity metrics such as likes, but these signals alone do not explain why some posts reach significantly larger audiences.

This project explores whether Instagram post reach can be predicted using engagement signals and identifies which engagement behaviors contribute most to content visibility.

The system includes:

- A **machine learning pipeline** for predicting post impressions  
- An **analytics engine** for engagement analysis and viral scoring  
- A **Django backend architecture** that exposes APIs and stores historical post data  

The best-performing model, **Ridge Regression**, achieved an **R² score of 0.9485** and **cross-validation R² of 0.8210**, indicating strong predictive performance.

---

## Problem Statement

Social media platforms distribute content based on complex engagement signals. However, creators often focus primarily on likes as a measure of success.

This raises an important question:

> Can post reach be predicted using engagement metrics, and which signals actually influence visibility?

Understanding these signals allows creators and marketing teams to design content that encourages meaningful engagement rather than focusing only on surface-level reactions.

---

## Dataset

The model was trained using **Instagram post-level engagement data**.

Each row in the dataset represents a single Instagram post and includes multiple engagement metrics.

### Features

- Likes  
- Saves  
- Comments  
- Shares  
- Profile Visits  
- Follows  
- Impressions from Home Feed  
- Impressions from Hashtags  
- Impressions from Explore Page  

### Target Variable

**Impressions**

Impressions represent the total number of times a post was displayed to users and serve as the primary indicator of post reach.

### Secondary Target

**Viral Score**

The viral score represents overall engagement quality derived from engagement signals.

---

## Assumptions

Several assumptions were considered during modeling:

**Stationarity**

Past engagement behavior for a given account is assumed to be relatively stable, allowing historical engagement patterns to be used for prediction.

**Saves vs Likes**

Saves and follower conversions are assumed to represent deeper user intent compared to passive reactions such as likes.

**Derived Viral Score**

The viral score is derived from engagement metrics rather than being an independent variable.

---

## Approach

### Feature Engineering

Raw engagement counts do not fully represent user interaction patterns. Several derived metrics were created to better capture engagement behavior.

| Feature | Formula | Purpose |
|--------|--------|--------|
| Engagement Rate | (Likes + Comments + Saves + Shares) / Impressions | Measures audience responsiveness |
| Save-to-Like Ratio | Saves / Likes | Indicates perceived content value |
| Follower Conversion Rate | Follows / Profile Visits | Measures audience growth potential |

---

### Model Training

Five regression models were trained and compared:

- Linear Regression  
- Ridge Regression  
- Lasso Regression  
- Gradient Boosting Regression  
- Random Forest Regression  

Training configuration:

- StandardScaler for feature normalization  
- 80/20 train–test split  
- 5-fold cross-validation  

---

### Evaluation Metrics

Models were evaluated using the following metrics:

- **R² Score** – Variance explained by the model  
- **Cross-Validation R²** – Model generalization performance  
- **MAE (Mean Absolute Error)** – Average prediction error  
- **RMSE (Root Mean Squared Error)** – Penalizes large prediction errors  

---

## Results

### Impressions Prediction

| Model | R² | CV R² | MAE | RMSE |
|------|------|------|------|------|
| **Ridge Regression** | **0.9485** | **0.8210** | 936.78 | 1414.19 |
| Lasso Regression | 0.9374 | 0.8057 | 1015.60 | 1559.64 |
| Linear Regression | 0.9360 | 0.8053 | 1026.58 | 1577.19 |
| Gradient Boosting | 0.9061 | 0.6435 | 743.21 | 1909.36 |
| Random Forest | 0.8670 | 0.6646 | 1062.64 | 2272.85 |

**Best Model:** Ridge Regression

Ridge Regression achieved the best balance between prediction accuracy and generalization.

---

### Viral Score Prediction

| Model | R² | CV R² | MAE |
|------|------|------|------|
| **Linear Regression** | **1.0000** | **1.0000** | ~0 |
| Ridge Regression | 0.9999 | 0.9998 | 0.06 |
| Lasso Regression | 0.9805 | 0.9478 | 1.26 |
| Gradient Boosting | 0.8297 | 0.8819 | 2.90 |
| Random Forest | 0.7685 | 0.8707 | 3.48 |

**Observation**

The perfect R² score for Linear Regression indicates that viral score is mathematically derived from engagement metrics rather than being an independent prediction target.

---

## Key Insight

The analysis reveals that **saves and follower growth are stronger predictors of reach than likes or comments**.

This suggests that social media algorithms prioritize engagement signals that indicate deeper user intent:

- Saves → content worth revisiting  
- Shares → content worth spreading  
- Follows → content that attracts new audience  

---
