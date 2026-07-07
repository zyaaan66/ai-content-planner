"""
ai_engine.py
------------
Encapsulates all communication with the Google Gemini API. Kept separate
from routes.py so the AI provider can be swapped later without touching
view logic (dependency inversion).
"""

import requests
from flask import current_app


class AIEngineError(Exception):
    """Base exception for AI engine failures."""


class AITimeoutError(AIEngineError):
    pass


class AIRateLimitError(AIEngineError):
    pass


class AIConfigError(AIEngineError):
    pass


# Prompt templates per content type. Kept centralized so prompt engineering
# can be tuned in one place.
PROMPT_TEMPLATES = {
    "idea": (
        "You are a senior content strategist. Generate 5 creative, high-engagement "
        "content ideas for the following topic. Return them as a numbered list with "
        "a one-line hook for each.\n\nTopic: {input}"
    ),
    "caption": (
        "You are a social media copywriter. Write 3 short, engaging captions "
        "(with relevant emojis and 3-5 hashtags each) for this topic.\n\nTopic: {input}"
    ),
    "seo_title": (
        "You are an SEO specialist. Generate 5 SEO-optimized titles (under 60 characters) "
        "for this topic, ranked by expected CTR.\n\nTopic: {input}"
    ),
    "keyword": (
        "You are an SEO researcher. List 10 relevant keywords/phrases for this topic, "
        "grouped into 'High Volume', 'Long-tail', and 'Trending'.\n\nTopic: {input}"
    ),
    "script": (
        "You are a scriptwriter for short-form video content. Write a 30-45 second "
        "script (Hook / Body / CTA structure) for this topic.\n\nTopic: {input}"
    ),
    "calendar": (
        "You are a content marketing manager. Create a 7-day content calendar "
        "(day, content type, topic, best posting time) for this theme.\n\nTheme: {input}"
    ),
    "rewrite": (
        "Rewrite the following content to be clearer and more engaging while keeping "
        "the original meaning intact:\n\n{input}"
    ),
    "improve": (
        "Improve the grammar, tone, and clarity of the following text. Return only the "
        "improved version:\n\n{input}"
    ),
}


def _build_prompt(content_type: str, user_input: str) -> str:
    template = PROMPT_TEMPLATES.get(content_type)
    if not template:
        raise AIEngineError(f"Unknown content type: {content_type}")
    return template.format(input=user_input)


def generate_content(content_type: str, user_input: str) -> str:
    """
    Calls the Gemini API and returns generated text.
    Raises AIConfigError, AITimeoutError, AIRateLimitError, or AIEngineError.
    """
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise AIConfigError(
            "GEMINI_API_KEY is not configured. Set it in your .env file."
        )

    model = current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash")
    timeout = current_app.config.get("GEMINI_TIMEOUT", 30)
    prompt = _build_prompt(content_type, user_input)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 2048,
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise AITimeoutError("The AI request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise AIEngineError("Could not reach the AI service. Check your internet connection.")

    if response.status_code == 429:
        raise AIRateLimitError("Rate limit exceeded. Please wait a moment and try again.")

    if response.status_code == 400:
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:300]
        raise AIConfigError(f"Gemini rejected the request: {detail or 'unknown reason (400 Bad Request)'}")

    if not response.ok:
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:300]
        raise AIEngineError(f"AI service returned an error (status {response.status_code}): {detail}")

    try:
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise AIEngineError("The AI returned no content. Try rephrasing your input.")
        parts = candidates[0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts)
        if not text.strip():
            raise AIEngineError("The AI returned an empty response.")
        return text.strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise AIEngineError(f"Unexpected AI response format: {exc}")
