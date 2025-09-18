from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random
from datetime import timedelta
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount  # For social user check

User = get_user_model()

# -------------------- SIGNUP --------------------
def signup_view(request):
    if request.method != "POST":
        return render(request, "auth/signup.html")

    username = request.POST.get("username")
    email = request.POST.get("email")
    password1 = request.POST.get("password1")
    password2 = request.POST.get("password2")

    # Password match check
    if password1 != password2:
        messages.error(request, "❌ Passwords do not match!", extra_tags="auth")
        return redirect("signup")

    # Strong password check
    try:
        validate_password(password1)
    except ValidationError as e:
        messages.error(request, f"⚠️ Weak Password: {' '.join(e.messages)}", extra_tags="auth")
        return redirect("signup")

    # Existing user check
    if User.objects.filter(email=email).exists():
        messages.error(request, "⚠️ Email already registered!", extra_tags="auth")
        return redirect("signup")

    if User.objects.filter(username=username).exists():
        messages.error(request, "⚠️ Username already taken!", extra_tags="auth")
        return redirect("signup")

    # Generate OTP
    otp = str(random.randint(100000, 999999))

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password1,
        otp=otp,
        is_verified=False
    )
    user.save()

    # Send OTP email
    subject = "Your Saharathi AI OTP Verification"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [email]

    html_content = render_to_string("emails/otp_email.html", {
        "username": username,
        "otp": otp,
    })
    text_content = strip_tags(html_content)

    email_message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email_message.attach_alternative(html_content, "text/html")
    email_message.send()

    request.session["email_for_verification"] = email
    messages.success(request, "✅ Signup successful! Check your email for OTP verification.", extra_tags="auth")
    return redirect("verify_otp")

# -------------------- VERIFY OTP --------------------
def verify_otp_view(request):
    if request.method == "POST":
        email = request.session.get("email_for_verification")
        otp_entered = request.POST.get("otp")

        try:
            user = User.objects.get(email=email)
            if user.otp == otp_entered:
                user.is_verified = True
                user.otp = None
                user.save()
                messages.success(request, "✅ OTP verified successfully! You can now login.", extra_tags="auth")
                return redirect("login")
            else:
                messages.error(request, "❌ Invalid OTP. Please try again.", extra_tags="auth")
                return redirect("verify_otp")
        except User.DoesNotExist:
            messages.error(request, "⚠️ User not found.", extra_tags="auth")
            return redirect("signup")

    return render(request, "auth/verify_otp.html")

# -------------------- LOGIN --------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
            if not user.is_verified:
                messages.error(request, "❌ Please verify your email first!", extra_tags="auth")
                return redirect("verify_otp")
        except User.DoesNotExist:
            messages.error(request, "❌ Invalid email or password", extra_tags="auth")
            return redirect("login")

        user = authenticate(request, username=user.email, password=password)
        if user:
            login(request, user)
            messages.success(request, f"✅ Welcome back {user.username}!", extra_tags="auth")
            return redirect("index")
        else:
            messages.error(request, "❌ Invalid email or password", extra_tags="auth")
            return redirect("login")

    return render(request, "auth/login.html")

# -------------------- LOGOUT --------------------
def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully", extra_tags="auth")
    return redirect("login")

# -------------------- FORGOT PASSWORD --------------------
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            # Send OTP via email
            subject = "Saharathi AI Password Reset OTP"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [email]

            html_content = render_to_string("emails/reset_otp_email.html", {"username": user.username, "otp": otp})
            text_content = strip_tags(html_content)

            email_message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            messages.success(request, "✅ OTP sent to your email!")
            return redirect("reset_password", email=email)

        except User.DoesNotExist:
            messages.error(request, "❌ Email not found!")
    return render(request, "auth/forgot-password.html")

# -------------------- RESET PASSWORD --------------------
def reset_password(request, email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "⚠️ User not found!")
        return redirect("forgot_password")

    if request.method == "POST":
        otp_input = request.POST.get("otp")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Check OTP
        if otp_input != user.otp:
            messages.error(request, "❌ Invalid OTP!")
            return redirect("reset_password", email=email)

        # Check OTP expiry (10 minutes)
        if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=10):
            messages.error(request, "❌ OTP expired! Please request a new one.")
            return redirect("forgot_password")

        # Check passwords match
        if password1 != password2:
            messages.error(request, "❌ Passwords do not match!")
            return redirect("reset_password", email=email)

        # Set new password
        try:
            validate_password(password1)
        except ValidationError as e:
            messages.error(request, f"⚠️ Weak Password: {' '.join(e.messages)}")
            return redirect("reset_password", email=email)

        user.set_password(password1)
        user.otp = None
        user.otp_created_at = None
        user.save()

        messages.success(request, "✅ Password reset successful! You can now login.")
        return redirect("login")

    return render(request, "auth/reset_password.html", {"email": email})


def confirm_email(request):
    return render(request, "auth/confirm_email.html")