def audit_claim(claim):
    """
    Perform basic rule-based checks on a synthetic claim.
    This is part of the student MVP.
    """

    findings = []

    if claim["required_document_missing"] == "Yes":
        findings.append({
            "type": "MISSING_INFORMATION",
            "reason": "A required document is missing.",
            "source": "Synthetic Claim Audit Rules - Rule 2"
        })

    if claim["duplicate_claim_flag"] == "Yes":
        findings.append({
            "type": "DUPLICATE_CLAIM",
            "reason": "This claim was flagged as a possible duplicate.",
            "source": "Synthetic Claim Audit Rules - Rule 4"
        })

    if claim["expected_case"] == "CODE_REVIEW_FLAG":
        findings.append({
            "type": "CODE_REVIEW",
            "reason": "Diagnosis and procedure information requires human review.",
            "source": "Synthetic Claim Audit Rules - Rule 3"
        })

    if not findings:
        return {
            "status": "PASS",
            "findings": [],
            "reason": "No audit flags were identified.",
            "source": "Synthetic Claim Audit Rules"
        }

    return {
        "status": "FLAG",
        "findings": findings,
        "reason": "One or more audit findings require human review."
    }