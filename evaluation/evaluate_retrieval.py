"""Deterministic retrieval checks for the local synthetic-data prototype."""

from pathlib import Path
import sys

# Direct execution starts in evaluation/; make the existing tools importable.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.database_queries import get_member, get_policy, get_claim_context
from tools.rule_retriever import retrieve_relevant_rules


# SQL is for stored facts. Expected values are fixed, not copied from results.
# The method is assigned explicitly; this does not test automatic routing.
SQL_CASES = [
    {
        "case_id": "SQL01",
        "question": "What is member M003's first and last name?",
        "expected_method": "SQL",
        "lookup": get_member,
        "record_id": "M003",
        "expected_answer": {"first_name": "Mia", "last_name": "Patel"},
    },
    {
        "case_id": "SQL02",
        "question": "What is the status of policy P002?",
        "expected_method": "SQL",
        "lookup": get_policy,
        "record_id": "P002",
        "expected_answer": {"status": "Expired"},
    },
    {
        "case_id": "SQL03",
        "question": "What are policy P001's effective and expiration dates?",
        "expected_method": "SQL",
        "lookup": get_policy,
        "record_id": "P001",
        "expected_answer": {
            "effective_date": "2026-01-01", "expiration_date": "2026-12-31"
        },
    },
    {
        "case_id": "SQL04",
        "question": "What is the copay for policy P004?",
        "expected_method": "SQL",
        "lookup": get_policy,
        "record_id": "P004",
        "expected_answer": {"copay": "15"},
    },
    {
        "case_id": "SQL05",
        "question": "What are the claim amount and claim type for C003?",
        "expected_method": "SQL",
        "lookup": get_claim_context,
        "record_id": "C003",
        "expected_answer": {
            "claim_amount": "650.0", "claim_type": "Diagnostic Test"
        },
    },
]

# RAG is for rule text. Send the question itself to the existing retriever.
RAG_CASES = [
    {
        "case_id": "RAG01",
        "question": "What is the eligibility rule if the service date is before the policy effective date?",
        "expected_method": "RAG",
        "expected_keyword": "Rule 1 - Eligibility",
    },
    {
        "case_id": "RAG02",
        "question": "What happens if required information or a required document is missing?",
        "expected_method": "RAG",
        "expected_keyword": "Rule 2 - Missing Information",
    },
    {
        "case_id": "RAG03",
        "question": "What is the code review rule when diagnosis and procedure information appears inconsistent?",
        "expected_method": "RAG",
        "expected_keyword": "Rule 3 - Code Review",
    },
    {
        "case_id": "RAG04",
        "question": "What happens if a duplicate or unusual claim pattern is detected?",
        "expected_method": "RAG",
        "expected_keyword": "Rule 4 - Duplicate / Anomaly Review",
    },
    {
        "case_id": "RAG05",
        "question": "Does the AI assistant or a human reviewer make the final payment or denial decision?",
        "expected_method": "RAG",
        "expected_keyword": "Rule 5 - Human-in-the-Loop",
    },
]


def evaluate_retrieval():
    """Return all case records with actual answers and boolean pass results."""
    results = []
    for case in SQL_CASES + RAG_CASES:
        # Keep executable lookup settings out of the reported case record.
        result = {
            key: value for key, value in case.items()
            if key not in ("lookup", "record_id")
        }
        try:
            if case["expected_method"] == "SQL":
                record = case["lookup"](case["record_id"])
                actual = (
                    {field: record.get(field) for field in case["expected_answer"]}
                    if record is not None else None
                )
                passed = actual == case["expected_answer"]
            else:
                actual = retrieve_relevant_rules(case["question"])
                passed = case["expected_keyword"] in actual
            result.update(actual_answer=actual, passed=passed)
        except Exception as error:
            # A retrieval error counts as a failure, never a skipped success.
            result.update(actual_answer=None, passed=False, error=str(error))
        results.append(result)
    return results


def print_results(results):
    """Print answers for inspection, followed by the table and metrics."""
    for result in results:
        print(f"\n{result['case_id']}: {result['question']}")
        expected = result.get("expected_answer", result.get("expected_keyword"))
        print(f"Expected: {expected}")
        print(f"Actual: {result['actual_answer']}")
        if "error" in result:
            print(f"Error: {result['error']}")

    print("\nCase ID | Method | Passed")
    print("--------|--------|-------")
    for result in results:
        print(f"{result['case_id']} | {result['expected_method']} | {result['passed']}")

    total = len(results)
    passed = sum(result["passed"] for result in results)
    print(f"\nTotal evaluation cases: {total}")
    for method in ("SQL", "RAG"):
        cases = [result for result in results if result["expected_method"] == method]
        count = sum(result["passed"] for result in cases)
        print(f"{method} cases passed: {count} / {len(cases)}")
    print(f"Overall cases passed: {passed} / {total}")
    print(f"Overall accuracy: {100 * passed / total if total else 0:.1f}%")
    print("Accuracy covers these fixed synthetic cases, not automatic method selection.")


if __name__ == "__main__":
    print_results(evaluate_retrieval())
