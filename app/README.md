# 📧 OutreachAI | Intelligent Auto Email Generator

> **AI-powered Cold Email Generator that matches candidate skills and portfolio projects to any job opening or careers page using LangChain, Groq LLMs, and ChromaDB vector search.**

---

## 🚀 Key Features

- **🎨 Modern UI/UX**: Dark glassmorphic design built with Streamlit and custom CSS.
- **📄 Universal CV & Resume Parsing**: Ingests PDF, DOCX, CSV, and plain text resumes.
- **💼 Dual Job Ingestion**: Scrape job URLs or paste raw job descriptions / recruiter notes directly.
- **🧠 Semantic Vector Search**: ChromaDB matches the candidate's actual projects to job requirements.
- **💡 Subject Line Generator**: AI creates 3 high-converting subject lines with 1-click selection.
- **✉️ 1-Click Mail Dispatch with CV Attached**: Automatically launches Apple Mail with To, Subject, Body, and the uploaded CV attached in 1 click.
- **📮 Multi-Channel Exports**: Open in Gmail Web, download `.eml` drafts with CV attached, or export as `.txt`/`.md`.
- **✨ 1-Click Demo Profile & Job**: Test all features instantly with sample data.

---

## 🧰 Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | Streamlit + Custom CSS |
| **LLM Models** | Groq (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`) |
| **LLM Orchestration** | LangChain & LangChain-Groq |
| **Vector Database** | ChromaDB |
| **Document Processing** | `pypdf`, `python-docx`, `pandas`, `beautifulsoup4` |

---

## 🗂️ Project Structure

```
├── main.py              # Streamlit application
├── chain.py             # LLM prompt logic, job extraction, and email generation
├── portfolio.py         # ChromaDB vector store operations
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md
```

---

## 📦 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/arrathikan/auto-email-generator.git
cd auto-email-generator
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your Groq API Key
Create a `.env` file in the root directory:
```env
API_KEY=your_groq_api_key_here
```

### 5. Run the application
```bash
streamlit run main.py
```
