"""Test the local API with synthetic claims, without starting a server."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    # TestClient sends requests directly to the app in this process.
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "ok"
    assert result["app"] == "InsureAI Copilot"


def test_c001_review_passes(client):
    response = client.get("/claims/C001/review")

    assert response.status_code == 200
    result = response.json()
    assert result["claim_id"] == "C001"
    assert result["eligibility"]["status"] == "PASS"
    assert result["policy"]["status"] == "PASS"
    assert result["audit"]["status"] == "PASS"


def test_c003_review_flags_missing_information(client):
    response = client.get("/claims/C003/review")

    assert response.status_code == 200
    result = response.json()
    assert result["claim_id"] == "C003"
    assert result["audit"]["status"] == "FLAG"
    assert result["audit"]["findings"][0]["type"] == "MISSING_INFORMATION"


def test_c003_workflow_requires_human_review(client):
    response = client.get("/claims/C003/workflow")

    assert response.status_code == 200
    result = response.json()
    assert result["claim_id"] == "C003"
    assert result["workflow_status"] == "FLAG"
    assert "Rule 2" in result["retrieved_rule"]
    assert result["requires_human_review"] is True
    assert result["next_step"] == "Human review required."


@pytest.mark.parametrize(
    "path",
    ["/claims/C999", "/claims/C999/review", "/claims/C999/workflow"],
)
def test_unknown_claim_returns_404(client, path):
    # Each claim endpoint should report a missing record consistently.
    response = client.get(path)

    assert response.status_code == 404
