import json
import os
import threading
from typing import Any, Dict, Optional

try:
    import vertexai  # type: ignore
    from vertexai.generative_models import (  # type: ignore
        GenerativeModel,
        GenerationConfig,
    )
except ImportError as exc:  # pragma: no cover - dependency guard
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore
    GenerationConfig = None  # type: ignore
    _import_error = exc
else:
    _import_error = None


class LLMNotConfiguredError(RuntimeError):
    """Raised when the LLM client cannot be initialized due to missing config."""


_model_lock = threading.Lock()
_model_instance: Optional[GenerativeModel] = None


def _ensure_model() -> GenerativeModel:
    if vertexai is None or GenerativeModel is None:
        raise LLMNotConfiguredError(
            "vertexai package is not installed. Install google-cloud-aiplatform and vertexai."
        ) from _import_error

    project = os.getenv("GCP_PROJECT")
    location = os.getenv("GCP_LOCATION", "us-central1")
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro-002")

    if not project:
        raise LLMNotConfiguredError(
            "Set the GCP_PROJECT environment variable so Vertex AI can authenticate."
        )

    global _model_instance
    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:
                vertexai.init(project=project, location=location)
                _model_instance = GenerativeModel(model_name)
    return _model_instance


def generate_brand_response(payload: Dict[str, Any]) -> str:
    """
    Generate upbeat, on-brand copy via Gemini using the provided itinerary payload.
    """
    model = _ensure_model()

    system_brief = (
        "You are Ferris, a cheerful, upbeat travel concierge. "
        "Deliver one concise setup line, followed by a single lively paragraph (no more than 60 words) that sells the stay. "
        "Close with exactly three punchy bullet highlights (each under 10 words). "
        "Tone: optimistic, encouraging, confident, never over-the-top. "
        "Always reference why the recommendation matches prior travel patterns when provided. "
        "If transportation options are supplied, nod to the strongest one with the key benefit (duration or comfort). "
        "When catalog options are supplied, mention one alternative by name and why it might be a backup fit. "
        "Do not fabricate data beyond what is supplied in the payload. "
        "Do not use emojis or emoticons anywhere in the response."
    )

    prompt = {
        "instructions": system_brief,
        "travel_context": payload,
        "response_requirements": {
            "sections": [
                "A positive acknowledgement of the user's request.",
                "A short paragraph describing the stay and why it fits.",
                "Three bullet highlights under 10 words each.",
                "Invite the user to book or refine.",
            ],
            "style": {
                "emoji_usage": "not allowed",
                "voice": "human concierge, first person plural 'we' acceptable",
            },
        },
    }

    try:
        response = model.generate_content(
            json.dumps(prompt, indent=2),
            generation_config=GenerationConfig(
                max_output_tokens=2048,
                temperature=0.65,
                top_p=0.8,
            ),
        )
    except Exception as exc:
        raise LLMNotConfiguredError(str(exc)) from exc

    # Collect all text fragments from the leading candidate
    text_fragments = []
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        primary = candidates[0]
        parts = getattr(getattr(primary, "content", None), "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if part_text:
                text_fragments.append(part_text.strip())
        finish_reason = getattr(primary, "finish_reason", None)
    else:
        finish_reason = None

    text = "\n\n".join([frag for frag in text_fragments if frag]) or getattr(response, "text", "") or ""
    cleaned = text.strip()
    if not cleaned:
        raise LLMNotConfiguredError("Gemini response was empty.")
    return cleaned
