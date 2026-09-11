"""
Simple diagnostic test script for LearnMate AI's Gemini integration.
Run: python test_gemini.py
"""

import sys

# Ensure UTF-8 output encoding for Windows command prompts
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from gemini_service import (
    DEFAULT_MODEL,
    GeminiServiceError,
    generate_response,
    is_api_configured,
)
from prompts import get_tutor_system_prompt


def run_test():
    print("=" * 60)
    print("LearnMate AI - Gemini Integration Test")
    print("=" * 60)

    # 1. Check API Key configuration
    if not is_api_configured():
        print("[!] GEMINI_API_KEY is not configured or is still the placeholder.")
        print("    Please open the '.env' file and insert your actual API key:")
        print("    GEMINI_API_KEY=your_actual_key_here")
        return

    print("[+] GEMINI_API_KEY detected in environment.")
    print(f"[*] Testing model: {DEFAULT_MODEL}...")

    # 2. Test prompt
    test_prompt = "In one sentence, why is education important for society?"
    system_prompt = get_tutor_system_prompt(learner_level="Beginner")

    try:
        response = generate_response(
            prompt=test_prompt,
            system_instruction=system_prompt,
        )
        print("\n[+] Successfully received response from Gemini:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        print("\n[SUCCESS] Gemini integration is working properly!\n")
    except GeminiServiceError as err:
        print(f"\n[-] Error during Gemini request: {err}")
    except Exception as ex:
        print(f"\n[-] Unexpected error: {ex}")


if __name__ == "__main__":
    run_test()
