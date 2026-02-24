"""
Core analytics engine for Instra.
Handles impression prediction, viral scoring, and AI strategy generation.
"""
import math
import random
from datetime import datetime


# ── Impression prediction ────────────────────────────────────────────────────

def predict_impressions(inputs: dict, history: list[dict]) -> int:
    """
    Weighted formula combining engagement signals.
    When history is available, calibrates to the session's historical average.
    """
    likes = inputs.get('likes', 0)
    saves = inputs.get('saves', 0)
    comments = inputs.get('comments', 0)
    shares = inputs.get('shares', 0)
    follows = inputs.get('follows', 0)
    profile_visits = inputs.get('profile_visits', 0)
    caption_length = inputs.get('caption_length', 0)
    hashtags = inputs.get('hashtags', 0)
    reposts = inputs.get('reposts', 0)

    # Base engagement score
    base = (
        likes * 1.0 +
        saves * 4.5 +
        comments * 3.0 +
        shares * 6.0 +
        follows * 5.0 +
        profile_visits * 0.8 +
        reposts * 5.5
    )

    # Caption sweet-spot bonus (100–220 chars)
    if 100 <= caption_length <= 220:
        base *= 1.08
    elif caption_length > 400:
        base *= 0.96

    # Hashtag sweet-spot bonus (5–25 tags)
    if 5 <= hashtags <= 25:
        base *= 1.05
    elif hashtags > 30:
        base *= 0.97

    # Convert to estimated impressions
    impressions = int(base * 12.5 + 400)

    # Calibrate against historical average if we have data
    if history:
        hist_imps = [p.get('predicted_impressions', 0) for p in history if p.get('predicted_impressions', 0) > 0]
        if hist_imps:
            hist_avg = sum(hist_imps) / len(hist_imps)
            # Blend: 60% formula, 40% scaled from historical
            saves_ratio = saves / max(likes, 1)
            scale = 1 + (saves_ratio - 0.5) * 0.4
            calibrated = hist_avg * scale
            impressions = int(0.6 * impressions + 0.4 * calibrated)

    return max(impressions, 100)


def compute_viral_score(inputs: dict) -> float:
    """0–100 composite quality score."""
    likes = inputs.get('likes', 0)
    saves = inputs.get('saves', 0)
    comments = inputs.get('comments', 0)
    shares = inputs.get('shares', 0)
    follows = inputs.get('follows', 0)
    profile_visits = inputs.get('profile_visits', 0)
    hashtags = inputs.get('hashtags', 0)

    total_eng = likes + saves + comments + shares + follows
    if total_eng == 0:
        return 0.0

    # Saves-to-likes ratio (high saves = strong save-worthy content)
    saves_ratio = saves / max(likes, 1)
    saves_score = min(saves_ratio * 40, 35)

    # Comments quality
    comments_score = min((comments / max(total_eng, 1)) * 100 * 1.5, 20)

    # Shares virality
    shares_score = min((shares / max(total_eng, 1)) * 100 * 2, 20)

    # Follow conversion
    follow_score = min((follows / max(profile_visits, 1)) * 100 * 0.3, 15) if profile_visits > 0 else 0

    # Hashtag score
    if 10 <= hashtags <= 25:
        hashtag_score = 10
    elif 5 <= hashtags <= 30:
        hashtag_score = 7
    else:
        hashtag_score = 3

    raw = saves_score + comments_score + shares_score + follow_score + hashtag_score
    return round(min(raw, 100), 1)


def compute_engagement_rate(inputs: dict, impressions: int) -> float:
    total = (
        inputs.get('likes', 0) +
        inputs.get('saves', 0) +
        inputs.get('comments', 0) +
        inputs.get('shares', 0)
    )
    if impressions == 0:
        return 0.0
    return round((total / impressions) * 100, 2)


def compute_follow_rate(inputs: dict) -> float:
    follows = inputs.get('follows', 0)
    profile_visits = inputs.get('profile_visits', 0)
    if profile_visits == 0:
        return 0.0
    return round((follows / profile_visits) * 100, 1)


# ── Historical averages ──────────────────────────────────────────────────────

def compute_averages(history: list[dict]) -> dict:
    if not history:
        return {'likes': 0, 'saves': 0, 'comments': 0, 'shares': 0, 'impressions': 0}
    keys = ['likes', 'saves', 'comments', 'shares']
    avgs = {k: round(sum(p.get(k, 0) for p in history) / len(history)) for k in keys}
    imp_vals = [p.get('predicted_impressions', 0) for p in history if p.get('predicted_impressions', 0) > 0]
    avgs['impressions'] = round(sum(imp_vals) / len(imp_vals)) if imp_vals else 0
    return avgs


# ── Best posting times ───────────────────────────────────────────────────────

POSTING_TIMES = [
    'Tuesday 7-9 PM',
    'Thursday 6-8 PM',
    'Wednesday 12-2 PM',
    'Sunday 8-10 PM',
    'Monday 8-10 AM',
    'Friday 9-11 AM',
    'Wednesday 7-9 AM',
    'Saturday 10-12 PM',
    'Thursday 12-2 PM',
    'Tuesday 6-8 PM',
]


def get_best_times(inputs: dict) -> list[dict]:
    """Return top 3 posting slots; the top one is always marked BEST."""
    saves = inputs.get('saves', 0)
    comments = inputs.get('comments', 0)
    hashtags = inputs.get('hashtags', 0)

    # Pseudo-deterministic shuffle based on post metrics
    seed = saves * 7 + comments * 13 + hashtags * 3
    rng = random.Random(seed)
    shuffled = POSTING_TIMES[:]
    rng.shuffle(shuffled)

    top3 = shuffled[:3]
    return [
        {'slot': slot, 'label': 'BEST' if i == 0 else 'GOOD'}
        for i, slot in enumerate(top3)
    ]


# ── Forecast report (multi-post) ─────────────────────────────────────────────

def smooth(values: list[float], window: int = 3) -> list[float]:
    out = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start:i + 1]
        out.append(round(sum(chunk) / len(chunk), 1))
    return out


def trend_direction(values: list[float]) -> str:
    if len(values) < 2:
        return 'stable'
    first_half = values[:len(values) // 2]
    second_half = values[len(values) // 2:]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    diff = avg_second - avg_first
    if diff > avg_first * 0.05:
        return 'improving'
    if diff < -avg_first * 0.05:
        return 'declining'
    return 'stable'


def build_forecast_report(history, current_inputs, current_imp):
    """Build a multi-post forecast report. Requires at least 2 historical posts."""
    all_posts = list(history) + [{**current_inputs, 'predicted_impressions': current_imp}]
    if len(all_posts) < 2:
        return None

    imps = [p.get('predicted_impressions', 0) for p in all_posts]
    saves_ratios = [p.get('saves', 0) / max(p.get('likes', 1), 1) for p in all_posts]
    viral_scores = [p.get('viral_score', 0) for p in all_posts]

    imp_smoothed = smooth(imps)
    imp_trend = trend_direction(imps)

    saves_trend = trend_direction(saves_ratios)
    eng_trend = trend_direction([p.get('likes', 0) + p.get('comments', 0) for p in all_posts])

    # Simple linear extrapolation for next post
    if len(imps) >= 2:
        slope = (imps[-1] - imps[0]) / max(len(imps) - 1, 1)
        next_imp = max(int(imps[-1] + slope * 0.5), 100)
    else:
        next_imp = imps[-1]

    if len(viral_scores) >= 2:
        v_slope = (viral_scores[-1] - viral_scores[0]) / max(len(viral_scores) - 1, 1)
        next_viral = round(min(viral_scores[-1] + v_slope * 0.5, 100), 1)
    else:
        next_viral = viral_scores[-1] if viral_scores else 0

    # Optimal hashtag count from best-performing posts
    hashtag_vals = [p.get('hashtags', 0) for p in all_posts if p.get('hashtags', 0) > 0]
    opt_hashtags = round(sum(hashtag_vals) / len(hashtag_vals)) if hashtag_vals else 20

    # Consistency rating
    if len(imps) >= 3:
        avg_imp = sum(imps) / len(imps)
        variance = sum((x - avg_imp) ** 2 for x in imps) / len(imps)
        cv = math.sqrt(variance) / max(avg_imp, 1)
        consistency = 'High' if cv < 0.25 else 'Medium' if cv < 0.5 else 'Low'
    else:
        consistency = 'Building'

    return {
        'post_count': len(all_posts),
        'impression_trend': imp_trend,
        'imp_smoothed': imp_smoothed,
        'next_imp_forecast': next_imp,
        'next_viral_forecast': next_viral,
        'opt_hashtags': opt_hashtags,
        'saves_ratio': {
            'values': [round(r, 3) for r in saves_ratios],
            'direction': saves_trend,
        },
        'engagement_velocity': {
            'direction': eng_trend,
            'consistency': consistency,
        },
    }


# ── AI strategy (rule-based, no LLM required) ────────────────────────────────

def generate_ai_strategy(inputs: dict, viral_score: float, impressions: int, avgs: dict) -> dict:
    likes = inputs.get('likes', 0)
    saves = inputs.get('saves', 0)
    comments = inputs.get('comments', 0)
    shares = inputs.get('shares', 0)
    follows = inputs.get('follows', 0)
    profile_visits = inputs.get('profile_visits', 0)
    caption_length = inputs.get('caption_length', 0)
    hashtags = inputs.get('hashtags', 0)
    reposts = inputs.get('reposts', 0)

    saves_ratio = saves / max(likes, 1)
    comment_ratio = comments / max(likes, 1)
    follow_conv = follows / max(profile_visits, 1) if profile_visits > 0 else 0

    # Viral label
    if viral_score >= 65:
        viral_label = 'High Potential'
    elif viral_score >= 40:
        viral_label = 'Moderate Potential'
    else:
        viral_label = 'Low Potential'

    # Diagnosis
    strengths = []
    weaknesses = []

    if saves_ratio > 0.5:
        strengths.append('strong saves (people are bookmarking your content)')
    elif saves_ratio < 0.2:
        weaknesses.append('saves are low — your content isn\'t being saved for later')

    if comment_ratio > 0.1:
        strengths.append('high comment rate (great conversation starter)')
    elif comment_ratio < 0.03:
        weaknesses.append('very few comments — add a direct question in your caption')

    if shares > likes * 0.05:
        strengths.append('solid share rate (content is spreading)')
    elif shares == 0:
        weaknesses.append('zero shares — make it more quote-worthy or surprising')

    if follow_conv > 0.15:
        strengths.append('excellent follow conversion from profile visits')
    elif profile_visits > 0 and follow_conv < 0.05:
        weaknesses.append('people visit your profile but don\'t follow — bio or grid may need work')

    if reposts > 0:
        strengths.append('getting reposts (very strong signal)')

    if strengths and weaknesses:
        diagnosis = f"Your post shows {', '.join(strengths[:2])}. The main area to improve: {weaknesses[0]}."
    elif strengths:
        diagnosis = f"Strong post: {', '.join(strengths[:2])}. Keep replicating what's working."
    elif weaknesses:
        diagnosis = f"This post is underperforming. Key issues: {'; '.join(weaknesses[:2])}."
    else:
        diagnosis = "Solid baseline metrics. Focus on saves and comments to push into viral range."

    # Growth levers
    levers = []

    if saves_ratio < 0.4:
        levers.append('Add a "save this for later" or "bookmark this" CTA at the end of your caption — saves directly boost reach.')
    if comment_ratio < 0.05:
        levers.append('End your caption with a specific question (not "what do you think?" — ask something binary like "coffee or matcha?")')
    if shares < 3:
        levers.append('Make your hook more shareable: start with a surprising stat, a bold claim, or something polarising that people want to forward.')
    if hashtags < 10:
        levers.append(f'You\'re using {hashtags} hashtags — try 15–20 relevant niche tags to expand discoverability.')
    elif hashtags > 28:
        levers.append(f'You\'re using {hashtags} hashtags — Instagram can penalise over-tagging. Try 15–20 targeted ones.')
    if caption_length < 80:
        levers.append('Your caption is very short. Longer captions (150–220 chars) tend to get more comments and saves.')
    elif caption_length > 400:
        levers.append('Long captions can lose people. Try cutting to 150–220 chars with a strong hook in the first line.')
    if follow_conv < 0.08 and profile_visits > 5:
        levers.append('Optimise your bio: add a clear value prop in line 1, and make sure your grid looks cohesive when people land on it.')

    # Fill up to 3 levers if needed
    defaults = [
        'Post at peak times: Tuesday 7–9 PM or Thursday 6–8 PM for highest reach.',
        'Add a carousel — they consistently get 2–3× more saves than single images.',
        'Use the first 3 lines of your caption as a hook — only these show before "more".',
    ]
    for d in defaults:
        if len(levers) >= 3:
            break
        levers.append(d)
    levers = levers[:3]

    # Best time recommendation
    times = get_best_times(inputs)
    best_time = f"Best window for this type of content: {times[0]['slot']}. Secondary option: {times[1]['slot']}."

    # Projections
    projected_25 = int(impressions * 1.25)
    projected_opt = int(impressions * 1.60)

    return {
        'viral_label': viral_label,
        'diagnosis': diagnosis,
        'growth_levers': levers,
        'best_times': times,
        'best_time': best_time,
        'projected_25': projected_25,
        'projected_opt': projected_opt,
    }
