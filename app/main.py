"""Read-only API for InsureAI Copilot claim information and review results."""

from pathlib import Path

from fastapi import FastAPI, HTTPException

from tools.database_queries import get_claim_context
from tools.eligibility_checker import check_member_eligibility
from tools.policy_reviewer import review_policy
from tools.claim_auditor import audit_claim
from tools.claim_orchestrator import review_claim_workflow


app = FastAPI(title="InsureAI Copilot")

# The existing eligibility and policy tools still read the local policy CSV.
POLICIES_PATH = Path(__file__).resolve().parent.parent / "data" / "policies.csv"


def _get_claim_or_404(claim_id):
    """Load the joined record, or report that the claim does not exist."""
    claim = get_claim_context(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@app.get("/health")
def health():
    return {"status": "ok", "app": "InsureAI Copilot"}


@app.get("/claims/{claim_id}")
def read_claim(claim_id: str):
    # The query layer opens SQLite in read-only mode.
    return _get_claim_or_404(claim_id)


@app.get("/claims/{claim_id}/review")
def review_claim(claim_id: str):
    claim = _get_claim_or_404(claim_id)

    # Reuse all three checks without changing their rules or saving results.
    eligibility_result = check_member_eligibility(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"],
        service_date=claim["service_date"],
        policies_path=POLICIES_PATH,
    )
    policy_result = review_policy(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"],
        policies_path=POLICIES_PATH,
    )
    audit_result = audit_claim(claim)

    # Convert the Pandas/NumPy copay scalar to a JSON-compatible Python number.
    if "copay" in policy_result and hasattr(policy_result["copay"], "item"):
        policy_result["copay"] = policy_result["copay"].item()

    return {
        "claim_id": claim["claim_id"],
        "eligibility": eligibility_result,
        "policy": policy_result,
        "audit": audit_result,
    }


@app.get("/claims/{claim_id}/workflow")
def read_claim_workflow(claim_id: str):
    # Run the read-only workflow and return all of its result fields.
    result = review_claim_workflow(claim_id)
    if result["workflow_status"] == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Claim not found")
    return result
