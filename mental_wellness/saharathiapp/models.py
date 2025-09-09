
from django.db import models
from accounts.models import CustomUser 

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

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="mood_entries")
    mood_level = models.IntegerField(choices=MOOD_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_mood_level_display()} ({self.created_at.date()})"
