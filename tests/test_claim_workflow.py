"""Check the workflow using existing local synthetic claims."""

from tools.claim_orchestrator import review_claim_workflow


def test_c001_passes_all_checks():
    # A clean claim is ready for the next processing step.
    result = review_claim_workflow("C001")

    assert result["workflow_status"] == "PASS"
    assert result["eligibility"]["status"] == "PASS"
    assert result["policy"]["status"] == "PASS"
    assert result["audit"]["status"] == "PASS"
    assert result["requires_human_review"] is False
    assert result["next_step"] == "Ready for the next processing step."


def test_c003_missing_information_requires_human_review():
    # Missing information should retrieve Rule 2 for the human reviewer.
    result = review_claim_workflow("C003")

    assert result["workflow_status"] == "FLAG"
    assert result["eligibility"]["status"] == "PASS"
    assert result["policy"]["status"] == "PASS"
    assert result["audit"]["status"] == "FLAG"
    assert result["audit"]["findings"][0]["type"] == "MISSING_INFORMATION"
    assert "Rule 2" in result["retrieved_rule"]
    assert result["requires_human_review"] is True
    assert result["next_step"] == "Human review required."


def test_c005_duplicate_claim_requires_human_review():
    # A duplicate claim should retrieve Rule 4 for the human reviewer.
    result = review_claim_workflow("C005")

    assert result["workflow_status"] == "FLAG"
    assert result["audit"]["status"] == "FLAG"
    assert result["audit"]["findings"][0]["type"] == "DUPLICATE_CLAIM"
    assert "Rule 4" in result["retrieved_rule"]
    assert result["requires_human_review"] is True
