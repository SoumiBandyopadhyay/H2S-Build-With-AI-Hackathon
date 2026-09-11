import os
import json
import google.generativeai as genai # pyright: ignore[reportMissingImports]
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-flash"

CATEGORIES = [
    "Roads", "Water Supply", "Electricity", "Sanitation", "Healthcare",
    "Education", "Public Transport", "Housing", "Digital Connectivity", "Other"
]


def classify_complaint(text: str, language: str = "en") -> dict:
    """
    Uses Gemini to classify a citizen complaint/request.
    Returns category, urgency (1-5), sentiment, and a short English summary.
    Falls back to a keyword heuristic if no API key is configured, so the
    app still runs end-to-end without a live key during development.
    """
    if not API_KEY:
        return _fallback_classify(text)

    prompt = f"""
You are analyzing a citizen infrastructure complaint/request submitted in India.
The text may be in any Indian language or English.

Text: "{text}"
Language code: {language}

Classify it and respond ONLY with valid JSON, no markdown, no extra text:
{{
  "category": one of {CATEGORIES},
  "urgency": integer 1-5 (5 = most urgent/critical, e.g. safety risk),
  "sentiment": "positive" | "neutral" | "negative" | "frustrated",
  "summary": "one line English summary of the request"
}}
"""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        if data.get("category") not in CATEGORIES:
            data["category"] = "Other"
        return data
    except Exception as e:
        print(f"Gemini classification failed, using fallback: {e}")
        return _fallback_classify(text)


def _fallback_classify(text: str) -> dict:
    """Simple keyword-based fallback so the app still works without an API key."""
    text_lower = text.lower()
    keyword_map = {
        "Roads": ["road", "pothole", "highway", "bridge", "রাস্তা", "सड़क"],
        "Water Supply": ["water", "pipeline", "tap", "জল", "पानी"],
        "Electricity": ["electricity", "power", "transformer", "বিদ্যুৎ", "बिजली"],
        "Sanitation": ["garbage", "sewage", "drain", "toilet", "sanitation", "गटर", "নালা"],
        "Healthcare": ["hospital", "doctor", "clinic", "health", "হাসপাতাল", "अस्पताल"],
        "Education": ["school", "college", "teacher", "education", "স্কুল", "स्कूल"],
        "Digital Connectivity": ["internet", "network", "mobile signal", "wifi"],
    }
    category = "Other"
    for cat, keywords in keyword_map.items():
        if any(k in text_lower for k in keywords):
            category = cat
            break

    urgent_words = ["urgent", "emergency", "danger", "accident", "died", "collapse"]
    urgency = 5 if any(w in text_lower for w in urgent_words) else 3

    return {
        "category": category,
        "urgency": urgency,
        "sentiment": "neutral",
        "summary": text[:100],
    }


def compute_priority_score(urgency: int, similar_complaints_count: int) -> float:
    """
    Explainable scoring: combines urgency with how many people reported
    similar issues in the same district (demand signal).
    """
    base = urgency * 10
    demand_boost = min(similar_complaints_count * 5, 50)
    return round(base + demand_boost, 2)


def generate_area_recommendation(state: str, district: str, category_counts: dict, avg_urgency: float) -> str:
    """
    Turns aggregated district-level data into a short, policymaker-facing
    recommendation using Gemini. Falls back to a template without a key.
    """
    if not API_KEY:
        top_category = max(category_counts, key=category_counts.get) if category_counts else "infrastructure"
        return (f"{top_category} is the most reported issue "
                f"({category_counts.get(top_category, 0)} complaints, avg urgency {avg_urgency:.1f}/5). "
                f"Recommend prioritizing {top_category.lower()} investment in this district.")

    prompt = f"""
You are advising Indian policymakers on infrastructure investment priorities.

District: {district}, State: {state}
Complaint category breakdown: {json.dumps(category_counts)}
Average urgency: {avg_urgency:.1f}/5

Write ONE short, actionable recommendation (max 40 words) for a policymaker, in plain English.
"""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini recommendation failed, using fallback: {e}")
        top_category = max(category_counts, key=category_counts.get) if category_counts else "infrastructure"
        return f"Prioritize {top_category.lower()} improvements in {district}, {state}."