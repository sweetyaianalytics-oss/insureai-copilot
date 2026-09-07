"""Coordinate local claim checks without making final claim decisions."""

from pathlib import Path
from pprint import pprint
import sys

# Allow this file to run directly as well as be imported as a module.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.database_queries import get_claim
from tools.eligibility_checker import check_member_eligibility
from tools.policy_reviewer import review_policy
from tools.claim_auditor import audit_claim
from tools.rule_retriever import retrieve_relevant_rules


def review_claim_workflow(claim_id):
    """Return review results; skipped checks remain None."""
    result = {
        "claim_id": claim_id,
        "workflow_status": "NOT_FOUND",
        "eligibility": None,
        "policy": None,
        "audit": None,
        "retrieved_rule": "",
        "requires_human_review": True,
        "next_step": "Claim not found. Verify the claim ID.",
    }
    claim = get_claim(claim_id)
    if claim is None:
        return result

    # Existing checks use the local policy CSV; keep their rules unchanged.
    policies_path = PROJECT_ROOT / "data" / "policies.csv"
    result["eligibility"] = check_member_eligibility(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"],
        service_date=claim["service_date"],
        policies_path=policies_path,
    )
    result["workflow_status"] = "FLAG"
    result["next_step"] = "Human review required."

    # Stop here when eligibility fails; policy and audit stay unrun.
    if not result["eligibility"]["eligible"]:
        return result

    result["policy"] = review_policy(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"],
        policies_path=policies_path,
    )
    # Convert the CSV reader's numeric scalar to a plain Python number.
    if "copay" in result["policy"] and hasattr(result["policy"]["copay"], "item"):
        result["policy"]["copay"] = result["policy"]["copay"].item()

    if result["policy"]["status"] != "PASS":
        return result

    result["audit"] = audit_claim(claim)
    if result["audit"]["status"] == "PASS":
        result["workflow_status"] = "PASS"
        result["requires_human_review"] = False
        result["next_step"] = "Ready for the next processing step."
        return result

    # Retrieve supporting knowledge only for flagged audit findings.
    if result["audit"]["status"] == "FLAG":
        query = "\n".join(
            f"- {finding['type']}: {finding['reason']} "
            f"(Source: {finding['source']})"
            for finding in result["audit"]["findings"]
        )
        result["retrieved_rule"] = retrieve_relevant_rules(query)

    return result


if __name__ == "__main__":
    for claim_id in ("C001", "C003"):
        print(f"Workflow result for {claim_id}:")
        pprint(review_claim_workflow(claim_id), sort_dicts=False)
        print()
