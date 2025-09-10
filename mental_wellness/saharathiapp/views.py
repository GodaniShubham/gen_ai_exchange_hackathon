import requests
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import MoodEntry
from django.utils import timezone
from datetime import datetime
from collections import defaultdict

# ========== MAIN PAGES ==========
def index(request):
    return render(request, "index.html")

def chat_page(request):
    return render(request, "chatbot.html")

@csrf_exempt
def save_mood(request):
    if request.method == "POST":
        data = json.loads(request.body)
        MoodEntry.objects.create(
            user=request.user,
            mood_level=data.get("mood_level"),
            notes=data.get("notes", "")
        )
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

@login_required
def mood_analytics(request):
    entries = MoodEntry.objects.filter(user=request.user).order_by("created_at")

    data = [
        {
            "level": e.mood_level,
            "notes": e.notes,
            "date": e.created_at.isoformat()
        }
        for e in entries
    ]
    return render(request, "mood_analytics.html", {"moods_json": json.dumps(data)})

@login_required
def mood_insights(request):
    mode = request.GET.get('mode', 'daily')  # Default to 'daily' if mode not provided
    entries = MoodEntry.objects.filter(user=request.user).order_by("-created_at")[:30]
    if not entries:
        return JsonResponse({"insights": "Log some moods to get your first insights ✨"})

    # Aggregate mood history based on mode
    mood_history = ""
    if mode == 'daily':
        mood_history = "\n".join(
            [f"{e.created_at.strftime('%Y-%m-%d')} - Level {e.mood_level}, Notes: {e.notes or 'None'}"
             for e in entries]
        )
    elif mode == 'weekly':
        weekly_data = defaultdict(list)
        for e in entries:
            week_key = e.created_at.strftime('%Y-W%W')  # ISO week format (e.g., 2025-W36)
            weekly_data[week_key].append(e)
        mood_history = "\n".join(
            [f"Week {week_key.split('-W')[1]} ({datetime.strptime(week_key + '-1', '%Y-W%W-%w').strftime('%Y-%m-%d')}) - Avg Level {sum(e.mood_level for e in data) / len(data):.1f}, Notes: {', '.join(e.notes or 'None' for e in data)}"
             for week_key, data in weekly_data.items()]
        )
    elif mode == 'monthly':
        monthly_data = defaultdict(list)
        for e in entries:
            month_key = e.created_at.strftime('%Y-%m')
            monthly_data[month_key].append(e)
        mood_history = "\n".join(
            [f"{month_key} - Avg Level {sum(e.mood_level for e in data) / len(data):.1f}, Notes: {', '.join(e.notes or 'None' for e in data)}"
             for month_key, data in monthly_data.items()]
        )
    elif mode == 'heatmap':
        # For heatmap, we can use daily data but summarize by week
        weekly_data = defaultdict(list)
        for e in entries:
            week_key = e.created_at.strftime('%Y-W%W')
            weekly_data[week_key].append(e)
        mood_history = "\n".join(
            [f"Week {week_key.split('-W')[1]} ({datetime.strptime(week_key + '-1', '%Y-W%W-%w').strftime('%Y-%m-%d')}) - Avg Level {sum(e.mood_level for e in data) / len(data):.1f}"
             for week_key, data in weekly_data.items()]
        )

    last_entry = entries.first()
    last_mood = last_entry.mood_level
    mood_labels = ["Stressed", "Sad", "Okay", "Good", "Great"]
    last_mood_label = mood_labels[last_mood]

    prompt = f"""
You are an enthusiastic, empathetic, and creative wellness coach, always infusing your advice with warmth, humor, and originality to make users feel seen and inspired. Vary your language, metaphors, and suggestions each time to keep things fresh—never repeat phrases like "take a walk" or "breathe deeply" without twisting them creatively based on the history.

The user's most recent mood was **{last_mood_label} (level {last_mood})** based on {mode} data.
- If it's Great/Good: Explode with joy! Use fun, vivid imagery (like "You're on fire like a shooting star!") to celebrate their vibe, highlight progress from {mode} history, and spark ideas to amplify it further with exciting, unique twists.
- If it's Okay/Sad/Stressed: Respond with gentle compassion, like a close friend wrapping them in a hug. Draw from their {mode} history for personalized encouragement, offering fresh, actionable micro-steps (e.g., if patterns show weekend dips, suggest a quirky ritual like "dance to one song from your childhood"). Focus on empowerment and small wins without clichés.

Analyze their recent mood history (up to 30 entries) for trends based on {mode} view:
{mood_history}

Craft a response with:
1. A vibrant, 1-2 sentence summary of overall trends, tying into their latest mood with personality.
2. 1-2 intriguing patterns (e.g., "Your moods soar mid-week like a caffeine boost, but dip on Sundays—perhaps post-weekend recharge?").
3. 2-3 tailored, inventive suggestions that build on patterns and current mood, making them feel achievable and fun.

Keep the tone uplifting, motivational, and human—like chatting with a wise, fun buddy. Limit to under 6 sentences total, ending on a high note of hope or excitement.
"""

    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250},
        }

        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=payload
        )
        response.raise_for_status()
        data = response.json()

        insights = data["candidates"][0]["content"]["parts"][0]["text"]
        return JsonResponse({"insights": insights})

    except Exception as e:
        return JsonResponse({"insights": f"⚠️ Error generating insights: {str(e)}"})

# ========== AUTH VIEWS ==========
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password", extra_tags="login")
            return redirect("index")

    return redirect("index")

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match", extra_tags="signup")
            return redirect("index")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken", extra_tags="signup")
            return redirect("index")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered", extra_tags="signup")
            return redirect("index")

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Signup successful! Please log in.", extra_tags="login")
        return redirect("index")

# ========== CHATBOT API ==========
@csrf_exempt
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "⚠️ Only POST requests are allowed."})

    user_message = request.POST.get("message", "").strip()
    if not user_message:
        return JsonResponse({"reply": "⚠️ Please say something!"})

    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        )

        payload = {
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200},
        }

        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=payload
        )
        response.raise_for_status()
        data = response.json()

        bot_reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return JsonResponse({"reply": bot_reply})

    except Exception as e:
        return JsonResponse({"reply": f"⚠️ Error: {str(e)}"})
    
# ========== EXTRA PAGES ==========
@login_required
def breathing_page(request):
    return render(request, "breathing.html")

@login_required
def focus_page(request):
    return render(request, "focus.html")

@login_required
def selfcare_page(request):
    return render(request, "selfcare.html")

@login_required
def wellness_page(request):
    return render(request, "wellness.html")
