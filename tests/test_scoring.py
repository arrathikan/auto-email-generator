import pytest
from chain import audit_and_calculate_score

class TestDeterministicScoring:
    def test_full_match_scores_high(self):
        evidence = [
            {"requirement": "Python", "importance": "Critical requirement", "status": "MATCHED"},
            {"requirement": "FastAPI", "importance": "Critical requirement", "status": "MATCHED"},
            {"requirement": "Docker", "importance": "Preferred requirement", "status": "MATCHED"},
            {"requirement": "Communication", "importance": "Soft skill", "status": "MATCHED"},
        ]
        res = audit_and_calculate_score(evidence)
        assert res["mathematical_score"] >= 90
        assert "Outstanding Alignment" in res["fit_level"]
        assert res["critical_accuracy"]["matched"] == 2
        assert res["critical_accuracy"]["missing"] == 0

    def test_partial_match_gives_half_credit(self):
        evidence = [
            {"requirement": "Python", "importance": "Critical requirement", "status": "PARTIALLY MATCHED"},
            {"requirement": "FastAPI", "importance": "Critical requirement", "status": "MISSING"}
        ]
        res = audit_and_calculate_score(evidence)
        # 1 partial out of 2 = 0.5 / 2 = 25% critical score
        assert res["critical_accuracy"]["percentage"] == 25.0
        assert res["critical_accuracy"]["partial"] == 1
        assert res["critical_accuracy"]["missing"] == 1

    def test_noise_excluded_from_weighting(self):
        evidence_with_noise = [
            {"requirement": "Python", "importance": "Critical requirement", "status": "MATCHED"},
            {"requirement": "Marine biology expertise", "importance": "Irrelevant/Noise", "status": "NOT RELEVANT"}
        ]
        res = audit_and_calculate_score(evidence_with_noise)
        # The critical requirement is 100% matched; noise must not drag the score down
        assert res["critical_accuracy"]["percentage"] == 100.0
        assert res["mathematical_score"] >= 95

    def test_empty_requirements_safe_fallback(self):
        res = audit_and_calculate_score([])
        assert res["mathematical_score"] == 50
        assert "fit_level" in res
