import streamlit as st
import pandas as pd

from database.database import (
    get_invoice_management_data,
)

from ai.finance_ai import (
    generate_finance_insights,
    generate_collection_priorities,
)


def show_analytics_page():

    st.title("Analytics")

    st.caption(
        "Understand revenue, collections, risk and collection priorities."
    )

    invoices = get_invoice_management_data()

    if not invoices:
        st.info(
            "No invoice data available yet."
        )
        return

    # ==================================================
    # FINANCE INTELLIGENCE
    # ==================================================

    insights = generate_finance_insights(
        invoices
    )

    st.subheader("Finance Intelligence")

    for insight in insights:

        insight_type = insight["type"]
        title = insight["title"]
        message = insight["message"]

        content = (
            f"**{title}**\n\n"
            f"{message}"
        )

        if insight_type == "risk":
            st.error(content)

        elif insight_type == "warning":
            st.warning(content)

        elif insight_type == "success":
            st.success(content)

        else:
            st.info(content)

    st.divider()

    # ==================================================
    # COLLECTION PRIORITY ENGINE
    # ==================================================

    st.subheader("Collection Priorities")

    st.caption(
        "Invoices are ranked automatically by collection urgency."
    )

    priorities = generate_collection_priorities(
        invoices
    )

    if not priorities:

        st.success(
            "No outstanding invoices currently require collection action."
        )

    else:

        priority_rows = []

        for item in priorities:

            reasons = ", ".join(
                item["reasons"]
            )

            priority_rows.append({
                "Priority": item["priority"],
                "Score": item["score"],
                "Invoice": item["invoice_number"],
                "Client": item["client"],
                "Outstanding": (
                    f"PKR {item['outstanding']:,.2f}"
                ),
                "Payment Progress": (
                    f"{item['payment_progress']:.1f}%"
                ),
                "Days Overdue": (
                    item["days_overdue"]
                ),
                "Due Date": (
                    item["due_date"] or "—"
                ),
                "Why": reasons,
                "Recommended Action": (
                    item["action"]
                ),
            })

        st.dataframe(
            priority_rows,
            width="stretch",
            hide_index=True
        )

        top_priority = priorities[0]

        st.markdown(
            "#### Highest Collection Priority"
        )

        top_content = (
            f"**{top_priority['priority']} Priority — "
            f"{top_priority['invoice_number']}**\n\n"
            f"{top_priority['client']} currently has "
            f"PKR {top_priority['outstanding']:,.2f} outstanding.\n\n"
            f"**Priority score:** {top_priority['score']}/100\n\n"
            f"**Recommended action:** "
            f"{top_priority['action']}"
        )

        if top_priority["priority"] == "Critical":
            st.error(top_content)

        elif top_priority["priority"] == "High":
            st.warning(top_content)

        else:
            st.info(top_content)

    st.divider()

    # ==================================================
    # BUILD FINANCE DATAFRAME
    # ==================================================

    rows = []

    for invoice in invoices:

        invoice_number = invoice[0]
        client = invoice[1]
        amount = float(
            invoice[2] or 0
        )
        status = invoice[3]
        invoice_date = invoice[4]
        due_date = invoice[5]
        total_paid = float(
            invoice[6] or 0
        )

        outstanding = max(
            amount - total_paid,
            0
        )

        rows.append({
            "Invoice": invoice_number,
            "Client": client,
            "Amount": amount,
            "Paid": total_paid,
            "Outstanding": outstanding,
            "Status": status,
            "Invoice Date": invoice_date,
            "Due Date": due_date,
        })

    df = pd.DataFrame(
        rows
    )

    # ==================================================
    # CORE METRICS
    # ==================================================

    total_invoiced = (
        df["Amount"].sum()
    )

    total_paid = (
        df["Paid"].sum()
    )

    total_outstanding = (
        df["Outstanding"].sum()
    )

    overdue_amount = df.loc[
        df["Status"].str.lower()
        == "overdue",
        "Outstanding"
    ].sum()

    if total_invoiced > 0:

        collection_rate = (
            total_paid
            / total_invoiced
        ) * 100

    else:

        collection_rate = 0

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Total Invoiced",
            f"PKR {total_invoiced:,.2f}"
        )

    with col2:

        st.metric(
            "Collected",
            f"PKR {total_paid:,.2f}"
        )

    with col3:

        st.metric(
            "Outstanding",
            f"PKR {total_outstanding:,.2f}"
        )

    with col4:

        st.metric(
            "Collection Rate",
            f"{collection_rate:.1f}%"
        )

    st.divider()

    # ==================================================
    # COLLECTIONS RISK
    # ==================================================

    st.subheader(
        "Collections Risk"
    )

    risk1, risk2 = (
        st.columns(2)
    )

    with risk1:

        st.metric(
            "Overdue Amount",
            f"PKR {overdue_amount:,.2f}"
        )

    with risk2:

        overdue_count = len(
            df[
                df["Status"]
                .str.lower()
                == "overdue"
            ]
        )

        st.metric(
            "Overdue Invoices",
            overdue_count
        )

    st.divider()

    # ==================================================
    # CLIENT EXPOSURE
    # ==================================================

    st.subheader(
        "Outstanding by Client"
    )

    client_summary = (
        df.groupby(
            "Client",
            as_index=False
        )
        .agg({
            "Amount": "sum",
            "Paid": "sum",
            "Outstanding": "sum"
        })
        .sort_values(
            "Outstanding",
            ascending=False
        )
    )

    st.dataframe(
        client_summary,
        width="stretch",
        hide_index=True
    )

    st.bar_chart(
        client_summary
        .set_index(
            "Client"
        )["Outstanding"]
    )

    st.divider()

    # ==================================================
    # INVOICE STATUS
    # ==================================================

    st.subheader(
        "Invoice Status"
    )

    status_summary = (
        df.groupby(
            "Status"
        )
        .size()
        .reset_index(
            name="Invoices"
        )
    )

    st.dataframe(
        status_summary,
        width="stretch",
        hide_index=True
    )

    st.bar_chart(
        status_summary
        .set_index(
            "Status"
        )["Invoices"]
    )

    st.divider()

    # ==================================================
    # INVOICE TREND
    # ==================================================

    st.subheader(
        "Invoice Trend"
    )

    trend_df = (
        df.copy()
    )

    trend_df[
        "Invoice Date"
    ] = pd.to_datetime(
        trend_df[
            "Invoice Date"
        ],
        errors="coerce"
    )

    trend_df = (
        trend_df.dropna(
            subset=[
                "Invoice Date"
            ]
        )
    )

    if trend_df.empty:

        st.info(
            "Not enough dated invoice data "
            "for trend analysis yet."
        )

    else:

        monthly = (
            trend_df
            .groupby(
                trend_df[
                    "Invoice Date"
                ]
                .dt.to_period("M")
                .astype(str)
            )
            .agg({
                "Amount": "sum",
                "Paid": "sum"
            })
        )

        st.line_chart(
            monthly
        )

    st.divider()

    # ==================================================
    # FULL FINANCE TABLE
    # ==================================================

    st.subheader(
        "Finance Detail"
    )

    display_df = (
        df.copy()
    )

    display_df[
        "Amount"
    ] = display_df[
        "Amount"
    ].map(
        lambda x:
        f"PKR {x:,.2f}"
    )

    display_df[
        "Paid"
    ] = display_df[
        "Paid"
    ].map(
        lambda x:
        f"PKR {x:,.2f}"
    )

    display_df[
        "Outstanding"
    ] = display_df[
        "Outstanding"
    ].map(
        lambda x:
        f"PKR {x:,.2f}"
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )