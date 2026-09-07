"""Retrieve claim-review rules locally using simple keyword matching."""

from pathlib import Path
import re


def retrieve_relevant_rules(query):
    """Return the rule with the most matching query words, or an empty string."""
    # Find the knowledge file relative to this script, so the current working
    # directory does not affect where we look for the rules.
    rules_path = (
        Path(__file__).resolve().parent.parent
        / "knowledge"
        / "claim_review_rules.txt"
    )
    rules_text = rules_path.read_text(encoding="utf-8")

    # Each rule starts with "Rule <number> -". Skip the introductory text and
    # keep each rule's heading together with its explanation.
    sections = re.split(r"(?m)(?=^Rule \d+\s*-)", rules_text)
    rules = [section.strip() for section in sections if section.startswith("Rule ")]

    # Lowercase words let "Missing" match "missing". Sets count each word only
    # once, and punctuation does not affect the match.
    query_words = set(re.findall(r"\b\w+\b", query.lower()))
    best_rule = ""
    best_score = 0

    for rule in rules:
        rule_words = set(re.findall(r"\b\w+\b", rule.lower()))
        score = len(query_words & rule_words)

        # Keep the rule with the most shared words. If scores tie, the first
        # matching rule wins. No shared words means we return an empty string.
        if score > best_score:
            best_rule = rule
            best_score = score

    return best_rule


if __name__ == "__main__":
    query = "required document missing human review"
    print(retrieve_relevant_rules(query))
