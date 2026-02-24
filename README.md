# Social Media Engagement Forecasting

Predicting Instagram post impressions and viral potential using 
machine learning. Trained and compared 5 regression models on real 
Instagram data, achieving R² of 0.9485 with Ridge Regression.

The project also challenges a common assumption — saves and follower 
growth predict reach better than likes, which most creators focus on.

**Best Model:** Ridge Regression — R² 0.9485, CV R² 0.8210

---

## The Problem

Content creators publish posts without knowing in advance which ones 
will perform well. Most rely on intuition or past experience, but 
that doesn't scale — and likes alone don't explain why some posts 
reach 10x more people than others.

**Core Question:**  
Can we predict how many impressions a post will get using engagement 
signals — and identify which signals matter most?

**Why it matters:**  
If a creator knows that saves drive reach more than likes, they can 
design content specifically to earn saves — leading to higher 
algorithmic amplification and audience growth.

---

## Dataset

- Source: Instagram post-level performance data
- Features used: Likes, Saves, Comments, Shares, Profile Visits, 
  Follows, Impressions from Home / Hashtags / Explore
- Target variable: **Impressions** (total reach per post)
- Secondary target: **Viral Score** (derived engagement metric)

---

## Assumptions

Before building the model, a few assumptions were made:

- **Stationarity:** Past engagement patterns are stable enough to 
  predict future performance on the same account. This may not hold 
  if the account changes its content style significantly.

- **Saves > Likes:** Saves and follower conversions signal intent and 
  algorithmic reward more than passive reactions. This was confirmed 
  by feature importance analysis.

- **Viral Score is derived:** The perfect R² = 1.000 for Viral Score 
  prediction revealed it is mathematically computed from input 
  features — not an independent target. This is a data insight, not 
  a modeling achievement, and was deprioritized accordingly.

---

## Approach

### Step 1 — Feature Engineering

Raw engagement counts (likes, comments) don't tell the full story. 
Three derived features were created to capture behavioral patterns:

| Feature | Formula | Why it matters |
|---------|---------|----------------|
| Engagement Rate | (Likes + Comments) / Impressions | Measures audience responsiveness |
| Save-to-Like Ratio | Saves / Likes | Signals content value beyond reaction |
| Follower Conversion Rate | Follows / Impressions | Measures new audience acquisition |

### Step 2 — Model Training

Five regression models were trained and evaluated:

- **Linear Regression** — baseline, interpretable
- **Ridge Regression** — L2 regularization, handles correlated features
- **Lasso Regression** — L1 regularization, automatic feature selection
- **Gradient Boosting** — sequential ensemble, captures non-linearity
- **Random Forest** — parallel ensemble, captures feature interactions

All models used:
- StandardScaler for feature normalization
- 80/20 train-test split
- 5-fold cross-validation to check generalization

### Step 3 — Evaluation

Models were ranked on four metrics:
- **R²** — how much variance the model explains
- **CV R²** — how well it generalizes to unseen data
- **MAE** — average prediction error in absolute terms
- **RMSE** — penalizes large errors more heavily

---

## Results

### Impressions Prediction

| Model | R² | CV R² | MAE | RMSE |
|-------|----|-------|-----|------|
| **Ridge** ✅ | **0.9485** | **0.8210** | 936.78 | 1414.19 |
| Lasso | 0.9374 | 0.8057 | 1015.60 | 1559.64 |
| Linear Regression | 0.9360 | 0.8053 | 1026.58 | 1577.19 |
| Gradient Boosting | 0.9061 | 0.6435 | 743.21 | 1909.36 |
| Random Forest | 0.8670 | 0.6646 | 1062.64 | 2272.85 |

**Ridge wins** — highest R² and strongest CV R², meaning it explains 
the most variance and generalizes the best to unseen posts.

### Viral Score Prediction

| Model | R² | CV R² | MAE |
|-------|----|-------|-----|
| **Linear Regression** ✅ | **1.0000** | **1.0000** | ~0.00 |
| Ridge | 0.9999 | 0.9998 | 0.06 |
| Lasso | 0.9805 | 0.9478 | 1.26 |
| Gradient Boosting | 0.8297 | 0.8819 | 2.90 |
| Random Forest | 0.7685 | 0.8707 | 3.48 |

> **Note:** Linear Regression's perfect R² = 1.000 means Viral Score 
> is a direct linear combination of input features. This is a data 
> finding — the target variable is not truly independent. Impressions 
> prediction is the more meaningful task.

---

## Trade-offs Considered

**Ridge vs Gradient Boosting:**  
Gradient Boosting had the lowest MAE (743.21), meaning its individual 
predictions were closest on average. But its CV R² collapsed to 
0.6435 — a clear sign of overfitting on this dataset size. Ridge 
sacrifices a little MAE but generalizes far more reliably.

**Why Random Forest underperformed:**  
Random Forest is powerful for non-linear data, but this dataset has 
mostly linear relationships between engagement signals and reach. A 
complex ensemble added noise rather than signal.

**Feature engineering risk:**  
Derived ratios (save-to-like, follower conversion) improve accuracy 
but assume consistent posting behavior. They may not generalize well 
to accounts with very different audience sizes or posting frequencies.

**Dataset limitation:**  
This model is trained on data from a single account. Performance 
on a different account with a different niche or audience may vary — 
retraining on account-specific data would improve accuracy.

---

## Key Finding

> Saves and follower growth predict reach better than likes or 
> comments.

This suggests Instagram's algorithm rewards content that earns 
genuine intent — bookmarks signal "I want to revisit this" and 
follows signal "I want more from this creator." Passive likes 
carry less weight than most creators assume.

**Actionable takeaway for creators:** Optimize for saves and 
follower conversion, not just likes.

---

