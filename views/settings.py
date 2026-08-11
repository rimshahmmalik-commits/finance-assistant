import streamlit as st

from database.database import (
    BUSINESS_TYPES,
    get_business_settings,
    save_business_settings,
    ensure_business_categories,
    get_business_categories,
    add_business_category,
    update_business_category,
    delete_business_category,
    reset_business_categories_to_industry_defaults,
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
        "Configure your business profile, finance defaults, "
        "categories and reminder preferences."
    )

    settings = get_business_settings()

    ensure_business_categories(
        settings["business_type"]
    )

    (
        tab_profile,
        tab_finance,
        tab_categories,
        tab_reminders,
    ) = st.tabs(
        [
            "Business Profile",
            "Finance Defaults",
            "Categories",
            "Reminders",
        ]
    )

    # --------------------------------------------------
    # BUSINESS PROFILE
    # --------------------------------------------------

    with tab_profile:
        st.subheader("Business Profile")

        st.caption(
            "Your business type helps Finance Assistant suggest "
            "more relevant categories and defaults."
        )

        with st.form("business_profile_form"):
            col1, col2 = st.columns(2)

            with col1:
                business_name = st.text_input(
                    "Business Name",
                    value=settings["business_name"],
                    placeholder="e.g. Atlas Trading Co."
                )

                business_type = st.selectbox(
                    "Business Type",
                    BUSINESS_TYPES,
                    index=(
                        BUSINESS_TYPES.index(settings["business_type"])
                        if settings["business_type"] in BUSINESS_TYPES
                        else BUSINESS_TYPES.index("Other")
                    )
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
                old_business_type = settings["business_type"]

                save_business_settings(
                    business_name,
                    business_type,
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

                if old_business_type != business_type:
                    st.session_state["business_type_changed"] = True

                st.success("Business profile saved.")
                st.rerun()

        if st.session_state.get("business_type_changed"):
            st.info(
                "Business type changed. Your existing categories were kept. "
                "Use the Categories tab if you want to reset them to the "
                "new industry defaults."
            )
            st.session_state["business_type_changed"] = False

    # --------------------------------------------------
    # FINANCE DEFAULTS
    # --------------------------------------------------

    with tab_finance:
        st.subheader("Finance Defaults")

        st.caption(
            "Set the defaults used across invoices and finance screens."
        )

        with st.form("finance_defaults_form"):
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

            finance_saved = st.form_submit_button(
                "Save Finance Defaults",
                type="primary",
                use_container_width=True
            )

            if finance_saved:
                prefix = invoice_prefix.strip().upper()

                if not prefix:
                    st.error("Invoice prefix cannot be empty.")

                else:
                    save_business_settings(
                        settings["business_name"],
                        settings["business_type"],
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

                    st.success("Finance defaults saved.")
                    st.rerun()

    # --------------------------------------------------
    # CATEGORY MANAGEMENT
    # --------------------------------------------------

    with tab_categories:
        st.subheader("Category Management")

        st.caption(
            "Customize income and expense categories for your business. "
            "Your learned transaction corrections continue to work separately."
        )

        income_categories = get_business_categories("Income")
        expense_categories = get_business_categories("Expense")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Income Categories")

            if income_categories:
                for category in income_categories:
                    st.write(f"• {category['name']}")
            else:
                st.caption("No income categories yet.")

        with col2:
            st.markdown("#### Expense Categories")

            if expense_categories:
                for category in expense_categories:
                    st.write(f"• {category['name']}")
            else:
                st.caption("No expense categories yet.")

        st.divider()

        with st.form("add_category_form"):
            add_col1, add_col2 = st.columns(2)

            with add_col1:
                new_category_name = st.text_input(
                    "New Category Name",
                    placeholder="e.g. Packaging"
                )

            with add_col2:
                new_category_type = st.selectbox(
                    "Category Type",
                    ["Expense", "Income"]
                )

            add_submitted = st.form_submit_button(
                "Add Category",
                type="primary",
                use_container_width=True
            )

            if add_submitted:
                try:
                    add_business_category(
                        new_category_name,
                        new_category_type
                    )

                    st.success("Category added.")
                    st.rerun()

                except ValueError as error:
                    st.error(str(error))

        all_categories = get_business_categories()

        if all_categories:
            st.divider()
            st.markdown("#### Edit or Delete Category")

            category_labels = {
                f"{item['type']} — {item['name']}": item
                for item in all_categories
            }

            selected_label = st.selectbox(
                "Choose Category",
                list(category_labels.keys())
            )

            selected_category = category_labels[selected_label]

            new_name = st.text_input(
                "Rename Category",
                value=selected_category["name"],
                key="rename_category"
            )

            edit_col1, edit_col2 = st.columns(2)

            with edit_col1:
                if st.button(
                    "Save Category Name",
                    use_container_width=True
                ):
                    try:
                        update_business_category(
                            selected_category["id"],
                            new_name
                        )

                        st.success("Category updated.")
                        st.rerun()

                    except Exception as error:
                        st.error(str(error))

            with edit_col2:
                if st.button(
                    "Delete Category",
                    use_container_width=True
                ):
                    delete_business_category(
                        selected_category["id"]
                    )

                    st.success("Category deleted.")
                    st.rerun()

        st.divider()

        if st.button(
            "Reset Categories to Business Type Defaults",
            use_container_width=True
        ):
            reset_business_categories_to_industry_defaults()

            st.success(
                "Categories reset to the suggested defaults for "
                f"{settings['business_type']}."
            )
            st.rerun()

    # --------------------------------------------------
    # REMINDERS
    # --------------------------------------------------

    with tab_reminders:
        st.subheader("Reminder Preferences")

        st.caption(
            "Control the default behavior of your collection reminder workflow."
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

            reminder_saved = st.form_submit_button(
                "Save Reminder Preferences",
                type="primary",
                use_container_width=True
            )

            if reminder_saved:
                save_business_settings(
                    settings["business_name"],
                    settings["business_type"],
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