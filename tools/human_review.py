import pandas as pd
from datetime import datetime
from pathlib import Path

def save_human_review(
    claim_id,
    reviewer_action,
    reviewer_note="",
    output_path="data/human_reviews.csv"
):
    """
    Save the human review decision for a claim.
    """
    review = {
        "claim_id": claim_id,
        "reviewer_action": reviewer_action,
        "reviewer_note": reviewer_note,
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    output_file = Path(output_path)

    if output_file.exists():
        existing_reviews = pd.read_csv(output_file)
        updated_reviews = pd.concat(
            [existing_reviews, pd.DataFrame([review])],
            ignore_index=True
        )
    else:
        updated_reviews = pd.DataFrame([review])

    updated_reviews.to_csv(output_file, index=False)
    return review