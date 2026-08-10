import os
import json

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY was not found. Check your .env file."
    )

client = OpenAI(api_key=api_key)


def test_ai_connection():
    response = client.responses.create(
        model="gpt-5.4-mini",
        input=(
            "You are the AI engine inside a finance operations "
            "assistant. Reply with exactly: Finance AI connected"
        )
    )

    return response.output_text


def review_invoice_with_ai(
    invoice_number,
    client_name,
    amount,
    issue,
    risk_score
):
    """
    Reviews a suspicious invoice and returns an AI-generated
    explanation and recommended action.
    """

    prompt = f"""
You are an AI finance operations assistant.

A company's automatic invoice validation system has flagged
the following invoice for human review.

Invoice number: {invoice_number}
Client: {client_name}
Amount: PKR {amount:,.2f}
Risk score: {risk_score}/100
Detected issue: {issue}

Your job is NOT to approve, reject, pay, or modify the invoice.

Analyze why the detected issue may matter and recommend what
a finance employee should check before making a decision.

Return ONLY valid JSON using exactly this structure:

{{
    "summary": "short explanation",
    "recommendation": "specific action for the finance employee"
}}

Keep both values concise and professional.
"""

    try:
        response = client.responses.create(
            model="gpt-5.4-mini",
            input=prompt
        )

        result = response.output_text.strip()

        # Remove Markdown fences if the model ever adds them.
        if result.startswith("```"):
            result = result.replace("```json", "")
            result = result.replace("```", "")
            result = result.strip()

        data = json.loads(result)

        return {
            "summary": data.get(
                "summary",
                "AI analysis unavailable."
            ),
            "recommendation": data.get(
                "recommendation",
                "Review this invoice manually."
            )
        }

    except Exception as error:
        return {
            "summary": "AI analysis could not be completed.",
            "recommendation": "Review this invoice manually.",
            "error": str(error)
        }


if __name__ == "__main__":
    print(test_ai_connection())