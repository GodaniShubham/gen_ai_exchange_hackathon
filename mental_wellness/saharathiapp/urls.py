from django.urls import path
from . import views

urlpatterns = [
    # 🏠 Home Page
    path('', views.index, name='index'),

    # 🔑 Auth
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),

    # 💬 Chat Page (frontend UI)
    path("chat/", views.chat_page, name="chat_page"),

    # 📊 Mood Analytics
    path("analysis/", views.mood_analytics, name="analysis"),
    path("save_mood/", views.save_mood, name="save_mood"),
    path("mood_insights/", views.mood_insights, name="mood_insights"),

    # 🤖 Chat API (backend endpoint for AI reply)
    path("chatbot_api/", views.chatbot_api, name="chatbot_api"),

   

    # ⚙️ Settings & Privacy
    path("settings/", views.settings_privacy, name="settings_privacy"),

    # 💾 Get chat history (per session)
    path("get_chat_messages/<uuid:session_id>/", views.get_chat_messages, name="get_chat_messages"),

    # 🌿 Wellness Features
    path("breathing/", views.breathing_page, name="breathing"),
    path("focus/", views.focus_page, name="focus"),
    path("selfcare/", views.selfcare_page, name="selfcare"),
    path("wellness/", views.wellness_page, name="wellness"),
]
