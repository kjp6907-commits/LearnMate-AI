import json
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Load environment variables from .env file
load_dotenv()

# Default Gemini Flash model supported by the official google-genai SDK
DEFAULT_MODEL = "gemini-2.5-flash"

# Competition security safeguard: Maximum characters allowed per user prompt
MAX_PROMPT_LENGTH = 10000


class GeminiServiceError(Exception):
    """Custom exception raised for Gemini service-related errors."""
    pass


def _sanitize_and_format_error(e: Exception) -> str:
    """
    Sanitizes exception strings to ensure API keys are never exposed,
    and returns student-friendly messages for rate limits and auth issues.
    """
    err_str = str(e)

    # Redact raw API key if present anywhere in the error message
    raw_key = os.getenv("GEMINI_API_KEY", "").strip()
    if raw_key and raw_key != "your_gemini_api_key_here" and raw_key in err_str:
        err_str = err_str.replace(raw_key, "[REDACTED_API_KEY]")

    # Check for Rate Limit / Quota exhaustion (HTTP 429)
    if isinstance(e, APIError) and getattr(e, "code", None) == 429:
        return "The AI tutor is currently experiencing high demand (rate limit reached). Please wait a moment and try again."
    if any(term in err_str for term in ["429", "RESOURCE_EXHAUSTED", "rate limit", "quota"]):
        return "The AI tutor service reached its temporary request quota. Please wait a moment and try again."

    # Check for authentication / authorization errors
    if isinstance(e, APIError) and getattr(e, "code", None) in [401, 403]:
        return "Authentication error: Please verify that your GEMINI_API_KEY is valid and authorized (keys from Google AI Studio start with AIzaSy...)."
    if any(term in err_str for term in ["API_KEY_INVALID", "invalid api key", "PERMISSION_DENIED", "UNAUTHENTICATED"]):
        return "Invalid or unauthorized API key. Please check your GEMINI_API_KEY in Streamlit Secrets or sidebar."

    # Generic API error
    if isinstance(e, APIError):
        msg = getattr(e, "message", str(e))
        if raw_key and raw_key in msg:
            msg = msg.replace(raw_key, "[REDACTED_API_KEY]")
        return f"Gemini API notice: {msg}"

    return f"Tutor service error: {err_str}"



def get_api_key() -> str:
    """
    Retrieves and validates the Gemini API key from environment variables,
    Streamlit Cloud secrets, or session state.
    Never returns placeholder values.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
            elif "gemini_api_key" in st.secrets:
                api_key = str(st.secrets["gemini_api_key"]).strip()
            elif hasattr(st, "session_state") and "gemini_api_key" in st.session_state:
                api_key = str(st.session_state.get("gemini_api_key", "")).strip()
        except Exception:
            pass

    if api_key and api_key != "your_gemini_api_key_here":
        os.environ["GEMINI_API_KEY"] = api_key
        return api_key

    raise GeminiServiceError(
        "GEMINI_API_KEY is not configured. Please set your key in the .env file or Streamlit Cloud Secrets."
    )


def is_api_configured() -> bool:
    """Checks whether a valid non-placeholder Gemini API key is configured."""
    try:
        key = get_api_key()
        return bool(key and key != "your_gemini_api_key_here")
    except Exception:
        return False


def get_gemini_client() -> genai.Client:
    """
    Creates and returns an authenticated genai.Client instance using the environment key.
    """
    api_key = get_api_key()
    return genai.Client(api_key=api_key)


def generate_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Sends a single prompt to the Gemini model and returns a clean text response.
    """
    if not prompt or not prompt.strip():
        raise GeminiServiceError("Prompt cannot be empty.")

    if len(prompt) > MAX_PROMPT_LENGTH:
        raise GeminiServiceError(
            f"Prompt exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters."
        )

    client = get_gemini_client()

    config = None
    if system_instruction:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction.strip()
        )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt.strip(),
            config=config,
        )
        if not response.text:
            return "I was unable to generate a response. Please rephrase your question."
        return response.text.strip()
    except Exception as e:
        raise GeminiServiceError(_sanitize_and_format_error(e)) from e


def generate_chat_response(
    messages: List[dict],
    system_instruction: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Sends full conversation history to Gemini and returns the assistant's reply.

    Args:
        messages: List of message dicts: [{'role': 'user'|'assistant', 'content': str}]
        system_instruction: Optional pedagogical instructions for the tutor.
        model: Gemini model name.

    Returns:
        Clean text response string from Gemini.
    """
    if not messages:
        raise GeminiServiceError("Conversation history cannot be empty.")

    client = get_gemini_client()

    config = None
    if system_instruction:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction.strip()
        )

    # Format history into Gemini types.Content
    # 1. Map 'assistant' to 'model'
    # 2. Filter out leading assistant greeting because Gemini requires the first turn to be 'user'
    contents: List[types.Content] = []
    for msg in messages:
        role = "model" if msg.get("role") in ["assistant", "model"] else "user"
        content_text = str(msg.get("content", "")).strip()
        if not content_text:
            continue

        # Ensure conversation starts with a user turn
        if not contents and role != "user":
            continue

        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=content_text)],
            )
        )

    if not contents:
        raise GeminiServiceError("No user messages found to send to Gemini.")

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        if not response.text:
            return "I was unable to generate a response. Please try asking again."
        return response.text.strip()
    except Exception as e:
        raise GeminiServiceError(_sanitize_and_format_error(e)) from e


def generate_quiz_question(
    topic: str,
    learner_level: str = "Beginner",
    previous_questions: Optional[List[str]] = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Generates a single multiple-choice question on the specified educational topic,
    calibrated to the learner level, returning structured JSON data.

    Returns:
        Dict with keys: 'question', 'options' (dict with A, B, C, D),
        'correct_option' (str), and 'explanation' (str).
    """
    if not topic or not topic.strip():
        raise GeminiServiceError("Quiz topic cannot be empty.")

    client = get_gemini_client()

    avoid_clause = ""
    if previous_questions and len(previous_questions) > 0:
        quoted_previous = "\n".join(f"- {q}" for q in previous_questions[-10:])
        avoid_clause = f"\nDo NOT repeat or closely rephrase any of these previous questions:\n{quoted_previous}\n"

    system_instruction = (
        "You are LearnMate AI's Quiz Master, an expert educational assessment specialist "
        "supporting UN SDG 4: Quality Education. Create rigorous, engaging, and pedagogically sound "
        "multiple-choice questions tailored to the requested topic and level."
    )

    prompt = f"""Generate exactly ONE educational multiple-choice question.

Target Topic: {topic.strip()}
Learner Level: {learner_level}
{avoid_clause}
Rules:
1. Focus strictly on testing understanding of '{topic.strip()}'.
2. Provide exactly 4 plausible choices labeled 'A', 'B', 'C', and 'D'.
3. Exactly one choice must be objectively correct.
4. Provide a clear, constructive explanation of why that choice is right and how it relates to the concept.
5. Never output markdown around the JSON.

Output format must be valid JSON:
{{
  "question": "The question text here?",
  "options": {{
    "A": "First choice",
    "B": "Second choice",
    "C": "Third choice",
    "D": "Fourth choice"
  }},
  "correct_option": "A",
  "explanation": "Why A is correct and the core lesson behind it."
}}"""

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.7,
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        if not response.text:
            raise GeminiServiceError("Empty response received from Gemini for quiz question.")

        data = json.loads(response.text.strip())

        # Validate structure
        required_keys = {"question", "options", "correct_option", "explanation"}
        if not required_keys.issubset(data.keys()):
            raise GeminiServiceError("Gemini quiz output missing required fields.")

        # Ensure correct_option is uppercase
        data["correct_option"] = str(data["correct_option"]).strip().upper()
        if data["correct_option"] not in ["A", "B", "C", "D"]:
            # Fallback if model answered with text or lowercase
            data["correct_option"] = data["correct_option"][:1]

        # Ensure 4 options exist
        if not isinstance(data.get("options"), dict) or len(data["options"]) < 4:
            raise GeminiServiceError("Quiz question options must contain 4 choices (A, B, C, D).")

        return data

    except json.JSONDecodeError as e:
        raise GeminiServiceError("Failed to parse quiz response into valid JSON.") from e
    except Exception as e:
        raise GeminiServiceError(_sanitize_and_format_error(e)) from e

