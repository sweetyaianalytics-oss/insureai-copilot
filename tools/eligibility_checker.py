import pandas as pd

def check_member_eligibility(member_id, policy_id, service_date, policies_path="data/policies.csv"):
    policies = pd.read_csv(policies_path)
    match = policies[(policies["member_id"] == member_id) & (policies["policy_id"] == policy_id)]

    if match.empty:
        return {"eligible": False, "status": "FLAG", "reason": "Policy not found for this member."}

    policy = match.iloc[0]
    service_date = pd.to_datetime(service_date)
    effective_date = pd.to_datetime(policy["effective_date"])
    expiration_date = pd.to_datetime(policy["expiration_date"])

    if service_date < effective_date:
        return {"eligible": False, "status": "FLAG", "reason": "Service date is before the policy effective date."}

    if service_date > expiration_date:
        return {"eligible": False, "status": "FLAG", "reason": "Policy was expired on the service date."}

    return {"eligible": True, "status": "PASS", "reason": "Policy was active on the service date."}
