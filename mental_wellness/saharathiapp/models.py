
from django.db import models
from accounts.models import CustomUser 
from django.db import models
import uuid
from django.utils import timezone

class Message(models.Model):
    sender = models.CharField(max_length=10)  # 'user' ya 'bot'
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        (0, "Stressed"),
        (1, "Sad"),
        (2, "Okay"),
        (3, "Good"),
        (4, "Great"),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="mood_entries",
        null=True,
        blank=True
    )
    session_id = models.CharField(max_length=50, null=True, blank=True)
    mood_level = models.IntegerField(choices=MOOD_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_mood_level_display()} ({self.created_at.date()})"


# 🔹 ChatSession model
class ChatSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)   # Track last message time
    title = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)         # Soft-delete / archive flag

    def __str__(self):
        return self.title if self.title else f"Session {self.session_id}"

    def message_count(self):
        return self.messages.count()
    message_count.short_description = "Messages"


# 🔹 Message model
class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'User'),
        ('bot', 'Bot'),
    )
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)   # Track if message has been read

    def save(self, *args, **kwargs):
        """Set session title if first user message and update last_activity"""
        super().save(*args, **kwargs)
        if self.sender == "user" and not self.session.title:
            self.session.title = self.text[:50]
        self.session.last_activity = timezone.now()
        self.session.save()

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}"

    def short_text(self):
        return self.text[:50] + ("..." if len(self.text) > 50 else "")
