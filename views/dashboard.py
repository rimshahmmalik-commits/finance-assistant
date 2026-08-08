import streamlit as st
from database.database import get_invoices


def show_dashboard_page():
    st.title("Dashboard")
    st.caption("Overview of your finance operations.")

    invoices = get_invoices()

    invoice_count = len(invoices)

    pending_count = 0
    overdue_count = 0
    total_revenue = 0

    for invoice in invoices:
        amount = invoice[2]
        status = invoice[3].strip().lower()

        if status == "pending":
            pending_count += 1

        elif status == "overdue":
            overdue_count += 1

        elif status == "paid":
            total_revenue += amount

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Revenue",
            f"PKR {total_revenue:,.2f}"
        )

    with col2:
        st.metric(
            "Invoices Sent",
            invoice_count
        )

    with col3:
        st.metric(
            "Pending",
            pending_count
        )

    with col4:
        st.metric(
            "Overdue",
            overdue_count
        )