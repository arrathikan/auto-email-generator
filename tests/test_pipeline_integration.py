import pytest
from unittest.mock import MagicMock
from chain import Chain

@pytest.fixture(autouse=True)
def mock_groq_env(monkeypatch):
    """
    Ensures tests run in a completely isolated offline environment
    without consuming external API credits or making live network requests.
    """
    monkeypatch.setenv("API_KEY", "dummy_key")
    monkeypatch.setenv("GROQ_API_KEY", "dummy_key")

class TestPipelineIntegrationWithMockLLM:
    def test_offline_mode_job_extraction(self):
        chain = Chain(api_key="dummy_key")
        jobs = chain.extract_jobs("We are looking for a Python backend engineer with machine learning experience.")
        assert len(jobs) >= 1
        job = jobs[0]
        assert "role" in job
        assert "critical_requirements" in job
        assert "skills" in job

    def test_offline_mode_candidate_profile_parsing(self):
        chain = Chain(api_key="dummy_key")
        cv_text = "John Doe\nAI Engineer\nSkills: Python, TensorFlow, PyTorch"
        profile = chain.parse_candidate_profile_from_cv(cv_text)
        assert profile["full_name"] == "John Doe"
        assert "portfolio" in profile
        # Verifies no fake links are hallucinated
        for p in profile["portfolio"]:
            assert "candidate/project-name" not in p.get("Links", "")

    def test_offline_mode_email_generation(self):
        chain = Chain(api_key="dummy_key")
        job = {
            "role": "AI Engineer",
            "company": "DeepTech",
            "domain": "Artificial Intelligence",
            "skills": ["Python", "PyTorch"],
            "critical_requirements": ["Python", "PyTorch"],
            "key_focus_areas": ["Model Training"]
        }
        res = chain.write_mail(
            job=job,
            links=["https://github.com/johndoe/ai-project"],
            user_name="John Doe",
            user_study="Computer Science",
            user_college="MIT",
            user_position="AI Engineer",
            cv_text="Built machine learning systems in Python and PyTorch."
        )
        assert "body" in res
        assert "subject_lines" in res
        assert len(res["subject_lines"]) >= 1
        assert "DeepTech" in res["body"] or "AI Engineer" in res["body"]

    def test_offline_job_fit_analysis(self):
        chain = Chain(api_key="dummy_key")
        job = {
            "critical_requirements": ["Python", "PyTorch"],
            "preferred_requirements": ["FastAPI", "Kubernetes"],
            "soft_skills": ["Teamwork"],
            "irrelevant_noise": ["Random Noise"]
        }
        cv_text = "Experienced software engineer. Highly proficient in Python and PyTorch. Great teamwork skills."
        fit = chain.analyze_job_fit(
            job=job,
            portfolio_summary="",
            user_name="John Doe",
            cv_text=cv_text
        )
        assert "match_score" in fit
        assert "fit_level" in fit
        assert "evidence_breakdown" in fit
        # Python and PyTorch should be MATCHED
        statuses = {item["requirement"]: item["status"] for item in fit["evidence_breakdown"]}
        assert statuses.get("Python") == "MATCHED"
        assert statuses.get("PyTorch") == "MATCHED"
        # FastAPI is PARTIALLY MATCHED because candidate has related Python foundation
        assert statuses.get("FastAPI") == "PARTIALLY MATCHED"
        # Kubernetes is completely MISSING
        assert statuses.get("Kubernetes") == "MISSING"
        # Random Noise is marked NOT RELEVANT
        assert statuses.get("Random Noise") == "NOT RELEVANT"

    def test_mocked_llm_email_generation_schema(self):
        """
        Tests email generation when LLM returns a structured mock JSON response.
        """
        from langchain_core.runnables import RunnableLambda
        chain = Chain(api_key="test_key_long_enough_12345")
        mock_response = MagicMock()
        mock_response.content = '{"subject_lines": ["Custom Subject"], "body": "Custom Body", "match_summary": "High alignment", "key_highlights_used": ["Python"], "focus_areas_addressed": "Backend"}'
        
        chain.llm = RunnableLambda(lambda x: mock_response)

        job = {"role": "Backend Dev", "company": "Acme", "skills": ["Python"]}
        result = chain.write_mail(job=job, links=[], user_name="Alice", cv_text="Python dev")
        assert result["body"] == "Custom Body"
        assert result["subject"] == "Custom Subject"
