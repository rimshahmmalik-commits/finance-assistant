import streamlit as st

from database.database import create_tables

from views.dashboard import show_dashboard_page
from views.clients import show_clients_page
from views.invoices import show_invoices_page
from views.imports import show_import_page
from views.reminders import show_reminders_page
from views.analytics import show_analytics_page
from views.transactions import show_transactions_page
from views.reports import show_reports_page
from views.forecast import show_forecast_page

st.set_page_config(
    page_title="Finance Assistant",
    page_icon="💼",
    layout="wide"
)


# Create any missing database tables
create_tables()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Finance Assistant")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Smart Import",
        "Clients",
        "Invoices",
        "Transactions",
        "Reports",
        "Cash Flow Forecast",
        "Reminder Center",
        "Analytics",
        "AI Assistant",
        "Settings",
    ]
)


# --------------------------------------------------
# PAGE ROUTING
# --------------------------------------------------

if page == "Dashboard":
    show_dashboard_page()

elif page == "Smart Import":
    show_import_page()

elif page == "Clients":
    show_clients_page()

elif page == "Invoices":
    show_invoices_page()

elif page == "Transactions":
    show_transactions_page()

elif page == "Reports":
    show_reports_page()


elif page == "Cash Flow Forecast":
    show_forecast_page()


elif page == "Reminder Center":
    show_reminders_page()


elif page == "Analytics":
    show_analytics_page()


elif page == "AI Assistant":
    st.title("AI Assistant")
    st.info("Coming soon.")


elif page == "Settings":
    st.title("Settings")
    st.info("Coming soon.")