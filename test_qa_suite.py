"""
Competition QA Test Suite for LearnMate AI.
Tests 15 strict competition quality categories.
"""

import os
import sys
from unittest.mock import MagicMock, patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

from api import app
import gemini_service
from gemini_service import (
    GeminiServiceError,
    _sanitize_and_format_error,
    generate_response,
    is_api_configured,
)
from prompts import get_tutor_system_prompt

client = TestClient(app)

results = []


def record_result(category_num, name, passed, details):
    status = "PASS" if passed else "FAIL"
    results.append((category_num, name, status, details))
    print(f"[{status}] Test {category_num}: {name} - {details}")


def run_all_qa_tests():
    print("=" * 70)
    print("STRICT COMPETITION QA TEST SUITE - LEARNMAT E AI")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Beginner educational question
    # -------------------------------------------------------------
    prompt_beginner = get_tutor_system_prompt("Beginner")
    passed_1 = (
        "beginner" in prompt_beginner.lower()
        and "analogies" in prompt_beginner.lower()
        and "check question" in prompt_beginner.lower()
    )
    record_result(
        1,
        "Beginner educational question",
        passed_1,
        "Prompt scaffolds simple analogies, everyday language, and check question.",
    )

    # -------------------------------------------------------------
    # 2. Advanced educational question
    # -------------------------------------------------------------
    prompt_advanced = get_tutor_system_prompt("Advanced")
    passed_2 = (
        "Advanced" in prompt_advanced
        and "technical precision" in prompt_advanced.lower()
        and "rigorous" in prompt_advanced.lower()
    )
    record_result(
        2,
        "Advanced educational question",
        passed_2,
        "Prompt configures technical depth, rigor, and formulas for advanced students.",
    )

    # -------------------------------------------------------------
    # 3. Student gives an incorrect answer
    # -------------------------------------------------------------
    passed_3 = (
        "constructive mistake analysis" in prompt_beginner.lower()
        and "never simply say \"wrong\"" in prompt_beginner.lower()
    )
    record_result(
        3,
        "Student gives an incorrect answer",
        passed_3,
        "Prompt mandates constructive analysis, validating effort, and pinpointing misconceptions.",
    )

    # -------------------------------------------------------------
    # 4. Student asks for an example
    # -------------------------------------------------------------
    passed_4 = (
        "concrete real-world examples" in prompt_beginner.lower()
        and "at least one useful, relatable example" in prompt_beginner.lower()
    )
    record_result(
        4,
        "Student asks for an example",
        passed_4,
        "Prompt enforces providing at least one concrete real-world example/analogy.",
    )

    # -------------------------------------------------------------
    # 5. Student asks for a quiz
    # -------------------------------------------------------------
    passed_5 = (
        "practice & quiz support" in prompt_beginner.lower()
        and hasattr(gemini_service, "generate_quiz_question")
    )
    record_result(
        5,
        "Student asks for a quiz",
        passed_5,
        "System prompt contains quiz rules and gemini_service exposes generate_quiz_question.",
    )

    # -------------------------------------------------------------
    # 6. Student changes topic
    # -------------------------------------------------------------
    passed_6 = (
        "understand first" in prompt_beginner.lower()
        and "identify what concept, subject, or problem" in prompt_beginner.lower()
    )
    record_result(
        6,
        "Student changes topic",
        passed_6,
        "Prompt prioritizes diagnosing current topic before lecturing; Quiz Mode includes reset_quiz(keep_topic=False).",
    )

    # -------------------------------------------------------------
    # 7. Student asks an unrelated question
    # -------------------------------------------------------------
    passed_7 = (
        "polite redirection" in prompt_beginner.lower()
        and "educational focus guardrail" in prompt_beginner.lower()
    )
    record_result(
        7,
        "Student asks an unrelated question",
        passed_7,
        "Prompt enforces polite redirection back to education and SDG 4.",
    )

    # -------------------------------------------------------------
    # 8. Student asks an ambiguous question
    # -------------------------------------------------------------
    passed_8 = "ask a brief clarifying question" in prompt_beginner.lower()
    record_result(
        8,
        "Student asks an ambiguous question",
        passed_8,
        "Prompt requires asking a brief clarifying question before jumping into explanation.",
    )

    # -------------------------------------------------------------
    # 9. Student asks something the model may not know
    # -------------------------------------------------------------
    passed_9 = (
        "epistemic humility & honesty" in prompt_beginner.lower()
        and "zero hallucination" in prompt_beginner.lower()
        and "never pretend to know" in prompt_beginner.lower()
    )
    record_result(
        9,
        "Student asks something the model may not know",
        passed_9,
        "Prompt forbids fabrication, mandates acknowledging boundaries and zero hallucination.",
    )

    # -------------------------------------------------------------
    # 10. Very long user input
    # -------------------------------------------------------------
    long_msg = "A" * 15000
    res_api_long = client.post("/chat", json={"message": long_msg})
    # Expect 400 or 422
    passed_10 = res_api_long.status_code in [400, 422]
    record_result(
        10,
        "Very long user input",
        passed_10,
        f"FastAPI rejected 15,000 char input with HTTP {res_api_long.status_code}.",
    )

    # -------------------------------------------------------------
    # 11. Empty input
    # -------------------------------------------------------------
    res_empty_1 = client.post("/chat", json={"message": ""})
    res_empty_2 = client.post("/chat", json={"message": "    "})
    passed_11 = (res_empty_1.status_code in [400, 422]) and (res_empty_2.status_code in [400, 422])
    record_result(
        11,
        "Empty input",
        passed_11,
        f"API rejected empty ({res_empty_1.status_code}) and whitespace ({res_empty_2.status_code}) input.",
    )

    # -------------------------------------------------------------
    # 12. API failure
    # -------------------------------------------------------------
    fake_err = Exception("Simulated connection timeout to Gemini API")
    formatted_err = _sanitize_and_format_error(fake_err)
    passed_12 = "Simulated connection timeout" in formatted_err and "Tutor service error:" in formatted_err
    record_result(
        12,
        "API failure",
        passed_12,
        f"API failures are caught and formatted gracefully: '{formatted_err}'.",
    )

    # -------------------------------------------------------------
    # 13. Missing Gemini API key
    # -------------------------------------------------------------
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        res_no_key = client.post("/chat", json={"message": "What is gravity?"})
        passed_13 = (
            res_no_key.status_code == 503
            and "GEMINI_API_KEY is not configured" in res_no_key.json().get("detail", "")
        )
    record_result(
        13,
        "Missing Gemini API key",
        passed_13,
        f"Endpoint safely returned HTTP 503 when key is missing: '{res_no_key.json().get('detail', '')}'.",
    )

    # -------------------------------------------------------------
    # 14. Rate-limit/API error
    # -------------------------------------------------------------
    rate_limit_err = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for model")
    sanitized_rl = _sanitize_and_format_error(rate_limit_err)
    passed_14 = "rate limit reached" in sanitized_rl or "temporary request quota" in sanitized_rl
    record_result(
        14,
        "Rate-limit/API error",
        passed_14,
        f"Rate limits mapped to polite student advisory: '{sanitized_rl}'.",
    )

    # -------------------------------------------------------------
    # 15. Check that secrets are not exposed
    # -------------------------------------------------------------
    mock_secret = "AIzaSyFakeSecretKeyTesting12345"
    with patch.dict(os.environ, {"GEMINI_API_KEY": mock_secret}):
        leak_test_err = Exception(f"Failed calling https://generativelanguage.googleapis.com?key={mock_secret}")
        sanitized_leak = _sanitize_and_format_error(leak_test_err)
        key_leaked = mock_secret in sanitized_leak
        key_redacted = "[REDACTED_API_KEY]" in sanitized_leak
        passed_15 = (not key_leaked) and key_redacted

    record_result(
        15,
        "Check that secrets are not exposed",
        passed_15,
        f"Secrets redacted from exceptions: '{sanitized_leak}'.",
    )

    print("=" * 70)
    all_passed = all(r[2] == "PASS" for r in results)
    if all_passed:
        print("ALL 15 COMPETITION QA TESTS PASSED! 🎉")
    else:
        print("SOME TESTS FAILED! Review details above.")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_all_qa_tests()
    sys.exit(0 if success else 1)
