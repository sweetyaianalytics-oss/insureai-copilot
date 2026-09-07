from tools.eligibility_checker import check_member_eligibility

def test_active_policy():
    assert check_member_eligibility("M001", "P001", "2026-07-10")["eligible"] is True

def test_expired_policy():
    assert check_member_eligibility("M002", "P002", "2026-03-15")["eligible"] is False
