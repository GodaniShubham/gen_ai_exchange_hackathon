import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User


# ========== MAIN PAGES ==========
def index(request):
    return render(request, "index.html")

def chat_page(request):
    return render(request, "chatbot.html")

def analysis(request):
    return render(request, "mood_analytics.html")


# ========== AUTH VIEWS ==========
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect("index")  # redirect after successful login
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

        # --- Password check ---
        if password != confirm_password:
            messages.error(request, "Passwords do not match", extra_tags="signup")
            return redirect("index")  # stay on home, open signup modal

        # --- Unique username/email check ---
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken", extra_tags="signup")
            return redirect("index")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered", extra_tags="signup")
            return redirect("index")

        # --- Create user ---
        User.objects.create_user(username=username, email=email, password=password)

        # --- Success message: open login modal ---
        messages.success(request, "Signup successful! Please log in.", extra_tags="login")
        return redirect("index")  # redirect to home page

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
