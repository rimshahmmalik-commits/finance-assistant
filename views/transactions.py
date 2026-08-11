import streamlit as st
import pandas as pd
from datetime import date

from database.database import (
    add_transaction,
    get_transactions,
    get_transaction_summary,
    categorize_transaction,
    update_transaction_category,
)


CATEGORIES = {
    "Income": [
        "Sales",
        "Services",
        "Other Income",
    ],
    "Expense": [
        "Inventory",
        "Rent",
        "Utilities",
        "Payroll",
        "Salaries",
        "Transport",
        "Marketing",
        "Office",
        "Office Supplies",
        "Bank Fees",
        "Taxes",
        "Other Expense",
        "Uncategorized",
    ],
}


def get_category_options(transaction_type):
    return CATEGORIES.get(
        transaction_type,
        ["Uncategorized"]
    )


def normalize_suggestion(
    suggestion,
    transaction_type
):
    """
    Keep backend suggestions compatible with the UI category list.
    """
    if transaction_type == "Income" and suggestion == "Income":
        return "Other Income"

    options = get_category_options(
        transaction_type
    )

    if suggestion in options:
        return suggestion

    return "Uncategorized"


def show_transactions_page():
    st.title("Transactions")

    st.caption(
        "Track income and expenses across your business accounts."
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    summary = get_transaction_summary()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Income",
            f"PKR {summary['income']:,.2f}"
        )

    with col2:
        st.metric(
            "Total Expenses",
            f"PKR {summary['expenses']:,.2f}"
        )

    with col3:
        st.metric(
            "Net Cash Flow",
            f"PKR {summary['net']:,.2f}"
        )

    st.divider()

    # --------------------------------------------------
    # ADD TRANSACTION
    # --------------------------------------------------

    with st.expander(
        "Add Transaction",
        expanded=False
    ):

        transaction_type = st.selectbox(
            "Transaction Type",
            ["Income", "Expense"],
            key="new_transaction_type"
        )

        transaction_date = st.date_input(
            "Date",
            value=date.today(),
            key="new_transaction_date"
        )

        description = st.text_input(
            "Description",
            placeholder="e.g. LESCO bill July, Meta Ads, customer payment",
            key="new_transaction_description"
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            step=100.0,
            key="new_transaction_amount"
        )

        # Smart suggestion updates automatically as the description changes.
        raw_suggestion = categorize_transaction(
            description,
            transaction_type
        )

        suggested_category = normalize_suggestion(
            raw_suggestion,
            transaction_type
        )

        category_options = get_category_options(
            transaction_type
        )

        suggested_index = (
            category_options.index(
                suggested_category
            )
            if suggested_category in category_options
            else 0
        )

        if description.strip():
            if suggested_category == "Uncategorized":
                st.warning(
                    "Smart categorization is unsure. "
                    "Choose the correct category before saving."
                )
            else:
                st.info(
                    f"Suggested category: **{suggested_category}**"
                )

        category = st.selectbox(
            "Category",
            category_options,
            index=suggested_index,
            key=(
                f"new_transaction_category_"
                f"{transaction_type}_"
                f"{suggested_category}"
            )
        )

        remember_new_category = st.checkbox(
            "Remember this category for similar future descriptions",
            value=True,
            help=(
                "If you change the suggested category, "
                "Finance Assistant can learn from your correction."
            ),
            key="remember_new_category"
        )

        account = st.text_input(
            "Account",
            value="Cash",
            placeholder="e.g. Cash, Bank, JazzCash",
            key="new_transaction_account"
        )

        reference = st.text_input(
            "Reference",
            placeholder="Optional transaction reference",
            key="new_transaction_reference"
        )

        if st.button(
            "Save Transaction",
            type="primary",
            key="save_new_transaction"
        ):

            if amount <= 0:
                st.error(
                    "Amount must be greater than zero."
                )

            elif not description.strip():
                st.error(
                    "Description is required."
                )

            else:
                add_transaction(
                    transaction_date.isoformat(),
                    transaction_type,
                    description.strip(),
                    amount,
                    category,
                    account.strip() or "Manual",
                    reference.strip() or None,
                    "Manual"
                )

                # If the user deliberately changed the suggestion,
                # optionally teach the system that correction.
                if (
                    remember_new_category
                    and category != suggested_category
                ):
                    from database.database import (
                        remember_category_correction,
                    )

                    remember_category_correction(
                        description.strip(),
                        category
                    )

                st.success(
                    "Transaction saved successfully."
                )

                st.rerun()

    st.divider()

    # --------------------------------------------------
    # TRANSACTION HISTORY
    # --------------------------------------------------

    st.subheader("Transaction History")

    transactions = get_transactions()

    if not transactions:
        st.info("No transactions recorded yet.")
        return

    rows = []

    for tx in transactions:
        rows.append({
            "ID": tx[0],
            "Date": tx[1],
            "Type": tx[2],
            "Description": tx[3],
            "Amount": float(tx[4] or 0),
            "Category": tx[5],
            "Account": tx[6],
            "Reference": tx[7] or "—",
            "Source": tx[8],
        })

    df = pd.DataFrame(rows)

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------

    filter1, filter2, filter3 = st.columns(3)

    with filter1:
        type_filter = st.selectbox(
            "Type Filter",
            ["All", "Income", "Expense"]
        )

    with filter2:
        category_filter = st.selectbox(
            "Category Filter",
            ["All"] + sorted(
                df["Category"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    with filter3:
        account_filter = st.selectbox(
            "Account Filter",
            ["All"] + sorted(
                df["Account"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    filtered = df.copy()

    if type_filter != "All":
        filtered = filtered[
            filtered["Type"] == type_filter
        ]

    if category_filter != "All":
        filtered = filtered[
            filtered["Category"] == category_filter
        ]

    if account_filter != "All":
        filtered = filtered[
            filtered["Account"] == account_filter
        ]

    st.caption(
        f"{len(filtered)} transaction(s) found."
    )

    display_df = filtered.drop(
        columns=["ID"]
    ).copy()

    display_df["Amount"] = (
        display_df["Amount"]
        .map(
            lambda x: f"PKR {x:,.2f}"
        )
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------
    # CATEGORY CORRECTIONS / LEARNING
    # --------------------------------------------------

    st.subheader("Review Categories")

    st.caption(
        "Correct a category once and Finance Assistant can remember it "
        "for matching descriptions in the future."
    )

    for _, row in filtered.iterrows():

        transaction_id = int(row["ID"])
        transaction_type = str(row["Type"])
        description = str(row["Description"] or "")
        current_category = str(
            row["Category"] or "Uncategorized"
        )

        label = (
            f"{description} — "
            f"PKR {float(row['Amount']):,.2f} — "
            f"{current_category}"
        )

        with st.expander(label):

            suggested = normalize_suggestion(
                categorize_transaction(
                    description,
                    transaction_type
                ),
                transaction_type
            )

            st.write(
                f"**Current category:** {current_category}"
            )

            st.write(
                f"**System suggestion:** {suggested}"
            )

            options = get_category_options(
                transaction_type
            )

            if current_category not in options:
                options = options + [
                    current_category
                ]

            current_index = options.index(
                current_category
            )

            corrected_category = st.selectbox(
                "Correct Category",
                options,
                index=current_index,
                key=f"correct_category_{transaction_id}"
            )

            remember_correction = st.checkbox(
                "Remember this correction",
                value=True,
                key=f"remember_correction_{transaction_id}"
            )

            if st.button(
                "Save Category Correction",
                key=f"save_category_{transaction_id}"
            ):

                if corrected_category == current_category:
                    st.info(
                        "No category change was made."
                    )

                else:
                    updated = update_transaction_category(
                        transaction_id,
                        corrected_category,
                        learn_from_correction=remember_correction
                    )

                    if updated:
                        st.success(
                            "Category updated successfully."
                        )
                        st.rerun()
                    else:
                        st.error(
                            "Transaction could not be found."
                        )