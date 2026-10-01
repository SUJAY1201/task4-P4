"""
utils package
=============

This package contains the supporting modules for the Intelligent Code
Reviewer & Explainer application:

- `file_handler`: file validation and reading utilities.
- `prompts`: centralized prompt templates and system instructions for Gemini.
- `analyzer`: Gemini API client wrapper and analysis orchestration.

Keeping these concerns in separate modules keeps `app.py` focused purely on
Streamlit UI logic.
"""

from . import file_handler
from . import prompts
from . import analyzer

__all__ = ["file_handler", "prompts", "analyzer"]
