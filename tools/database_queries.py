"""Read claims, members, and policies from the local SQLite database."""

from pathlib import Path
from pprint import pprint
import sqlite3


def _fetch_one(query, parameters):
    """Return one row as a dictionary, or None when no record matches."""
    database_path = (
        Path(__file__).resolve().parent.parent / "data" / "insureai.db"
    )
    # Read-only mode prevents changes and never creates a missing database.
    connection = sqlite3.connect(f"{database_path.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        # Values are passed separately from the SQL using placeholders.
        row = connection.execute(query, parameters).fetchone()
        return dict(row) if row is not None else None
    finally:
        connection.close()


def get_claim(claim_id):
    """Return the matching claim dictionary, or None if it is not found."""
    return _fetch_one("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))


def get_member(member_id):
    """Return the matching member dictionary, or None if it is not found."""
    return _fetch_one("SELECT * FROM members WHERE member_id = ?", (member_id,))


def get_policy(policy_id):
    """Return the matching policy dictionary, or None if it is not found."""
    return _fetch_one("SELECT * FROM policies WHERE policy_id = ?", (policy_id,))


def get_claim_context(claim_id):
    """Return a claim with member and policy details, or None if not found."""
    # LEFT JOIN keeps the claim even if related data is missing (then None).
    # Unique column names prevent fields from overwriting each other.
    query = """
        SELECT
            c.*,
            m.first_name,
            m.last_name,
            m.dob,
            m.state,
            p.member_id AS policy_member_id,
            p.plan_name,
            p.effective_date,
            p.expiration_date,
            p.status AS policy_status,
            p.copay
        FROM claims AS c
        LEFT JOIN members AS m ON c.member_id = m.member_id
        LEFT JOIN policies AS p ON c.policy_id = p.policy_id
        WHERE c.claim_id = ?
    """
    return _fetch_one(query, (claim_id,))


if __name__ == "__main__":
    print("Claim context for C003:")
    pprint(get_claim_context("C003"), sort_dicts=False)
