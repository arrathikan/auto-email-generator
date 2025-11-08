import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from chain import Chain
from portfolio import portfolio
import re
import sys
import os
import pandas as pd
from pypdf import PdfReader

sys.path.append(os.path.dirname(__file__))

def clean_text(text):
    text = re.sub(r'<[^>]*?>', '', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_cv_to_dataframe(uploaded_file, chain):
    raw_text = ""
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            raw_text += page.extract_text()
    elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        raise NotImplementedError("DOCX/DOC file processing is not supported in this example. Please use PDF or CSV.")
    else:
        raw_text = uploaded_file.read().decode("utf-8")

    if not raw_text:
        raise ValueError("Could not extract text from the uploaded CV file.")

    structured_data = chain.extract_portfolio_data(raw_text)
    return pd.DataFrame(structured_data)

def create_streamlit_app(chain, portfolio_cls, clean_text):
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    st.title("📧 Auto Email Generator")

    user_name = st.text_input("Enter Your Name (for email signature):", placeholder="e.g., Arrathikan")
    user_possition = st.text_input("What is your position:", placeholder="e.g., Student")
    user_study = st.text_input("Enter your degree:", placeholder="e.g., BSc in Information Technology")
    user_college = st.text_input("Where do you study:", placeholder="e.g., University of Moratuwa")
    uploaded_file = st.file_uploader("Upload Your CV (PDF) or Portfolio CSV:", type=["pdf", "csv", "docx"])
    url_input = st.text_input("Enter a Job URL:", placeholder="e.g., https://careers.nike.com/job-opening")
    submit_button = st.button("Generate Email")

    if submit_button:
        if not user_name or not uploaded_file:
            st.error("⚠️ Please enter your name and upload your CV/Portfolio file.")
            return
        if not all([user_college, user_study, user_possition]):
            st.warning("⚠️ For better results, fill in your college, degree, and position details.")

        try:
            if uploaded_file.name.endswith('.csv'):
                portfolio_df = pd.read_csv(uploaded_file)
            else:
                portfolio_df = process_cv_to_dataframe(uploaded_file, chain)

            portfolio_instance = portfolio_cls(data=portfolio_df)
            portfolio_instance.load_portfolio()

            loader = WebBaseLoader([url_input])
            page_content = loader.load().pop().page_content
            data = clean_text(page_content)
            jobs = chain.extract_jobs(data)

            for job in jobs:
                skills = job.get("skills", [])
                links = portfolio_instance.query_links(skills)
                email = chain.write_mail(
                    job,
                    links,
                    user_name,
                    user_college,
                    user_study,
                    user_possition
                )
                with st.expander(f"Generated Email for: {job.get('role', 'Job Posting')}"):
                    st.markdown(f"```\n{email}\n```")

        except NotImplementedError as e:
            st.error(f"⚠️ {e}")
        except Exception as e:
            st.error(f"⚠️ An error occurred: {e}")

if __name__ == "__main__":
    chain = Chain()
    create_streamlit_app(chain, portfolio, clean_text)
