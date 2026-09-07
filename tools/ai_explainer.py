import os

from dotenv import load_dotenv
from openai import OpenAI

from tools.rule_retriever import retrieve_relevant_rules

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def explain_claim_finding(claim, findings):
    """
    Use OpenAI to explain claim findings in simple language.
    The AI does not make the final approve/deny decision.
    """

    findings_text = "\n".join(
        [
            f"- {finding['type']}: {finding['reason']} "
            f"(Source: {finding['source']})"
            for finding in findings
        ]
    )

    # Use the existing findings to look up a relevant local claim-review rule.
    query = findings_text
    retrieved_rule = retrieve_relevant_rules(query)

    prompt = f"""
You are an AI assistant for a student health insurance claims prototype.

Explain the following claim review findings in simple English
for a human claims reviewer.

Do not approve or deny the claim.
The human reviewer makes the final review and payment or denial decision.
Use only the provided claim information, findings, and retrieved rule.
Do not invent medical, coding, insurance, or payment rules.
Do not recommend actions that are not explicitly supported by the retrieved
rule or the provided claim information.
Do not invent workflow steps, contact instructions, provider actions,
patient actions, medical guidance, coding rules, insurance rules, or payment
decisions.
For "Suggested next step for the reviewer", do not generate examples,
possible actions, or workflow steps unless they are explicitly stated in
the retrieved rule.
If the retrieved rule does not specify a next action beyond human review,
the suggested next step must contain only this exact sentence:
"Review the flagged claim and determine the appropriate next action based on the identified finding and applicable review procedures."
Do not add examples such as contacting a provider or patient, obtaining
documents, requesting clarification, payment actions, denial actions, or
other dispositions unless those actions appear explicitly in the retrieved
knowledge.
If the retrieved rule is empty or does not support a finding, say so rather
than inventing a rule or explanation.

Claim ID: {claim['claim_id']}
Claim Type: {claim['claim_type']}
Claim Amount: {claim['claim_amount']}
Diagnosis Code: {claim['diagnosis_code']}
Procedure Code: {claim['procedure_code']}

Findings:
{findings_text}

Retrieved claim-review rule:
{retrieved_rule}

Give:
1. A short explanation
2. Why human review is needed
3. A suggested next step for the reviewer
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text
