import pytest
from chain import (
    find_cv_evidence,
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
