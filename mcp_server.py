"""Local MCP tools for the InsureAI synthetic-data prototype.

Run with: .venv/bin/python mcp_server.py
The MCP client communicates over standard input/output, not an HTTP port.
"""

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from tools.database_queries import get_claim_context as load_claim_context
from tools.eligibility_checker import check_member_eligibility
from tools.policy_reviewer import review_policy
from tools.claim_auditor import audit_claim
from tools.rule_retriever import retrieve_relevant_rules


mcp = FastMCP(
    "InsureAI Copilot",
    instructions=(
        "Use only this project's local synthetic data. These tools provide "
        "read-only context and review findings, not approvals, denials, or "
        "payment decisions. A human reviewer remains the final decision maker."
    ),
)
POLICIES_PATH = Path(__file__).resolve().parent / "data" / "policies.csv"
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _require_claim(claim_id: str) -> dict[str, Any]:
    # The existing query layer uses a read-only SQLite connection.
    claim = load_claim_context(claim_id)
    if claim is None:
        raise ValueError(f"Claim not found: {claim_id}")
    return claim


@mcp.tool(annotations=READ_ONLY)
def get_claim_context(claim_id: str) -> dict[str, Any]:
    """Get combined synthetic claim, member, and policy information."""
    return _require_claim(claim_id)


@mcp.tool(annotations=READ_ONLY)
def check_claim_eligibility(claim_id: str) -> dict[str, Any]:
    """Check member eligibility for a synthetic claim using existing rules."""
    claim = _require_claim(claim_id)
    return check_member_eligibility(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"],
        service_date=claim["service_date"],
        policies_path=POLICIES_PATH,
    )


@mcp.tool(annotations=READ_ONLY)
def review_claim_policy(claim_id: str) -> dict[str, Any]:
    """Review the synthetic claim's policy using the existing policy reviewer."""
    claim = _require_claim(claim_id)
    result = review_policy(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"],
        policies_path=POLICIES_PATH,
    )
    # Convert the CSV reader's numeric scalar for JSON serialization.
    if "copay" in result and hasattr(result["copay"], "item"):
        result["copay"] = result["copay"].item()
    return result


@mcp.tool(annotations=READ_ONLY)
def audit_insurance_claim(claim_id: str) -> dict[str, Any]:
    """Return existing audit findings; a human makes the final decision."""
    return audit_claim(_require_claim(claim_id))


@mcp.tool(annotations=READ_ONLY)
def retrieve_claim_rule(query: str) -> str:
    """Retrieve a local synthetic claim-review rule, or empty text if unmatched."""
    return retrieve_relevant_rules(query)


if __name__ == "__main__":
    # Keep stdout reserved for MCP protocol messages.
    mcp.run(transport="stdio")
