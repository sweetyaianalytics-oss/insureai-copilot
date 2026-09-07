import pandas as pd

def review_policy(member_id, policy_id, policies_path="data/policies.csv"):
    """
    Review basic policy information for a claim.
    """
    policies = pd.read_csv(policies_path)
    policy_match = policies[policies["policy_id"] == policy_id]

    if policy_match.empty:
        return {"status": "FLAG", "reason": "Policy not found."}

    policy = policy_match.iloc[0]

    if policy["member_id"] != member_id:
        return {"status": "FLAG", "reason": "Policy does not belong to this member."}

    return {
        "status": "PASS",
        "reason": "Policy belongs to the member.",
        "plan_name": policy["plan_name"],
        "policy_status": policy["status"],
        "effective_date": policy["effective_date"],
        "expiration_date": policy["expiration_date"],
        "copay": policy["copay"]
    }