import json
import os
import httpx
from django.http import JsonResponse
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
    extra_posts = body.get('extra_posts', [])

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

    db_posts = list(
        Post.objects.filter(session_key=session_key)
        .order_by('created_at')
        .values()
    )

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

    impressions = predict_impressions(inputs, all_history)
    viral_score = compute_viral_score(inputs)
    eng_rate = compute_engagement_rate(inputs, impressions)
    follow_rate = compute_follow_rate(inputs)
    avgs = compute_averages(all_history)
    ai = generate_ai_strategy(inputs, viral_score, impressions, avgs)
    forecast_report = build_forecast_report(all_history, inputs, impressions)

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


# ── Agent context builder ──────────────────────────────────────────────────────

def _build_agent_system_prompt(db_posts: list, extra_context: dict) -> str:
    """
    Builds a rich system prompt grounding the LLM in the user's actual data.
    Called on every request so every turn has full context — no data loss across turns.
    """

    base = """You are an expert Instagram growth strategist embedded inside the Instra analytics app.
You have access to the user's full post history and ML model outputs shown below.
Give concise, specific, actionable advice grounded in the numbers. Be direct.
Format key numbers like **1,234 impressions** in bold. Use bullet points for lists.
Never waffle. Never repeat the question back. Get straight to the insight.
If the data supports a clear recommendation, make it confidently."""

    if not db_posts:
        return base + "\n\nNo post history yet — the user hasn't analyzed any posts this session."

    count = len(db_posts)
    avg_likes = sum(p['likes'] for p in db_posts) / count
    avg_saves = sum(p['saves'] for p in db_posts) / count
    avg_comments = sum(p['comments'] for p in db_posts) / count
    avg_shares = sum(p['shares'] for p in db_posts) / count
    avg_follows = sum(p['follows'] for p in db_posts) / count
    avg_imp = sum(p['predicted_impressions'] for p in db_posts) / count
    avg_score = sum(p['viral_score'] for p in db_posts) / count
    avg_hashtags = sum(p['hashtags'] for p in db_posts) / count
    saves_to_likes = avg_saves / max(avg_likes, 1)

    best = max(db_posts, key=lambda p: p['predicted_impressions'])
    worst = min(db_posts, key=lambda p: p['predicted_impressions'])

    # Impression trend (first half vs second half)
    imps = [p['predicted_impressions'] for p in db_posts]
    if count >= 4:
        mid = count // 2
        first_avg = sum(imps[:mid]) / mid
        second_avg = sum(imps[mid:]) / (count - mid)
        if second_avg > first_avg * 1.05:
            imp_trend = f"IMPROVING (up {((second_avg/first_avg)-1)*100:.0f}% recent vs early)"
        elif second_avg < first_avg * 0.95:
            imp_trend = f"DECLINING (down {((first_avg/second_avg)-1)*100:.0f}% recent vs early)"
        else:
            imp_trend = "STABLE"
    elif count >= 2:
        imp_trend = "IMPROVING" if imps[-1] > imps[0] else "DECLINING" if imps[-1] < imps[0] else "STABLE"
    else:
        imp_trend = "only 1 post — no trend yet"

    # Viral score band
    if avg_score >= 65:
        score_band = "strong (above viral threshold)"
    elif avg_score >= 40:
        score_band = "moderate (below viral threshold of 65)"
    else:
        score_band = "weak (well below viral threshold)"

    # Latest AI strategy from engine (if available)
    strategy_section = ""
    if extra_context.get('last_ai'):
        ai = extra_context['last_ai']
        levers = "\n".join(f"  - {l}" for l in ai.get('growth_levers', []))
        strategy_section = f"""
LATEST ML MODEL DIAGNOSIS (most recent post):
  Label: {ai.get('viral_label', 'N/A')}
  Diagnosis: {ai.get('diagnosis', 'N/A')}
  Top growth levers identified:
{levers}
  Best posting time: {ai.get('best_time', 'N/A')}
  Projected impressions with small tweaks: {ai.get('projected_25', 'N/A'):,}
  Projected impressions fully optimised: {ai.get('projected_opt', 'N/A'):,}"""

    # Forecast report summary (if available)
    forecast_section = ""
    if extra_context.get('forecast'):
        f = extra_context['forecast']
        forecast_section = f"""
FORECAST MODEL OUTPUT:
  Impression trend: {f.get('impression_trend', 'N/A').upper()}
  Next post impression forecast: {f.get('next_imp_forecast', 'N/A'):,}
  Next post viral score forecast: {f.get('next_viral_forecast', 'N/A')}
  Save ratio trend: {f.get('saves_ratio', {}).get('direction', 'N/A').upper()}
  Engagement consistency: {f.get('engagement_velocity', {}).get('consistency', 'N/A')}
  Optimal hashtag count (from your data): {f.get('opt_hashtags', 'N/A')}"""

    # Per-post rows (capped at 20 to avoid context bloat)
    recent = db_posts[-20:]
    post_rows = []
    for i, p in enumerate(recent, 1):
        post_rows.append(
            f"  Post {i}: likes={p['likes']}, saves={p['saves']}, comments={p['comments']}, "
            f"shares={p['shares']}, follows={p['follows']}, impressions={p['predicted_impressions']:,}, "
            f"viral_score={p['viral_score']}, hashtags={p['hashtags']}, caption_len={p['caption_length']}, "
            f"label={p['ai_viral_label']}"
        )

    system = f"""{base}

════════════════════════════════════════
USER ACCOUNT SUMMARY ({count} posts analysed)
════════════════════════════════════════
AVERAGES:
  Likes:        {avg_likes:.0f}
  Saves:        {avg_saves:.0f}
  Comments:     {avg_comments:.0f}
  Shares:       {avg_shares:.0f}
  Follows:      {avg_follows:.0f}
  Impressions:  {avg_imp:,.0f}
  Viral score:  {avg_score:.1f}/100 — {score_band}
  Hashtags:     {avg_hashtags:.0f}
  Save/Like ratio: {saves_to_likes:.2f} {'✅ healthy' if saves_to_likes >= 0.3 else '⚠️ low — key growth lever'}

IMPRESSION TREND: {imp_trend}

BEST POST:  {best['predicted_impressions']:,} impressions | viral score {best['viral_score']} | saves={best['saves']}, likes={best['likes']}, shares={best['shares']}
WORST POST: {worst['predicted_impressions']:,} impressions | viral score {worst['viral_score']} | saves={worst['saves']}, likes={worst['likes']}, shares={worst['shares']}
{strategy_section}
{forecast_section}

RAW POST DATA (most recent {len(recent)} of {count}):
{chr(10).join(post_rows)}
════════════════════════════════════════
When answering, cite specific numbers from above. Be concrete and direct."""

    return system


# ── /api/agent/ ───────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def agent(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_message = body.get('message', '').strip()
    history_msgs = body.get('history', [])   # previous turns [{role, content}]
    session_key = body.get('session_key', 'anonymous')

    # Optional: frontend can pass the latest ai + forecast objects
    # so the agent sees the most recent ML outputs without a DB re-query
    extra_context = {
        'last_ai': body.get('last_ai'),         # generate_ai_strategy output
        'forecast': body.get('forecast_report'), # build_forecast_report output
    }

    if not user_message:
        return JsonResponse({'error': 'No message provided'}, status=400)

    # Fetch post history
    db_posts = list(
        Post.objects.filter(session_key=session_key)
        .order_by('created_at')
        .values(
            'likes', 'saves', 'comments', 'shares', 'follows',
            'profile_visits', 'predicted_impressions', 'viral_score',
            'ai_viral_label', 'hashtags', 'caption_length',
        )
    )

    # Build rich system prompt — always contains full data, every turn
    system_prompt = _build_agent_system_prompt(db_posts, extra_context)

    # Build conversation history (previous turns only, no data injection needed —
    # the system prompt handles grounding for every turn)
    messages = []
    MAX_HISTORY_TURNS = 10  # keep last 10 turns to avoid context bloat
    relevant_history = history_msgs[-(MAX_HISTORY_TURNS * 2):]  # user+assistant pairs
    for turn in relevant_history:
        if turn.get('role') in ('user', 'assistant') and turn.get('content'):
            messages.append({'role': turn['role'], 'content': turn['content']})

    # Always append the current user message clean (no context injection in user turn)
    messages.append({'role': 'user', 'content': user_message})

    api_key = getattr(settings, 'GROQ_API_KEY', '') or os.environ.get('GROQ_API_KEY', '')

    if not api_key:
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
                    'max_tokens': 1024,  # was 600 — enough for a 7-day plan
                    'temperature': 0.7,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        *messages,
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data['choices'][0]['message']['content']
    except Exception as e:
        reply = _fallback_agent_response(user_message, db_posts)

    return JsonResponse({'reply': reply})


# ── Fallback (no API key) ──────────────────────────────────────────────────────

def _fallback_agent_response(message: str, posts: list) -> str:
    """Rule-based fallback when no API key is configured."""
    msg = message.lower()
    count = len(posts)

    if count == 0:
        return (
            "I don't have any post data yet — analyze a post first and I'll give you "
            "personalised advice. Quick tip while you set up: saves are the #1 algorithmic "
            "signal on Instagram right now. Add a 'save this' CTA to every caption."
        )

    avg_saves = sum(p['saves'] for p in posts) / count
    avg_likes = sum(p['likes'] for p in posts) / count
    avg_score = sum(p['viral_score'] for p in posts) / count
    avg_imp = sum(p['predicted_impressions'] for p in posts) / count
    best_post = max(posts, key=lambda p: p['predicted_impressions'])
    saves_ratio = avg_saves / max(avg_likes, 1)

    if 'save' in msg:
        if saves_ratio < 0.3:
            return (
                f"Your saves-to-likes ratio is **{saves_ratio:.2f}** — that's low. "
                "Instagram heavily weights saves. Fix: (1) end every caption with 'save this for later', "
                "(2) create list-style content people want to reference again, "
                "(3) tutorials and how-tos earn saves better than opinion posts."
            )
        return (
            f"Your saves ratio is **{saves_ratio:.2f}** — solid. To push higher: make content "
            "more reference-worthy. Checklists, step-by-step guides, and comparison posts "
            "consistently earn saves."
        )

    if any(w in msg for w in ['next', 'plan', 'calendar', 'content', 'post']):
        return (
            f"Based on your **{count} posts**: avg viral score **{avg_score:.1f}/100**, "
            f"avg **{avg_imp:,.0f} impressions**. Your best post hit "
            f"**{best_post['predicted_impressions']:,} impressions** "
            f"with {best_post['saves']} saves and {best_post['likes']} likes. "
            "Replicate that format, post Tuesday 7–9 PM or Thursday 6–8 PM, "
            "and add a saves CTA to every caption."
        )

    if 'follow' in msg:
        return (
            "To convert visitors into followers: (1) Your bio headline should state your value "
            "in 6 words or fewer. (2) Pin your 3 best-performing posts. "
            "(3) Grid visual consistency matters more than any single post."
        )

    if 'hashtag' in msg:
        avg_tags = sum(p['hashtags'] for p in posts) / count
        return (
            f"You're averaging **{avg_tags:.0f} hashtags** per post. "
            "Sweet spot: 15–20 niche-specific tags. Mix: 5 tiny niche tags (under 50K posts), "
            "10 mid-size (50K–500K), 5 broader (500K–2M). Avoid mega-tags with 10M+ posts."
        )

    # Generic with data
    return (
        f"Across your **{count} post{'s' if count != 1 else ''}**: "
        f"avg **{avg_likes:.0f} likes**, **{avg_saves:.0f} saves**, "
        f"viral score **{avg_score:.1f}/100**, avg **{avg_imp:,.0f} impressions**. "
        f"Save/like ratio: **{saves_ratio:.2f}** {'✅' if saves_ratio >= 0.3 else '⚠️ — this is your main lever'}. "
        "Ask me something specific — content ideas, timing, why a post underperformed, "
        "or build a 7-day content plan."
    )