import streamlit as st
import pandas as pd

from database.database import add_invoice, get_invoices


def normalize_column_name(name):
    return str(name).strip().lower().replace(" ", "_")


def find_suggested_column(columns, keywords):
    for column in columns:
        cleaned = normalize_column_name(column)

        for keyword in keywords:
            if keyword in cleaned:
                return column

    return None


def show_import_page():
    st.title("Smart Import")
    st.caption(
        "Turn Excel or CSV data into validated invoice drafts."
    )

    uploaded_file = st.file_uploader(
        "Upload finance data",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is None:
        st.info(
            "Upload an Excel or CSV file containing invoice data."
        )
        return

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

    except Exception as error:
        st.error(f"Could not read this file: {error}")
        return

    if df.empty:
        st.warning("The uploaded file contains no rows.")
        return

    df.columns = [str(column).strip() for column in df.columns]

    st.success(
        f"File loaded successfully — {len(df)} rows found."
    )

    st.subheader("Preview")

    st.dataframe(
        df.head(20),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("Column Mapping")

    columns = list(df.columns)

    suggested_invoice = find_suggested_column(
        columns,
        ["invoice_number", "invoice", "inv_no", "bill_no"]
    )

    suggested_client = find_suggested_column(
        columns,
        ["client", "company", "customer", "business"]
    )

    suggested_amount = find_suggested_column(
        columns,
        ["amount", "total", "value", "invoice_value"]
    )

    invoice_index = (
        columns.index(suggested_invoice)
        if suggested_invoice in columns
        else 0
    )

    client_index = (
        columns.index(suggested_client)
        if suggested_client in columns
        else 0
    )

    amount_index = (
        columns.index(suggested_amount)
        if suggested_amount in columns
        else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        invoice_column = st.selectbox(
            "Invoice Number",
            columns,
            index=invoice_index
        )

    with col2:
        client_column = st.selectbox(
            "Client / Company",
            columns,
            index=client_index
        )

    with col3:
        amount_column = st.selectbox(
            "Amount",
            columns,
            index=amount_index
        )

    st.divider()

    st.subheader("Validation")

    existing_invoices = get_invoices()

    existing_numbers = {
        str(invoice[0]).strip().lower()
        for invoice in existing_invoices
    }

    valid_rows = []
    problem_rows = []

    seen_numbers = set()

    for row_number, row in df.iterrows():

        invoice_number = str(
            row[invoice_column]
        ).strip()

        client = str(
            row[client_column]
        ).strip()

        raw_amount = row[amount_column]

        problems = []

        if (
            not invoice_number
            or invoice_number.lower() == "nan"
        ):
            problems.append("Missing invoice number")

        if (
            not client
            or client.lower() == "nan"
        ):
            problems.append("Missing client")

        try:
            amount = float(raw_amount)

            if amount <= 0:
                problems.append(
                    "Amount must be greater than zero"
                )

        except (ValueError, TypeError):
            amount = 0
            problems.append("Invalid amount")

        normalized_invoice = invoice_number.lower()

        if normalized_invoice in existing_numbers:
            problems.append(
                "Invoice already exists in database"
            )

        if normalized_invoice in seen_numbers:
            problems.append(
                "Duplicate invoice inside uploaded file"
            )

        seen_numbers.add(normalized_invoice)

        row_data = {
            "Row": row_number + 2,
            "Invoice": invoice_number,
            "Client": client,
            "Amount": amount
        }

        if problems:
            row_data["Problem"] = ", ".join(problems)
            problem_rows.append(row_data)

        else:
            valid_rows.append(row_data)

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Rows Detected",
            len(df)
        )

    with metric2:
        st.metric(
            "Ready to Generate",
            len(valid_rows)
        )

    with metric3:
        st.metric(
            "Problems Found",
            len(problem_rows)
        )

    if problem_rows:

        st.warning(
            f"{len(problem_rows)} row(s) need attention."
        )

        st.dataframe(
            problem_rows,
            use_container_width=True,
            hide_index=True
        )

    if valid_rows:

        st.subheader("Invoice Drafts")

        preview_rows = []

        for row in valid_rows:
            preview_rows.append({
                "Invoice": row["Invoice"],
                "Client": row["Client"],
                "Amount": f"PKR {row['Amount']:,.2f}",
                "Status": "Draft"
            })

        st.dataframe(
            preview_rows,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Nothing is saved until you approve the drafts."
        )

        if st.button(
            f"Approve & Create {len(valid_rows)} Draft Invoices",
            type="primary",
            use_container_width=True
        ):

            created = 0

            for row in valid_rows:
                add_invoice(
                    row["Invoice"],
                    row["Client"],
                    row["Amount"],
                    "Draft"
                )

                created += 1

            st.success(
                f"{created} invoice drafts created successfully."
            )

            st.balloons()