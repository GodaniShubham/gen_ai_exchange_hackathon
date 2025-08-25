from django.urls import path
from . import views

urlpatterns = [
    # Home Page
    path('', views.index, name='index'),

    # Chat Page (frontend UI)
    path("chat/", views.chat_page, name="chat_page"),

    # Chat API (backend endpoint for AI reply)
    path("chatbot_api/", views.chatbot_api, name="chatbot_api"),
]
