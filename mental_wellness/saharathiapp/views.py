import requests
import json
import math
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.utils import timezone
from .models import ChatSession, MoodEntry, Consultant, Booking
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)
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
            "🙏 You are not alone — please talk to someone you trust. 💙    "
        )})

    
    sad_keywords = ["sad", "lonely", "crying", "heartbroken"]
    stress_keywords = ["stressed", "tired", "anxious", "overwhelmed", "pressure"]

    context = "Casual friendly conversation."
    if any(kw in lm for kw in sad_keywords):
        context = "The user feels sad. Reply like a caring, empathetic friend in natural casual language."
    elif any(kw in lm for kw in stress_keywords):
        context = "The user feels stressed. Reply casually and consolingly, offering light encouragement and support."
  
    # -----------------------
    # 3) Build system prompt (multilingual)
    # -----------------------
    system_prompt = (
        "You are a supportive, casual mental wellness friend. "
        "You can reply in English, Hindi, or any regional language depending on the user's input language. "
        "Always answer kindly and empathetically, give practical coping tips (breathing, grounding, sleep hygiene, small routines). "
        "Keep replies natural, and human-like.Never sound like a therapist, just a warm companion "
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

def sleep_tracker(request):
    return render(request, "sleeptracker.html")

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


def consultations(request):
    """Main consultation page"""
    consultants = Consultant.objects.all()
    consultant_data = [
        {
            'id': c.id,
            'name': c.name,
            'specialty': c.specialty,
            'availability': c.availability,
            'rating': float(c.rating),
            'latitude': float(c.latitude),
            'longitude': float(c.longitude),
            'is_online': c.is_online,
            'bio': c.bio or 'No bio available.'
        }
        for c in consultants
    ]
    context = {
        'consultants': consultant_data,
        'specialties': Consultant.SPECIALTIES,
        'availability_options': Consultant.AVAILABILITY_CHOICES,
    }
    return render(request, 'consultations.html', context)


@require_http_methods(["GET"])
def get_consultants_json(request):
    """API endpoint to get consultants as JSON"""
    try:
        search = request.GET.get('search', '')
        specialty = request.GET.get('specialty', '')
        availability = request.GET.get('availability', '')
        rating = request.GET.get('rating', '')
        user_lat = request.GET.get('lat', 28.6139)
        user_lng = request.GET.get('lng', 77.2090)

        # Validate latitude and longitude
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            if not (-90 <= user_lat <= 90) or not (-180 <= user_lng <= 180):
                raise ValueError("Invalid coordinates")
        except ValueError:
            logger.warning(f"Invalid coordinates received: lat={user_lat}, lng={user_lng}")
            user_lat, user_lng = 28.6139, 77.2090  # Default to Delhi

        logger.info(f"Fetching consultants with params: search={search}, specialty={specialty}, availability={availability}, rating={rating}, lat={user_lat}, lng={user_lng}")

        consultants = Consultant.objects.all()

        if search:
            consultants = consultants.filter(name__icontains=search)
        if specialty and specialty != 'All':
            if specialty not in [s[0] for s in Consultant.SPECIALTIES]:
                return JsonResponse({"success": False, "message": "Invalid specialty"}, status=400)
            consultants = consultants.filter(specialty=specialty)
        if availability and availability != 'All':
            if availability not in [a[0] for a in Consultant.AVAILABILITY_CHOICES]:
                return JsonResponse({"success": False, "message": "Invalid availability"}, status=400)
            consultants = consultants.filter(availability=availability)
        if rating and rating != 'All':
            min_rating = 4.0 if rating == '4+ Stars' else 5.0
            consultants = consultants.filter(rating__gte=min_rating)

        consultant_data = [
            {
                'id': c.id,
                'name': c.name,
                'specialty': c.specialty,
                'bio': c.bio or 'No bio available.',
                'latitude': float(c.latitude),
                'longitude': float(c.longitude),
                'rating': float(c.rating),
                'availability': c.availability,
                'is_online': c.is_online,
                'distance': f"{calculate_distance(user_lat, user_lng, c.latitude, c.longitude):.1f} km"
            }
            for c in consultants
        ]

        # Sort by distance
        consultant_data.sort(key=lambda x: float(x['distance'].replace(' km', '')))

        if not consultant_data:
            return JsonResponse({"success": True, "consultants": [], "message": "No consultants found matching your criteria"})

        return JsonResponse({"success": True, "consultants": consultant_data})
    except Exception as e:
        logger.error(f"Error in get_consultants_json: {str(e)}")
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in km
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

@csrf_exempt
@require_http_methods(["POST"])
def book_consultation(request):
    """Handle booking submission"""
    try:
        data = json.loads(request.body)
        consultant_id = data.get('consultant_id')
        session_type = data.get('session_type')
        date_time = data.get('date_time')
        email = data.get('email')
        phone = data.get('phone')

        # Validate inputs
        if not all([consultant_id, session_type, date_time, email, phone]):
            return JsonResponse({"success": False, "message": "Missing required fields"}, status=400)

        consultant = get_object_or_404(Consultant, id=consultant_id)

        if session_type not in [s[0] for s in Booking.SESSION_TYPES]:
            return JsonResponse({"success": False, "message": "Invalid session type"}, status=400)

        try:
            booking_time = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
            if booking_time < timezone.now():
                return JsonResponse({"success": False, "message": "Booking time must be in the future"}, status=400)
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid date/time format"}, status=400)

        # Validate phone (basic regex for +91 or 10-12 digits)
        import re
        if not re.match(r'^\+?\d{10,12}$', phone):
            return JsonResponse({"success": False, "message": "Invalid phone number"}, status=400)

        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        booking = Booking.objects.create(
            consultant=consultant,
            user=request.user if request.user.is_authenticated else None,
            session_id=None if request.user.is_authenticated else session_key,
            session_type=session_type,
            date_time=booking_time,
            email=email,
            phone=phone
        )

        logger.info(f"Booking created: ID={booking.id}, Consultant={consultant.name}, User={'Authenticated' if request.user.is_authenticated else 'Guest'}")
        return JsonResponse({
            'success': True,
            'message': f'Booking confirmed with {consultant.name} for {booking_time.strftime("%Y-%m-%d %H:%M")}',
            'booking_id': booking.id
        })
    except Exception as e:
        logger.error(f"Error in book_consultation: {str(e)}")
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=400)
