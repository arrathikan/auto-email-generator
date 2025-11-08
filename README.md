# 📧 Auto Email Generator

> **AI-powered Streamlit app that automatically generates personalized professional emails for job applications.**  
> Upload your CV, paste a job URL, and let the app match your skills to the job and draft a tailored email using **Llama 3.3** and **Groq API**.

---

## 🚀 Features

- 🧠 **AI Email Generation** – Creates a professional email tailored to your background and the job description.  
- 📄 **CV Parsing** – Extracts your technical skills and project links from your uploaded CV (PDF).  
- 🌐 **Web Scraping** – Reads job details directly from any career or job listing page URL.  
- 🧩 **Vector Search** – Matches your portfolio projects with job-required skills using **ChromaDB**.  
- ⚡ **Groq Integration** – Powered by **Llama 3.3 (70B Versatile)** model for fast and intelligent text generation.  
- 🖥️ **Streamlit UI** – Simple, clean, and interactive web interface.  

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Frontend** | Streamlit |
| **AI Model** | Llama 3.3 (via Groq API) |
| **Backend** | LangChain |
| **Vector Database** | ChromaDB |
| **Utilities** | PyPDF, Pandas, dotenv |

---

## 🗂️ Project Structure
app/
│
├── app.py # Streamlit main application
├── chain.py # LLM prompt logic and data parsing
├── portfolio.py # Portfolio and vector database operations
├── .env # (Ignored) Contains your Groq API key
├── requirements.txt # Python dependencies
└── README.md

## 💡 How It Works

1. Upload your **CV (PDF)** or **Portfolio CSV**.  
2. Paste a **Job URL** from a company’s career site.  
3. Fill in your **name**, **degree**, **college**, and **position**.  
4. Click **“Generate Email”**.  
5. The AI analyzes your CV and the job description to create a **professional, personalized email**!

