
from django.db import models
from accounts.models import CustomUser 
from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

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
    
class Consultant(models.Model):
    SPECIALTIES = [
        ('OCD', 'OCD'),
        ('Neuropsychiatry', 'Neuropsychiatry'),
        ('De-addiction', 'De-addiction'),
        ('Child Psychiatry', 'Child Psychiatry'),
        ('Psychiatry', 'Psychiatry'),
        ('Mental Health', 'Mental Health'),
        ('Addiction Psychiatry', 'Addiction Psychiatry'),
        ('Geriatric Psychiatry', 'Geriatric Psychiatry'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('Today', 'Today'),
        ('This Week', 'This Week'),
        ('Next Month', 'Next Month'),
    ]
    
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=50, choices=SPECIALTIES)
    bio = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.name} - {self.specialty}"
    
    class Meta:
        ordering = ['name']

class Booking(models.Model):
    SESSION_TYPES = [
        ('Virtual', 'Virtual Session'),
        ('In-Person', 'In-Person'),
        ('Hybrid', 'Hybrid'),
    ]
    
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True
    )
    session_id = models.CharField(max_length=50, null=True, blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    date_time = models.DateTimeField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Booking with {self.consultant.name} - {self.date_time}"