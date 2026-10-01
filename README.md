# 🧠 Intelligent Code Reviewer & Explainer

An AI-powered professional code audit tool that leverages **Google Gemini** to analyze source code, identify bugs, evaluate security, and provide an optimized rewrite.

## ✨ Features

- **Professional Audit**: Beyond simple bug finding, it provides:
  - 📈 **Code Quality Score**: A numeric score (0-100) with justification.
  - ⚙️ **Complexity Analysis**: Evaluation of cyclomatic complexity and maintainability.
  - 🛡️ **Security Audit**: Identification of vulnerabilities based on industry standards (OWASP).
  - 🐛 **Bug Report**: Detailed list of logical errors and edge-case failures.
  - 📖 **Plain-Language Explanation**: A high-level architectural walkthrough.
  - 💡 **Actionable Improvements**: Specific suggestions for performance and readability.
  - ✨ **Optimized Code**: A complete, refactored, and runnable version of the submitted code.
- **Multi-Language Support**: Fully supports Python (`.py`), JavaScript (`.js`), and Java (`.java`).
- **Portfolio-Ready UX**:
  - **Executive Summary**: KPI tiles for quick health checks.
  - **Tabbed Interface**: Organized detailed analysis.
  - **Exportable Reports**: Download the full analysis as a `.md` file for documentation.
  - **Secure Handling**: API keys are managed via environment variables.

---

## 🛠 Tech Stack

- **Language**: Python 3.12+
- **UI Framework**: [Streamlit](https://streamlit.io/)
- **AI Engine**: [Google Gemini API](https://ai.google.dev/) (`google-genai` SDK)
- **Environment**: `python-dotenv`

---

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/intelligent-code-reviewer.git
   cd intelligent-code-reviewer
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🔑 Environment Setup

1. **Obtain a Gemini API Key**:
   Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to generate your free API key.

2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and enter your key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

---

## ▶️ Running the Application

Start the Streamlit server:
```bash
streamlit run app.py
```
Open the provided local URL (usually `http://localhost:8501`) in your browser.

---

## 📁 Project Structure

```
intelligent-code-reviewer/
├── app.py                # Streamlit UI & Presentation Layer
├── requirements.txt      # Project dependencies
├── README.md             # Documentation
├── .env.example          # Env template
├── .gitignore            # Git exclusion rules
└── utils/                # Core Business Logic
    ├── __init__.py       # Package marker
    ├── analyzer.py       # Gemini API Wrapper & Error Handling
    ├── prompts.py        # Professional Prompt Engineering & System Instructions
    └── file_handler.py   # File Validation & Decoding
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Manages the user interface, handles file uploads, parses AI responses, and renders results. |
| `utils/analyzer.py` | Handles the lifecycle of the API request, manages the Gemini Client, and catches SDK exceptions. |
| `utils/prompts.py` | Defines strict system instructions to ensure consistent, professional, and structured AI output. |
| `utils/file_handler.py` | Ensures uploaded files are within size limits and are of supported types before processing. |

---

## 🚀 Future Enhancements

- [ ] **Language Expansion**: Add support for TypeScript, Rust, and Go.
- [ ] **Diff Viewer**: Implement a side-by-side comparison between original and optimized code.
- [ ] **Direct Input**: Add a text area for pasting code snippets directly.
- [ ] **Batch Analysis**: Allow uploading multiple files for project-wide analysis.
- [ ] **PDF Export**: Generate a branded PDF report for clients/stakeholders.

---

## ⚠️ Disclaimer

This tool is designed to assist developers. AI-generated code and reviews should always be verified by a human engineer before being deployed to production.
