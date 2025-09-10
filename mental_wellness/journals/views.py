import json, re, datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from .models import JournalEntry, WeeklyReflection
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyAVp8SaRX7JvL_RSOMrFSCtwr9PDctk2EQ")

def generate_ai_reflection(content):
    """Call Gemini API and parse response into summary, highlights, coping."""
    prompt = f"""
    User wrote:

    "{content}"

    Generate:
    1. Summary
    2. 3 Highlights
    3. 3 Coping strategies

    Format:
    Summary: ...
    Highlights:
    - ...
    - ...
    - ...
    Coping:
    - ...
    - ...
    - ...
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = response.text
    except Exception as e:
        print("Gemini API error:", e)
        text = """
        Summary: Could not generate AI reflection.
        Highlights:
        - N/A
        Coping:
        - Take a deep breath
        - Take breaks
        - Reach out to a friend
        """

    # Parse
    summary_match = re.search(r"Summary:\s*(.*)", text, re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else "Here’s a gentle reflection."

    highlights_match = re.search(r"Highlights:\s*((?:\s*[-*].*)+?)\n(?:Coping:|$)", text, re.IGNORECASE | re.DOTALL)
    highlights = [h.strip().lstrip("-* ").strip() for h in highlights_match.group(1).strip().splitlines()] if highlights_match else ["N/A"]

    coping_match = re.search(r"Coping:\s*((?:\s*[-*].*)+)", text, re.IGNORECASE | re.DOTALL)
    coping = [c.strip().lstrip("-* ").strip() for c in coping_match.group(1).strip().splitlines()] if coping_match else ["Take a deep breath"]

    return summary, highlights, coping

def journal_page(request):
    entries = JournalEntry.objects.all().order_by("-is_pinned", "-created_at")
    # Weekly reflection (optional)
    today = now().date()
    start_week = today - datetime.timedelta(days=today.weekday())
    end_week = start_week + datetime.timedelta(days=6)
    reflection = WeeklyReflection.objects.filter(week_start=start_week, week_end=end_week).first()
    return render(request, "journals/journal_page.html", {"entries": entries, "reflection": reflection})

@csrf_exempt
def submit_entry(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    data = json.loads(request.body)
    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Content is empty"}, status=400)

    summary, highlights, coping = generate_ai_reflection(content)
    entry = JournalEntry.objects.create(content=content, summary=summary, highlights=highlights, coping=coping)
    return JsonResponse({"summary": summary, "highlights": highlights, "coping": coping}, status=200)

def delete_entry(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id)
    if request.method == "POST":
        entry.delete()
    return redirect("journals:journal_page")

@csrf_exempt
def edit_entry(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id)
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content","").strip()
        if content:
            entry.content = content
            entry.save()
            return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})

def toggle_pin(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id)
    if request.method == "POST":
        entry.is_pinned = not entry.is_pinned
        entry.save()
    return redirect("journals:journal_page")
