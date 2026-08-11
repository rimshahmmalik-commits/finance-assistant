import re
from datetime import date

import streamlit as st

from database.database import (
    get_financial_assistant_snapshot,
    get_spending_by_category,
    get_top_expenses,
    get_outstanding_customers,
    get_collection_priorities,
    get_monthly_financial_snapshot,
    get_invoice_management_data,
    get_transactions,
)

from ai.finance_ai import generate_advisor_intelligence


MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def money(value):
    return f"PKR {float(value or 0):,.2f}"


def detect_month_year(question):
    """
    Detect basic month/year wording such as:
    - this month
    - last month
    - August
    - August 2026
    """
    text = question.lower().strip()
    today = date.today()

    if "this month" in text:
        return today.year, today.month

    if "last month" in text:
        if today.month == 1:
            return today.year - 1, 12
        return today.year, today.month - 1

    month_lookup = {
        name.lower(): number
        for number, name in MONTH_NAMES.items()
    }

    for month_name, month_number in month_lookup.items():
        if month_name in text:
            year_match = re.search(r"\b(20\d{2})\b", text)
            year = int(year_match.group(1)) if year_match else today.year
            return year, month_number

    return None, None


def detect_category(question):
    text = question.lower()

    categories = [
        "Inventory",
        "Utilities",
        "Marketing",
        "Rent",
        "Payroll",
        "Salaries",
        "Transport",
        "Office",
        "Office Supplies",
        "Bank Fees",
        "Taxes",
        "Sales",
        "Services",
        "Other Income",
        "Other Expense",
        "Uncategorized",
    ]

    aliases = {
        "ads": "Marketing",
        "advertising": "Marketing",
        "electricity": "Utilities",
        "lesco": "Utilities",
        "fuel": "Transport",
        "petrol": "Transport",
        "salary": "Payroll",
        "wages": "Payroll",
        "stock": "Inventory",
        "supplier": "Inventory",
    }

    for alias, category in aliases.items():
        if alias in text:
            return category

    for category in categories:
        if category.lower() in text:
            return category

    return None


def answer_finance_question(question):
    """
    Deterministic natural-language query layer.

    It routes questions to verified database functions.
    It does not invent or calculate financial values itself.
    """
    clean_question = question.strip()

    if not clean_question:
        return {
            "title": "Ask a finance question",
            "answer": "Type a question about your business finances.",
            "data": None,
        }

    text = clean_question.lower()
    year, month = detect_month_year(clean_question)
    category = detect_category(clean_question)

    # --------------------------------------------------
    # CATEGORY SPENDING
    # --------------------------------------------------

    if (
        "spend" in text
        or "spent" in text
        or "expense" in text
        or "expenses" in text
    ) and category:

        rows = get_spending_by_category(
            category=category,
            year=year,
            month=month,
        )

        total = sum(
            row["amount"]
            for row in rows
        )

        if year and month:
            period = f"{MONTH_NAMES[month]} {year}"
        else:
            period = "all recorded periods"

        return {
            "title": f"{category} Spending",
            "answer": (
                f"You spent {money(total)} on {category} "
                f"during {period}."
            ),
            "data": rows,
        }

    # --------------------------------------------------
    # BIGGEST EXPENSES
    # --------------------------------------------------

    if (
        "biggest expense" in text
        or "largest expense" in text
        or "top expense" in text
        or "biggest spending" in text
    ):

        rows = get_top_expenses(
            limit=5,
            year=year,
            month=month,
        )

        if not rows:
            answer = "No matching expense transactions were found."
        else:
            answer = (
                f"Your largest recorded expense is "
                f"{money(rows[0]['amount'])} for "
                f"{rows[0]['description']}."
            )

        return {
            "title": "Largest Expenses",
            "answer": answer,
            "data": rows,
        }

    # --------------------------------------------------
    # WHO OWES ME MOST
    # --------------------------------------------------

    if (
        "who owes" in text
        or "owes me" in text
        or "largest customer balance" in text
        or "biggest debtor" in text
        or "outstanding customer" in text
    ):

        rows = get_outstanding_customers(
            limit=10
        )

        if not rows:
            answer = "No customers currently have an outstanding balance."
        else:
            top = rows[0]

            answer = (
                f"{top['client']} currently owes the most at "
                f"{money(top['outstanding'])} across "
                f"{top['open_invoice_count']} open invoice(s)."
            )

        return {
            "title": "Outstanding Customers",
            "answer": answer,
            "data": rows,
        }

    # --------------------------------------------------
    # COLLECTION PRIORITIES
    # --------------------------------------------------

    if (
        "chase" in text
        or "collect first" in text
        or "collection priority" in text
        or "which invoice" in text
        or "follow up" in text
    ):

        rows = get_collection_priorities(
            limit=5
        )

        if not rows:
            answer = "There are no unpaid invoices requiring collection."
        else:
            top = rows[0]

            overdue_text = (
                f" It is {top['days_overdue']} day(s) overdue."
                if top["days_overdue"] > 0
                else ""
            )

            answer = (
                f"Prioritize invoice {top['invoice_number']} for "
                f"{top['client']}. "
                f"{money(top['outstanding'])} remains outstanding."
                f"{overdue_text}"
            )

        return {
            "title": "Collection Priorities",
            "answer": answer,
            "data": rows,
        }

    # --------------------------------------------------
    # MONTHLY CASH FLOW / PROFIT
    # --------------------------------------------------

    if (
        "cash flow" in text
        or "net cash" in text
        or "profit" in text
        or "loss" in text
        or "income" in text
        or "revenue" in text
    ) and year and month:

        snapshot = get_monthly_financial_snapshot(
            year,
            month
        )

        return {
            "title": f"{MONTH_NAMES[month]} {year} Snapshot",
            "answer": (
                f"Income was {money(snapshot['income'])}, "
                f"expenses were {money(snapshot['expenses'])}, "
                f"and net cash flow was "
                f"{money(snapshot['net_cash_flow'])}."
            ),
            "data": snapshot,
        }

    # --------------------------------------------------
    # FINANCIAL ADVISOR INTELLIGENCE
    # --------------------------------------------------

    advisor_phrases = (
        "what should i worry",
        "what should i be worried",
        "what should i do first",
        "what should i do next",
        "give me advice",
        "advise me",
        "financial risk",
        "financial risks",
        "biggest risk",
        "biggest risks",
        "business risk",
        "business risks",
        "needs attention",
        "need attention",
        "what is wrong",
        "what's wrong",
        "priority right now",
        "priorities right now",
    )

    if any(phrase in text for phrase in advisor_phrases):
        invoices = get_invoice_management_data()
        transactions = get_transactions()

        advisor = generate_advisor_intelligence(
            invoices,
            transactions
        )

        priorities = advisor.get("top_priorities", [])

        if priorities:
            top = priorities[0]
            answer = (
                f"Overall status: {advisor['overall_status']}. "
                f"Your first priority is {top['title'].lower()}. "
                f"{top['message']} "
                f"Recommended action: {top['action']}"
            )
        else:
            answer = (
                "No major rule-based financial warning is currently "
                "detected from the recorded data."
            )

        return {
            "title": "Financial Advisor",
            "answer": answer,
            "data": advisor,
            "advisor": True,
        }

    # --------------------------------------------------
    # CURRENT BUSINESS SNAPSHOT
    # --------------------------------------------------

    if (
        "overview" in text
        or "snapshot" in text
        or "how am i doing" in text
        or "financial position" in text
        or "current position" in text
        or "current risk" in text
        or "risks" in text
    ):

        snapshot = get_financial_assistant_snapshot()

        answer = (
            f"Recorded income is {money(snapshot['income'])}, "
            f"expenses are {money(snapshot['expenses'])}, "
            f"net cash flow is {money(snapshot['net_cash_flow'])}, "
            f"and {money(snapshot['total_outstanding'])} is still "
            f"outstanding from customers."
        )

        if snapshot["overdue_invoice_count"] > 0:
            answer += (
                f" There are {snapshot['overdue_invoice_count']} "
                f"overdue invoice(s)."
            )

        return {
            "title": "Financial Snapshot",
            "answer": answer,
            "data": snapshot,
        }

    # --------------------------------------------------
    # OUTSTANDING TOTAL
    # --------------------------------------------------

    if (
        "outstanding" in text
        or "receivable" in text
        or "unpaid" in text
    ):

        snapshot = get_financial_assistant_snapshot()

        return {
            "title": "Outstanding Receivables",
            "answer": (
                f"Customers currently owe "
                f"{money(snapshot['total_outstanding'])}."
            ),
            "data": snapshot,
        }

    return {
        "title": "I need a more specific finance question",
        "answer": (
            "Try asking about spending by category, biggest expenses, "
            "who owes you money, which invoices to chase, monthly cash flow, "
            "or your overall financial position."
        ),
        "data": None,
    }


def show_ai_assistant_page():
    st.title("AI Financial Assistant")

    st.caption(
        "Ask questions about your business finances. "
        "Every PKR figure is pulled from verified database calculations."
    )

    st.info(
        "This V1 uses a controlled finance-query engine rather than "
        "free-form generative answers, so it won't invent financial figures."
    )

    suggestions = [
        "How much did I spend on marketing this month?",
        "What are my biggest expenses?",
        "Who owes me the most money?",
        "Which invoices should I chase first?",
        "What is my cash flow this month?",
        "Give me a financial overview.",
        "What should I worry about?",
        "What should I do first?",
        "Give me advice based on my business numbers.",
    ]

    with st.expander(
        "Example questions",
        expanded=False
    ):
        for item in suggestions:
            st.write(f"• {item}")

    if "assistant_history" not in st.session_state:
        st.session_state["assistant_history"] = []

    question = st.chat_input(
        "Ask about spending, customers, invoices, cash flow..."
    )

    if question:
        result = answer_finance_question(
            question
        )

        st.session_state[
            "assistant_history"
        ].append({
            "question": question,
            "result": result,
        })

    for message in st.session_state[
        "assistant_history"
    ]:

        with st.chat_message("user"):
            st.write(
                message["question"]
            )

        result = message["result"]

        with st.chat_message("assistant"):
            st.markdown(
                f"**{result['title']}**"
            )

            st.write(
                result["answer"]
            )

            data = result.get(
                "data"
            )

            if result.get("advisor") and isinstance(data, dict):
                priorities = data.get("top_priorities", [])

                if priorities:
                    st.markdown("#### Priority Actions")

                    for index, priority in enumerate(priorities, start=1):
                        severity = priority.get(
                            "severity",
                            "medium"
                        ).upper()

                        st.markdown(
                            f"**{index}. {priority['title']} — {severity}**"
                        )
                        st.write(priority["message"])
                        st.caption(
                            f"Recommended action: {priority['action']}"
                        )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Outstanding",
                        money(data.get("total_outstanding", 0))
                    )

                with col2:
                    st.metric(
                        "Collection Rate",
                        f"{float(data.get('collection_rate', 0)):.1f}%"
                    )

                with col3:
                    st.metric(
                        "Net Cash Flow",
                        money(data.get("net_cash_flow", 0))
                    )

                with st.expander("Verified data used"):
                    st.json(data)

                disclaimer = data.get("disclaimer")
                if disclaimer:
                    st.caption(disclaimer)

            elif isinstance(data, list) and data:
                st.dataframe(
                    data,
                    width="stretch",
                    hide_index=True
                )

            elif isinstance(data, dict) and data:
                with st.expander(
                    "Verified data used"
                ):
                    st.json(data)