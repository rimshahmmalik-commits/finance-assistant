import streamlit as st

from utils.theme import apply_midnight_pro_theme

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
    layout="wide",
)


apply_midnight_pro_theme()


@st.cache_resource
def initialize_database():
    create_tables()
    return True


initialize_database()


# --------------------------------------------------
# NAVIGATION STATE
# --------------------------------------------------

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"


def navigate(page_name):
    st.session_state.current_page = page_name


def nav_button(label, page_name, icon=""):
    active = st.session_state.current_page == page_name

    button_label = f"{icon} {label}".strip()

    if st.sidebar.button(
        button_label,
        key=f"nav_{page_name}",
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        navigate(page_name)
        st.rerun()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 💼 Finance Assistant")
    st.caption("Business finance command center")

    st.divider()

    st.caption("OVERVIEW")
    nav_button("Dashboard", "Dashboard", "▦")

    st.caption("MONEY")
    nav_button("Invoices", "Invoices", "▤")
    nav_button("Transactions", "Transactions", "↔")
    nav_button("Clients", "Clients", "◉")

    st.caption("AUTOMATION")
    nav_button("Smart Import", "Smart Import", "⇩")
    nav_button("Reminders", "Reminder Center", "◷")

    st.caption("INTELLIGENCE")
    nav_button("AI Advisor", "AI Assistant", "✦")
    nav_button("Analytics", "Analytics", "⌁")

    st.divider()

    st.caption("WORKSPACE")
    nav_button("Settings", "Settings", "⚙")


page = st.session_state.current_page


# --------------------------------------------------
# PAGE ROUTING
# --------------------------------------------------

if page == "Dashboard":
    show_dashboard_page()

elif page == "Invoices":
    show_invoices_page()

elif page == "Transactions":
    show_transactions_page()

elif page == "Clients":
    show_clients_page()

elif page == "Smart Import":
    show_import_page()

elif page == "Reminder Center":
    show_reminders_page()

elif page == "Analytics":
    show_analytics_page()

elif page == "AI Assistant":
    st.title("AI Advisor")
    st.info(
        "The advisor page will be connected into the redesigned interface "
        "during the Midnight Pro pass."
    )

elif page == "Settings":
    show_settings_page()