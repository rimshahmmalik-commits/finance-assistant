import streamlit as st


def show_dashboard_page():
    st.title("Dashboard")
    st.caption("Overview of your finance operations.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Revenue", "PKR 0")

    with col2:
        st.metric("Invoices Sent", "0")

    with col3:
        st.metric("Pending", "0")

    with col4:
        st.metric("Overdue", "0")