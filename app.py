"""
app.py
=======

Intelligent Code Reviewer & Explainer
--------------------------------------

A professional Streamlit application that leverages Google Gemini to
provide high-fidelity code reviews, security audits, and refactored code.
"""

import re
import streamlit as st
from typing import Dict, Optional, List
from dotenv import load_dotenv

from utils.analyzer import analyze_code, is_api_key_configured
from utils.file_handler import (
    get_streamlit_language_tag,
    get_supported_extensions,
    validate_and_read_file,
)
from utils.prompts import (
    SECTION_BUG_REPORT,
    SECTION_EXPLANATION,
    SECTION_IMPROVEMENTS,
    SECTION_OPTIMIZED_CODE,
    SECTION_QUALITY_SCORE,
    SECTION_COMPLEXITY,
    SECTION_SECURITY,
)

# Load environment variables
load_dotenv()

# Ordered list of sections we expect from Gemini for parsing.
EXPECTED_SECTIONS = [
    SECTION_QUALITY_SCORE,
    SECTION_COMPLEXITY,
    SECTION_SECURITY,
    SECTION_BUG_REPORT,
    SECTION_EXPLANATION,
    SECTION_IMPROVEMENTS,
    SECTION_OPTIMIZED_CODE,
]


def parse_gemini_response(markdown_text: str) -> Dict[str, str]:
    """
    Split a Gemini Markdown response into its named sections based on H1 headers.

    Args:
        markdown_text: The raw Markdown text returned by Gemini.

    Returns:
        Dict[str, str]: Mapping of section name -> section body text.
    """
    sections: Dict[str, str] = {}

    # Build a regex that captures each "# Heading" and everything after it
    # up until the next "# Heading" or the end of the string.
    heading_pattern = "|".join(re.escape(name) for name in EXPECTED_SECTIONS)
    pattern = re.compile(
        rf"#\s*({heading_pattern})\s*\n(.*?)(?=\n#\s*(?:{heading_pattern})|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    for match in pattern.finditer(markdown_text):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        # Normalize heading casing to match our known constants.
        for expected in EXPECTED_SECTIONS:
            if heading.lower() == expected.lower():
                sections[expected] = body
                break

    return sections


def extract_code_block(section_text: str) -> Optional[str]:
    """Extract the contents of the first fenced code block from a section."""
    match = re.search(r"```[a-zA-Z]*\n(.*?)```", section_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def render_metrics(sections: Dict[str, str]) -> None:
    """Render the high-level metrics (Score, Complexity, Security) as KPI tiles."""
    col1, col2, col3 = st.columns(3)

    with col1:
        score_text = sections.get(SECTION_QUALITY_SCORE, "N/A")
        # Try to extract just the number for the big metric
        score_match = re.search(r"(\d+)", score_text)
        score_val = score_match.group(1) if score_match else "N/A"
        st.metric("Code Quality Score", f"{score_val}/100")
        st.caption(score_text.replace(score_val, "").strip())

    with col2:
        complexity_text = sections.get(SECTION_COMPLEXITY, "No data available.")
        st.subheader("⚙️ Complexity")
        st.markdown(complexity_text)

    with col3:
        security_text = sections.get(SECTION_SECURITY, "No data available.")
        st.subheader("🛡️ Security")
        st.markdown(security_text)


def render_results(markdown_text: str, language_tag: str, model_used: Optional[str] = None) -> None:
    """
    Render a parsed Gemini response into a professional, tabbed interface.
    """
    sections = parse_gemini_response(markdown_text)

    if not sections:
        st.warning(
            "Could not parse the response into structured sections. "
            "Showing the raw model output below."
        )
        st.markdown(markdown_text)
        return

    # 1. Render High-Level Metrics First
    st.markdown("### 📊 Executive Summary")

    # Show which model was actually used for the analysis
    if model_used:
        st.caption(f"✨ Analysis performed by: `{model_used}`")

    render_metrics(sections)
    st.divider()

    # 2. Use Tabs for the detailed analysis to reduce page length and improve UX
    tab1, tab2, tab3, tab4 = st.tabs([
        "🐛 Bug Report",
        "📖 Explanation",
        "💡 Improvements",
        "✨ Optimized Code"
    ])

    with tab1:
        st.markdown(sections.get(SECTION_BUG_REPORT, "_No bug report returned._"))

    with tab2:
        st.markdown(sections.get(SECTION_EXPLANATION, "_No explanation returned._"))

    with tab3:
        st.markdown(sections.get(SECTION_IMPROVEMENTS, "_No improvements returned._"))

    with tab4:
        optimized_section = sections.get(SECTION_OPTIMIZED_CODE, "")
        code_block = extract_code_block(optimized_section)
        if code_block:
            st.code(code_block, language=language_tag)
        elif optimized_section:
            st.markdown(optimized_section)
        else:
            st.info("No optimized code was returned.")

    # 3. Provide a downloadable report
    st.divider()
    st.markdown("### 📥 Export Analysis")
    st.download_button(
        label="Download Full Analysis (.md)",
        data=markdown_text,
        file_name="code_analysis_report.md",
        mime="text/markdown",
    )


def render_sidebar() -> None:
    """Render the sidebar with app metadata and API key status."""
    with st.sidebar:
        st.title("🧠 AI Code Reviewer")
        st.markdown(
            "**Intelligent Code Reviewer & Explainer** uses Google Gemini "
            "to analyze source code and return a professional audit: "
            "metrics, security, bugs, and refactored code."
        )

        st.divider()
        st.subheader("Supported Languages")
        for ext, lang in [(".py", "Python"), (".js", "JavaScript"), (".java", "Java")]:
            st.markdown(f"- `{ext}` : {lang}")

        st.divider()
        st.subheader("System Status")
        if is_api_key_configured():
            st.success("Gemini API key configured ✅")
        else:
            st.error("API key NOT found ❌")
            st.caption(
                "Set `GEMINI_API_KEY` in a `.env` file "
                "to enable analysis."
            )


def main() -> None:
    """Application entry point."""
    st.set_page_config(
        page_title="Intelligent Code Reviewer",
        page_icon="🧠",
        layout="wide",
    )

    render_sidebar()

    st.title("🧠 Intelligent Code Reviewer & Explainer")
    st.markdown(
        "Upload your source code to get a professional audit including "
        "**quality scoring, security analysis, bug detection, and optimized code**."
    )

    supported_exts = get_supported_extensions()
    supported_str = ", ".join(supported_exts)

    uploaded_file = st.file_uploader(
        f"Upload a source code file ({supported_str})",
        type=[ext.lstrip(".") for ext in supported_exts],
    )

    if uploaded_file is None:
        st.info("👆 Please upload a file to begin the analysis.")
        return

    # --- Validate and read the uploaded file ---
    validation_result = validate_and_read_file(uploaded_file)
    if not validation_result.is_valid:
        st.error(validation_result.error_message)
        return

    code_content = validation_result.content
    language = validation_result.language
    extension = validation_result.extension
    language_tag = get_streamlit_language_tag(extension)

    st.subheader(f"📄 File: `{uploaded_file.name}`")
    st.caption(f"Language: **{language}**")

    with st.expander("View Source Code", expanded=False):
        st.code(code_content, language=language_tag)

    st.divider()

    if st.button("🔍 Start Professional Analysis", type="primary", use_container_width=True):
        # Guard: missing API key
        if not is_api_key_configured():
            st.error("Gemini API key is missing. Please check your .env configuration.")
            return

        with st.spinner("🤖 Gemini is auditing your code... this may take a few seconds."):
            result = analyze_code(
                code=code_content,
                language=language,
                filename=uploaded_file.name,
            )

        if not result.success:
            st.error(f"Analysis failed: {result.error_message}")
            return

        st.success("Analysis complete!")
        render_results(result.content, language_tag, result.model_used)


if __name__ == "__main__":
    main()
