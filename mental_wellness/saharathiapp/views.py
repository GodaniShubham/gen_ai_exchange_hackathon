import json
import requests
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from .models import ChatSession, Message
from uuid import UUID

# 🏠 Home Page
def index(request):
    return render(request, "index.html")


# 💬 Chatbot UI Page
def chat_page(request):
    sessions = ChatSession.objects.all().order_by("-created_at")
    return render(request, "chatbot.html", {"sessions": sessions})


# 🤖 Normal Chatbot API
@csrf_exempt
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "⚠️ Only POST requests are allowed."})

    user_message = request.POST.get("message", "").strip()
    session_id = request.POST.get("session_id")
    if not user_message:
        return JsonResponse({"reply": "⚠️ Please say something!"})

    if not settings.GEMINI_API_KEY:
        return JsonResponse({"reply": "⚠️ Gemini API key missing! Set GEMINI_API_KEY in .env"})

    # ✅ Get or create session using UUID
    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(session_id=UUID(session_id))
        except:
            session = ChatSession.objects.create()
    else:
        session = ChatSession.objects.create()

    # Save user message
    Message.objects.create(session=session, sender="user", text=user_message)
    if not session.title:
        session.title = user_message[:50]
        session.save()

    # Gemini API request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"You are a supportive Mental Wellness Chatbot. User asked: {user_message}"}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
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


# 📜 Fetch Chat Messages
def get_chat_messages(request, session_id):
    try:
        session = ChatSession.objects.get(session_id=UUID(session_id))
    except:
        return JsonResponse({"messages": []})

    messages_qs = session.messages.all().order_by("timestamp")
    return JsonResponse({
        "messages": [{"sender": m.sender, "text": m.text} for m in messages_qs]
    })


# 🤖 Streaming Chatbot API
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
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
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


# ⚙️ Settings & Privacy


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
