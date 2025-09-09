def simple_summary(text, max_sentences=2):
    sentences = text.split(".")
    return ". ".join(sentences[:max_sentences]).strip() + "."

def extract_highlights(text, top_n=4):
    words = [w for w in text.split() if len(w) > 5]
    return list(set(words))[:top_n]

def generate_coping_suggestions(text):
    suggestions = [
        "Take a short break and practice deep breathing.",
        "Break big tasks into smaller steps.",
        "Reach out to a trusted friend or mentor.",
        "Try journaling daily to track your emotions.",
    ]
    return suggestions
