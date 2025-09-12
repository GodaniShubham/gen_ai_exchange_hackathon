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
from django.utils import timezone
import requests
import json

# ========== MAIN PAGES ==========
def index(request):
    return render(request, "index.html")

def chat_page(request):
    return render(request, "chatbot.html")

# ========== MOOD TRACKING ==========
@csrf_exempt
def save_mood(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mood_level = data.get("mood_level")
            notes = data.get("notes", "")

            # Ensure session exists for anonymous users
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            MoodEntry.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=None if request.user.is_authenticated else session_key,
                mood_level=mood_level,
                notes=notes
            )

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def mood_analytics(request):
    if request.user.is_authenticated:
        entries = MoodEntry.objects.filter(user=request.user).order_by("created_at")
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        entries = MoodEntry.objects.filter(session_id=session_key).order_by("created_at")

    data = [
        {
            "level": e.mood_level,
            "notes": e.notes,
            "date": e.created_at.isoformat()
        }
        for e in entries
    ]
    return render(request, "mood_analytics.html", {"moods_json": json.dumps(data)})

def mood_insights(request):
    mode = request.GET.get("mode", "daily")

    # ✅ Handle logged-in OR guest (session_id based) users
    if request.user.is_authenticated:
        entries = MoodEntry.objects.filter(user=request.user).order_by("-created_at")[:30]
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        entries = MoodEntry.objects.filter(session_id=session_key).order_by("-created_at")[:30]

    if not entries:
        return JsonResponse({"insights": "Log some moods to get your first insights ✨"})

    # =========================
    # 📊 Build mood history text
    # =========================
    mood_history = ""
    if mode == "daily":
        mood_history = "\n".join(
            [f"{e.created_at.strftime('%Y-%m-%d')} - Level {e.mood_level}, Notes: {e.notes or 'None'}"
             for e in entries]
        )
    elif mode == "weekly":
        weekly_data = defaultdict(list)
        for e in entries:
            week_key = e.created_at.strftime("%Y-W%W")
            weekly_data[week_key].append(e)
        mood_history = "\n".join(
            [f"Week {week_key.split('-W')[1]} ({datetime.strptime(week_key + '-1', '%Y-W%W-%w').strftime('%Y-%m-%d')}) - "
             f"Avg Level {sum(e.mood_level for e in data) / len(data):.1f}, Notes: {', '.join(e.notes or 'None' for e in data)}"
             for week_key, data in weekly_data.items()]
        )
    elif mode == "monthly":
        monthly_data = defaultdict(list)
        for e in entries:
            month_key = e.created_at.strftime("%Y-%m")
            monthly_data[month_key].append(e)
        mood_history = "\n".join(
            [f"{month_key} - Avg Level {sum(e.mood_level for e in data) / len(data):.1f}, "
             f"Notes: {', '.join(e.notes or 'None' for e in data)}"
             for month_key, data in monthly_data.items()]
        )
    elif mode == "heatmap":
        weekly_data = defaultdict(list)
        for e in entries:
            week_key = e.created_at.strftime("%Y-W%W")
            weekly_data[week_key].append(e)
        mood_history = "\n".join(
            [f"Week {week_key.split('-W')[1]} ({datetime.strptime(week_key + '-1', '%Y-W%W-%w').strftime('%Y-%m-%d')}) - "
             f"Avg Level {sum(e.mood_level for e in data) / len(data):.1f}"
             for week_key, data in weekly_data.items()]
        )

    # =========================
    # 🎭 Prepare AI prompt
    # =========================
    last_entry = entries.first()
    last_mood = last_entry.mood_level
    mood_labels = ["Stressed", "Sad", "Okay", "Good", "Great"]
    last_mood_label = mood_labels[last_mood]

    prompt = f"""
You are an enthusiastic, empathetic, and creative wellness coach...
(reuse your original prompt text)
{mood_history}
"""

    # =========================
    # 🤖 Call Gemini API
    # =========================
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        )
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

# ========== CHATBOT API ==========
@csrf_exempt
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "⚠️ Only POST requests are allowed."})

    user_message_raw = request.POST.get("message", "")
    user_message = user_message_raw.strip()
    if not user_message:
        return JsonResponse({"reply": "⚠️ Please say something!"})

    lm = user_message.lower()

    # -----------------------
    # 1) Crisis / suicide check (highest priority)
    # -----------------------
    crisis_indicators = [
        "suicide", "kill myself", "i want to die", "i'll kill myself",
        "i want to end my life", "ending my life", "die"
    ]
    if any(ind in lm for ind in crisis_indicators):
        return JsonResponse({"reply": (
            "💙 I'm really concerned by what you said. If you're thinking about ending your life, "
            "please reach out to someone you trust or contact emergency services right now.\n\n"
            "🇮🇳 India Helpline (AASRA): +91-98204 66726\n"
            "🌍 If you are elsewhere, please look up your local suicide prevention hotline.\n\n"
            "🙏 You are not alone — please talk to someone you trust. 💙"
        )})

    # -----------------------
    # 2) Wellness keyword detection (allow only wellness topics)
    # -----------------------
    wellness_keywords = [
        "stress", "anxiety", "sleep", "mood", "depression", "self care",
        "meditation", "wellness", "focus", "relax", "happy", "sad", "tired",
        "mental health", "panic", "lonely", "anger", "fear", "overthinking"
    ]
    contains_wellness = any(keyword in lm for keyword in wellness_keywords)

    if not contains_wellness:
        # ❌ Reject if not wellness related
        return JsonResponse({
            "reply": (
                "⚠️ I only provide information and support about mental health, mood, and wellness topics.\n\n"
                "🙏 कृपया केवल मानसिक स्वास्थ्य, मूड या वेलनेस से जुड़े सवाल पूछें।\n\n"
                "⚠️ હું ફક્ત માનસિક સ્વાસ્થ્ય, મૂડ અને વેલનેસ વિષયક પ્રશ્નોના જવાબ આપી શકું છું."
            )
        })

    # -----------------------
    # 3) Build system prompt (multilingual)
    # -----------------------
    system_prompt = (
        "You are a compassionate, multilingual Mental Wellness Assistant. "
        "You can reply in English, Hindi, or Gujarati depending on the user's input language. "
        "Always answer kindly and empathetically, give practical coping tips (breathing, grounding, sleep hygiene, small routines). "
        "Never give medical diagnoses or prescriptions. "
        "If the user appears in crisis, remind them to seek emergency help and provide helpline information. "
    )

    full_prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"

    # -----------------------
    # 4) Call Gemini API
    # -----------------------
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300},
        }
        resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        reply = "⚠️ No reply received."
        candidates = data.get("candidates", [])
        if candidates and candidates[0].get("content"):
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                reply = parts[0].get("text", reply)

        return JsonResponse({"reply": reply})
    except requests.exceptions.RequestException as e:
        return JsonResponse({"reply": f"⚠️ API Error: {str(e)}"})
    except Exception as e:
        return JsonResponse({"reply": f"⚠️ Unexpected Error: {str(e)}"})



# ========== EXTRA PAGES ==========

def breathing_page(request):
    return render(request, "breathing.html")


def focus_page(request):
    return render(request, "focus.html")

def selfcare_page(request):
    return render(request, "selfcare.html")


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



def get_chat_messages(request, session_id):
    # Replace this with your actual logic
    messages = [
        {"sender": "bot", "text": "Hello!"},
        {"sender": "user", "text": "Hi there!"}
    ]
    return JsonResponse({"session_id": str(session_id), "messages": messages})
