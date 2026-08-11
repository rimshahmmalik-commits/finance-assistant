import streamlit as st
import pandas as pd
from datetime import date

from database.database import (
    get_monthly_profit_and_loss,
    get_monthly_expense_breakdown,
    get_monthly_cash_flow,
    get_monthly_transaction_details,
)


MONTHS = {
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


def get_previous_month(year, month):
    if month == 1:
        return year - 1, 12

    return year, month - 1


def calculate_change(current, previous):
    if previous == 0:
        return None

    return (
        (current - previous)
        / abs(previous)
    ) * 100


def show_reports_page():

    st.title("Financial Reports")

    st.caption(
        "Review monthly profit, expenses and cash-flow performance."
    )

    today = date.today()

    # --------------------------------------------------
    # PERIOD SELECTOR
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        selected_month = st.selectbox(
            "Month",
            list(MONTHS.keys()),
            index=today.month - 1,
            format_func=lambda month: MONTHS[month]
        )

    with col2:
        selected_year = st.number_input(
            "Year",
            min_value=2020,
            max_value=2100,
            value=today.year,
            step=1
        )

    selected_year = int(
        selected_year
    )

    previous_year, previous_month = (
        get_previous_month(
            selected_year,
            selected_month
        )
    )

    # --------------------------------------------------
    # P&L
    # --------------------------------------------------

    current_report = (
        get_monthly_profit_and_loss(
            selected_year,
            selected_month
        )
    )

    previous_report = (
        get_monthly_profit_and_loss(
            previous_year,
            previous_month
        )
    )

    income = current_report["income"]
    expenses = current_report["expenses"]
    net_profit = current_report[
        "net_profit"
    ]

    income_change = calculate_change(
        income,
        previous_report["income"]
    )

    expense_change = calculate_change(
        expenses,
        previous_report["expenses"]
    )

    profit_change = calculate_change(
        net_profit,
        previous_report["net_profit"]
    )

    st.subheader(
        f"Profit & Loss — "
        f"{MONTHS[selected_month]} {selected_year}"
    )

    metric1, metric2, metric3 = (
        st.columns(3)
    )

    with metric1:

        delta = (
            f"{income_change:+.1f}% vs previous month"
            if income_change is not None
            else None
        )

        st.metric(
            "Income",
            f"PKR {income:,.2f}",
            delta=delta
        )

    with metric2:

        delta = (
            f"{expense_change:+.1f}% vs previous month"
            if expense_change is not None
            else None
        )

        st.metric(
            "Expenses",
            f"PKR {expenses:,.2f}",
            delta=delta,
            delta_color="inverse"
        )

    with metric3:

        delta = (
            f"{profit_change:+.1f}% vs previous month"
            if profit_change is not None
            else None
        )

        st.metric(
            "Net Profit / Loss",
            f"PKR {net_profit:,.2f}",
            delta=delta
        )

    if net_profit > 0:
        st.success(
            f"The business generated "
            f"PKR {net_profit:,.2f} in net profit "
            f"for this period."
        )

    elif net_profit < 0:
        st.error(
            f"The business recorded a net loss of "
            f"PKR {abs(net_profit):,.2f} "
            f"for this period."
        )

    else:
        st.info(
            "Income and expenses are currently equal "
            "for this period."
        )

    st.divider()

    # --------------------------------------------------
    # EXPENSE BREAKDOWN
    # --------------------------------------------------

    st.subheader(
        "Expense Breakdown"
    )

    expenses_by_category = (
        get_monthly_expense_breakdown(
            selected_year,
            selected_month
        )
    )

    if not expenses_by_category:

        st.info(
            "No expenses recorded for this month."
        )

    else:

        expense_df = pd.DataFrame(
            expenses_by_category
        )

        expense_df.columns = [
            "Category",
            "Amount"
        ]

        total_expense_value = (
            expense_df[
                "Amount"
            ].sum()
        )

        expense_df[
            "Share"
        ] = expense_df[
            "Amount"
        ].apply(
            lambda amount:
            (
                amount
                / total_expense_value
                * 100
            )
            if total_expense_value > 0
            else 0
        )

        display_expenses = (
            expense_df.copy()
        )

        display_expenses[
            "Amount"
        ] = display_expenses[
            "Amount"
        ].map(
            lambda value:
            f"PKR {value:,.2f}"
        )

        display_expenses[
            "Share"
        ] = display_expenses[
            "Share"
        ].map(
            lambda value:
            f"{value:.1f}%"
        )

        st.dataframe(
            display_expenses,
            width="stretch",
            hide_index=True
        )

        st.bar_chart(
            expense_df.set_index(
                "Category"
            )["Amount"]
        )

    st.divider()

    # --------------------------------------------------
    # MONTHLY CASH FLOW
    # --------------------------------------------------

    st.subheader(
        "Cash Flow Trend"
    )

    cash_flow = (
        get_monthly_cash_flow()
    )

    if not cash_flow:

        st.info(
            "No transaction history is available "
            "for cash-flow analysis yet."
        )

    else:

        cash_rows = []

        for row in cash_flow:

            month_value = row["month"]

            cash_rows.append({
                "Month": (
                    month_value.strftime(
                        "%Y-%m"
                    )
                    if hasattr(
                        month_value,
                        "strftime"
                    )
                    else str(
                        month_value
                    )[:7]
                ),
                "Income": row["income"],
                "Expenses": row["expenses"],
                "Net": row["net"],
            })

        cash_df = pd.DataFrame(
            cash_rows
        )

        st.line_chart(
            cash_df.set_index(
                "Month"
            )[
                [
                    "Income",
                    "Expenses",
                    "Net"
                ]
            ]
        )

        display_cash = (
            cash_df.copy()
        )

        for column in [
            "Income",
            "Expenses",
            "Net"
        ]:

            display_cash[
                column
            ] = display_cash[
                column
            ].map(
                lambda value:
                f"PKR {value:,.2f}"
            )

        st.dataframe(
            display_cash,
            width="stretch",
            hide_index=True
        )

    st.divider()

    # --------------------------------------------------
    # TRANSACTION DETAIL
    # --------------------------------------------------

    st.subheader(
        "Monthly Transaction Detail"
    )

    transaction_details = (
        get_monthly_transaction_details(
            selected_year,
            selected_month
        )
    )

    if not transaction_details:

        st.info(
            "No transactions recorded "
            "for this month."
        )

    else:

        detail_rows = []

        for transaction in (
            transaction_details
        ):

            detail_rows.append({
                "Date": transaction[0],
                "Type": transaction[1],
                "Description": transaction[2],
                "Amount": (
                    float(
                        transaction[3]
                        or 0
                    )
                ),
                "Category": transaction[4],
                "Account": transaction[5],
                "Reference": (
                    transaction[6]
                    or "—"
                ),
                "Source": transaction[7],
            })

        detail_df = pd.DataFrame(
            detail_rows
        )

        display_detail = (
            detail_df.copy()
        )

        display_detail[
            "Amount"
        ] = display_detail[
            "Amount"
        ].map(
            lambda value:
            f"PKR {value:,.2f}"
        )

        st.dataframe(
            display_detail,
            width="stretch",
            hide_index=True
        )