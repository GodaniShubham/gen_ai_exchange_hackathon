from django.urls import path
from . import views

urlpatterns = [
    # Home Page
    path('', views.index, name='index'),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    # Chat Page (frontend UI)
    path("chat/", views.chat_page, name="chat_page"),
    path("analysis/", views.mood_analytics, name="analysis"),
     path("save_mood/", views.save_mood, name="save_mood"),
     path("mood_insights/", views.mood_insights, name="mood_insights"),

    # Chat API (backend endpoint for AI reply)
    path("chatbot_api/", views.chatbot_api, name="chatbot_api"),
]
