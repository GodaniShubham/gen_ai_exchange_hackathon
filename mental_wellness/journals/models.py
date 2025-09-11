from django.db import models
from django.contrib.postgres.fields import ArrayField  # optional if using PostgreSQL
from django.utils.timezone import now

class JournalEntry(models.Model):
    content = models.TextField()
    summary = models.TextField(default="No summary provided")
    # Store highlights and coping as lists
    highlights = models.JSONField(default=list, blank=True)  # works on all DBs with Django 4+
    coping = models.JSONField(default=list, blank=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.created_at}: {self.content[:30]}"

class WeeklyReflection(models.Model):
    week_start = models.DateField()
    week_end = models.DateField()
    reflection = models.TextField()