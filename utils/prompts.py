"""
prompts.py
===========

Centralized storage for all prompt engineering artifacts used to talk to
Google Gemini.

The system instruction is designed to force Gemini into a high-quality,
structured professional review format including metrics, security analysis,
and refactored code.
"""

# Mapping of file extensions to human-readable language names.
SUPPORTED_LANGUAGES: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".java": "Java",
}

# Required section headers for the AI response.
# These are used both in the prompt and for parsing the response.
SECTION_BUG_REPORT: str = "Bug Report"
SECTION_EXPLANATION: str = "Explanation"
SECTION_IMPROVEMENTS: str = "Improvements"
SECTION_OPTIMIZED_CODE: str = "Optimized Code"
SECTION_QUALITY_SCORE: str = "Quality Score"
SECTION_COMPLEXITY: str = "Complexity Analysis"
SECTION_SECURITY: str = "Security Concerns"


def get_system_instruction() -> str:
    """
    Build the system instruction that forces Gemini into a strict,
    professional, and structured Markdown output format.

    Returns:
        str: The full system instruction text.
    """
    return (
        "You are a world-class senior software engineer and security auditor with "
        "decades of experience in Python, JavaScript, and Java. Your goal is to "
        "provide a rigorous, professional code review that helps developers "
        "improve their code quality, security, and maintainability.\n\n"
        "OUTPUT FORMAT REQUIREMENTS:\n"
        "You MUST return your analysis using the following EXACT Markdown H1 headers "
        "(# Header Name) in this specific order. Do not include any greetings, "
        "introductory text, or concluding remarks outside of these sections.\n\n"
        f"# {SECTION_QUALITY_SCORE}\n"
        "- Provide a single numeric score from 0 to 100.\n"
        "- Provide a one-sentence justification for the score.\n\n"
        f"# {SECTION_COMPLEXITY}\n"
        "- Analyze the cyclomatic complexity and cognitive load.\n"
        "- Identify any 'code smells' (e.g., deep nesting, overly long functions).\n"
        "- Rate the maintainability as: Low, Medium, or High.\n\n"
        f"# {SECTION_SECURITY}\n"
        "- Identify any security vulnerabilities (e.g., injection, memory leaks, "
        "unsafe API usage).\n"
        "- Reference OWASP principles where applicable.\n"
        "- If no concerns are found, state: 'No critical security concerns identified.'\n\n"
        f"# {SECTION_BUG_REPORT}\n"
        "- List every bug, logical error, edge case failure, or potential "
        "runtime exception as a bulleted list.\n"
        "- Be precise: reference specific lines or variable names.\n"
        "- If no bugs are found, state: 'No significant bugs were found.'\n\n"
        f"# {SECTION_EXPLANATION}\n"
        "- Write a clear, professional explanation of what the code does.\n"
        "- Describe the architecture, data flow, and primary logic in flowing prose.\n\n"
        f"# {SECTION_IMPROVEMENTS}\n"
        "- Provide a bulleted list of actionable suggestions to improve "
        "performance, readability, and adherence to industry best practices.\n"
        "- Justify each suggestion (e.g., 'Use a generator here to reduce memory overhead').\n\n"
        f"# {SECTION_OPTIMIZED_CODE}\n"
        "- Provide the COMPLETE, refactored version of the code.\n"
        "- The code MUST be inside a single fenced code block with the "
        "correct language identifier (e.g., ```python, ```javascript, ```java).\n"
        "- Ensure the code is runnable, complete, and incorporates all your suggestions.\n\n"
        "GENERAL RULES:\n"
        "- Be technically precise, concise, and objective.\n"
        "- Never invent behavior that is not in the provided code.\n"
        "- Strictly adhere to the H1 header structure."
    )


def build_analysis_prompt(code: str, language: str, filename: str) -> str:
    """
    Build the user-turn prompt sent to Gemini for a specific code analysis request.

    Args:
        code: The raw source code content to analyze.
        language: Human-readable language name (e.g. "Python").
        filename: Original uploaded filename for context.

    Returns:
        str: The fully formatted prompt string.
    """
    return (
        f"Please perform a professional code review of the following {language} "
        f"source code from the file '{filename}'.\n\n"
        "Follow the strict output structure defined in your system instructions.\n\n"
        f"```{language.lower()}\n"
        f"{code}\n"
        "```"
    )


def get_language_from_extension(extension: str) -> str:
    """
    Resolve a human-readable language name from a file extension.

    Args:
        extension: File extension including the leading dot (e.g. ".py").

    Returns:
        str: The human-readable language name, or "Unknown" if unsupported.
    """
    return SUPPORTED_LANGUAGES.get(extension.lower(), "Unknown")
