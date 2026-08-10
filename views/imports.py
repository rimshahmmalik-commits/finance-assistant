import streamlit as st
import pandas as pd

from database.database import add_invoice, get_invoices


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def normalize_column_name(name):
    return str(name).strip().lower().replace(" ", "_")


def find_suggested_column(columns, keywords):
    for column in columns:
        cleaned = normalize_column_name(column)

        for keyword in keywords:
            if keyword in cleaned:
                return column

    return None


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def calculate_amount_statistics(df, amount_column):
    """
    Calculate typical invoice values so we can flag
    unusually large amounts.
    """

    numeric_amounts = pd.to_numeric(
        df[amount_column],
        errors="coerce"
    )

    positive_amounts = numeric_amounts[
        numeric_amounts > 0
    ]

    if positive_amounts.empty:
        return None, None

    median_amount = positive_amounts.median()

    # Simple anomaly threshold for V2.
    # Later this can become client-specific / AI-driven.
    unusual_threshold = median_amount * 5

    return median_amount, unusual_threshold


def calculate_risk(problems, warnings):
    """
    Convert detected issues into a simple risk score.
    """

    score = 0

    serious_problems = {
        "Missing invoice number": 50,
        "Missing client": 40,
        "Invalid amount": 50,
        "Amount must be greater than zero": 50,
        "Invoice already exists in database": 60,
        "Duplicate invoice inside uploaded file": 60,
    }

    for problem in problems:
        score += serious_problems.get(problem, 30)

    score += len(warnings) * 20

    score = min(score, 100)

    if score >= 60:
        risk_level = "High Risk"
    elif score >= 20:
        risk_level = "Needs Review"
    else:
        risk_level = "Ready"

    return score, risk_level


def generate_recommendation(problems, warnings):
    """
    Explain what the finance user should do next.
    """

    if "Invoice already exists in database" in problems:
        return "Do not import — verify whether this invoice was already processed."

    if "Duplicate invoice inside uploaded file" in problems:
        return "Review duplicate — keep only the correct invoice entry."

    if "Missing invoice number" in problems:
        return "Add an invoice number before processing."

    if "Missing client" in problems:
        return "Identify and assign the correct client before processing."

    if "Invalid amount" in problems:
        return "Correct the invoice amount."

    if "Amount must be greater than zero" in problems:
        return "Verify the amount before processing."

    if warnings:
        return "Review this invoice before approval."

    return "Safe to create as draft."


# --------------------------------------------------
# PAGE
# --------------------------------------------------

def show_import_page():
    st.title("Smart Import")
    st.caption(
        "Validate, risk-score and convert finance data into invoice drafts."
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

    # --------------------------------------------------
    # READ FILE
    # --------------------------------------------------

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

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    st.success(
        f"File loaded successfully — {len(df)} rows found."
    )

    # --------------------------------------------------
    # PREVIEW
    # --------------------------------------------------

    st.subheader("Preview")

    st.dataframe(
        df.head(20),
        width="stretch",
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------
    # COLUMN MAPPING
    # --------------------------------------------------

    st.subheader("Column Mapping")

    columns = list(df.columns)

    suggested_invoice = find_suggested_column(
        columns,
        [
            "invoice_number",
            "invoice",
            "inv_no",
            "bill_no"
        ]
    )

    suggested_client = find_suggested_column(
        columns,
        [
            "client",
            "company",
            "customer",
            "business"
        ]
    )

    suggested_amount = find_suggested_column(
        columns,
        [
            "amount",
            "total",
            "value",
            "invoice_value"
        ]
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

    # Prevent accidentally mapping one column to everything.

    if len({
        invoice_column,
        client_column,
        amount_column
    }) < 3:

        st.error(
            "Invoice Number, Client and Amount must use different columns."
        )
        return

    st.divider()

    # --------------------------------------------------
    # SMART ANALYSIS
    # --------------------------------------------------

    st.subheader("Smart Analysis")

    existing_invoices = get_invoices()

    existing_numbers = {
        clean_text(invoice[0]).lower()
        for invoice in existing_invoices
    }

    median_amount, unusual_threshold = (
        calculate_amount_statistics(
            df,
            amount_column
        )
    )

    ready_rows = []
    review_rows = []
    blocked_rows = []

    all_analysis = []

    seen_numbers = set()

    for row_number, row in df.iterrows():

        invoice_number = clean_text(
            row[invoice_column]
        )

        client = clean_text(
            row[client_column]
        )

        raw_amount = row[amount_column]

        problems = []
        warnings = []

        # --------------------------
        # REQUIRED FIELDS
        # --------------------------

        if not invoice_number:
            problems.append(
                "Missing invoice number"
            )

        if not client:
            problems.append(
                "Missing client"
            )

        # --------------------------
        # AMOUNT VALIDATION
        # --------------------------

        try:
            amount = float(raw_amount)

            if amount <= 0:
                problems.append(
                    "Amount must be greater than zero"
                )

        except (ValueError, TypeError):
            amount = 0
            problems.append(
                "Invalid amount"
            )

        normalized_invoice = invoice_number.lower()

        # --------------------------
        # DUPLICATE DETECTION
        # --------------------------

        if (
            normalized_invoice
            and normalized_invoice in existing_numbers
        ):
            problems.append(
                "Invoice already exists in database"
            )

        if (
            normalized_invoice
            and normalized_invoice in seen_numbers
        ):
            problems.append(
                "Duplicate invoice inside uploaded file"
            )

        if normalized_invoice:
            seen_numbers.add(
                normalized_invoice
            )

        # --------------------------
        # ANOMALY DETECTION
        # --------------------------

        if (
            unusual_threshold is not None
            and amount > unusual_threshold
        ):
            warnings.append(
                "Amount is unusually high compared with this file"
            )

        # --------------------------
        # RISK ENGINE
        # --------------------------

        risk_score, risk_level = calculate_risk(
            problems,
            warnings
        )

        recommendation = generate_recommendation(
            problems,
            warnings
        )

        issue_list = problems + warnings

        row_data = {
            "Row": row_number + 2,
            "Invoice": invoice_number,
            "Client": client,
            "Amount": amount,
            "Risk Score": risk_score,
            "Risk": risk_level,
            "Issue": (
                ", ".join(issue_list)
                if issue_list
                else "None"
            ),
            "Recommendation": recommendation
        }

        all_analysis.append(row_data)

        if problems:
            blocked_rows.append(row_data)

        elif warnings:
            review_rows.append(row_data)

        else:
            ready_rows.append(row_data)

    # --------------------------------------------------
    # ANALYSIS SUMMARY
    # --------------------------------------------------

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "Rows Analysed",
            len(df)
        )

    with metric2:
        st.metric(
            "Ready",
            len(ready_rows)
        )

    with metric3:
        st.metric(
            "Needs Review",
            len(review_rows)
        )

    with metric4:
        st.metric(
            "Blocked",
            len(blocked_rows)
        )

    if median_amount is not None:
        st.caption(
            f"Typical invoice amount in this file: "
            f"PKR {median_amount:,.2f}"
        )

    # --------------------------------------------------
    # REVIEW QUEUE
    # --------------------------------------------------

    if review_rows or blocked_rows:

        st.subheader("Review Queue")

        attention_rows = (
            blocked_rows + review_rows
        )

        st.dataframe(
            attention_rows,
            width="stretch",
            hide_index=True
        )

        if blocked_rows:
            st.error(
                f"{len(blocked_rows)} invoice(s) are blocked "
                "and will not be created."
            )

        if review_rows:
            st.warning(
                f"{len(review_rows)} invoice(s) contain "
                "unusual activity and require review."
            )

    # --------------------------------------------------
    # READY INVOICES
    # --------------------------------------------------

    if ready_rows:

        st.subheader("Safe Drafts")

        preview_rows = []

        for row in ready_rows:
            preview_rows.append({
                "Invoice": row["Invoice"],
                "Client": row["Client"],
                "Amount": f"PKR {row['Amount']:,.2f}",
                "Risk": row["Risk"],
                "Recommendation": row["Recommendation"]
            })

        st.dataframe(
            preview_rows,
            width="stretch",
            hide_index=True
        )

        st.success(
            f"{len(ready_rows)} invoice(s) passed all automatic checks."
        )

        st.caption(
            "Nothing is saved until you approve the safe drafts."
        )

        # --------------------------------------------------
        # HUMAN APPROVAL
        # --------------------------------------------------

        if st.button(
            f"Approve & Create {len(ready_rows)} Safe Drafts",
            type="primary",
            width="stretch"
        ):

            created = 0

            for row in ready_rows:

                add_invoice(
                    row["Invoice"],
                    row["Client"],
                    row["Amount"],
                    "Draft"
                )

                created += 1

            st.success(
                f"{created} safe invoice drafts created successfully."
            )

            st.balloons()

    elif not review_rows and not blocked_rows:

        st.info(
            "No invoices are available to process."
        )

    # --------------------------------------------------
    # FULL AUDIT VIEW
    # --------------------------------------------------

    with st.expander("View Full Analysis"):

        st.dataframe(
            all_analysis,
            width="stretch",
            hide_index=True
        )