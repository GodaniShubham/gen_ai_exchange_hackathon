import json, re, datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from .models import JournalEntry, WeeklyReflection
import google.generativeai as genai

# ✅ Configure Gemini API (use env variable in production!)
genai.configure(api_key="AIzaSyAVp8SaRX7JvL_RSOMrFSCtwr9PDctk2EQ")

# ------------------ Gemini AI Helper ------------------
def generate_ai_reflection(content: str):
    """
    Call Gemini API and parse response into structured data:
    - summary (str)
    - highlights (list[str])
    - coping (list[str])
    """
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
        text = response.text.strip() if response and response.text else ""
    except Exception as e:
        print("Gemini API error:", e)
        text = ""

    # --- Parse Summary ---
    summary_match = re.search(r"Summary:\s*(.*)", text, re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else "Here’s a gentle reflection."

    # --- Parse Highlights ---
    highlights_match = re.search(
        r"Highlights:\s*((?:\s*[-*].*\n?)+)(?=\s*Coping:|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    highlights = []
    if highlights_match:
        highlights = [
            h.strip().lstrip("-* ").strip()
            for h in highlights_match.group(1).strip().splitlines()
            if h.strip()
        ]
    if not highlights:
        highlights = ["N/A"]

    # --- Parse Coping ---
    coping_match = re.search(
        r"Coping:\s*((?:\s*[-*].*\n?)+)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    coping = []
    if coping_match:
        coping = [
            c.strip().lstrip("-* ").strip()
            for c in coping_match.group(1).strip().splitlines()
            if c.strip()
        ]
    if not coping:
        coping = ["Take a deep breath", "Take breaks", "Reach out to a friend"]

    return summary, highlights, coping


# ------------------ Views ------------------
def journal_page(request):
    """Show all journal entries + current week's reflection."""
    entries = JournalEntry.objects.all().order_by("-is_pinned", "-created_at")
    today = now().date()
    start_week = today - datetime.timedelta(days=today.weekday())
    end_week = start_week + datetime.timedelta(days=6)
    reflection = WeeklyReflection.objects.filter(
        week_start=start_week, week_end=end_week
    ).first()
    return render(
        request,
        "journals/journal_page.html",
        {"entries": entries, "reflection": reflection},
    )


@csrf_exempt
def submit_entry(request):
    """Create new journal entry with AI reflection."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "Content is empty"}, status=400)

    summary, highlights, coping = generate_ai_reflection(content)
    entry = JournalEntry.objects.create(
        content=content, summary=summary, highlights=highlights, coping=coping
    )
    return JsonResponse(
        {
            "content": entry.content,
            "summary": summary,
            "highlights": highlights,
            "coping": coping,
        },
        status=200,
    )


@csrf_exempt
def edit_entry(request, entry_id):
    """Edit an existing journal entry and regenerate AI reflection."""
    entry = get_object_or_404(JournalEntry, id=entry_id)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"})

        content = data.get("content", "").strip()
        if not content:
            return JsonResponse({"success": False, "error": "Content cannot be empty"})

        # Update + regenerate reflections
        entry.content = content
        summary, highlights, coping = generate_ai_reflection(content)
        entry.summary = summary
        entry.highlights = highlights
        entry.coping = coping
        entry.save()

        return JsonResponse(
            {
                "success": True,
                "summary": summary,
                "highlights": highlights,
                "coping": coping,
            }
        )

    return JsonResponse({"success": False, "error": "Invalid request"})


@csrf_exempt
def delete_entry(request, entry_id):
    """Delete a journal entry."""
    entry = get_object_or_404(JournalEntry, id=entry_id)
    if request.method == "POST":
        entry.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})


@csrf_exempt
def toggle_pin(request, entry_id):
    """Pin/unpin a journal entry."""
    entry = get_object_or_404(JournalEntry, id=entry_id)
    if request.method == "POST":
        entry.is_pinned = not entry.is_pinned
        entry.save()
        return JsonResponse({"success": True, "is_pinned": entry.is_pinned})
    return JsonResponse({"success": False, "error": "Invalid request"})
