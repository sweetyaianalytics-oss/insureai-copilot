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
.stApp, [data-testid="stAppViewContainer"] {background:#0D1927;color:#EAF4F6;}
.block-container {padding-top:2rem;padding-bottom:3rem;max-width:1100px;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4 {color:#F2FAFB;font-family:Arial,sans-serif;}
.stApp p,.stApp label,.stApp span {color:inherit;}
[data-testid="stMarkdownContainer"] p {color:#E0EBF0;}
[data-testid="stCaptionContainer"] {color:#A8BDC9;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
[data-baseweb="select"] > div,textarea,input {background:#192D3B!important;color:#F3FAFB!important;border-radius:10px!important;}
[data-baseweb="select"] span {color:#F3FAFB!important;}
.stButton > button {background:#167C70;color:white;border:1px solid #2AA995;border-radius:10px;font-weight:650;padding:.5rem 1rem;}
.stButton > button:hover {background:#209A89;color:white;border-color:#5DE1BE;}
[data-testid="stAlert"] {border-radius:12px;}
[data-testid="stMetric"] {background:linear-gradient(135deg,#192D3B,#1B3541);padding:23px 25px;border-radius:17px;border:1px solid #30505D;min-height:124px;}
[data-testid="stMetricLabel"] {color:#B8CBD3!important;font-size:14px!important;} [data-testid="stMetricValue"] {color:#F2FAFB!important;font-size:35px!important;font-weight:750!important;}
hr {border-color:#284454;margin:1.3rem 0;}
.claim-card {background:#192D3B;border:1px solid #284454;border-radius:14px;padding:1.1rem 1rem .8rem;height:100%;box-shadow:0 4px 16px rgba(0,0,0,.12);}
.claim-card h4 {margin:0 0 .9rem;color:#F2FAFB;font-size:1.08rem;font-weight:700;}
.claim-card .detail-row {display:flex;justify-content:space-between;align-items:center;gap:.8rem;padding:.5rem 0;border-bottom:1px solid #284454;}
.claim-card .detail-row:last-child {border-bottom:none;}
.claim-card .label {color:#A9BDCB;font-size:.9rem;font-weight:600;}
.claim-card .value {color:#F2FAFB;font-size:.92rem;font-weight:700;text-align:right;overflow-wrap:anywhere;}
@media(max-width:640px){.block-container{padding-left:1rem;padding-right:1rem}.claim-card{margin-bottom:12px}}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    """
<div style="padding:20px 22px;border-radius:16px;background:linear-gradient(120deg,#183C43,#192D3B 65%);border:1px solid #32635F;margin-bottom:28px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-size:30px;">🛡️</span>
    <div>
      <h1 style="color:#F2FAFB;margin:0;font-size:35px;">InsureAI Copilot</h1>
      <p style="color:#5DE1BE;margin:5px 0 0;font-size:14px;font-weight:600;">AI Assists. Humans Decide.</p>
    </div>
  </div>
  <p style="color:#A8BDC9;margin:14px 0 0;font-size:13px;">AI-Assisted Health Insurance Claims Review · Synthetic-data prototype</p>
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
    claim_ids,
    index=claim_ids.index("C003"),
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
# LIVE DASHBOARD SUMMARY (computed from synthetic claim records)
# ---------------------------------------------------------

def summarize_claims(ids):
    """Summarize the five demo claims without changing any review decisions."""
    total = passed = flagged = review_required = 0
    for claim_id in ids:
        record = get_claim(claim_id)
        if record is None:
            continue
        total += 1
        eligibility = check_member_eligibility(
            member_id=record["member_id"],
            policy_id=record["policy_id"],
            service_date=record["service_date"],
        )
        if not eligibility["eligible"]:
            flagged += 1
            review_required += 1
            continue
        policy = review_policy(
            member_id=record["member_id"], policy_id=record["policy_id"]
        )
        if policy["status"] != "PASS":
            flagged += 1
            review_required += 1
            continue
        result = audit_claim(record)
        if result["status"] == "PASS":
            passed += 1
        else:
            flagged += 1
            review_required += 1
    return total, passed, flagged, review_required


total_claims, passed_claims, flagged_claims, review_required_claims = summarize_claims(claim_ids)

st.markdown(
    '<div style="margin:10px 0 16px;">'
    '<div style="font-size:12px;letter-spacing:2px;color:#5DE1BE;font-weight:700;">CLAIMS OPERATIONS</div>'
    '<h2 style="margin:6px 0 4px;color:#F2FAFB;">Dashboard Overview</h2>'
    '<p style="color:#A8BDC9;">Real-time checks across five synthetic demonstration claims</p>'
    '</div>',
    unsafe_allow_html=True,
)
metric_left, metric_right = st.columns(2, gap="medium")
with metric_left:
    st.metric("Total Claims", f"{total_claims:02d}")
with metric_right:
    st.metric("Passed Checks", f"{passed_claims:02d}")
metric_left, metric_right = st.columns(2, gap="medium")
with metric_left:
    st.metric("Flagged Claims", f"{flagged_claims:02d}")
with metric_right:
    st.metric("Review Required", f"{review_required_claims:02d}")

st.markdown(
    '<div style="background:linear-gradient(110deg,#183C43,#192D3B);'
    'border:1px solid #32635F;border-radius:17px;padding:22px 25px;margin:20px 0 20px;">'
    '<div style="font-size:12px;letter-spacing:1.7px;color:#5DE1BE;font-weight:700;">WORKSPACE</div>'
    '<div style="font-weight:750;color:#F2FAFB;font-size:23px;margin-top:6px;">Claim Review</div>'
    '<div style="color:#B9CCD5;margin-top:8px;">Eligibility → Policy → Audit → Evidence → Human Decision</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# CLAIM DETAILS
# ---------------------------------------------------------

st.subheader("Selected Claim Details")

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

        review_status = "Passed Checks" if audit_result["status"] == "PASS" else "Needs Review"
        review_color = "#5DE1BE" if audit_result["status"] == "PASS" else "#F4BF65"
        audit_summary = "No audit flags" if audit_result["status"] == "PASS" else "Audit findings require human review"
        st.markdown(
            f'<div style="background:#192D3B;border:1px solid #284454;'
            f'border-radius:14px;padding:15px 20px;margin:12px 0;">'
            f'<strong style="color:#F2FAFB;">Claim {selected_claim_id}</strong>'
            f'<span style="float:right;color:{review_color};'
            f'font-weight:700;">{review_status}</span>'
            f'<div style="color:#A8BDC9;margin-top:8px;">'
            f'✓ Eligibility &amp; policy checks complete · '
            f'{audit_summary}'
            f'</div></div>',
            unsafe_allow_html=True,
        )


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
                        "Check the test app’s Streamlit secrets and API access. "
                        "Do not share API keys in screenshots."
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
