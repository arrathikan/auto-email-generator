import pytest
from chain import (
    find_cv_evidence,
    evaluate_requirement,
    verify_and_ground_llm_claims,
    is_valid_url,
    sanitize_extracted_portfolio,
    skill_match_regex
)

class TestSkillMatching:
    def test_exact_skill_match_with_word_boundary(self):
        cv = "Experienced Software Engineer. Proficient in Python, C++, and Docker."
        status, quote, conf = find_cv_evidence("Python", cv)
        assert status == "MATCHED"
        assert conf == "High"
        assert "Python" in quote

        status_cpp, quote_cpp, conf_cpp = find_cv_evidence("C++", cv)
        assert status_cpp == "MATCHED"
        assert conf_cpp == "High"

    def test_prevents_false_positive_substring_matches(self):
        # 'go' should NOT match inside 'good' or 'algorithm'
        cv_text = "I have a good understanding of sorting algorithms."
        status, _, _ = find_cv_evidence("Go", cv_text)
        assert status == "MISSING"

        # 'c' should NOT match inside 'clean' or 'code'
        cv_clean = "I write clean and maintainable code in Java."
        status_c, _, _ = find_cv_evidence("C", cv_clean)
        assert status_c == "MISSING"

    def test_canonical_synonym_matches(self):
        # 'k8s' should match requirement 'Kubernetes'
        cv = "Managed production clusters on k8s and AWS."
        status, quote, conf = find_cv_evidence("Kubernetes", cv)
        assert status == "MATCHED"
        assert "k8s" in quote

        # 'golang' should match requirement 'Go'
        cv_go = "Developed high-concurrency microservices with Golang."
        status_go, _, _ = find_cv_evidence("Go", cv_go)
        assert status_go == "MATCHED"

    def test_adjacent_library_labeled_partially_matched_not_full_match(self):
        # Candidate has Pandas and NumPy, but NOT Django.
        # Knowing Pandas should NOT count as a full match for Django!
        cv = "Data analyst with deep experience in Python, Pandas, and NumPy."
        status, explanation, conf = find_cv_evidence("Django", cv)
        assert status == "PARTIALLY MATCHED"
        assert "Django" in explanation
        assert conf == "Medium"

    def test_missing_skill_completely_absent(self):
        cv = "Frontend engineer specializing in React and CSS."
        status, explanation, conf = find_cv_evidence("Rust", cv)
        assert status == "MISSING"
        assert "Rust" in explanation

    def test_portfolio_evidence_matching(self):
        cv = "General Software Developer."
        portfolio = [
            {"Techstack": "FastAPI, PostgreSQL, Redis", "Links": "https://github.com/user/api"}
        ]
        status, quote, conf = find_cv_evidence("FastAPI", cv, portfolio_items=portfolio)
        assert status == "MATCHED"
        assert "Demonstrated in Portfolio" in quote

    def test_compound_requirement_partial_match(self):
        cv = "Proficient in FastAPI backend services."
        status, quote, conf = find_cv_evidence("FastAPI and PostgreSQL", cv)
        assert status == "PARTIALLY MATCHED"
        assert "fastapi" in quote.lower()


class TestExactMatches:
    """Tests for exact matches across technical, educational, experience, and soft skills."""
    def test_exact_technical_skill_pytorch_match(self):
        cv = "Deep learning research engineer developing novel transformer architectures in PyTorch."
        res = evaluate_requirement("PyTorch", cv, category="Critical Technical Skill")
        assert res["status"] == "MATCHED"
        assert res["category"] == "Critical Technical Skill"
        assert "PyTorch" in res["supporting_evidence"]
        assert res["confidence"] == "High"
        assert res["uncertainty"] <= 0.15

    def test_exact_educational_qualification_match(self):
        cv = "Education: Bachelor of Science in Computer Science, Magna Cum Laude."
        res = evaluate_requirement("Bachelor's degree in Computer Science", cv, category="Educational Qualification")
        assert res["status"] == "MATCHED"
        assert res["category"] == "Educational Qualification"
        assert "Computer Science" in res["supporting_evidence"]
        assert res["confidence"] == "High"

    def test_exact_experience_requirement_match(self):
        cv = "Senior Software Architect with 5+ years of experience in distributed systems."
        res = evaluate_requirement("3+ years of experience", cv, category="Experience Requirement")
        assert res["status"] == "MATCHED"
        assert res["category"] == "Experience Requirement"
        assert "years of experience" in res["supporting_evidence"]
        assert res["confidence"] == "High"

    def test_exact_soft_skill_match(self):
        cv = "Demonstrated cross-functional collaboration and proactive problem solving across 4 product teams."
        res = evaluate_requirement("Problem Solving", cv, category="Soft Skill")
        assert res["status"] == "MATCHED"
        assert res["category"] == "Soft Skill"
        assert "problem solving" in res["supporting_evidence"].lower()


class TestTechnicalSkillNormalizationAndPartialMatches:
    """
    Tests for skill normalization:
    - PyTorch is NOT automatically equivalent to TensorFlow.
    - AWS experience is NOT automatically equivalent to Azure.
    - Knowledge of Python does NOT imply knowledge of FastAPI.
    """
    def test_pytorch_not_automatically_equivalent_to_tensorflow(self):
        cv = "Built NLP classification pipelines using TensorFlow and Keras."
        res = evaluate_requirement("PyTorch", cv, category="Critical Technical Skill")
        assert res["status"] == "PARTIALLY MATCHED"
        assert "TensorFlow" in res["candidate_evidence"]
        assert "not automatically equivalent" in res["explanation"].lower()
        assert res["confidence"] == "Medium"

    def test_tensorflow_not_automatically_equivalent_to_pytorch(self):
        cv = "Trained computer vision models using PyTorch on multi-GPU nodes."
        res = evaluate_requirement("TensorFlow", cv, category="Critical Technical Skill")
        assert res["status"] == "PARTIALLY MATCHED"
        assert "PyTorch" in res["candidate_evidence"]
        assert "not automatically equivalent" in res["explanation"].lower()

    def test_aws_not_automatically_equivalent_to_azure(self):
        cv = "Cloud operations engineer managing workloads on Microsoft Azure and Azure DevOps."
        res = evaluate_requirement("AWS", cv, category="Critical Technical Skill")
        assert res["status"] == "PARTIALLY MATCHED"
        assert "azure" in res["candidate_evidence"].lower()
        assert "not automatically equivalent" in res["explanation"].lower()

    def test_python_does_not_imply_fastapi(self):
        cv = "Software Engineer experienced in Python data pipelines and automation scripts."
        res = evaluate_requirement("FastAPI", cv, category="Preferred Technical Skill")
        assert res["status"] == "PARTIALLY MATCHED"
        assert "python" in res["candidate_evidence"].lower()
        assert "FastAPI" in res["explanation"]
        assert res["confidence"] == "Medium"

    def test_degree_in_adjacent_stem_discipline(self):
        cv = "Education: Bachelor of Science in Applied Physics with minor in Mathematics."
        res = evaluate_requirement("Bachelor's degree in Computer Science", cv, category="Educational Qualification")
        assert res["status"] == "PARTIALLY MATCHED"
        assert res["category"] == "Educational Qualification"
        assert res["confidence"] == "Medium"


class TestMissingSkills:
    """Tests for missing competencies."""
    def test_completely_missing_technical_skill(self):
        cv = "Frontend web developer specializing in React, HTML, CSS, and modern JavaScript."
        res = evaluate_requirement("Rust", cv, category="Critical Technical Skill")
        assert res["status"] == "MISSING"
        assert res["supporting_evidence"] == ""
        assert "No direct or related evidence" in res["explanation"]
        assert res["confidence"] == "High"

    def test_missing_educational_qualification(self):
        cv = "Self-taught backend programmer with 6 years of software consulting."
        res = evaluate_requirement("Master's degree in Computer Science", cv, category="Educational Qualification")
        assert res["status"] == "MISSING"
        assert res["supporting_evidence"] == ""
        assert res["confidence"] == "High"

    def test_missing_experience_requirement(self):
        cv = "Recent graduate eager to learn backend technologies."
        res = evaluate_requirement("5+ years of experience", cv, category="Experience Requirement")
        assert res["status"] == "MISSING"
        assert res["supporting_evidence"] == ""


class TestConflictingEvidence:
    """Tests for candidate CVs containing explicit conflicting or negative statements."""
    def test_explicit_no_experience_conflict(self):
        cv = "Full-stack developer with 3 years in Node.js, but have no experience with PyTorch."
        res = evaluate_requirement("PyTorch", cv, category="Critical Technical Skill")
        assert res["status"] == "MISSING"
        assert "Conflicting evidence" in res["explanation"]
        assert res["confidence"] == "High"

    def test_zero_experience_in_cloud_conflict(self):
        cv = "Systems administrator with zero experience in AWS or cloud infrastructure."
        res = evaluate_requirement("AWS", cv, category="Critical Technical Skill")
        assert res["status"] == "MISSING"
        assert "Conflicting evidence" in res["explanation"]

    def test_basic_introductory_knowledge_conflict(self):
        cv = "Python developer with basic knowledge of FastAPI."
        res = evaluate_requirement("FastAPI", cv, category="Critical Technical Skill")
        assert res["status"] == "PARTIALLY MATCHED"
        assert "introductory/basic familiarity" in res["explanation"]

    def test_currently_learning_conflict(self):
        cv = "Senior Java engineer currently learning Go."
        res = evaluate_requirement("Go", cv, category="Critical Technical Skill")
        assert res["status"] == "PARTIALLY MATCHED"
        assert "introductory/basic familiarity" in res["explanation"]


class TestEmptyCVHandling:
    """Tests that empty or whitespace-only CVs never generate hallucinated matches."""
    def test_empty_string_cv(self):
        res = evaluate_requirement("Python", "", category="Critical Technical Skill")
        assert res["status"] == "MISSING"
        assert res["supporting_evidence"] == ""
        assert "empty" in res["candidate_evidence"].lower()
        assert res["uncertainty"] == 0.05

    def test_whitespace_only_cv(self):
        res = evaluate_requirement("Docker", "   \n\t  ", category="Critical Technical Skill")
        assert res["status"] == "MISSING"
        assert res["supporting_evidence"] == ""
        assert "empty" in res["candidate_evidence"].lower()

    def test_verify_and_ground_claims_with_empty_cv(self):
        unsupported_claims = [
            {"requirement": "Python", "status": "MATCHED", "supporting_evidence": "Expert in Python"},
            {"requirement": "PyTorch", "status": "MATCHED", "supporting_evidence": "Deep learning research"}
        ]
        grounded = verify_and_ground_llm_claims(unsupported_claims, cv_text="")
        for g in grounded:
            assert g["status"] == "MISSING"
            assert g["supporting_evidence"] == ""
            assert "empty" in g["candidate_evidence"].lower()


class TestInvalidLLMResponsesAndGrounding:
    """Tests strict grounding: Never count unsupported LLM claims as evidence."""
    def test_unsupported_claim_downgraded_to_missing(self):
        cv = "Software Engineer specialized in Python and PostgreSQL."
        hallucinated_breakdown = [
            {
                "requirement": "Rust",
                "category": "Critical Technical Skill",
                "importance": "Critical requirement",
                "status": "MATCHED",
                "supporting_evidence": "Built high-performance microservices in Rust.",  # Fake LLM quote!
                "explanation": "Candidate knows Rust."
            }
        ]
        grounded = verify_and_ground_llm_claims(hallucinated_breakdown, cv)
        assert len(grounded) == 1
        assert grounded[0]["status"] == "MISSING"
        assert grounded[0]["supporting_evidence"] == ""
        assert "Unsupported LLM claim rejected" in grounded[0]["explanation"]

    def test_unsupported_claim_for_non_equivalent_tool_downgraded_to_partial(self):
        cv = "Deep learning engineer with 2 years of production experience in TensorFlow."
        hallucinated_breakdown = [
            {
                "requirement": "PyTorch",
                "category": "Critical Technical Skill",
                "importance": "Critical requirement",
                "status": "MATCHED",
                "supporting_evidence": "Extensive experience in PyTorch.",  # Hallucinated!
                "explanation": "Candidate is an expert in PyTorch."
            }
        ]
        grounded = verify_and_ground_llm_claims(hallucinated_breakdown, cv)
        assert len(grounded) == 1
        assert grounded[0]["status"] == "PARTIALLY MATCHED"
        assert "TensorFlow" in grounded[0]["candidate_evidence"]

    def test_fake_quote_substituted_with_exact_cv_passage(self):
        cv = "Experienced Python developer working with Django and Celery."
        llm_claim = [
            {
                "requirement": "Python",
                "category": "Critical Technical Skill",
                "importance": "Critical requirement",
                "status": "MATCHED",
                "supporting_evidence": "Lead Python Core Developer at Google for 10 years.",  # Fabricated quote!
                "explanation": "Candidate knows Python."
            }
        ]
        grounded = verify_and_ground_llm_claims(llm_claim, cv)
        assert len(grounded) == 1
        assert grounded[0]["status"] == "MATCHED"
        # The fabricated quote MUST be discarded in favor of genuine CV text
        assert "Google" not in grounded[0]["supporting_evidence"]
        assert "Python" in grounded[0]["supporting_evidence"]


class TestStructuredRequirementsAndScoring:
    """Tests the 5 structured requirement categories and weighted scoring preservation."""
    def test_job_extraction_contains_all_five_categories(self):
        from chain import Chain
        chain = Chain(api_key=None)  # Offline mode
        jobs = chain.extract_jobs("We are seeking a Backend Engineer with Python and Docker.")
        assert len(jobs) >= 1
        job = jobs[0]
        assert "critical_technical_skills" in job
        assert "preferred_technical_skills" in job
        assert "soft_skills" in job
        assert "experience_requirements" in job
        assert "educational_qualifications" in job

    def test_scoring_weights_65_25_10(self):
        from chain import audit_and_calculate_score
        # 1 critical full match, 1 preferred missing, 1 soft missing
        breakdown = [
            {"requirement": "Python", "category": "Critical Technical Skill", "status": "MATCHED"},
            {"requirement": "Redis", "category": "Preferred Technical Skill", "status": "MISSING"},
            {"requirement": "Teamwork", "category": "Soft Skill", "status": "MISSING"}
        ]
        meta = audit_and_calculate_score(breakdown)
        # Critical = 100% * 0.65 = 65 points
        assert meta["mathematical_score"] == 65

    def test_noise_excluded_from_scoring(self):
        from chain import audit_and_calculate_score
        breakdown = [
            {"requirement": "Python", "category": "Critical Technical Skill", "status": "MATCHED"},
            {"requirement": "Free snacks and ping pong table", "category": "Irrelevant/Noise", "status": "NOT RELEVANT"}
        ]
        meta = audit_and_calculate_score(breakdown)
        assert meta["critical_accuracy"]["percentage"] == 100.0
        assert meta["mathematical_score"] >= 95


class TestURLValidationAndSanitization:
    def test_valid_urls_accepted(self):
        assert is_valid_url("https://github.com/johndoe/microservices")
        assert is_valid_url("https://myportfolio.dev/projects/ml-engine")
        assert is_valid_url("http://gitlab.com/research/paper")

    def test_fake_placeholder_urls_rejected(self):
        assert not is_valid_url("https://github.com/candidate/project-name")
        assert not is_valid_url("https://github.com/username/project-name")
        assert not is_valid_url("https://example.com")
        assert not is_valid_url("https://github.com/profile")
        assert not is_valid_url("not_a_url")
        assert not is_valid_url("")

    def test_sanitize_extracted_portfolio_preserves_unlinked_projects(self):
        extracted = [
            {"Techstack": "Python, PyTorch", "Links": "https://github.com/candidate/project-name"},  # fake link
            {"Techstack": "React, TypeScript", "Links": "https://github.com/realuser/react-app"},     # real link
            {"Techstack": "Docker, Kubernetes", "Links": ""}                                          # unlinked project
        ]
        cleaned = sanitize_extracted_portfolio(extracted)
        assert len(cleaned) == 3
        # Fake link must be stripped to empty string without dropping the project
        assert cleaned[0]["Techstack"] == "Python, PyTorch"
        assert cleaned[0]["Links"] == ""
        # Real link is preserved
        assert cleaned[1]["Links"] == "https://github.com/realuser/react-app"
        # Unlinked project is preserved without inventing a fake URL
        assert cleaned[2]["Techstack"] == "Docker, Kubernetes"
        assert cleaned[2]["Links"] == ""

