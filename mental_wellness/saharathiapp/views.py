import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


def index(request):
    return render(request, "index.html")


def chat_page(request):
    return render(request, "chatbot.html")


@csrf_exempt
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"reply": "⚠️ Only POST requests are allowed."})

    user_message = request.POST.get("message", "").strip()
    if not user_message:
        return JsonResponse({"reply": "⚠️ Please say something!"})

    try:
        # ✅ Use API key directly in the URL (no Authorization header)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"

        payload = {
            "contents": [
                {"parts": [{"text": user_message}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 200
            }
        }

        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
        response.raise_for_status()
        data = response.json()

        # ✅ Correct response parsing
        bot_reply = data["candidates"][0]["content"]["parts"][0]["text"]

        return JsonResponse({"reply": bot_reply})

    except Exception as e:
        return JsonResponse({"reply": f"⚠️ Error: {str(e)}"})