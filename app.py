import streamlit as st

from database.database import create_tables

from views.dashboard import show_dashboard_page
from views.clients import show_clients_page
from views.invoices import show_invoices_page
from views.imports import show_import_page
from views.reminders import show_reminders_page
from views.analytics import show_analytics_page
from views.transactions import show_transactions_page
from views.settings import show_settings_page


st.set_page_config(
    page_title="Finance Assistant",
    page_icon="💼",
    layout="wide"
)


# Create any missing database tables.
create_tables()


st.sidebar.title("Finance Assistant")


page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Smart Import",
        "Clients",
        "Invoices",
        "Transactions",
        "Reminder Center",
        "Analytics",
        "AI Assistant",
        "Settings",
    ]
)


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

elif page == "Reminder Center":
    show_reminders_page()

elif page == "Analytics":
    show_analytics_page()

elif page == "AI Assistant":
    st.title("AI Assistant")
    st.info("Coming soon.")

elif page == "Settings":
    show_settings_page()