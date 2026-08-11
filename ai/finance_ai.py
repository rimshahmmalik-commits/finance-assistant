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


# ==================================================
# COLLECTION PRIORITY ENGINE
# ==================================================

def generate_collection_priorities(invoices):
    """Rank outstanding invoices by collection urgency."""

    if not invoices:
        return []

    today = date.today()
    priorities = []

    for invoice in invoices:
        invoice_number = invoice[0]
        client = invoice[1]
        amount = float(invoice[2] or 0)
        status = str(invoice[3] or "")
        due_date = invoice[5]
        total_paid = float(invoice[6] or 0)
        outstanding = max(amount - total_paid, 0)

        if outstanding <= 0:
            continue

        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = (
                    due_date if isinstance(due_date, date)
                    else date.fromisoformat(str(due_date))
                )
            except (ValueError, TypeError):
                pass

        days_overdue = 0
        days_until_due = None

        if parsed_due_date:
            difference = (parsed_due_date - today).days
            if difference < 0:
                days_overdue = abs(difference)
                days_until_due = 0
            else:
                days_until_due = difference

        score = 0
        reasons = []

        if days_overdue >= 30:
            score += 45
            reasons.append(f"{days_overdue} days overdue")
        elif days_overdue >= 14:
            score += 35
            reasons.append(f"{days_overdue} days overdue")
        elif days_overdue >= 7:
            score += 25
            reasons.append(f"{days_overdue} days overdue")
        elif days_overdue > 0:
            score += 15
            reasons.append(f"{days_overdue} days overdue")
        elif days_until_due is not None:
            if days_until_due == 0:
                score += 12
                reasons.append("Due today")
            elif days_until_due <= 3:
                score += 8
                reasons.append(f"Due in {days_until_due} day(s)")
            elif days_until_due <= 7:
                score += 4
                reasons.append(f"Due in {days_until_due} day(s)")

        if outstanding >= 500000:
            score += 35
            reasons.append("Very high outstanding balance")
        elif outstanding >= 250000:
            score += 28
            reasons.append("High outstanding balance")
        elif outstanding >= 100000:
            score += 20
            reasons.append("Significant outstanding balance")
        elif outstanding >= 50000:
            score += 12
            reasons.append("Moderate outstanding balance")
        else:
            score += 5

        payment_progress = (total_paid / amount * 100) if amount > 0 else 0

        if total_paid <= 0:
            score += 15
            reasons.append("No payment received")
        elif payment_progress < 50:
            score += 10
            reasons.append(f"Only {payment_progress:.1f}% collected")
        elif payment_progress < 100:
            score += 5
            reasons.append(f"{payment_progress:.1f}% collected")

        if status.lower() == "overdue":
            score += 5

        score = min(score, 100)

        if score >= 70:
            priority = "Critical"
        elif score >= 50:
            priority = "High"
        elif score >= 25:
            priority = "Medium"
        else:
            priority = "Low"

        if days_overdue >= 14:
            action = "Escalate collection follow-up and contact the client directly."
        elif days_overdue > 0:
            action = "Send an overdue payment reminder."
        elif days_until_due == 0:
            action = "Send a due-today reminder."
        elif days_until_due is not None and days_until_due <= 3:
            action = "Send a friendly upcoming-due reminder."
        elif outstanding >= 250000:
            action = "Monitor closely due to the high outstanding balance."
        else:
            action = "Continue standard collection monitoring."

        priorities.append({
            "invoice_number": invoice_number,
            "client": client,
            "invoice_amount": amount,
            "total_paid": total_paid,
            "outstanding": outstanding,
            "due_date": parsed_due_date.isoformat() if parsed_due_date else None,
            "days_overdue": days_overdue,
            "payment_progress": payment_progress,
            "score": score,
            "priority": priority,
            "reasons": reasons,
            "action": action,
        })

    priorities.sort(
        key=lambda item: (item["score"], item["outstanding"]),
        reverse=True
    )

    return priorities


def generate_cash_flow_forecast(
    transactions,
    invoices,
    forecast_days=30
):
    """
    Generate a cautious forward-looking cash-flow forecast.

    V1.1 adds data-quality safeguards:
    - Refuses to produce an operating forecast when history is too thin.
    - Returns Low / Medium / High confidence.
    - Separates projected operating activity from potential invoice collections.
    - Never treats invoice collections as guaranteed cash receipts.
    """

    today = date.today()

    # --------------------------------------------------
    # HISTORICAL CASH ACTIVITY
    # --------------------------------------------------

    historical_income = 0.0
    historical_expenses = 0.0
    valid_transaction_days = []
    valid_transaction_count = 0

    for transaction in transactions:

        try:
            transaction_date = transaction[1]
            transaction_type = str(
                transaction[2] or ""
            ).strip().lower()

            amount = float(
                transaction[4] or 0
            )

            if not isinstance(
                transaction_date,
                date
            ):
                transaction_date = (
                    date.fromisoformat(
                        str(transaction_date)
                    )
                )

        except (
            ValueError,
            TypeError,
            IndexError
        ):
            continue

        if transaction_type not in (
            "income",
            "expense"
        ):
            continue

        valid_transaction_count += 1

        valid_transaction_days.append(
            transaction_date
        )

        if transaction_type == "income":
            historical_income += amount

        elif transaction_type == "expense":
            historical_expenses += amount

    # --------------------------------------------------
    # HISTORY WINDOW
    # --------------------------------------------------

    if valid_transaction_days:

        earliest_date = min(
            valid_transaction_days
        )

        latest_date = max(
            valid_transaction_days
        )

        history_days = max(
            (latest_date - earliest_date).days + 1,
            1
        )

    else:

        history_days = 0

    # --------------------------------------------------
    # FORECAST CONFIDENCE
    # --------------------------------------------------

    warnings = []

    if (
        history_days >= 30
        and valid_transaction_count >= 20
    ):

        confidence = "High"
        forecast_available = True

    elif (
        history_days >= 7
        and valid_transaction_count >= 5
    ):

        confidence = "Medium"
        forecast_available = True

        warnings.append(
            "Forecast confidence is medium because "
            "the transaction history is still limited."
        )

    else:

        confidence = "Low"
        forecast_available = False

        warnings.append(
            "Not enough transaction history is available "
            "for a reliable operating cash-flow forecast."
        )

        warnings.append(
            "Add at least 7 days of history and 5 valid "
            "transactions before relying on operating projections."
        )

    # --------------------------------------------------
    # DAILY RUN RATE
    # --------------------------------------------------

    if history_days > 0:

        daily_income_rate = (
            historical_income
            / history_days
        )

        daily_expense_rate = (
            historical_expenses
            / history_days
        )

    else:

        daily_income_rate = 0.0
        daily_expense_rate = 0.0

    # --------------------------------------------------
    # PROJECT OPERATING ACTIVITY
    # --------------------------------------------------

    if forecast_available:

        projected_operating_income = (
            daily_income_rate
            * forecast_days
        )

        projected_operating_expenses = (
            daily_expense_rate
            * forecast_days
        )

    else:

        projected_operating_income = None
        projected_operating_expenses = None

    # --------------------------------------------------
    # POTENTIAL INVOICE COLLECTIONS
    # --------------------------------------------------

    forecast_end = (
        today
        + timedelta(
            days=forecast_days
        )
    )

    expected_collections = 0.0
    collection_candidates = []

    for invoice in invoices:

        try:
            invoice_number = invoice[0]
            client = invoice[1]

            invoice_amount = float(
                invoice[2] or 0
            )

            due_date = invoice[5]

            total_paid = float(
                invoice[6] or 0
            )

            outstanding = max(
                invoice_amount
                - total_paid,
                0
            )

            if outstanding <= 0:
                continue

            if not due_date:
                continue

            if not isinstance(
                due_date,
                date
            ):
                due_date = (
                    date.fromisoformat(
                        str(due_date)
                    )
                )

        except (
            ValueError,
            TypeError,
            IndexError
        ):
            continue

        if due_date <= forecast_end:

            expected_collections += (
                outstanding
            )

            collection_candidates.append({
                "invoice": invoice_number,
                "client": client,
                "amount": outstanding,
                "due_date": due_date,
            })

    collection_candidates.sort(
        key=lambda item: item["amount"],
        reverse=True
    )

    priority_collections = (
        collection_candidates[:3]
    )

    # --------------------------------------------------
    # FORECAST RESULT
    # --------------------------------------------------

    if forecast_available:

        projected_inflows = (
            projected_operating_income
            + expected_collections
        )

        projected_outflows = (
            projected_operating_expenses
        )

        projected_net_change = (
            projected_inflows
            - projected_outflows
        )

        if projected_net_change < 0:

            risk_level = "High"

        elif (
            projected_outflows > 0
            and projected_net_change
            < projected_outflows * 0.20
        ):

            risk_level = "Medium"

        else:

            risk_level = "Low"

    else:

        projected_inflows = None
        projected_outflows = None
        projected_net_change = None
        risk_level = "Insufficient Data"

    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------

    return {
        "forecast_days": forecast_days,

        "forecast_available":
            forecast_available,

        "confidence":
            confidence,

        "history_days":
            history_days,

        "transaction_count":
            valid_transaction_count,

        "historical_income":
            historical_income,

        "historical_expenses":
            historical_expenses,

        "daily_income_rate":
            daily_income_rate,

        "daily_expense_rate":
            daily_expense_rate,

        "projected_operating_income":
            projected_operating_income,

        "projected_operating_expenses":
            projected_operating_expenses,

        "expected_invoice_collections":
            expected_collections,

        "projected_inflows":
            projected_inflows,

        "projected_outflows":
            projected_outflows,

        "projected_net_change":
            projected_net_change,

        "risk_level":
            risk_level,

        "priority_collections":
            priority_collections,

        "forecast_end":
            forecast_end,

        "warnings":
            warnings,

        "assumptions": [
            (
                "Historical transaction activity is used "
                "to estimate operating income and expense run rates."
            ),
            (
                "Operating projections are only produced "
                "when the minimum history threshold is met."
            ),
            (
                "Outstanding invoices due within the forecast "
                "period are shown as potential collections."
            ),
            (
                "Potential invoice collections are not treated "
                "as guaranteed cash receipts."
            ),
            (
                "A projected closing bank balance is not shown "
                "because live account balances are not yet connected."
            ),
        ],
    }


# ==================================================
# FINANCIAL ADVISOR INTELLIGENCE
# ==================================================


def generate_advisor_intelligence(
    invoices,
    transactions=None
):
    """
    Turn verified invoice and transaction data into prioritized
    business risks and actions.

    This engine is deterministic: every financial figure comes
    directly from the supplied records. It does not invent values.
    """

    transactions = transactions or []
    today = date.today()

    total_invoiced = 0.0
    total_paid = 0.0
    total_outstanding = 0.0
    overdue_total = 0.0
    overdue_count = 0

    client_outstanding = {}
    overdue_items = []

    # --------------------------------------------------
    # RECEIVABLES
    # --------------------------------------------------

    for invoice in invoices or []:
        try:
            invoice_number = invoice[0]
            client = str(invoice[1] or "Unknown Client")
            amount = float(invoice[2] or 0)
            due_date = invoice[5]
            paid = float(invoice[6] or 0)
        except (IndexError, TypeError, ValueError):
            continue

        outstanding = max(amount - paid, 0)

        total_invoiced += amount
        total_paid += paid
        total_outstanding += outstanding

        if outstanding > 0:
            client_outstanding[client] = (
                client_outstanding.get(client, 0.0)
                + outstanding
            )

        if outstanding > 0 and due_date:
            try:
                parsed_due = (
                    due_date
                    if isinstance(due_date, date)
                    else date.fromisoformat(str(due_date))
                )
            except (TypeError, ValueError):
                parsed_due = None

            if parsed_due and parsed_due < today:
                days_overdue = (
                    today - parsed_due
                ).days

                overdue_count += 1
                overdue_total += outstanding

                overdue_items.append({
                    "invoice": invoice_number,
                    "client": client,
                    "outstanding": outstanding,
                    "days_overdue": days_overdue,
                    "due_date": parsed_due.isoformat(),
                })

    # --------------------------------------------------
    # TRANSACTION POSITION
    # --------------------------------------------------

    income = 0.0
    expenses = 0.0
    expense_categories = {}

    for transaction in transactions:
        try:
            transaction_type = str(
                transaction[2] or ""
            ).strip().lower()

            amount = float(
                transaction[4] or 0
            )

            category = str(
                transaction[5] or "Uncategorized"
            ).strip()

        except (IndexError, TypeError, ValueError):
            continue

        if transaction_type == "income":
            income += amount

        elif transaction_type == "expense":
            expenses += amount

            expense_categories[category] = (
                expense_categories.get(category, 0.0)
                + amount
            )

    net_cash_flow = income - expenses

    collection_rate = (
        (total_paid / total_invoiced) * 100
        if total_invoiced > 0
        else 0.0
    )

    risks = []

    # --------------------------------------------------
    # OVERDUE COLLECTION RISK
    # --------------------------------------------------

    if overdue_count > 0:
        severity = (
            "critical"
            if overdue_total >= 500000
            else "high"
        )

        risks.append({
            "severity": severity,
            "area": "Collections",
            "title": "Overdue receivables need attention",
            "message": (
                f"{overdue_count} invoice(s) worth "
                f"PKR {overdue_total:,.2f} are past due."
            ),
            "action": (
                "Contact the highest-value overdue customers first "
                "and confirm a payment date."
            ),
            "score": 95 if severity == "critical" else 80,
        })

    # --------------------------------------------------
    # COLLECTION PERFORMANCE
    # --------------------------------------------------

    if total_invoiced > 0 and collection_rate < 50:
        risks.append({
            "severity": "high",
            "area": "Collections",
            "title": "Collection performance is weak",
            "message": (
                f"Only {collection_rate:.1f}% of recorded "
                f"invoiced value has been collected."
            ),
            "action": (
                "Prioritize receivables follow-up before extending "
                "additional credit to slow-paying customers."
            ),
            "score": 78,
        })

    # --------------------------------------------------
    # CUSTOMER CONCENTRATION
    # --------------------------------------------------

    if total_outstanding > 0 and client_outstanding:
        top_client = max(
            client_outstanding,
            key=client_outstanding.get
        )

        top_balance = client_outstanding[
            top_client
        ]

        concentration = (
            top_balance
            / total_outstanding
            * 100
        )

        if concentration >= 50:
            risks.append({
                "severity": "high",
                "area": "Customer Risk",
                "title": "Receivables are concentrated",
                "message": (
                    f"{top_client} represents "
                    f"{concentration:.1f}% of outstanding "
                    f"receivables "
                    f"(PKR {top_balance:,.2f})."
                ),
                "action": (
                    "Reduce dependency on this single balance and "
                    "monitor its collection closely."
                ),
                "score": 75,
            })

    # --------------------------------------------------
    # CASH-FLOW PRESSURE
    # --------------------------------------------------

    if transactions and net_cash_flow < 0:
        risks.append({
            "severity": "high",
            "area": "Cash Flow",
            "title": "Recorded cash flow is negative",
            "message": (
                f"Recorded expenses exceed income by "
                f"PKR {abs(net_cash_flow):,.2f}."
            ),
            "action": (
                "Review the largest expenses and accelerate "
                "collection of outstanding invoices."
            ),
            "score": 85,
        })

    # --------------------------------------------------
    # EXPENSE CONCENTRATION
    # --------------------------------------------------

    if expenses > 0 and expense_categories:
        largest_category = max(
            expense_categories,
            key=expense_categories.get
        )

        largest_expense = expense_categories[
            largest_category
        ]

        expense_share = (
            largest_expense
            / expenses
            * 100
        )

        if expense_share >= 50:
            risks.append({
                "severity": "medium",
                "area": "Expenses",
                "title": "Spending is concentrated",
                "message": (
                    f"{largest_category} accounts for "
                    f"{expense_share:.1f}% of recorded expenses "
                    f"(PKR {largest_expense:,.2f})."
                ),
                "action": (
                    "Review this category for one-off entries, "
                    "pricing changes, duplicate costs, or savings."
                ),
                "score": 55,
            })

    # --------------------------------------------------
    # PRIORITY COLLECTION
    # --------------------------------------------------

    if overdue_items:
        overdue_items.sort(
            key=lambda item: (
                item["days_overdue"],
                item["outstanding"],
            ),
            reverse=True
        )

        top_overdue = overdue_items[0]

        risks.append({
            "severity": "action",
            "area": "Next Action",
            "title": "Collection action to take first",
            "message": (
                f"Invoice {top_overdue['invoice']} for "
                f"{top_overdue['client']} has "
                f"PKR {top_overdue['outstanding']:,.2f} "
                f"outstanding and is "
                f"{top_overdue['days_overdue']} day(s) overdue."
            ),
            "action": (
                "Contact this customer first and request a "
                "specific payment commitment."
            ),
            "score": 100,
        })

    elif total_outstanding > 0 and client_outstanding:
        top_client = max(
            client_outstanding,
            key=client_outstanding.get
        )

        risks.append({
            "severity": "action",
            "area": "Next Action",
            "title": "Largest collection opportunity",
            "message": (
                f"{top_client} currently has "
                f"PKR {client_outstanding[top_client]:,.2f} "
                f"outstanding."
            ),
            "action": (
                "Review the open invoices for this customer and "
                "schedule the appropriate collection follow-up."
            ),
            "score": 90,
        })

    # --------------------------------------------------
    # SORT + SUMMARY
    # --------------------------------------------------

    risks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    critical_count = sum(
        1
        for item in risks
        if item["severity"] == "critical"
    )

    high_count = sum(
        1
        for item in risks
        if item["severity"] == "high"
    )

    if critical_count:
        overall_status = "Critical"
    elif high_count:
        overall_status = "Needs Attention"
    elif risks:
        overall_status = "Monitor"
    else:
        overall_status = "Stable"

    return {
        "overall_status": overall_status,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "collection_rate": collection_rate,
        "overdue_total": overdue_total,
        "overdue_count": overdue_count,
        "income": income,
        "expenses": expenses,
        "net_cash_flow": net_cash_flow,
        "risks": risks,
        "top_priorities": risks[:3],
        "disclaimer": (
            "Recommendations are based only on recorded finance "
            "data and are decision support, not accounting, tax, "
            "legal, or banking advice."
        ),
    }