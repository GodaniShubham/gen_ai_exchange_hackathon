from django.urls import path
from . import views

urlpatterns = [
    # 🏠 Home Page
    path("", views.index, name="index"),

    # 💬 Chat UI Page
    path("chat/", views.chat_page, name="chat_page"),

    # 🤖 Normal Chat API (single reply)
    path("chatbot_api/", views.chatbot_api, name="chatbot_api"),

    # ⌨️ Streaming Chat API (typing effect)
    path("chatbot_stream/", views.chatbot_stream, name="chatbot_stream"),

    path('settings/', views.settings_privacy, name='settings_privacy'),

    path('get_chat_messages/<uuid:session_id>/', views.get_chat_messages, name='get_chat_messages'),
]
