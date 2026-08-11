from datetime import date
import os

from dotenv import load_dotenv

load_dotenv()


# ==================================================
# SMART IMPORT — INDIVIDUAL INVOICE REVIEW
# ==================================================

def review_invoice_with_ai(
    invoice_number,
    client_name,
    amount,
    issue,
    risk_score
):
    """
    Review a single invoice flagged by Smart Import.

    This currently uses deterministic finance logic so
    Smart Import works even without an external AI API.
    Later this function can be upgraded to an LLM call.
    """

    try:
        amount = float(amount or 0)
        risk_score = int(risk_score or 0)

        issue_text = str(issue or "").strip()
        issue_lower = issue_text.lower()

        # ----------------------------------------------
        # DETERMINE SEVERITY
        # ----------------------------------------------

        if risk_score >= 60:
            severity = "high"
        elif risk_score >= 20:
            severity = "medium"
        else:
            severity = "low"

        # ----------------------------------------------
        # GENERATE FINANCE REVIEW
        # ----------------------------------------------

        if "already exists" in issue_lower:

            summary = (
                f"Invoice {invoice_number} for {client_name} "
                f"appears to already exist in the finance system. "
                f"Creating it again could result in duplicate "
                f"billing or duplicate receivables."
            )

            recommendation = (
                "Compare this invoice with the existing database "
                "record and source document before approving it."
            )

        elif "duplicate invoice" in issue_lower:

            summary = (
                f"Invoice {invoice_number} appears more than once "
                f"in the uploaded finance data. This creates a "
                f"duplicate-processing risk."
            )

            recommendation = (
                "Verify which entry is correct and approve only "
                "one version of the invoice."
            )

        elif "missing invoice number" in issue_lower:

            summary = (
                f"An invoice for {client_name} worth "
                f"PKR {amount:,.2f} is missing its invoice number. "
                f"This prevents reliable tracking and reconciliation."
            )

            recommendation = (
                "Verify the source document and assign the correct "
                "invoice number before processing."
            )

        elif "missing client" in issue_lower:

            summary = (
                f"Invoice {invoice_number} worth "
                f"PKR {amount:,.2f} does not have a valid client "
                f"assigned."
            )

            recommendation = (
                "Identify the correct customer from the source "
                "document before approving this invoice."
            )

        elif (
            "invalid amount" in issue_lower
            or "greater than zero" in issue_lower
        ):

            summary = (
                f"Invoice {invoice_number} contains an invalid "
                f"financial amount. Processing it could distort "
                f"receivables and reporting."
            )

            recommendation = (
                "Verify the invoice total against the original "
                "document before approving."
            )

        elif "unusually high" in issue_lower:

            summary = (
                f"Invoice {invoice_number} for {client_name} is "
                f"PKR {amount:,.2f}, which is unusually high "
                f"relative to other invoices in this import."
            )

            recommendation = (
                "Check the amount against the purchase order, "
                "contract, or original invoice before approval."
            )

        else:

            summary = (
                f"Invoice {invoice_number} for {client_name} "
                f"has been flagged for {severity}-level review. "
                f"Detected issue: {issue_text or 'unspecified issue'}."
            )

            recommendation = (
                "Review the source invoice and supporting records "
                "before making a final approval decision."
            )

        return {
            "summary": summary,
            "recommendation": recommendation,
            "risk_level": severity,
        }

    except Exception as error:

        return {
            "summary": (
                "The finance reviewer could not complete "
                "this invoice analysis."
            ),
            "recommendation": (
                "Perform a manual review before processing "
                "this invoice."
            ),
            "error": str(error),
        }


# ==================================================
# ANALYTICS — PORTFOLIO FINANCE INSIGHTS
# ==================================================

def generate_finance_insights(invoices):
    """
    Analyse invoice data and generate
    finance/collection recommendations.
    """

    if not invoices:
        return []

    total_invoiced = 0
    total_paid = 0
    total_outstanding = 0

    client_outstanding = {}
    overdue_invoices = []

    today = date.today()

    for invoice in invoices:
        invoice_number = invoice[0]
        client = invoice[1]

        amount = float(invoice[2] or 0)
        due_date = invoice[5]
        paid = float(invoice[6] or 0)

        outstanding = max(
            amount - paid,
            0
        )

        total_invoiced += amount
        total_paid += paid
        total_outstanding += outstanding

        client_outstanding[client] = (
            client_outstanding.get(client, 0)
            + outstanding
        )

        # Detect overdue invoices using actual due date.
        if outstanding > 0 and due_date:

            try:
                parsed_due_date = (
                    due_date
                    if isinstance(due_date, date)
                    else date.fromisoformat(str(due_date))
                )

                if parsed_due_date < today:
                    overdue_invoices.append({
                        "invoice": invoice_number,
                        "client": client,
                        "amount": outstanding,
                        "due_date": parsed_due_date,
                    })

            except (ValueError, TypeError):
                pass

    insights = []

    # ----------------------------------------------
    # CASH POSITION
    # ----------------------------------------------

    if total_outstanding > 0:

        insights.append({
            "type": "warning",
            "title": "Outstanding Receivables",
            "message": (
                f"PKR {total_outstanding:,.2f} "
                f"is currently awaiting collection."
            )
        })

    # ----------------------------------------------
    # COLLECTION RATE
    # ----------------------------------------------

    if total_invoiced > 0:

        collection_rate = (
            total_paid / total_invoiced
        ) * 100

        if collection_rate < 40:

            insights.append({
                "type": "risk",
                "title": "Low Collection Rate",
                "message": (
                    f"Only {collection_rate:.1f}% of "
                    f"invoiced value has been collected."
                )
            })

        elif collection_rate < 80:

            insights.append({
                "type": "warning",
                "title": "Collections Need Attention",
                "message": (
                    f"Your current collection rate is "
                    f"{collection_rate:.1f}%."
                )
            })

        else:

            insights.append({
                "type": "success",
                "title": "Strong Collection Performance",
                "message": (
                    f"{collection_rate:.1f}% of invoiced "
                    f"value has been collected."
                )
            })

    # ----------------------------------------------
    # OVERDUE EXPOSURE
    # ----------------------------------------------

    overdue_total = sum(
        item["amount"]
        for item in overdue_invoices
    )

    if overdue_invoices:

        insights.append({
            "type": "risk",
            "title": "Overdue Exposure",
            "message": (
                f"{len(overdue_invoices)} invoice(s) "
                f"worth PKR {overdue_total:,.2f} "
                f"are past their due date."
            )
        })

    # ----------------------------------------------
    # CLIENT CONCENTRATION RISK
    # ----------------------------------------------

    if total_outstanding > 0 and client_outstanding:

        largest_client = max(
            client_outstanding,
            key=client_outstanding.get
        )

        largest_balance = (
            client_outstanding[largest_client]
        )

        concentration = (
            largest_balance / total_outstanding
        ) * 100

        if concentration >= 50:

            insights.append({
                "type": "risk",
                "title": "Client Concentration Risk",
                "message": (
                    f"{largest_client} represents "
                    f"{concentration:.1f}% of your "
                    f"outstanding receivables "
                    f"(PKR {largest_balance:,.2f})."
                )
            })

    # ----------------------------------------------
    # PRIORITY COLLECTION ACTION
    # ----------------------------------------------

    if overdue_invoices:

        priority = max(
            overdue_invoices,
            key=lambda x: x["amount"]
        )

        insights.append({
            "type": "action",
            "title": "Recommended Collection Action",
            "message": (
                f"Prioritize invoice "
                f"{priority['invoice']} for "
                f"{priority['client']}. "
                f"PKR {priority['amount']:,.2f} "
                f"remains unpaid."
            )
        })

    elif total_outstanding > 0 and client_outstanding:

        priority_client = max(
            client_outstanding,
            key=client_outstanding.get
        )

        priority_amount = (
            client_outstanding[priority_client]
        )

        insights.append({
            "type": "action",
            "title": "Recommended Action",
            "message": (
                f"Monitor {priority_client}, currently "
                f"your largest outstanding account at "
                f"PKR {priority_amount:,.2f}."
            )
        })

    return insights