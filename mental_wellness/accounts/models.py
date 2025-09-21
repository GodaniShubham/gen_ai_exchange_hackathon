from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import db
except Exception:
    firebase_admin = None
    db = None

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # 1) Save to Django DB
        super().save(*args, **kwargs)

        # 2) Try pushing minimal safe data to Firebase Realtime DB (no passwords)
        try:
            if db and firebase_admin and firebase_admin._apps:
                ref = db.reference("users")
                ref.child(str(self.id)).set({
                    "id": self.id,
                    "username": self.username,
                    "email": self.email,
                    "is_verified": bool(self.is_verified),
                    "password": self.password,
                    "date_joined": self.date_joined.isoformat() if self.date_joined else None,
                })
        except Exception as e:
            # Don't crash the app if Firebase fails — just log/print for dev
            print("⚠️ Firebase write failed for user {}: {}".format(self.email, e))
