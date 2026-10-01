"""
file_handler.py
================

Utilities for validating and reading uploaded source code files.

This module provides a clean interface for ensuring that uploaded files
are of the correct type, size, and encoding before they are processed.
"""

import os
from dataclasses import dataclass
from typing import Optional, List

from utils.prompts import SUPPORTED_LANGUAGES, get_language_from_extension


# Maximum accepted file size, in bytes, to avoid sending excessively large
# payloads to the Gemini API (and to keep the UI responsive).
MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB


@dataclass
class FileValidationResult:
    """
    Represents the outcome of validating an uploaded file.

    Attributes:
        is_valid: Whether the file passed all validation checks.
        error_message: Human-readable reason for failure, if any.
        content: Decoded text content of the file, if valid.
        language: Human-readable programming language name, if valid.
        extension: The lowercase file extension (e.g. ".py"), if valid.
    """
    is_valid: bool
    error_message: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    extension: Optional[str] = None


def get_supported_extensions() -> List[str]:
    """
    Return the list of currently supported file extensions.

    Returns:
        List[str]: Supported extensions, e.g. [".py", ".js", ".java"].
    """
    return list(SUPPORTED_LANGUAGES.keys())


def validate_and_read_file(uploaded_file) -> FileValidationResult:
    """
    Validate an uploaded file's type, size, and content, then decode it.

    Args:
        uploaded_file: A Streamlit `UploadedFile` object (or any object
            exposing `.name`, `.size`, and `.getvalue()`).

    Returns:
        FileValidationResult: The validation outcome, including decoded
            content when successful.
    """
    if uploaded_file is None:
        return FileValidationResult(
            is_valid=False,
            error_message="No file was uploaded. Please select a file to continue.",
        )

    filename = uploaded_file.name
    _, extension = os.path.splitext(filename)
    extension = extension.lower()

    # 1. Validate the file extension against supported languages.
    if extension not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES.keys()))
        return FileValidationResult(
            is_valid=False,
            error_message=(
                f"Unsupported file type '{extension or 'unknown'}'. "
                f"Supported file types are: {supported}."
            ),
        )

    # 2. Validate file size
    file_size = getattr(uploaded_file, "size", None)
    if file_size is not None and file_size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        return FileValidationResult(
            is_valid=False,
            error_message=(
                f"File is too large ({file_size / (1024 * 1024):.2f} MB). "
                f"Maximum allowed size is {max_mb:.0f} MB."
            ),
        )

    if file_size == 0:
        return FileValidationResult(
            is_valid=False,
            error_message="The uploaded file is empty. Please upload a file with content.",
        )

    # 3. Read and decode raw bytes as UTF-8 text.
    try:
        raw_bytes = uploaded_file.getvalue()
    except Exception as exc:
        return FileValidationResult(
            is_valid=False,
            error_message=f"Failed to read the uploaded file: {exc}",
        )

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return FileValidationResult(
            is_valid=False,
            error_message=(
                "The file could not be decoded as UTF-8 text. Please upload "
                "a plain text source code file."
            ),
        )

    # 4. Reject files that are empty or contain only whitespace.
    if not content.strip():
        return FileValidationResult(
            is_valid=False,
            error_message="The uploaded file is empty or contains only whitespace.",
        )

    language = get_language_from_extension(extension)

    return FileValidationResult(
        is_valid=True,
        content=content,
        language=language,
        extension=extension,
    )


def get_streamlit_language_tag(extension: str) -> str:
    """
    Map a file extension to the syntax-highlighting language tag expected
    by `st.code(..., language=...)`.

    Args:
        extension: File extension including the leading dot (e.g. ".py").

    Returns:
        str: A language identifier understood by Streamlit/Pygments.
    """
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".java": "java",
    }
    return mapping.get(extension.lower(), "text")
