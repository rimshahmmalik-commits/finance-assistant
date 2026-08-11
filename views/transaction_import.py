import streamlit as st
import pandas as pd

from database.database import (
    add_transaction,
    categorize_transaction,
    transaction_exists,
)


def find_column(columns, keywords):
    """
    Try to automatically identify a column based on common names.
    """
    for column in columns:
        normalized = str(column).strip().lower()

        for keyword in keywords:
            if keyword in normalized:
                return column

    return None


def show_transaction_import_page():

    st.title("Smart Transaction Import")

    st.caption(
        "Upload a bank statement or transaction file. "
        "Transactions are detected and categorized automatically."
    )

    uploaded_file = st.file_uploader(
        "Upload transaction file",
        type=["csv", "xlsx", "xls"],
        key="transaction_import_file",
    )

    if uploaded_file is None:
        st.info(
            "Upload a CSV or Excel transaction file to begin."
        )
        return

    # --------------------------------------------------
    # READ FILE
    # --------------------------------------------------

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

    except Exception as error:
        st.error(
            f"Could not read this file: {error}"
        )
        return

    if df.empty:
        st.warning("The uploaded file contains no transactions.")
        return

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    st.success(
        f"{len(df)} row(s) detected."
    )

    # --------------------------------------------------
    # COLUMN DETECTION
    # --------------------------------------------------

    columns = df.columns.tolist()

    detected_date = find_column(
        columns,
        [
            "transaction date",
            "date",
            "posted",
        ],
    )

    detected_description = find_column(
        columns,
        [
            "description",
            "details",
            "narration",
            "merchant",
            "remarks",
            "memo",
        ],
    )

    detected_amount = find_column(
        columns,
        [
            "amount",
            "value",
        ],
    )

    detected_debit = find_column(
        columns,
        [
            "debit",
            "withdrawal",
            "money out",
        ],
    )

    detected_credit = find_column(
        columns,
        [
            "credit",
            "deposit",
            "money in",
        ],
    )

    detected_reference = find_column(
        columns,
        [
            "reference",
            "transaction id",
            "transaction no",
            "ref",
        ],
    )

    st.subheader("Column Mapping")

    st.caption(
        "We've suggested mappings where possible. "
        "Check them before continuing."
    )

    no_column = "— Not available —"
    mapping_options = [no_column] + columns

    def default_index(column):
        if column in columns:
            return mapping_options.index(column)
        return 0

    map1, map2 = st.columns(2)

    with map1:
        date_column = st.selectbox(
            "Date",
            mapping_options,
            index=default_index(detected_date),
        )

        description_column = st.selectbox(
            "Description",
            mapping_options,
            index=default_index(detected_description),
        )

        amount_column = st.selectbox(
            "Amount",
            mapping_options,
            index=default_index(detected_amount),
        )

    with map2:
        debit_column = st.selectbox(
            "Debit / Money Out",
            mapping_options,
            index=default_index(detected_debit),
        )

        credit_column = st.selectbox(
            "Credit / Money In",
            mapping_options,
            index=default_index(detected_credit),
        )

        reference_column = st.selectbox(
            "Reference",
            mapping_options,
            index=default_index(detected_reference),
        )

    # --------------------------------------------------
    # VALIDATE MAPPING
    # --------------------------------------------------

    if date_column == no_column:
        st.warning("Select the transaction date column.")
        return

    if description_column == no_column:
        st.warning("Select the description column.")
        return

    has_single_amount = amount_column != no_column

    has_debit_credit = (
        debit_column != no_column
        or credit_column != no_column
    )

    if not has_single_amount and not has_debit_credit:
        st.warning(
            "Select either an Amount column or "
            "Debit/Credit columns."
        )
        return

    # --------------------------------------------------
    # NORMALIZE TRANSACTIONS
    # --------------------------------------------------

    normalized_rows = []

    for _, row in df.iterrows():

        description = str(
            row.get(description_column, "")
        ).strip()

        raw_date = row.get(date_column)

        parsed_date = pd.to_datetime(
            raw_date,
            errors="coerce",
        )

        if pd.isna(parsed_date):
            continue

        transaction_date = parsed_date.date().isoformat()

        transaction_type = None
        amount = 0.0

        # ----------------------------------------------
        # FORMAT A — SEPARATE DEBIT/CREDIT COLUMNS
        # ----------------------------------------------

        if has_debit_credit:

            debit = 0.0
            credit = 0.0

            if debit_column != no_column:
                debit = pd.to_numeric(
                    row.get(debit_column),
                    errors="coerce",
                )

                debit = (
                    0.0
                    if pd.isna(debit)
                    else float(debit)
                )

            if credit_column != no_column:
                credit = pd.to_numeric(
                    row.get(credit_column),
                    errors="coerce",
                )

                credit = (
                    0.0
                    if pd.isna(credit)
                    else float(credit)
                )

            if credit > 0:
                transaction_type = "Income"
                amount = credit

            elif debit > 0:
                transaction_type = "Expense"
                amount = debit

        # ----------------------------------------------
        # FORMAT B — ONE SIGNED AMOUNT COLUMN
        # ----------------------------------------------

        elif has_single_amount:

            raw_amount = pd.to_numeric(
                row.get(amount_column),
                errors="coerce",
            )

            if pd.isna(raw_amount):
                continue

            raw_amount = float(raw_amount)

            if raw_amount >= 0:
                transaction_type = "Income"
                amount = raw_amount

            else:
                transaction_type = "Expense"
                amount = abs(raw_amount)

        if not transaction_type or amount <= 0:
            continue

        category = categorize_transaction(
            description,
            transaction_type,
        )

        reference = None

        if reference_column != no_column:
            raw_reference = row.get(
                reference_column
            )

            if pd.notna(raw_reference):
                reference = str(
                    raw_reference
                ).strip()

        normalized_rows.append({
            "Import": True,
            "Date": transaction_date,
            "Type": transaction_type,
            "Description": description,
            "Amount": amount,
            "Category": category,
            "Reference": reference or "",
        })

    if not normalized_rows:
        st.error(
            "No valid transactions could be detected "
            "using the selected columns."
        )
        return

    preview_df = pd.DataFrame(
        normalized_rows
    )

    # --------------------------------------------------
    # REVIEW
    # --------------------------------------------------

    st.divider()

    st.subheader("Review Transactions")

    st.caption(
        "Review the detected transactions and categories "
        "before adding them to your books."
    )

    edited_df = st.data_editor(
        preview_df,
        width="stretch",
        hide_index=True,
        disabled=[
            "Date",
            "Type",
            "Description",
            "Amount",
            "Reference",
        ],
        column_config={
            "Import": st.column_config.CheckboxColumn(
                "Import",
                default=True,
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="PKR %.2f",
            ),
            "Category": st.column_config.TextColumn(
                "Category",
                help=(
                    "You can correct the suggested category "
                    "before importing."
                ),
            ),
        },
        key="transaction_import_editor",
    )

    selected_df = edited_df[
        edited_df["Import"] == True
    ]

    income_total = selected_df.loc[
        selected_df["Type"] == "Income",
        "Amount",
    ].sum()

    expense_total = selected_df.loc[
        selected_df["Type"] == "Expense",
        "Amount",
    ].sum()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Transactions Selected",
            len(selected_df),
        )

    with col2:
        st.metric(
            "Income Detected",
            f"PKR {income_total:,.2f}",
        )

    with col3:
        st.metric(
            "Expenses Detected",
            f"PKR {expense_total:,.2f}",
        )

    # --------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------

    account = st.text_input(
        "Import into account",
        placeholder="e.g. HBL Business, JazzCash, Cash",
    )

    # --------------------------------------------------
    # IMPORT
    # --------------------------------------------------

    if st.button(
        "Import Transactions",
        type="primary",
        use_container_width=True,
    ):

        if selected_df.empty:
            st.warning(
                "Select at least one transaction."
            )
            return

        if not account.strip():
            st.warning(
                "Enter the account these transactions belong to."
            )
            return

        imported = 0
        duplicates = 0
        failed = 0

        progress = st.progress(0)

        total_rows = len(selected_df)
        import_account = account.strip()

        for position, (_, transaction) in enumerate(
            selected_df.iterrows(),
            start=1,
        ):

            try:
                raw_reference = transaction["Reference"]

                reference = (
                    str(raw_reference).strip()
                    if pd.notna(raw_reference)
                    and str(raw_reference).strip()
                    else None
                )

                already_exists = transaction_exists(
                    transaction["Date"],
                    transaction["Type"],
                    transaction["Description"],
                    float(transaction["Amount"]),
                    import_account,
                    reference,
                )

                if already_exists:
                    duplicates += 1

                else:
                    add_transaction(
                        transaction["Date"],
                        transaction["Type"],
                        transaction["Description"],
                        float(transaction["Amount"]),
                        transaction["Category"],
                        import_account,
                        reference,
                        "Statement Import",
                    )

                    imported += 1

            except Exception:
                failed += 1

            progress.progress(
                position / total_rows
            )

        if imported:
            st.success(
                f"{imported} new transaction(s) imported successfully."
            )

        if duplicates:
            st.warning(
                f"{duplicates} duplicate transaction(s) were skipped."
            )

        if failed:
            st.error(
                f"{failed} transaction(s) could not be imported."
            )

        if imported == 0 and duplicates > 0 and failed == 0:
            st.info(
                "No new transactions were added. "
                "This statement appears to have already been imported."
            )

        elif imported:
            st.info(
                "Your Transactions, Reports and Cash Flow "
                "Forecast can now use the imported data."
            )