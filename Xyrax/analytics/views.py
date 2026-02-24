import json
import os
import httpx
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.conf import settings

from .models import Post
from .engine import (
    predict_impressions,
    compute_viral_score,
    compute_engagement_rate,
    compute_follow_rate,
    compute_averages,
    generate_ai_strategy,
    build_forecast_report,
)


def index(request):
    """Serve the main SPA."""
    return render(request, 'index.html')


# ── /api/analyze/ ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def analyze(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    session_key = body.get('session_key', 'anonymous')
    extra_posts = body.get('extra_posts', [])  # CSV uploads from frontend

    inputs = {
        'likes': int(body.get('likes', 0)),
        'saves': int(body.get('saves', 0)),
        'comments': int(body.get('comments', 0)),
        'shares': int(body.get('shares', 0)),
        'follows': int(body.get('follows', 0)),
        'profile_visits': int(body.get('profile_visits', 0)),
        'caption_length': int(body.get('caption_length', 0)),
        'hashtags': int(body.get('hashtags', 0)),
        'reposts': int(body.get('reposts', 0)),
    }

    # Fetch session history from DB
    db_posts = list(
        Post.objects.filter(session_key=session_key)
        .order_by('created_at')
        .values()
    )

    # Merge CSV posts + DB history for predictions
    all_history = extra_posts + [
        {
            'likes': p['likes'], 'saves': p['saves'], 'comments': p['comments'],
            'shares': p['shares'], 'follows': p['follows'],
            'predicted_impressions': p['predicted_impressions'],
            'viral_score': p['viral_score'],
            'hashtags': p['hashtags'],
        }
        for p in db_posts
    ]

    # Core calculations
    impressions = predict_impressions(inputs, all_history)
    viral_score = compute_viral_score(inputs)
    eng_rate = compute_engagement_rate(inputs, impressions)
    follow_rate = compute_follow_rate(inputs)
    avgs = compute_averages(all_history)
    ai = generate_ai_strategy(inputs, viral_score, impressions, avgs)

    # Forecast report (needs ≥2 posts)
    forecast_report = build_forecast_report(all_history, inputs, impressions)

    # Persist to DB
    post = Post.objects.create(
        session_key=session_key,
        **inputs,
        predicted_impressions=impressions,
        viral_score=viral_score,
        eng_rate=eng_rate,
        follow_rate=follow_rate,
        ai_viral_label=ai.get('viral_label', ''),
    )

    return JsonResponse({
        'impressions': impressions,
        'viral_score': viral_score,
        'eng_rate': eng_rate,
        'follow_rate': follow_rate,
        'avg_impressions': avgs.get('impressions', 0),
        'avgs': avgs,
        'inputs': inputs,
        'ai': ai,
        'forecast_report': forecast_report,
        'history_count': Post.objects.filter(session_key=session_key).count(),
    })


# ── /api/history/ ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def history(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    session_key = body.get('session_key', 'anonymous')
    posts = list(
        Post.objects.filter(session_key=session_key)
        .order_by('created_at')
        .values(
            'likes', 'saves', 'comments', 'shares', 'follows',
            'profile_visits', 'caption_length', 'hashtags', 'reposts',
            'predicted_impressions', 'viral_score', 'eng_rate',
            'follow_rate', 'ai_viral_label', 'created_at',
        )
    )

    # Convert datetime for JSON serialisation
    for p in posts:
        p['created_at'] = p['created_at'].isoformat()

    return JsonResponse({'posts': posts, 'count': len(posts)})


# ── /api/clear/ ───────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def clear(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    session_key = body.get('session_key', 'anonymous')
    deleted, _ = Post.objects.filter(session_key=session_key).delete()
    return JsonResponse({'deleted': deleted})


# ── /api/agent/ ───────────────────────────────────────────────────────────────

AGENT_SYSTEM = """You are an expert Instagram growth strategist embedded inside the Instra analytics app.
You have access to the user's post history (provided in their messages) and deep knowledge of Instagram's algorithm.

Your job is to give concise, specific, actionable advice. Be direct. Use data from the history when available.
Format key numbers like **1,234 impressions** in bold. Use bullet points for lists.
Never waffle. Never repeat the question back. Get straight to the insight.
If you don't have data to answer precisely, give your best strategic advice and say what data would help.
"""


@csrf_exempt
@require_http_methods(['POST'])
def agent(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message = body.get('message', '').strip()
    history_msgs = body.get('history', [])  # Previous turns
    session_key = body.get('session_key', 'anonymous')

    if not user_message:
        return JsonResponse({'error': 'No message provided'}, status=400)

    # Fetch session post data and inject as context
    db_posts = list(
        Post.objects.filter(session_key=session_key)
        .order_by('created_at')
        .values(
            'likes', 'saves', 'comments', 'shares', 'follows',
            'predicted_impressions', 'viral_score', 'ai_viral_label',
            'hashtags', 'caption_length',
        )
    )

    if db_posts:
        post_lines = []
        for i, p in enumerate(db_posts, 1):
            post_lines.append(
                f"Post {i}: likes={p['likes']}, saves={p['saves']}, "
                f"comments={p['comments']}, shares={p['shares']}, "
                f"follows={p['follows']}, predicted_impressions={p['predicted_impressions']}, "
                f"viral_score={p['viral_score']}, label={p['ai_viral_label']}, "
                f"hashtags={p['hashtags']}, caption_length={p['caption_length']}"
            )
        context_block = (
            f"\n\n--- USER'S POST HISTORY ({len(db_posts)} posts) ---\n"
            + "\n".join(post_lines)
            + "\n--- END HISTORY ---\n"
        )
        # Prepend context to the latest user message
        augmented_message = context_block + "\nUser question: " + user_message
    else:
        augmented_message = user_message

    # Build conversation for API
    messages = []
    for turn in history_msgs[:-1]:  # All but the last (we use augmented)
        if turn.get('role') in ('user', 'assistant'):
            messages.append({'role': turn['role'], 'content': turn['content']})
    messages.append({'role': 'user', 'content': augmented_message})

    # Call Groq API
    api_key = getattr(settings, 'GROQ_API_KEY', '') or os.environ.get('GROQ_API_KEY', '')

    if not api_key:
        # Fallback: rule-based response when no API key
        reply = _fallback_agent_response(user_message, db_posts)
        return JsonResponse({'reply': reply})

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'max_tokens': 600,
                    'messages': [{'role': 'system', 'content': AGENT_SYSTEM}] + messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data['choices'][0]['message']['content']
    except Exception as e:
        reply = _fallback_agent_response(user_message, db_posts)

    return JsonResponse({'reply': reply})


def _fallback_agent_response(message: str, posts: list) -> str:
    """Rule-based fallback when no API key is configured."""
    msg = message.lower()
    count = len(posts)

    if count == 0:
        return (
            "I don't have any post data yet — analyze a post first and I'll be able to give you "
            "personalized advice. In the meantime: saves are the #1 signal on Instagram right now. "
            "Add a 'save this' CTA to every caption."
        )

    avg_saves = sum(p['saves'] for p in posts) / count
    avg_likes = sum(p['likes'] for p in posts) / count
    avg_score = sum(p['viral_score'] for p in posts) / count
    best_post = max(posts, key=lambda p: p['predicted_impressions'])

    if 'save' in msg:
        ratio = avg_saves / max(avg_likes, 1)
        if ratio < 0.3:
            return (
                f"Your saves-to-likes ratio is **{ratio:.2f}** — that's low. "
                "Instagram heavily weights saves in its algorithm. Try: (1) end every caption with "
                "'save this for later', (2) create list-style content people want to reference again, "
                "(3) add value that justifies a bookmark — tutorials, tips, recipes."
            )
        else:
            return (
                f"Good news — your saves ratio is **{ratio:.2f}**, which is solid. "
                "To push it higher: make your content more 'reference-worthy'. Checklists, how-tos, "
                "and comparison posts consistently earn saves."
            )

    if 'next' in msg or 'post' in msg or 'content' in msg:
        return (
            f"Based on your **{count} posts**, your average viral score is **{avg_score:.1f}/100**. "
            f"Your best post got **{best_post['predicted_impressions']:,} impressions**. "
            "For your next post: replicate whatever format that best post used, "
            "post Tuesday 7–9 PM or Thursday 6–8 PM, and end with a saves CTA."
        )

    if 'follow' in msg:
        return (
            "To convert profile visitors into followers: (1) Your bio headline needs to state your value "
            "in 6 words or fewer. (2) Pin your 3 best posts — first impressions matter. "
            "(3) Your grid's visual consistency matters more than individual post quality."
        )

    if 'hashtag' in msg:
        avg_tags = sum(p['hashtags'] for p in posts) / count
        return (
            f"You're averaging **{avg_tags:.0f} hashtags** per post. "
            "The current sweet spot is 15–20 niche-specific tags (avoid mega-tags with 10M+ posts). "
            "Mix: 5 tiny niche tags (under 50K posts), 10 mid-size (50K–500K), 5 broader (500K–2M)."
        )

    # Generic response with data
    return (
        f"Looking at your **{count} post{'s' if count != 1 else ''}**: "
        f"average **{avg_likes:.0f} likes**, **{avg_saves:.0f} saves**, "
        f"viral score **{avg_score:.1f}/100**. "
        "Top priority: if your saves-to-likes ratio is under 0.3, that's your biggest growth lever. "
        "Ask me something more specific — content ideas, timing, why a post underperformed, etc."
    )
