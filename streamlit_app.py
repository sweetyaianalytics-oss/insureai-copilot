import pandas as pd
import streamlit as st

from tools.ai_explainer import explain_claim_finding
from tools.database_queries import get_claim, get_claim_context
from tools.eligibility_checker import check_member_eligibility
from tools.policy_reviewer import review_policy
from tools.claim_auditor import audit_claim
from tools.human_review import save_human_review
from tools.rule_retriever import retrieve_relevant_rules


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="InsureAI Copilot",
    page_icon="🛡️",
    layout="wide"
)


# ---------------------------------------------------------
# PROFESSIONAL UI STYLE
# ---------------------------------------------------------

st.markdown("""
<style>

/* Main app background */
.stApp {
    background: #f7f9fc;
}

/* Main page spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Section headings */
.stApp h1,
.stApp h2,
.stApp h3 {
    font-family: Arial, sans-serif;
    color: #17324d;
}

/* Normal text */
.stApp p,
.stApp label {
    color: #243447;
}

/* Select box */
[data-baseweb="select"] > div {
    border-radius: 10px;
}

/* Keep select-box text readable */
[data-baseweb="select"] span {
    color: white !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1rem;
}

/* Text area */
textarea {
    border-radius: 10px !important;
}

/* Alert/status boxes */
[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Divider */
hr {
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

/* Claim detail cards */
.claim-card {
    background: white;
    border: 1px solid #e3eaf2;
    border-radius: 14px;
    padding: 1.1rem 1rem 0.8rem;
    box-shadow: 0 4px 12px rgba(23, 50, 77, 0.08);
    height: 100%;
}

.claim-card h4 {
    margin: 0 0 0.9rem 0;
    color: #17324d;
    font-size: 1.1rem;
    font-weight: 700;
}

.claim-card .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.8rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #edf2f7;
}

.claim-card .detail-row:last-child {
    border-bottom: none;
}

.claim-card .label {
    color: #5c6878;
    font-size: 0.92rem;
    font-weight: 600;
}

.claim-card .value {
    color: #1f2d3d;
    font-size: 0.92rem;
    font-weight: 700;
    text-align: right;
    overflow-wrap: anywhere;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    """
<div style="padding:18px 22px; border-radius:12px; background:#17324d; margin-bottom:22px;">
<h1 style="color:white; margin:0; font-size:32px;">🛡️ InsureAI Copilot</h1>
<p style="color:white; margin:7px 0 0 0; font-size:16px;">AI-Assisted Health Insurance Claims Review</p>
<p style="color:#dbe7f0; margin:5px 0 0 0; font-size:13px;">Synthetic-data student prototype with human-in-the-loop review</p>
</div>
""",
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# LOAD CLAIM DATA
# ---------------------------------------------------------

claim_ids = ["C001", "C002", "C003", "C004", "C005"]

selected_claim_id = st.selectbox(
    "Select a Claim",
    claim_ids
)

claim_context = get_claim_context(selected_claim_id)
claim_record = get_claim(selected_claim_id)

if claim_context is None or claim_record is None:
    st.error("The selected claim was not found in the local database.")
    st.stop()

# Convert SQLite text values before creating the Series.
claim_data = {column: claim_context[column] for column in claim_record}
claim_data["claim_amount"] = float(claim_data["claim_amount"])
claim_data["procedure_code"] = int(claim_data["procedure_code"])

# Object dtype supports mixed numbers and text while preserving the original
# claim-only fields and Series shape used by the existing review flow.
claim = pd.Series(claim_data, dtype=object)


# ---------------------------------------------------------
# CLAIM DETAILS
# ---------------------------------------------------------

st.subheader("Claim Details")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class="claim-card">
            <h4>Claim Information</h4>
            <div class="detail-row"><span class="label">Claim ID</span><span class="value">{claim['claim_id']}</span></div>
            <div class="detail-row"><span class="label">Member ID</span><span class="value">{claim['member_id']}</span></div>
            <div class="detail-row"><span class="label">Policy ID</span><span class="value">{claim['policy_id']}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="claim-card">
            <h4>Service Information</h4>
            <div class="detail-row"><span class="label">Service Date</span><span class="value">{claim['service_date']}</span></div>
            <div class="detail-row"><span class="label">Claim Type</span><span class="value">{claim['claim_type']}</span></div>
            <div class="detail-row"><span class="label">Claim Amount</span><span class="value">${claim['claim_amount']}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="claim-card">
            <h4>Medical Coding</h4>
            <div class="detail-row"><span class="label">Diagnosis Code</span><span class="value">{claim['diagnosis_code']}</span></div>
            <div class="detail-row"><span class="label">Procedure Code</span><span class="value">{claim['procedure_code']}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# STEP 1 - MEMBER ELIGIBILITY
# ---------------------------------------------------------

st.subheader("1. Member Eligibility Check")

eligibility_result = check_member_eligibility(
    member_id=claim["member_id"],
    policy_id=claim["policy_id"],
    service_date=claim["service_date"]
)

if eligibility_result["eligible"]:
    st.success(eligibility_result["reason"])

else:
    st.error(eligibility_result["reason"])


# ---------------------------------------------------------
# CONTINUE ONLY IF MEMBER IS ELIGIBLE
# ---------------------------------------------------------

if eligibility_result["eligible"]:

    # -----------------------------------------------------
    # STEP 2 - POLICY REVIEW
    # -----------------------------------------------------

    st.subheader("2. Policy Review")

    policy_result = review_policy(
        member_id=claim["member_id"],
        policy_id=claim["policy_id"]
    )

    if policy_result["status"] == "PASS":

        st.success(policy_result["reason"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(
                "**Plan:**",
                policy_result["plan_name"]
            )

        with col2:
            st.write(
                "**Policy Status:**",
                policy_result["policy_status"]
            )

        with col3:
            st.write(
                "**Copay:**",
                f"${policy_result['copay']}"
            )


        # -------------------------------------------------
        # STEP 3 - CLAIM AUDIT
        # -------------------------------------------------

        st.subheader("3. Claim Audit")

        audit_result = audit_claim(claim)


        # ---------------------------------------------
        # CLAIM PASSES AUDIT
        # ---------------------------------------------

        if audit_result["status"] == "PASS":

            st.success(
                audit_result["reason"]
            )

            st.info(
                "Ready for the next processing step."
            )


        # ---------------------------------------------
        # CLAIM HAS AUDIT FINDINGS
        # ---------------------------------------------

        else:

            st.warning(
                audit_result["reason"]
            )

            # -----------------------------------------
            # STEP 4 - FINDINGS
            # -----------------------------------------

            st.subheader("4. Findings")

            for finding in audit_result["findings"]:

                st.write(
                    "**Flag:**",
                    finding["type"]
                )

                st.write(
                    "**Reason:**",
                    finding["reason"]
                )

                st.write(
                    "**Source:**",
                    finding["source"]
                )

                st.divider()


            # -----------------------------------------
            # RETRIEVED RAG SOURCE
            # -----------------------------------------

            # Match the findings query used by the AI explainer so the UI
            # shows the same local rule provided as grounding context.
            query = "\n".join(
                [
                    f"- {finding['type']}: {finding['reason']} "
                    f"(Source: {finding['source']})"
                    for finding in audit_result["findings"]
                ]
            )
            retrieved_rule = retrieve_relevant_rules(query)

            st.subheader("📚 Retrieved RAG Source")

            st.info(retrieved_rule or "No matching rule was found in the local claims knowledge base.")

            st.caption(
                "This rule was retrieved from the local claims knowledge base "
                "and is provided to the LLM as grounding context."
            )


            # -----------------------------------------
            # AI EXPLANATION
            # -----------------------------------------

            st.subheader("🤖 AI Explanation")

            st.caption(
                "The AI explains the audit findings. "
                "It does not make the final claim decision."
            )

            if st.button(
                "Generate AI Explanation",
                key="generate_ai_explanation"
            ):

                try:

                    with st.spinner(
                        "Generating explanation..."
                    ):

                        ai_explanation = explain_claim_finding(
                            claim=claim,
                            findings=audit_result["findings"]
                        )

                    st.write(ai_explanation)

                except Exception as error:

                    st.error(
                        "AI explanation is temporarily unavailable. "
                        "The rule-based claim findings are still available "
                        "for human review."
                    )

                    st.caption(
                        f"Technical message: {error}"
                    )


            # -----------------------------------------
            # STEP 5 - HUMAN REVIEW
            # -----------------------------------------

            st.subheader("5. Human Review")

            st.caption(
                "A human reviewer makes the final review decision."
            )

            reviewer_action = st.selectbox(
                "Reviewer Action",
                [
                    "ACCEPT_FLAG",
                    "REQUEST_MORE_INFORMATION",
                    "FURTHER_REVIEW"
                ],
                key="audit_reviewer_action"
            )

            reviewer_note = st.text_area(
                "Reviewer Note",
                key="audit_reviewer_note"
            )

            if st.button(
                "Save Human Review",
                key="save_audit_review"
            ):

                saved_review = save_human_review(
                    claim_id=claim["claim_id"],
                    reviewer_action=reviewer_action,
                    reviewer_note=reviewer_note
                )

                st.success(
                    "Human review saved successfully: "
                    f"{saved_review['reviewer_action']}"
                )


    # -----------------------------------------------------
    # POLICY REVIEW FAILED
    # -----------------------------------------------------

    else:

        st.error(
            policy_result["reason"]
        )


# ---------------------------------------------------------
# MEMBER IS NOT ELIGIBLE
# ---------------------------------------------------------

else:

    st.warning(
        "Claim review stopped because member eligibility failed."
    )

    st.subheader("Human Review")

    st.caption(
        "Eligibility issues require human review before "
        "the claim can continue."
    )

    reviewer_action = st.selectbox(
        "Reviewer Action",
        [
            "ACCEPT_FLAG",
            "REQUEST_MORE_INFORMATION",
            "FURTHER_REVIEW"
        ],
        key="eligibility_reviewer_action"
    )

    reviewer_note = st.text_area(
        "Reviewer Note",
        key="eligibility_reviewer_note"
    )

    if st.button(
        "Save Human Review",
        key="save_eligibility_review"
    ):

        saved_review = save_human_review(
            claim_id=claim["claim_id"],
            reviewer_action=reviewer_action,
            reviewer_note=reviewer_note
        )

        st.success(
            "Human review saved successfully: "
            f"{saved_review['reviewer_action']}"
        )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "InsureAI Copilot | Student prototype | Synthetic data only | "
    "Human-in-the-loop claim review"
)
