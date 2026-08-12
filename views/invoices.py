import streamlit as st
from io import BytesIO
from datetime import date, datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from database.database import (
    add_invoice,
    get_invoice_management_data,
    get_all_payment_events_grouped,
    get_clients,
    invoice_exists,
    update_invoice_status,
    update_invoice_dates,
    update_overdue_invoices,
    add_payment_event,
    get_payment_summary,
)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

STATUS_OPTIONS = [
    "Draft",
    "Pending",
    "Approved",
    "Hold",
    "Paid",
    "Overdue",
    "Rejected",
]


def parse_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        return None


def money(value):
    return f"PKR {float(value or 0):,.0f}"


def get_due_message(due_date_value, status):
    due = parse_date(due_date_value)

    if not due:
        return "No due date"

    if str(status).strip().lower() == "paid":
        return "Paid"

    days = (due - date.today()).days

    if days < 0:
        return f"{abs(days)} day(s) overdue"

    if days == 0:
        return "Due today"

    if days == 1:
        return "Due tomorrow"

    return f"Due in {days} days"


def status_tone(status):
    value = str(status or "").strip().lower()

    if value == "paid":
        return "#22c55e"

    if value == "overdue":
        return "#ef4444"

    if value in {"pending", "hold"}:
        return "#f59e0b"

    if value in {"approved"}:
        return "#38bdf8"

    if value in {"rejected"}:
        return "#fb7185"

    return "#8b5cf6"


def status_badge(status):
    color = status_tone(status)

    return f"""
    <span style="
        display:inline-block;
        padding:0.24rem 0.55rem;
        border-radius:999px;
        font-size:0.72rem;
        font-weight:700;
        border:1px solid {color}55;
        background:{color}18;
        color:{color};
    ">{status}</span>
    """


def invoice_health_badge(due_date_value, status):
    message = get_due_message(
        due_date_value,
        status
    )

    lowered = message.lower()

    if "overdue" in lowered:
        color = "#ef4444"
    elif "due today" in lowered or "due tomorrow" in lowered:
        color = "#f59e0b"
    elif "paid" in lowered:
        color = "#22c55e"
    else:
        color = "#94a3b8"

    return f"""
    <span style="
        display:inline-block;
        padding:0.24rem 0.55rem;
        border-radius:999px;
        font-size:0.72rem;
        font-weight:700;
        border:1px solid {color}44;
        background:{color}12;
        color:{color};
    ">{message}</span>
    """


def invoice_card_header(
    invoice_number,
    client,
    amount,
    status,
    due_date,
    total_paid,
    remaining
):
    """
    Render one invoice summary card as a single uninterrupted HTML string.
    Keeping the markup on one logical line prevents Streamlit Markdown from
    interpreting indented HTML fragments as code blocks.
    """
    amount = float(amount or 0)
    total_paid = float(total_paid or 0)
    remaining = float(remaining or 0)

    paid_ratio = 0
    if amount > 0:
        paid_ratio = min(
            100,
            max(0, int((total_paid / amount) * 100))
        )

    status_text = str(status or "Unknown")
    status_color = status_tone(status_text)

    due_message = get_due_message(
        due_date,
        status_text
    )
    due_lower = due_message.lower()

    if "overdue" in due_lower:
        due_color = "#ef4444"
    elif "due today" in due_lower or "due tomorrow" in due_lower:
        due_color = "#f59e0b"
    elif "paid" in due_lower:
        due_color = "#22c55e"
    else:
        due_color = "#94a3b8"

    safe_invoice = str(invoice_number or "—")
    safe_client = str(client or "Unknown client")

    html = (
        '<div class="fa-card" style="margin-bottom:0.55rem;">'
        '<div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;">'
        '<div style="min-width:0;">'
        '<div class="fa-muted" style="font-size:0.70rem;margin-bottom:0.15rem;">INVOICE</div>'
        f'<div class="fa-card-title" style="font-size:1.04rem;margin-bottom:0.18rem;">{safe_invoice}</div>'
        f'<div class="fa-muted" style="font-size:0.82rem;">{safe_client}</div>'
        '</div>'
        '<div style="text-align:right;">'
        f'<div style="color:#f8fafc;font-size:1.08rem;font-weight:760;margin-bottom:0.25rem;">{money(amount)}</div>'
        '<div style="display:flex;gap:0.35rem;justify-content:flex-end;flex-wrap:wrap;">'
        f'<span style="display:inline-block;padding:0.24rem 0.55rem;border-radius:999px;font-size:0.72rem;font-weight:700;border:1px solid {status_color}55;background:{status_color}18;color:{status_color};">{status_text}</span>'
        f'<span style="display:inline-block;padding:0.24rem 0.55rem;border-radius:999px;font-size:0.72rem;font-weight:700;border:1px solid {due_color}44;background:{due_color}12;color:{due_color};">{due_message}</span>'
        '</div>'
        '</div>'
        '</div>'
        '<div style="display:flex;justify-content:space-between;gap:0.75rem;margin-top:0.9rem;color:#94a3b8;font-size:0.74rem;">'
        f'<span>Paid {money(total_paid)}</span>'
        f'<span>Remaining {money(remaining)}</span>'
        '</div>'
        '<div class="fa-progress-track" style="margin-top:0.35rem;">'
        f'<div class="fa-progress-fill" style="width:{paid_ratio}%;"></div>'
        '</div>'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# PDF GENERATOR
# --------------------------------------------------

def generate_invoice_pdf(
    invoice_number,
    client,
    amount,
    status,
    invoice_date,
    due_date
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    content = []

    content.append(
        Paragraph(
            "<b>FINANCE ASSISTANT</b>",
            styles["Title"]
        )
    )

    content.append(
        Paragraph(
            "Professional Invoice",
            styles["Heading2"]
        )
    )

    content.append(Spacer(1, 25))

    invoice_details = [
        ["Invoice Number", invoice_number],
        ["Client", client],
        ["Invoice Date", invoice_date or "—"],
        ["Due Date", due_date or "—"],
        ["Status", status],
    ]

    details_table = Table(
        invoice_details,
        colWidths=[150, 300]
    )

    details_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#F1F3F5")
            ),
            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                10
            ),
        ])
    )

    content.append(details_table)
    content.append(Spacer(1, 30))

    amount_table = Table(
        [
            ["Description", "Amount"],
            [
                "Invoice Amount",
                f"PKR {amount:,.2f}"
            ]
        ],
        colWidths=[300, 150]
    )

    amount_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#212529")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "RIGHT"
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                10
            ),
        ])
    )

    content.append(amount_table)
    content.append(Spacer(1, 35))

    content.append(
        Paragraph(
            "Generated by Finance Assistant",
            styles["Normal"]
        )
    )

    document.build(content)
    buffer.seek(0)

    return buffer


# --------------------------------------------------
# PAGE
# --------------------------------------------------

def show_invoices_page():
    update_overdue_invoices()

    st.markdown(
        """
        <div class="fa-eyebrow">MONEY</div>
        <h1 style="margin-bottom:0.25rem;">Invoices</h1>
        <div class="fa-muted">
            Create invoices, track collections and manage payment status.
        </div>
        """,
        unsafe_allow_html=True,
    )

    clients = get_clients()

    if not clients:
        st.warning(
            "Add at least one client before creating an invoice."
        )
        return

    client_names = [
        client[1]
        for client in clients
    ]

    invoices = get_invoice_management_data()
    payment_events_by_invoice = (
        get_all_payment_events_grouped()
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    total_invoiced = 0.0
    total_paid = 0.0
    total_outstanding = 0.0
    overdue_count = 0

    for invoice in invoices:
        invoice_number = invoice[0]
        amount = float(invoice[2] or 0)
        status = str(invoice[3] or "")
        due_date = invoice[5]

        payment_summary = get_payment_summary(
            invoice_number
        )

        paid = (
            float(payment_summary["total_paid"])
            if payment_summary
            else 0.0
        )

        remaining = max(
            amount - paid,
            0
        )

        total_invoiced += amount
        total_paid += paid
        total_outstanding += remaining

        due_obj = parse_date(due_date)

        if (
            remaining > 0
            and (
                status.strip().lower() == "overdue"
                or (
                    due_obj is not None
                    and due_obj < date.today()
                )
            )
        ):
            overdue_count += 1

    st.markdown(
        "<div style='height:0.7rem'></div>",
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Total Invoiced",
            money(total_invoiced)
        )

    with m2:
        st.metric(
            "Collected",
            money(total_paid)
        )

    with m3:
        st.metric(
            "Outstanding",
            money(total_outstanding)
        )

    with m4:
        st.metric(
            "Overdue",
            overdue_count
        )

    st.markdown(
        "<div style='height:0.8rem'></div>",
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # CREATE INVOICE
    # --------------------------------------------------

    create_col, spacer_col = st.columns(
        [1.4, 3]
    )

    with create_col:
        with st.expander(
            "＋ Create New Invoice",
            expanded=False
        ):
            with st.form("invoice_form"):
                invoice_number = st.text_input(
                    "Invoice Number",
                    placeholder="e.g. INV-1042"
                )

                client = st.selectbox(
                    "Client",
                    client_names
                )

                amount = st.number_input(
                    "Amount",
                    min_value=0.0,
                    step=100.0
                )

                date_col1, date_col2 = st.columns(2)

                with date_col1:
                    invoice_date_value = st.date_input(
                        "Invoice Date",
                        value=date.today()
                    )

                with date_col2:
                    due_date_value = st.date_input(
                        "Due Date",
                        value=date.today()
                    )

                status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS
                )

                submitted = st.form_submit_button(
                    "Save Invoice",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    cleaned_number = invoice_number.strip()

                    if not cleaned_number:
                        st.error(
                            "Invoice number is required."
                        )

                    elif amount <= 0:
                        st.error(
                            "Invoice amount must be greater than zero."
                        )

                    elif due_date_value < invoice_date_value:
                        st.error(
                            "Due date cannot be before the invoice date."
                        )

                    elif invoice_exists(cleaned_number):
                        st.error(
                            "An invoice with this number already exists."
                        )

                    else:
                        add_invoice(
                            cleaned_number,
                            client,
                            amount,
                            status,
                            invoice_date_value.isoformat(),
                            due_date_value.isoformat()
                        )

                        st.success(
                            "Invoice saved successfully."
                        )

                        st.rerun()

    # --------------------------------------------------
    # SEARCH + FILTER
    # --------------------------------------------------

    st.markdown("### Invoice Management")
    st.caption(
        "Search, filter and open an invoice to manage dates, status and payments."
    )

    if not invoices:
        st.info("No invoices yet.")
        return

    search_col, status_col, due_col = st.columns(
        [1.7, 1, 1]
    )

    with search_col:
        search = st.text_input(
            "Search",
            placeholder="Invoice number or client...",
            label_visibility="collapsed"
        )

    statuses = sorted(
        {
            str(invoice[3])
            for invoice in invoices
        }
    )

    with status_col:
        status_filter = st.selectbox(
            "Status",
            ["All"] + statuses,
            label_visibility="collapsed"
        )

    with due_col:
        due_filter = st.selectbox(
            "Due",
            [
                "All",
                "Overdue",
                "Due Soon",
                "Not Due Soon",
            ],
            label_visibility="collapsed"
        )

    filtered_invoices = []

    for invoice in invoices:
        number = str(invoice[0])
        client_name = str(invoice[1])
        status = str(invoice[3])
        due_date = invoice[5]

        search_value = search.lower().strip()

        matches_search = (
            not search_value
            or search_value in number.lower()
            or search_value in client_name.lower()
        )

        matches_status = (
            status_filter == "All"
            or status == status_filter
        )

        due_obj = parse_date(due_date)
        days_remaining = None

        if due_obj:
            days_remaining = (
                due_obj - date.today()
            ).days

        if due_filter == "All":
            matches_due = True

        elif due_filter == "Overdue":
            matches_due = (
                days_remaining is not None
                and days_remaining < 0
                and status.strip().lower() != "paid"
            )

        elif due_filter == "Due Soon":
            matches_due = (
                days_remaining is not None
                and 0 <= days_remaining <= 7
                and status.strip().lower() != "paid"
            )

        else:
            matches_due = (
                days_remaining is None
                or days_remaining > 7
                or status.strip().lower() == "paid"
            )

        if (
            matches_search
            and matches_status
            and matches_due
        ):
            filtered_invoices.append(invoice)

    st.caption(
        f"{len(filtered_invoices)} invoice(s) found."
    )

    # --------------------------------------------------
    # INVOICE CARDS
    # --------------------------------------------------

    for invoice_index, invoice in enumerate(
        filtered_invoices
    ):
        invoice_number = invoice[0]
        client = invoice[1]
        amount = float(invoice[2] or 0)
        status = invoice[3]
        invoice_date = invoice[4]
        due_date = invoice[5]

        payment_summary = get_payment_summary(
            invoice_number
        )

        if payment_summary:
            total_paid = float(
                payment_summary["total_paid"]
            )

            remaining_balance = float(
                payment_summary["remaining"]
            )

            payment_count = int(
                payment_summary["payment_count"]
            )

            last_payment_at = (
                payment_summary["last_payment_at"]
            )
        else:
            total_paid = 0.0
            remaining_balance = amount
            payment_count = 0
            last_payment_at = None

        invoice_card_header(
            invoice_number,
            client,
            amount,
            status,
            due_date,
            total_paid,
            remaining_balance
        )

        with st.expander(
            f"Manage {invoice_number}",
            expanded=False
        ):
            # ------------------------------------------
            # OVERVIEW
            # ------------------------------------------

            overview1, overview2, overview3 = st.columns(
                3
            )

            with overview1:
                st.metric(
                    "Invoice Amount",
                    money(amount)
                )

            with overview2:
                st.metric(
                    "Paid",
                    money(total_paid)
                )

            with overview3:
                st.metric(
                    "Remaining",
                    money(remaining_balance)
                )

            st.divider()

            # ------------------------------------------
            # DATES
            # ------------------------------------------

            st.markdown("#### Dates")

            date1, date2 = st.columns(2)

            current_invoice_date = (
                parse_date(invoice_date)
                or date.today()
            )

            current_due_date = (
                parse_date(due_date)
                or current_invoice_date
            )

            with date1:
                edited_invoice_date = st.date_input(
                    "Invoice Date",
                    value=current_invoice_date,
                    key=(
                        f"invoice_date_"
                        f"{invoice_index}_"
                        f"{invoice_number}"
                    )
                )

            with date2:
                edited_due_date = st.date_input(
                    "Due Date",
                    value=current_due_date,
                    key=(
                        f"due_date_"
                        f"{invoice_index}_"
                        f"{invoice_number}"
                    )
                )

            if st.button(
                "Update Dates",
                key=(
                    f"dates_"
                    f"{invoice_index}_"
                    f"{invoice_number}"
                ),
                use_container_width=True
            ):
                if (
                    edited_due_date
                    < edited_invoice_date
                ):
                    st.error(
                        "Due date cannot be before invoice date."
                    )

                else:
                    update_invoice_dates(
                        invoice_number,
                        edited_invoice_date.isoformat(),
                        edited_due_date.isoformat()
                    )

                    st.success(
                        "Invoice dates updated."
                    )

                    st.rerun()

            due_object = parse_date(due_date)

            if (
                due_object
                and str(status).strip().lower()
                != "paid"
            ):
                days_remaining = (
                    due_object - date.today()
                ).days

                if days_remaining < 0:
                    st.error(
                        f"Payment is "
                        f"{abs(days_remaining)} "
                        f"day(s) overdue."
                    )

                elif days_remaining == 0:
                    st.warning(
                        "Payment is due today."
                    )

                elif days_remaining <= 7:
                    st.warning(
                        f"Payment is due in "
                        f"{days_remaining} day(s)."
                    )

                else:
                    st.info(
                        f"Payment due in "
                        f"{days_remaining} days."
                    )

            st.divider()

            # ------------------------------------------
            # STATUS
            # ------------------------------------------

            st.markdown("#### Status")

            if status in STATUS_OPTIONS:
                current_index = (
                    STATUS_OPTIONS.index(status)
                )
            else:
                current_index = 0

            status_col1, status_col2 = st.columns(
                [2.5, 1]
            )

            with status_col1:
                new_status = st.selectbox(
                    "Change Status",
                    STATUS_OPTIONS,
                    index=current_index,
                    key=(
                        f"status_"
                        f"{invoice_index}_"
                        f"{invoice_number}"
                    )
                )

            with status_col2:
                st.markdown(
                    "<div style='height:1.7rem'></div>",
                    unsafe_allow_html=True
                )

                if st.button(
                    "Update Status",
                    key=(
                        f"update_"
                        f"{invoice_index}_"
                        f"{invoice_number}"
                    ),
                    use_container_width=True
                ):
                    update_invoice_status(
                        invoice_number,
                        new_status
                    )

                    st.success(
                        f"{invoice_number} "
                        f"updated to {new_status}."
                    )

                    st.rerun()

            st.divider()

            # ------------------------------------------
            # PAYMENT TRACKING
            # ------------------------------------------

            st.markdown("#### Payment Tracking")

            if total_paid <= 0:
                payment_state = "Unpaid"

            elif total_paid < amount:
                payment_state = (
                    "Partially Paid"
                )

            else:
                payment_state = "Paid"

            pay1, pay2, pay3, pay4 = st.columns(4)

            with pay1:
                st.metric(
                    "Paid",
                    money(total_paid)
                )

            with pay2:
                st.metric(
                    "Remaining",
                    money(remaining_balance)
                )

            with pay3:
                st.metric(
                    "Payment State",
                    payment_state
                )

            with pay4:
                st.metric(
                    "Payments",
                    payment_count
                )

            if last_payment_at:
                st.caption(
                    f"Last payment recorded: "
                    f"{last_payment_at}"
                )

            if remaining_balance > 0:
                with st.form(
                    f"payment_form_"
                    f"{invoice_index}_"
                    f"{invoice_number}"
                ):
                    payment_amount = (
                        st.number_input(
                            "Payment Amount",
                            min_value=0.0,
                            max_value=float(
                                remaining_balance
                            ),
                            step=100.0,
                            key=(
                                f"payment_amount_"
                                f"{invoice_index}_"
                                f"{invoice_number}"
                            )
                        )
                    )

                    payment_note = (
                        st.text_input(
                            "Payment Note",
                            placeholder=(
                                "e.g. Bank transfer"
                            ),
                            key=(
                                f"payment_note_"
                                f"{invoice_index}_"
                                f"{invoice_number}"
                            )
                        )
                    )

                    payment_submitted = (
                        st.form_submit_button(
                            "Record Payment",
                            type="primary",
                            use_container_width=True
                        )
                    )

                    if payment_submitted:
                        if payment_amount <= 0:
                            st.error(
                                "Payment must be "
                                "greater than zero."
                            )

                        else:
                            if (
                                total_paid
                                + payment_amount
                                >= amount
                            ):
                                new_payment_status = (
                                    "Paid"
                                )
                            else:
                                new_payment_status = (
                                    "Partially Paid"
                                )

                            add_payment_event(
                                invoice_number,
                                new_payment_status,
                                payment_amount,
                                payment_note
                            )

                            if (
                                new_payment_status
                                == "Paid"
                            ):
                                update_invoice_status(
                                    invoice_number,
                                    "Paid"
                                )

                            elif (
                                new_payment_status
                                == "Partially Paid"
                            ):
                                if status not in (
                                    "Hold",
                                    "Rejected",
                                    "Overdue"
                                ):
                                    update_invoice_status(
                                        invoice_number,
                                        "Pending"
                                    )

                            st.success(
                                f"Payment of "
                                f"{money(payment_amount)} "
                                f"recorded."
                            )

                            st.rerun()

            else:
                st.success(
                    "Invoice has been fully paid."
                )

            # ------------------------------------------
            # PAYMENT HISTORY
            # ------------------------------------------

            payment_events = (
                payment_events_by_invoice.get(
                    invoice_number,
                    []
                )
            )

            if payment_events:
                st.markdown(
                    "#### Payment History"
                )

                payment_history = []

                for event in payment_events:
                    payment_history.append({
                        "Amount": money(event[2]),
                        "Status": event[1],
                        "Note": (
                            event[3]
                            if event[3]
                            else "—"
                        ),
                        "Recorded": event[4]
                    })

                st.dataframe(
                    payment_history,
                    use_container_width=True,
                    hide_index=True
                )

            # ------------------------------------------
            # PDF
            # ------------------------------------------

            st.divider()

            pdf = generate_invoice_pdf(
                invoice_number,
                client,
                amount,
                status,
                invoice_date,
                due_date
            )

            st.download_button(
                "Download PDF Invoice",
                data=pdf,
                file_name=f"{invoice_number}.pdf",
                mime="application/pdf",
                key=(
                    f"pdf_"
                    f"{invoice_index}_"
                    f"{invoice_number}"
                ),
                use_container_width=True
            )