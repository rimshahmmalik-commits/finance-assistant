import streamlit as st
import pandas as pd

from database.database import (
    add_invoice,
    get_invoices,
    add_review_decision,
    get_review_decisions,
    get_review_decision_for_invoice,
    update_invoice_status,
    invoice_exists,
)

from ai.finance_ai import review_invoice_with_ai


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
    unusual_threshold = median_amount * 5

    return median_amount, unusual_threshold


def calculate_risk(problems, warnings):
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
        "Validate, risk-score and intelligently review finance data."
    )

    uploaded_file = st.file_uploader(
        "Upload finance data",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is None:
        st.info(
            "Upload an Excel or CSV file containing invoice data."
        )

        show_audit_history()
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

        # REQUIRED FIELDS

        if not invoice_number:
            problems.append(
                "Missing invoice number"
            )

        if not client:
            problems.append(
                "Missing client"
            )

        # AMOUNT

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

        # DUPLICATES

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

        # ANOMALIES

        if (
            unusual_threshold is not None
            and amount > unusual_threshold
        ):
            warnings.append(
                "Amount is unusually high compared with this file"
            )

        # RISK

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
    # METRICS
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
            f"Typical invoice amount: "
            f"PKR {median_amount:,.2f}"
        )

    # --------------------------------------------------
    # REVIEW QUEUE
    # --------------------------------------------------

    attention_rows = (
        blocked_rows + review_rows
    )

    if attention_rows:

        st.subheader("Review Queue")

        st.dataframe(
            attention_rows,
            width="stretch",
            hide_index=True
        )

        st.subheader("AI Finance Reviewer")

        for row in attention_rows:

            invoice_label = (
                row["Invoice"]
                if row["Invoice"]
                else "Missing invoice"
            )

            client_label = (
                row["Client"]
                if row["Client"]
                else "Unknown client"
            )

            with st.expander(
                f"{invoice_label} — {client_label}"
            ):

                st.write(
                    f"**Amount:** "
                    f"PKR {row['Amount']:,.2f}"
                )

                st.write(
                    f"**Risk:** "
                    f"{row['Risk']} "
                    f"({row['Risk Score']}/100)"
                )

                st.write(
                    f"**Detected issue:** "
                    f"{row['Issue']}"
                )

                # ------------------------------------------
                # CHECK EXISTING HUMAN DECISION
                # ------------------------------------------

                existing_decision = None

                if row["Invoice"]:
                    existing_decision = (
                        get_review_decision_for_invoice(
                            row["Invoice"]
                        )
                    )

                if existing_decision:

                    st.success(
                        f"Decision already recorded: "
                        f"{existing_decision[7]}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{existing_decision[8] or 'No reason provided'}"
                    )

                    st.write(
                        f"**Decided at:** "
                        f"{existing_decision[9]}"
                    )

                    continue

                # ------------------------------------------
                # AI SESSION STATE
                # ------------------------------------------

                ai_key = (
                    f"ai_result_"
                    f"{row['Row']}_"
                    f"{row['Invoice']}"
                )

                button_key = (
                    f"ai_review_"
                    f"{row['Row']}_"
                    f"{row['Invoice']}"
                )

                if st.button(
                    "Ask AI to Review",
                    key=button_key
                ):

                    with st.spinner(
                        "AI Finance Reviewer is analysing..."
                    ):

                        analysis = (
                            review_invoice_with_ai(
                                invoice_number=row["Invoice"],
                                client_name=row["Client"],
                                amount=row["Amount"],
                                issue=row["Issue"],
                                risk_score=row["Risk Score"]
                            )
                        )

                    st.session_state[ai_key] = analysis

                # ------------------------------------------
                # SHOW AI RESULT
                # ------------------------------------------

                if ai_key in st.session_state:

                    analysis = (
                        st.session_state[ai_key]
                    )

                    st.markdown(
                        "#### AI Analysis"
                    )

                    st.write(
                        analysis["summary"]
                    )

                    st.markdown(
                        "#### Recommended Check"
                    )

                    st.write(
                        analysis["recommendation"]
                    )

                    if "error" in analysis:

                        st.error(
                            "AI review failed. "
                            "Manual review is required."
                        )

                    else:

                        st.divider()

                        st.markdown(
                            "#### Human Decision"
                        )

                        decision = st.radio(
                            "Decision",
                            [
                                "Approve",
                                "Hold",
                                "Reject"
                            ],
                            horizontal=True,
                            key=(
                                f"decision_"
                                f"{row['Row']}_"
                                f"{row['Invoice']}"
                            )
                        )

                        reason = st.text_area(
                            "Decision reason",
                            placeholder=(
                                "Example: Verified against "
                                "purchase order."
                            ),
                            key=(
                                f"reason_"
                                f"{row['Row']}_"
                                f"{row['Invoice']}"
                            )
                        )

                        save_key = (
                            f"save_decision_"
                            f"{row['Row']}_"
                            f"{row['Invoice']}"
                        )

                        if st.button(
                            "Save Decision",
                            type="primary",
                            key=save_key
                        ):

                            if not row["Invoice"]:

                                st.error(
                                    "Cannot save a decision "
                                    "without an invoice number."
                                )

                            elif not reason.strip():

                                st.warning(
                                    "Add a short reason "
                                    "before saving."
                                )

                            else:

                                add_review_decision(
                                    invoice_number=row["Invoice"],
                                    client=row["Client"],
                                    amount=row["Amount"],
                                    risk_score=row["Risk Score"],
                                    detected_issue=row["Issue"],
                                    ai_summary=analysis["summary"],
                                    ai_recommendation=(
                                        analysis["recommendation"]
                                    ),
                                    decision=decision,
                                    decision_reason=reason.strip()
                                )

                                # APPROVED
                                if decision == "Approve":

                                    if invoice_exists(
                                        row["Invoice"]
                                    ):

                                        update_invoice_status(
                                            row["Invoice"],
                                            "Approved"
                                        )

                                    else:

                                        add_invoice(
                                            row["Invoice"],
                                            row["Client"],
                                            row["Amount"],
                                            "Approved"
                                        )

                                # HOLD
                                elif decision == "Hold":

                                    if invoice_exists(
                                        row["Invoice"]
                                    ):

                                        update_invoice_status(
                                            row["Invoice"],
                                            "Hold"
                                        )

                                # REJECT
                                elif decision == "Reject":

                                    if invoice_exists(
                                        row["Invoice"]
                                    ):

                                        update_invoice_status(
                                            row["Invoice"],
                                            "Rejected"
                                        )

                                st.success(
                                    f"{decision} decision saved."
                                )

                                st.balloons()

                                del st.session_state[
                                    ai_key
                                ]

                                st.rerun()

        if blocked_rows:

            st.error(
                f"{len(blocked_rows)} invoice(s) "
                "are blocked from automatic creation."
            )

        if review_rows:

            st.warning(
                f"{len(review_rows)} invoice(s) "
                "require human review."
            )

    # --------------------------------------------------
    # SAFE DRAFTS
    # --------------------------------------------------

    if ready_rows:

        st.subheader(
            "Safe Drafts"
        )

        preview_rows = []

        for row in ready_rows:

            preview_rows.append({
                "Invoice": row["Invoice"],
                "Client": row["Client"],
                "Amount": (
                    f"PKR {row['Amount']:,.2f}"
                ),
                "Risk": row["Risk"],
                "Recommendation": (
                    row["Recommendation"]
                )
            })

        st.dataframe(
            preview_rows,
            width="stretch",
            hide_index=True
        )

        st.success(
            f"{len(ready_rows)} invoice(s) "
            "passed all automatic checks."
        )

        if st.button(
            (
                f"Approve & Create "
                f"{len(ready_rows)} Safe Drafts"
            ),
            type="primary",
            width="stretch"
        ):

            created = 0

            for row in ready_rows:

                if not invoice_exists(
                    row["Invoice"]
                ):

                    add_invoice(
                        row["Invoice"],
                        row["Client"],
                        row["Amount"],
                        "Draft"
                    )

                    created += 1

            st.success(
                f"{created} safe invoice drafts "
                "created successfully."
            )

            st.balloons()

    # --------------------------------------------------
    # FULL ANALYSIS
    # --------------------------------------------------

    with st.expander(
        "View Full Analysis"
    ):

        st.dataframe(
            all_analysis,
            width="stretch",
            hide_index=True
        )

    # --------------------------------------------------
    # AUDIT HISTORY
    # --------------------------------------------------

    show_audit_history()


# --------------------------------------------------
# AUDIT HISTORY
# --------------------------------------------------

def show_audit_history():

    st.divider()

    st.subheader(
        "Decision Audit Trail"
    )

    decisions = (
        get_review_decisions()
    )

    if not decisions:

        st.info(
            "No human review decisions recorded yet."
        )
        return

    audit_rows = []

    for decision in decisions:

        audit_rows.append({
            "Invoice": decision[0],
            "Client": decision[1],
            "Amount": (
                f"PKR {decision[2]:,.2f}"
            ),
            "Risk": decision[3],
            "Issue": decision[4],
            "Decision": decision[7],
            "Reason": decision[8],
            "Time": decision[9]
        })

    st.dataframe(
        audit_rows,
        width="stretch",
        hide_index=True
    )