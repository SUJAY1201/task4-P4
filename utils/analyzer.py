"""
analyzer.py
===========

Wraps all interaction with the Google Gemini API.

This module isolates the GenAI SDK logic, providing a clean interface
for the UI to request code analysis and receive structured results.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, List
from functools import lru_cache

from google import genai
from google.genai import types as genai_types

from utils.prompts import build_analysis_prompt, get_system_instruction

# Configure logging for production-level observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Generation parameters tuned for deterministic, technical output.
GENERATION_CONFIG_KWARGS: dict = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}


def list_supported_models() -> None:
    """
    Fetch and print all available Gemini models to the terminal.
    Useful for debugging and verifying supported model names.
    """
    try:
        client = get_gemini_client()
        print("\n--- Available Gemini Models ---")
        for model in client.models.list():
            print(f"Model Name: {model.name}")
        print("------------------------------\n")
    except Exception as exc:
        print(f"Failed to list models: {exc}")



@dataclass
class AnalysisResult:
    """
    Represents the outcome of a Gemini code analysis request.

    Attributes:
        success: Whether the analysis completed successfully.
        content: The raw Markdown response text from Gemini, if successful.
        error_message: Human-readable error description, if unsuccessful.
        model_used: The name of the model that successfully generated the response.
    """
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None


class GeminiNotConfiguredError(Exception):
    """Raised when the Gemini API key is missing or invalid."""


def is_api_key_configured() -> bool:
    """
    Check whether a Gemini API key is present in the environment.

    Returns:
        bool: True if `GEMINI_API_KEY` is set and non-empty.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    return bool(api_key and api_key.strip())


def get_gemini_client() -> genai.Client:
    """
    Build a configured `google-genai` Client using the API key from the environment.

    Returns:
        genai.Client: A ready-to-use Gemini client.

    Raises:
        GeminiNotConfiguredError: If the `GEMINI_API_KEY` environment variable is missing.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise GeminiNotConfiguredError(
            "GEMINI_API_KEY is not set. Please add it to your .env file "
            "or environment variables."
        )
    return genai.Client(api_key=api_key)


@lru_cache(maxsize=1)
def get_dynamic_model_list() -> List[str]:
    """
    Dynamically discover available Gemini models and filter for those
    suitable for code analysis (supporting generateContent).
    """
    try:
        client = get_gemini_client()
        available_models = []

        # Use the SDK's model list endpoint
        for model in client.models.list():
            name = model.name.replace("models/", "")

            # FILTERING LOGIC:
            # 1. Exclude embedding models
            if "embedding" in name.lower():
                continue

            # 2. Exclude specialized image/audio/tts models
            if any(keyword in name.lower() for keyword in ["image", "tts", "transcribe", "veo", "lyria", "audio"]):
                continue

            # 3. Exclude specific non-generative models (like aqa)
            if name.lower() == "aqa":
                continue

            # 4. Prefer general-purpose generative models
            # We keep names that look like 'gemini-...'
            if "gemini" in name.lower() or "gemma" in name.lower():
                available_models.append(name)

        # RANKING LOGIC:
        # We want a high-quality, stable sequence.
        def rank_model(m: str):
            m_lower = m.lower()
            # High penalty for preview/experimental models
            penalty = 0
            if any(x in m_lower for x in ["preview", "experimental", "omni"]):
                penalty = 1

            # Bonus for Flash models (preferred for interactive performance)
            bonus = 2 if "flash" in m_lower else 1

            # Secondary sort by version number (roughly)
            # This is a simple heuristic: longer names or specific versions
            # We'll use the name as a tie-breaker.
            return (bonus, -penalty, m)

        available_models.sort(key=rank_model, reverse=True)

        logger.info(f"Dynamically discovered {len(available_models)} suitable models.")
        return available_models

    except Exception as exc:
        logger.error(f"Failed to dynamically discover models: {exc}")
        return []


def is_retryable_model_error(exc: Exception) -> bool:
    """
    Determine if an exception is related to model unavailability
    and should trigger a fallback to the next model.
    """
    err_msg = str(exc).upper()

    # 1. Temporary capacity/high demand (503)
    if "503" in err_msg or "UNAVAILABLE" in err_msg or "HIGH DEMAND" in err_msg:
        return True

    # 2. Model specifically not found or deprecated (404)
    if "404" in err_msg or "NOT_FOUND" in err_msg:
        # Only retry if it's a model-specific 404
        # e.g., "model models/gemini-x is no longer available"
        if "MODEL" in err_msg or "NO LONGER AVAILABLE" in err_msg:
            return True

    # 3. Resource Exhausted (429)
    # We retry 429 if it's model-specific quota (limit: 0 for this model)
    # but NOT if it's a general account-wide quota exhaustion.
    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
        # Check if the error message indicates it's a model-specific limit
        # Typical pattern: "generate_content_free_tier_... limit: 0"
        if "LIMIT: 0" in err_msg or "MODEL" in err_msg:
            return True

    return False


def analyze_code(
    code: str,
    language: str,
    filename: str,
    model_name: Optional[str] = None,
) -> AnalysisResult:
    """
    Send source code to Gemini for analysis and return the structured Markdown response.
    Implements dynamic model discovery and automatic fallback logic.

    Args:
        code: The raw source code content to analyze.
        language: Human-readable language name (e.g. "Python").
        filename: Original uploaded filename, used for prompt context.
        model_name: Optional override for the starting model.

    Returns:
        AnalysisResult: Contains either the successful Markdown content or an error message.
    """
    try:
        client = get_gemini_client()
    except GeminiNotConfiguredError as exc:
        logger.error(f"Configuration error: {exc}")
        return AnalysisResult(success=False, error_message=str(exc))

    # 1. Build the candidate list dynamically
    dynamic_list = get_dynamic_model_list()

    # Define the sequence of models to try
    attempt_list = [model_name] if model_name else []
    attempt_list = [m for m in attempt_list if m]

    # Append dynamically discovered models, removing duplicates
    for m in dynamic_list:
        if m not in attempt_list:
            attempt_list.append(m)

    if not attempt_list:
        return AnalysisResult(
            success=False,
            error_message="No suitable Gemini models were discovered for your account."
        )

    prompt = build_analysis_prompt(code=code, language=language, filename=filename)

    # Explicitly disable Automatic Function Calling (AFC) by ensuring 'tools' is None.
    config = genai_types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        tools=None,
        **GENERATION_CONFIG_KWARGS,
    )

    for current_model in attempt_list:
        try:
            logger.info(f"Trying Gemini model: {current_model}")
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=config,
            )

            response_text = getattr(response, "text", None)
            if not response_text or not response_text.strip():
                logger.warning(f"Model {current_model} returned an empty response. Trying next model...")
                continue

            logger.info(f"Gemini analysis succeeded using model: {current_model}")
            return AnalysisResult(
                success=True,
                content=response_text,
                model_used=current_model
            )

        except Exception as exc:
            # Enhanced diagnostic logging for 503s/404s/429s
            err_msg = str(exc)
            logger.debug(f"Full API Error for {current_model}: {err_msg}")

            if is_retryable_model_error(exc):
                # Specifically log the nature of the unavailability
                msg_upper = err_msg.upper()
                if "503" in msg_upper or "UNAVAILABLE" in msg_upper:
                    logger.warning(f"Model {current_model} is experiencing high demand/capacity issues (503).")
                elif "404" in msg_upper or "NOT_FOUND" in msg_upper:
                    logger.warning(f"Model {current_model} is not found or deprecated (404).")
                elif "429" in msg_upper or "RESOURCE_EXHAUSTED" in msg_upper:
                    logger.warning(f"Model {current_model} has exhausted its specific quota (429).")

                logger.info(f"Trying fallback...")
                continue
            else:
                # Critical API errors (400, 401, 403, or general 429) fail immediately
                logger.exception(f"Critical API error with {current_model}: {exc}")

                # Provide a more helpful message for general quota exhaustion
                if "429" in err_msg.upper() or "RESOURCE_EXHAUSTED" in err_msg.upper():
                    return AnalysisResult(
                        success=False,
                        error_message="Your API project has exhausted its general quota. Please check your Google AI Studio billing/limits.",
                    )

                return AnalysisResult(
                    success=False,
                    error_message=f"Critical API error with {current_model}: {str(exc)}",
                )

    # Final failure state: Clear and descriptive
    logger.error("All discovered Gemini candidates failed.")
    return AnalysisResult(
        success=False,
        error_message="All available Gemini models are currently unavailable or failing. Please try again later.",
    )
