import json
import requests
from uuid import UUID
from datetime import datetime
from collections import defaultdict

from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .models import ChatSession, Message, MoodEntry


# ========== MAIN PAGES ==========
def index(request):
    return render(request, "index.html")


def chat_page(request):
    sessions = ChatSession.objects.all().order_by("-created_at")
    return render(request, "chatbot.html", {"sessions": sessions})


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


# ========== MOOD ANALYTICS ==========
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
    mode = request.GET.get('mode', 'daily')
    entries = MoodEntry.objects.filter(user=request.user).order_by("-created_at")[:30]
    if not entries:
        return JsonResponse({"insights": "Log some moods to get your first insights ✨"})

    # Aggregate mood history
    mood_history = ""
    if mode == 'daily':
        mood_history = "\n".join(
            [f"{e.created_at.strftime('%Y-%m-%d')} - Level {e.mood_level}, Notes: {e.notes or 'None'}"
             for e in entries]
        )
    elif mode == 'weekly':
        weekly_data = defaultdict(list)
        for e in entries:
            week_key = e.created_at.strftime('%Y-W%W')
            weekly_data[week_key].append(e)
        mood_history = "\n".join(
            [f"Week {wk.split('-W')[1]} ({datetime.strptime(wk + '-1', '%Y-W%W-%w').strftime('%Y-%m-%d')}) - "
             f"Avg Level {sum(e.mood_level for e in data) / len(data):.1f}, "
             f"Notes: {', '.join(e.notes or 'None' for e in data)}"
             for wk, data in weekly_data.items()]
        )
    elif mode == 'monthly':
        monthly_data = defaultdict(list)
        for e in entries:
            month_key = e.created_at.strftime('%Y-%m')
            monthly_data[month_key].append(e)
        mood_history = "\n".join(
            [f"{mk} - Avg Level {sum(e.mood_level for e in data) / len(data):.1f}, "
             f"Notes: {', '.join(e.notes or 'None' for e in data)}"
             for mk, data in monthly_data.items()]
        )
    elif mode == 'heatmap':
        weekly_data = defaultdict(list)
        for e in entries:
            week_key = e.created_at.strftime('%Y-W%W')
            weekly_data[week_key].append(e)
        mood_history = "\n".join(
            [f"Week {wk.split('-W')[1]} ({datetime.strptime(wk + '-1', '%Y-W%W-%w').strftime('%Y-%m-%d')}) - "
             f"Avg Level {sum(e.mood_level for e in data) / len(data):.1f}"
             for wk, data in weekly_data.items()]
        )

    # Latest mood
    last_entry = entries.first()
    last_mood = last_entry.mood_level
    mood_labels = ["Stressed", "Sad", "Okay", "Good", "Great"]
    last_mood_label = mood_labels[last_mood]

    # Prompt for Gemini
    prompt = f"""
You are an empathetic, creative wellness coach.
User's most recent mood was **{last_mood_label} (level {last_mood})** based on {mode} data.
Recent history:
{mood_history}

Write <6 sentences: trends, 1–2 patterns, 2–3 creative suggestions.
Keep it warm, uplifting, and fresh each time.
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


# ========== AUTH ==========
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
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
    session_id = request.POST.get("session_id")
    if not user_message:
        return JsonResponse({"reply": "⚠️ Please say something!"})
    if not settings.GEMINI_API_KEY:
        return JsonResponse({"reply": "⚠️ Gemini API key missing!"})

    # Get/create session
    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(session_id=UUID(session_id))
        except:
            session = ChatSession.objects.create()
    else:
        session = ChatSession.objects.create()

    # Save user msg
    Message.objects.create(session=session, sender="user", text=user_message)
    if not session.title:
        session.title = user_message[:50]
        session.save()

    # Gemini API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"You are a supportive Mental Wellness Chatbot. User asked: {user_message}"}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500},
    }

    try:
        r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        reply = "⚠️ No reply received."
        candidates = data.get("candidates", [])
        if candidates and candidates[0].get("content"):
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                reply = parts[0].get("text", reply)

        Message.objects.create(session=session, sender="bot", text=reply)
        return JsonResponse({
            "reply": reply,
            "session_id": str(session.session_id),
            "title": session.title or f"Chat {session.session_id}"
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({"reply": f"⚠️ API Error: {str(e)}"})


def get_chat_messages(request, session_id):
    try:
        session = ChatSession.objects.get(session_id=UUID(session_id))
    except:
        return JsonResponse({"messages": []})

    messages_qs = session.messages.all().order_by("timestamp")
    return JsonResponse({
        "messages": [{"sender": m.sender, "text": m.text} for m in messages_qs]
    })


# ========== STREAMING CHAT ==========
@csrf_exempt
def chatbot_stream(request):
    if request.method != "POST":
        return JsonResponse({"reply": "⚠️ Only POST requests are allowed."})

    user_message = request.POST.get("message", "").strip()
    session_id = request.POST.get("session_id")
    if not user_message:
        return JsonResponse({"reply": "⚠️ Please say something!"})

    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(session_id=UUID(session_id))
        except:
            session = ChatSession.objects.create()
    else:
        session = ChatSession.objects.create()

    Message.objects.create(session=session, sender="user", text=user_message)
    if not session.title:
        session.title = user_message[:50]
        session.save()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"You are a supportive Mental Wellness Chatbot. User asked: {user_message}"}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500},
    }

    def event_stream():
        final_reply_parts = []
        try:
            with requests.post(url, headers={"Content-Type": "application/json"}, json=payload, stream=True, timeout=60) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    line = line.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    try:
                        obj = json.loads(line.replace("data: ", ""))
                    except:
                        continue
                    candidates = obj.get("candidates", [])
                    if candidates and candidates[0].get("content"):
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            chunk = parts[0].get("text", "")
                            if chunk:
                                final_reply_parts.append(chunk)
                                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            final_reply = "".join(final_reply_parts)
            if final_reply:
                Message.objects.create(session=session, sender="bot", text=final_reply)
        except Exception as e:
            yield f"data: {json.dumps({'chunk': '⚠️ Error: ' + str(e)})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


# ========== SETTINGS ==========
def settings_privacy(request):
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

            # TXT export
            export_text = ""
            for s in sessions:
                export_text += f"--- {s.title or 'Chat'} ({s.created_at.strftime('%Y-%m-%d %H:%M')}) ---\n"
                for m in s.messages.all().order_by("timestamp"):
                    export_text += f"{m.sender.upper()}: {m.text}\n"
                export_text += "\n"
            response = HttpResponse(export_text, content_type="text/plain")
            response['Content-Disposition'] = 'attachment; filename="chat_data.txt"'
            return response

    saved_lang = request.session.get("lang", "Auto")
    return render(request, "settings_privacy.html", {"saved_lang": saved_lang})


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
