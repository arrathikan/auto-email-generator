# 📧 CareerLens | Intelligent AI Auto Email Generator & Job Match Studio

> **Production-grade AI-powered Cold Email & Job Match Studio that evaluates candidate resumes against any job posting, isolates multi-user vector storage in ChromaDB, secures SMTP credentials with authenticated encryption, and drafts personalized outreach emails using LangChain and Groq LLMs.**

---

## 🚀 Key Features

- **🎨 Modern Glassmorphic Interface**: Dark glassmorphic design built with Streamlit and tailored CSS tokens.
- **🔐 Hardened Authentication**:
  - **Argon2id** password hashing with automatic transparent migration for legacy salted hashes.
  - SQL injection-resistant parameterized database queries.
- **🛡️ Multi-User ChromaDB Isolation**:
  - Authenticated user ID isolation ensures candidate portfolios are stored in dedicated vector collections.
  - User A's uploads and deletions can never view, overwrite, or delete User B's portfolio data.
- **🚫 Zero-Hallucination Portfolio Linking**:
  - LLM prompts strictly enforce referencing only candidate-verified repository links.
  - Rejects placeholder and fabricated GitHub/website URLs while preserving unlinked projects.
- **🎯 Precise Evidence-Based Skill Matching**:
  - Boundary-aware regex matching handles punctuation-rich technical terms (`C++`, `C#`, `.NET`, `Node.js`, `CI/CD`).
  - Differentiates exact skills from merely adjacent ecosystem libraries (e.g. knowing Pandas does not falsely mark Django as matched).
  - Classifies requirements into `MATCHED`, `PARTIALLY MATCHED`, `MISSING`, and `NOT RELEVANT`.
- **📊 Deterministic Weighted Scoring**:
  - Mathematically audited match score: Critical Requirements (65%), Preferred Requirements (25%), Soft Skills (10%), Noise/Boilerplate (0%).
  - Clarifies that the alignment score is an objective ATS match percentage, not a hiring guarantee.
- **🌐 SSRF-Protected Job Ingestion**:
  - Safe URL extraction blocking requests to `localhost`, loopback addresses, internal private IP subnets (RFC 1918), and cloud metadata endpoints (`169.254.169.254`), including protection against redirect SSRF.
  - Intelligent HTML text parsing with automatic manual paste fallback for JavaScript-rendered or access-restricted pages.
- **📄 Resilient Universal CV Processing**:
  - Ingests PDF, DOCX, CSV, and plain text files with 15 MB file size and type validation.
  - Scanned PDF detection with optional OCR fallback via Tesseract (`pytesseract`).
- **🧠 Full-Context AI Processing**:
  - High-capacity context windows preserve education, skills, and multi-page project histories without premature 2,500-character truncation.
- **🔒 Authenticated SMTP Credential Protection**:
  - Email app passwords encrypted using Fernet (AES-128-CBC + HMAC-SHA256).
  - Encryption key is stored strictly outside the SQLite database (`ENCRYPTION_KEY` env or protected `.smtp_secret.key` file).
  - Legacy plaintext credentials are automatically encrypted on access without exposing secrets.
- **✉️ Multi-Channel Email Dispatch**:
  - 1-click launch in desktop clients (Apple Mail, Outlook, Thunderbird) with CV attached.
  - Compose in Gmail Web with pre-filled subject and body.
  - Download standard `.eml` email drafts with CV attached.
  - Direct dispatch via authenticated SMTP.

---

## 🧰 Tech Stack & Architecture

| Layer | Technologies |
|---|---|
| **Frontend** | Streamlit + Custom Glassmorphic CSS |
| **Authentication & Security** | Argon2id (`argon2-cffi`), Fernet (`cryptography`), SSRF defense |
| **LLM Orchestration** | LangChain, LangChain-Groq, LangChain-Community |
| **LLM Inference** | Groq (`openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`, `groq/compound`) |
| **Vector Database** | ChromaDB (multi-tenant isolated vector stores) |
| **Database** | SQLite3 (`tracker.db` with parameterized queries) |
| **Document Processing** | `pypdf`, `python-docx`, `beautifulsoup4`, `pandas`, optional `pytesseract` |
| **Testing** | `pytest` (comprehensive unit, security, and integration test suite) |

---

## 🗂️ Project Directory Structure

```
auto-email-generator/
├── .env.example              # Template for environment variables and secrets
├── .gitignore                # Git exclusions (credentials, databases, uploads, keys)
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation and guide
├── app/
│   ├── main.py               # Main Streamlit application and UI studio
│   ├── chain.py              # LLM prompts, evidence audit, and email generator
│   ├── cv_parser.py          # Resilient CV parser with validation and OCR fallback
│   ├── job_loader.py         # SSRF-protected job description fetcher
│   ├── mailer.py             # SMTP email dispatch and credential sanitization
│   ├── portfolio.py          # Multi-user isolated ChromaDB vector storage
│   ├── tracker.py            # Argon2id auth, SQLite database, and Fernet encryption
│   ├── email_sync.py         # Mail dispatch export interface
│   ├── requirements.txt      # Module dependencies
│   ├── README.md             # App-level documentation
│   ├── assets/               # Visual UI assets
│   ├── data/                 # SQLite database and vector storage (git-ignored)
│   └── uploads/              # Uploaded candidate CVs (git-ignored)
└── tests/
    ├── conftest.py           # Pytest test environment fixtures
    ├── test_auth_and_crypto.py # Tests for Argon2id, legacy migration, SQL injection, and Fernet
    ├── test_chain_matching.py  # Tests for skill matching, word boundaries, and URL validation
    ├── test_cv_parser.py     # Tests for CV extraction, file size, and scanned PDF detection
    ├── test_pipeline_integration.py # Integration tests for job fit and mocked email drafting
    ├── test_portfolio_isolation.py  # Tests for ChromaDB multi-user isolation
    ├── test_scoring.py       # Tests for deterministic weighted scoring formula
    └── test_url_security.py  # Security tests for SSRF protection and IP blocking
```

---

## 📦 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/arrathikan/auto-email-generator.git
cd auto-email-generator
```

### 2. Set Up a Virtual Environment

#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*(Optional OCR Support)*:
To enable optical character recognition for scanned PDFs, install Tesseract OCR on your operating system:
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Install [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your system PATH.
*(If Tesseract is not installed, the application will run normally and prompt you to paste text or upload text-based PDFs.)*

### 4. Configure Environment Variables
Create a `.env` file in the project root or inside `app/`:

```env
# Required: Your Groq API Key (get one free at https://console.groq.com)
API_KEY=gsk_your_groq_api_key_here

# Optional: Master encryption key for SMTP credentials.
# If omitted, a secure Fernet key will be generated automatically in app/data/.smtp_secret.key
# ENCRYPTION_KEY=your_generated_fernet_key_here
```

### 5. Run the Automated Test Suite
Verify that all unit, security, and integration tests pass:
```bash
pytest tests/ -v
```

### 6. Launch the Application

#### From the project root directory:
```bash
streamlit run app/main.py
```

#### Or from inside the `app/` directory:
```bash
cd app
streamlit run main.py
```

Open your browser at `http://localhost:8501`.

---

## 🧪 Automated Test Suite Coverage

The automated test suite runs 38 tests covering:
- **Security**: SQL injection resistance, SSRF prevention (localhost, private subnets, cloud metadata 169.254.169.254, redirect checks), authenticated Fernet credential encryption, and Argon2id password hashing.
- **Multi-Tenant Isolation**: ChromaDB collections isolated per user ID, ensuring independent index storage and deletion safety.
- **Skill Matching Accuracy**: Punctuation-safe word boundaries (`C++`, `.NET`), synonym aliases, and strict separation between exact matches and adjacent libraries.
- **Reliability**: Long-document preservation, mocked LLM fallbacks, and CV file validation.

Run tests anytime with:
```bash
pytest tests/ -v
```

---

## 🔒 Security Best Practices

1. **No Hardcoded Secrets**: Real API keys, passwords, and encryption keys are never committed or logged.
2. **Encrypted Credentials**: SMTP app passwords stored in SQLite are encrypted with authenticated Fernet encryption; encryption keys are kept out of the database.
3. **SSRF Guard**: Public job fetcher resolves DNS and validates IP destinations before connection, rejecting all private and link-local ranges.
4. **Input Constraints**: Uploaded CV files are strictly checked for supported formats and a 15 MB size ceiling.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
