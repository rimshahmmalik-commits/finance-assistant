import streamlit as st

from database.database import (
    get_business_settings,
    save_business_settings,
)


CURRENCIES = [
    "PKR",
    "USD",
    "GBP",
    "EUR",
    "AED",
    "SAR",
]

TIMEZONES = [
    "Asia/Karachi",
    "Asia/Dubai",
    "Asia/Riyadh",
    "Europe/London",
    "America/New_York",
    "America/Los_Angeles",
    "UTC",
]


def show_settings_page():
    st.title("Settings")

    st.caption(
        "Configure your business profile, invoice defaults "
        "and reminder preferences."
    )

    settings = get_business_settings()

    tab_profile, tab_invoices, tab_reminders = st.tabs(
        [
            "Business Profile",
            "Invoice Defaults",
            "Reminders",
        ]
    )

    # --------------------------------------------------
    # BUSINESS PROFILE
    # --------------------------------------------------

    with tab_profile:
        st.subheader("Business Profile")

        st.caption(
            "These details identify the business across "
            "your finance workspace."
        )

        with st.form("business_profile_form"):
            col1, col2 = st.columns(2)

            with col1:
                business_name = st.text_input(
                    "Business Name",
                    value=settings["business_name"],
                    placeholder="e.g. Atlas Trading Co."
                )

                email = st.text_input(
                    "Business Email",
                    value=settings["email"],
                    placeholder="accounts@company.com"
                )

            with col2:
                phone = st.text_input(
                    "Phone",
                    value=settings["phone"],
                    placeholder="+92 300 1234567"
                )

                timezone = st.selectbox(
                    "Timezone",
                    TIMEZONES,
                    index=(
                        TIMEZONES.index(settings["timezone"])
                        if settings["timezone"] in TIMEZONES
                        else 0
                    )
                )

            address = st.text_area(
                "Business Address",
                value=settings["address"],
                placeholder="City, province / state, country"
            )

            profile_saved = st.form_submit_button(
                "Save Business Profile",
                type="primary",
                use_container_width=True
            )

            if profile_saved:
                save_business_settings(
                    business_name,
                    email,
                    phone,
                    address,
                    settings["currency"],
                    timezone,
                    settings["payment_terms"],
                    settings["invoice_prefix"],
                    settings["tax_rate"],
                    settings["reminders_enabled"],
                    settings["reminder_days_before"],
                    settings["overdue_reminders_enabled"],
                )

                st.success("Business profile saved.")
                st.rerun()

    # --------------------------------------------------
    # INVOICE DEFAULTS
    # --------------------------------------------------

    with tab_invoices:
        st.subheader("Invoice Defaults")

        st.caption(
            "Set the defaults used when creating "
            "and presenting invoices."
        )

        with st.form("invoice_defaults_form"):
            col1, col2 = st.columns(2)

            with col1:
                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=(
                        CURRENCIES.index(settings["currency"])
                        if settings["currency"] in CURRENCIES
                        else 0
                    )
                )

                invoice_prefix = st.text_input(
                    "Invoice Prefix",
                    value=settings["invoice_prefix"],
                    max_chars=12,
                    placeholder="INV"
                )

            with col2:
                payment_terms = st.number_input(
                    "Default Payment Terms (days)",
                    min_value=0,
                    max_value=365,
                    value=int(settings["payment_terms"]),
                    step=1
                )

                tax_rate = st.number_input(
                    "Default Tax Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(settings["tax_rate"]),
                    step=0.5
                )

            st.info(
                "These defaults are saved now. During the interface "
                "pass we will connect them directly to invoice creation."
            )

            invoice_saved = st.form_submit_button(
                "Save Invoice Defaults",
                type="primary",
                use_container_width=True
            )

            if invoice_saved:
                prefix = invoice_prefix.strip().upper()

                if not prefix:
                    st.error("Invoice prefix cannot be empty.")

                else:
                    save_business_settings(
                        settings["business_name"],
                        settings["email"],
                        settings["phone"],
                        settings["address"],
                        currency,
                        settings["timezone"],
                        payment_terms,
                        prefix,
                        tax_rate,
                        settings["reminders_enabled"],
                        settings["reminder_days_before"],
                        settings["overdue_reminders_enabled"],
                    )

                    st.success("Invoice defaults saved.")
                    st.rerun()

    # --------------------------------------------------
    # REMINDERS
    # --------------------------------------------------

    with tab_reminders:
        st.subheader("Reminder Preferences")

        st.caption(
            "Control the default behavior of your "
            "collection reminder workflow."
        )

        with st.form("reminder_settings_form"):
            reminders_enabled = st.toggle(
                "Enable upcoming-payment reminders",
                value=settings["reminders_enabled"]
            )

            reminder_days_before = st.number_input(
                "Remind before due date (days)",
                min_value=0,
                max_value=30,
                value=int(settings["reminder_days_before"]),
                step=1,
                disabled=not reminders_enabled
            )

            overdue_reminders_enabled = st.toggle(
                "Enable overdue-payment reminders",
                value=settings["overdue_reminders_enabled"]
            )

            st.caption(
                "These preferences are stored now. Automated sending "
                "will later use them through the reminder automation layer."
            )

            reminder_saved = st.form_submit_button(
                "Save Reminder Preferences",
                type="primary",
                use_container_width=True
            )

            if reminder_saved:
                save_business_settings(
                    settings["business_name"],
                    settings["email"],
                    settings["phone"],
                    settings["address"],
                    settings["currency"],
                    settings["timezone"],
                    settings["payment_terms"],
                    settings["invoice_prefix"],
                    settings["tax_rate"],
                    reminders_enabled,
                    reminder_days_before,
                    overdue_reminders_enabled,
                )

                st.success("Reminder preferences saved.")
                st.rerun()