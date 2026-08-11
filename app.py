import streamlit as st
from views.reminders import show_reminders_page

from database.database import (
    create_tables,
    create_invoice_table
)

from views.dashboard import show_dashboard_page
from views.clients import show_clients_page
from views.invoices import show_invoices_page
from views.imports import show_import_page


st.set_page_config(
    page_title="Finance Assistant",
    page_icon="💼",
    layout="wide"
)

create_tables()
create_invoice_table()


st.sidebar.title("Finance Assistant")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Smart Import",
        "Clients",
        "Invoices",
        "Reminder Center",
        "Analytics",
        "AI Assistant",
        "Settings"
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

elif page == "Analytics":
    st.title("Analytics")
    st.info("Coming soon.")

elif page == "AI Assistant":
    st.title("AI Assistant")
    st.info("Coming soon.")

elif page == "Settings":
    st.title("Settings")
    st.info("Coming soon.")

elif page == "Reminder Center":
    show_reminders_page()