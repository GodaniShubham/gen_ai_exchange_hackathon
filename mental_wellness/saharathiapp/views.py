import requests
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import ChatSession, MoodEntry
from collections import defaultdict
from datetime import datetime

# ========== MAIN PAGES ==========
def index(request):
    return render(request, "index.html")

def chat_page(request):
    return render(request, "chatbot.html")

# ========== MOOD TRACKING ==========
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
        } for e in entries
    ]
    return render(request, "mood_analytics.html", {"moods_json": json.dumps(data)})

@login_required
def mood_insights(request):
    mode = request.GET.get('mode', 'daily')
    entries = MoodEntry.objects.filter(user=request.user).order_by("-created_at")[:30]
    if not entries:
        return JsonResponse({"insights": "Log some moods to get your first insights ✨"})

    # Aggregate mood history
    mood_history = "\n".join(
        [f"{e.created_at.strftime('%Y-%m-%d')} - Level {e.mood_level}, Notes: {e.notes or 'None'}"
         for e in entries]
    )

    last_entry = entries.first()
    last_mood = last_entry.mood_level
    mood_labels = ["Stressed", "Sad", "Okay", "Good", "Great"]
    last_mood_label = mood_labels[last_mood]

    prompt = f"""
You are a creative wellness coach. The user's most recent mood was {last_mood_label} (level {last_mood}) based on {mode} data.
Analyze recent mood history (up to 30 entries):
{mood_history}
Craft a short, uplifting response with insights and suggestions.
"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250},
        }
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
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
        if user:
            auth_login(request, user)
            return redirect("index")
        messages.error(request, "Invalid username or password", extra_tags="login")
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
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200},
        }
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
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

def settings_privacy(request):
    """
    ⚙️ Handles Settings & Privacy:
    - Clear all chat data
    - Set preferred language
    - Export chat data (TXT or JSON)
    """
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "clear":
            ChatSession.objects.all().delete()
            request.session.flush()
            messages.success(request, "✅ All your chat data has been cleared successfully.")
            return redirect("settings_privacy")

        elif action == "set_language":
            lang = request.POST.get("language", "Auto")
            request.session["lang"] = lang
            messages.success(request, f"🌐 Language set to '{lang}'.")
            return redirect("settings_privacy")

        elif action == "export":
            export_format = request.POST.get("format", "txt")
            sessions = ChatSession.objects.all().order_by("created_at")

            if export_format == "json":
                data = []
                for s in sessions:
                    session_data = {
                        "title": s.title or str(s.session_id),
                        "created_at": s.created_at.isoformat(),
                        "messages": [{"sender": m.sender, "text": m.text, "timestamp": m.timestamp.isoformat()} for m in s.messages.all().order_by("timestamp")]
                    }
                    data.append(session_data)
                response = JsonResponse(data, safe=False)
                response['Content-Disposition'] = 'attachment; filename="chat_data.json"'
                return response

            # Default: TXT export
            export_text = ""
            for s in sessions:
                export_text += f"--- {s.title or 'Chat'} ({s.created_at.strftime('%Y-%m-%d %H:%M')}) ---\n"
                for m in s.messages.all().order_by("timestamp"):
                    export_text += f"{m.sender.upper()}: {m.text}\n"
                export_text += "\n"
            response = HttpResponse(export_text, content_type="text/plain")
            response['Content-Disposition'] = 'attachment; filename="chat_data.txt"'
            return response

    # GET request
    saved_lang = request.session.get("lang", "Auto")
    return render(request, "settings_privacy.html", {"saved_lang": saved_lang})


@login_required
def get_chat_messages(request, session_id):
    # Replace this with your actual logic
    messages = [
        {"sender": "bot", "text": "Hello!"},
        {"sender": "user", "text": "Hi there!"}
    ]
    return JsonResponse({"session_id": str(session_id), "messages": messages})
