from datetime import date, datetime

import pandas as pd
import streamlit as st

from database.database import (
    get_export_clients,
    get_export_invoices,
    get_export_transactions,
    get_export_payments,
)


def _money(value):
    return f"PKR {float(value or 0):,.0f}"


def _to_date(value):
    """Convert supported date-like values into datetime.date safely."""
    if value is None:
        return None

    if isinstance(value, str) and not value.strip():
        return None

    # datetime is also an instance of date, so check it first.
    if isinstance(value, datetime):
        return value.date()

    # A plain date is already exactly what the dashboard needs.
    if isinstance(value, date):
        return value

    try:
        parsed = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed):
            return None

        if isinstance(parsed, pd.Timestamp):
            return parsed.date()

        if isinstance(parsed, datetime):
            return parsed.date()

        if isinstance(parsed, date):
            return parsed

        return None
    except (TypeError, ValueError, OverflowError):
        return None


def _invoice_rows():
    return [
        {
            "id": item[0],
            "invoice_number": item[1],
            "client": item[2],
            "amount": float(item[3] or 0),
            "status": str(item[4] or "").strip().lower(),
            "invoice_date": _to_date(item[5]),
            "due_date": _to_date(item[6]),
        }
        for item in get_export_invoices()
    ]


def _transaction_rows():
    return [
        {
            "id": item[0],
            "date": _to_date(item[1]),
            "type": str(item[2] or "").strip().lower(),
            "description": item[3] or "Untitled transaction",
            "amount": float(item[4] or 0),
            "category": item[5] or "Uncategorized",
            "account": item[6] or "—",
            "reference": item[7] or "—",
            "source": item[8] or "—",
            "created_at": item[9],
        }
        for item in get_export_transactions()
    ]


def _payment_totals():
    totals = {}

    for item in get_export_payments():
        invoice_number = item[1]
        totals[invoice_number] = (
            totals.get(invoice_number, 0)
            + float(item[3] or 0)
        )

    return totals


def _section_title(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def _kpi_card(label, value, note, tone="info"):
    st.markdown(
        f"""
        <div class="fa-kpi {tone}">
            <div class="fa-kpi-label">{label}</div>
            <div class="fa-kpi-value">{value}</div>
            <div class="fa-kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_dashboard_page():
    today = date.today()

    invoices = _invoice_rows()
    transactions = _transaction_rows()
    payments = _payment_totals()
    clients = get_export_clients()

    # --------------------------------------------------
    # FILTER
    # --------------------------------------------------

    period_labels = {
        "30D": 30,
        "3M": 90,
        "6M": 183,
        "12M": 365,
    }

    header_left, header_right = st.columns([4.3, 1])

    with header_left:
        st.markdown(
            """
            <div class="fa-eyebrow">OVERVIEW</div>
            <h1 style="margin-bottom:0.25rem;">Dashboard</h1>
            <div class="fa-muted">
                Your finance command center — cash, collections and activity at a glance.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_right:
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        period = st.segmented_control(
            "Period",
            list(period_labels.keys()),
            default="6M",
            label_visibility="collapsed",
        )

        if period is None:
            period = "6M"

        st.caption(f"Updated {today.strftime('%d %b %Y')}")

    days = period_labels[period]
    period_start = today - pd.Timedelta(days=days)
    period_start = _to_date(period_start)

    filtered_transactions = [
        tx
        for tx in transactions
        if tx["date"] is not None
        and tx["date"] >= period_start
    ]

    # --------------------------------------------------
    # CORE CALCULATIONS
    # --------------------------------------------------

    invoice_count = len(invoices)

    paid_invoice_value = sum(
        invoice["amount"]
        for invoice in invoices
        if invoice["status"] == "paid"
    )

    transaction_income = sum(
        tx["amount"]
        for tx in filtered_transactions
        if tx["type"] == "income"
    )

    transaction_expenses = sum(
        tx["amount"]
        for tx in filtered_transactions
        if tx["type"] == "expense"
    )

    net_cash_flow = transaction_income - transaction_expenses

    pending_invoices = [
        invoice
        for invoice in invoices
        if invoice["status"] == "pending"
    ]

    overdue_invoices = [
        invoice
        for invoice in invoices
        if (
            invoice["status"] == "overdue"
            or (
                invoice["status"] not in {"paid", "cancelled"}
                and invoice["due_date"] is not None
                and invoice["due_date"] < today
            )
        )
    ]

    outstanding_by_client = {}

    for invoice in invoices:
        if invoice["status"] in {"paid", "cancelled"}:
            continue

        paid_amount = payments.get(invoice["invoice_number"], 0)
        outstanding = max(invoice["amount"] - paid_amount, 0)

        if outstanding <= 0:
            continue

        client = invoice["client"] or "Unknown client"
        outstanding_by_client[client] = (
            outstanding_by_client.get(client, 0)
            + outstanding
        )

    total_outstanding = sum(outstanding_by_client.values())

    total_invoiced = sum(invoice["amount"] for invoice in invoices)
    total_collected = sum(payments.values())

    collection_rate = (
        (total_collected / total_invoiced) * 100
        if total_invoiced > 0
        else 0
    )

    # --------------------------------------------------
    # KPI ROW
    # --------------------------------------------------

    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        _kpi_card(
            "Recorded Revenue",
            _money(paid_invoice_value),
            f"{invoice_count} total invoices",
            "success",
        )

    with k2:
        _kpi_card(
            "Outstanding",
            _money(total_outstanding),
            f"{len(outstanding_by_client)} customer(s)",
            "violet",
        )

    with k3:
        _kpi_card(
            "Net Cash Flow",
            _money(net_cash_flow),
            f"{period} operating activity",
            "success" if net_cash_flow >= 0 else "danger",
        )

    with k4:
        _kpi_card(
            "Needs Attention",
            str(len(overdue_invoices)),
            "Overdue invoices",
            "danger" if overdue_invoices else "success",
        )

    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

    # --------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------

    _section_title(
        "Quick Actions",
        "Jump into the most common finance workflows.",
    )

    qa1, qa2, qa3, qa4 = st.columns(4)

    with qa1:
        if st.button("＋ Create Invoice", use_container_width=True):
            st.session_state.current_page = "Invoices"
            st.rerun()

    with qa2:
        if st.button("⇩ Smart Import", use_container_width=True):
            st.session_state.current_page = "Smart Import"
            st.rerun()

    with qa3:
        if st.button("◎ Add Client", use_container_width=True):
            st.session_state.current_page = "Clients"
            st.rerun()

    with qa4:
        if st.button("✦ Ask AI Advisor", use_container_width=True):
            st.session_state.current_page = "AI Assistant"
            st.rerun()

    st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

    # --------------------------------------------------
    # CASH FLOW + RECEIVABLES
    # --------------------------------------------------

    left, right = st.columns([1.65, 1])

    with left:
        _section_title(
            "Cash Flow",
            f"Recorded income and expenses over the selected {period} period.",
        )

        if filtered_transactions:
            monthly = {}

            for tx in filtered_transactions:
                month_key = tx["date"].replace(day=1)
                monthly.setdefault(
                    month_key,
                    {"Income": 0.0, "Expenses": 0.0},
                )

                if tx["type"] == "income":
                    monthly[month_key]["Income"] += tx["amount"]
                elif tx["type"] == "expense":
                    monthly[month_key]["Expenses"] += tx["amount"]

            chart_rows = []

            for month_key in sorted(monthly.keys()):
                chart_rows.append(
                    {
                        "Month": month_key.strftime("%b %y"),
                        "Income": monthly[month_key]["Income"],
                        "Expenses": monthly[month_key]["Expenses"],
                    }
                )

            cash_df = pd.DataFrame(chart_rows).set_index("Month")

            st.bar_chart(
                cash_df,
                height=300,
                use_container_width=True,
                color=["#22c55e", "#ef4444"],
            )
        else:
            st.info(
                "No transactions recorded in this period. "
                "Try a longer range or import new activity."
            )

        c1, c2, c3 = st.columns(3)

        with c1:
            _kpi_card(
                "Income",
                _money(transaction_income),
                period,
                "success",
            )

        with c2:
            _kpi_card(
                "Expenses",
                _money(transaction_expenses),
                period,
                "danger",
            )

        with c3:
            _kpi_card(
                "Net",
                _money(net_cash_flow),
                period,
                "success" if net_cash_flow >= 0 else "danger",
            )

    with right:
        _section_title(
            "Top Receivables",
            "Customers with the largest recorded outstanding balances.",
        )

        ranked_receivables = sorted(
            outstanding_by_client.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]

        if ranked_receivables:
            max_amount = max(amount for _, amount in ranked_receivables) or 1

            for position, (client, amount) in enumerate(
                ranked_receivables,
                start=1,
            ):
                width = max(8, int((amount / max_amount) * 100))

                st.markdown(
                    f"""
                    <div class="fa-card" style="margin-bottom:0.55rem;padding:0.78rem 0.88rem;">
                        <div style="display:flex;justify-content:space-between;gap:1rem;">
                            <div>
                                <span class="fa-muted" style="font-size:0.70rem;">#{position}</span>
                                <div class="fa-card-title" style="margin:0.08rem 0;">{client}</div>
                            </div>
                            <div style="font-weight:700;text-align:right;">{_money(amount)}</div>
                        </div>
                        <div class="fa-progress-track" style="margin-top:0.55rem;">
                            <div class="fa-progress-fill" style="width:{width}%;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("No outstanding customer balances recorded.")

    st.markdown("<div style='height:0.95rem'></div>", unsafe_allow_html=True)

    # --------------------------------------------------
    # ATTENTION + RECENT ACTIVITY
    # --------------------------------------------------

    attention_col, activity_col = st.columns([1, 1.65])

    with attention_col:
        _section_title(
            "Needs Attention",
            "Items worth checking first.",
        )

        if overdue_invoices:
            for invoice in sorted(
                overdue_invoices,
                key=lambda item: item["due_date"] or today,
            )[:4]:
                due_date = invoice["due_date"]

                if due_date:
                    days_overdue = max((today - due_date).days, 0)
                    due_text = due_date.strftime("%d %b %Y")
                    urgency = (
                        f"{days_overdue} day(s) overdue"
                        if days_overdue > 0
                        else "Due today"
                    )
                else:
                    due_text = "No due date"
                    urgency = "Review required"

                st.markdown(
                    f"""
                    <div class="fa-card" style="
                        margin-bottom:0.55rem;
                        border-left:3px solid #ef4444;
                    ">
                        <div style="display:flex;justify-content:space-between;gap:0.75rem;">
                            <div>
                                <div class="fa-card-title">
                                    {invoice["invoice_number"]} · {invoice["client"]}
                                </div>
                                <div class="fa-muted" style="font-size:0.80rem;">
                                    {_money(invoice["amount"])} · Due {due_text}
                                </div>
                            </div>
                            <div class="fa-negative" style="font-size:0.74rem;font-weight:700;text-align:right;">
                                {urgency}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        elif pending_invoices:
            st.info(
                f"{len(pending_invoices)} invoice(s) are pending, "
                "but none are currently overdue."
            )
        else:
            st.success("Nothing urgent is currently flagged.")

        if st.button(
            "Open Reminder Center",
            use_container_width=True,
            key="dashboard_reminders",
        ):
            st.session_state.current_page = "Reminder Center"
            st.rerun()

    with activity_col:
        _section_title(
            "Recent Transactions",
            "Latest recorded business activity.",
        )

        recent = sorted(
            transactions,
            key=lambda tx: tx["date"] or date.min,
            reverse=True,
        )[:6]

        if recent:
            activity_df = pd.DataFrame(
                [
                    {
                        "Date": (
                            tx["date"].strftime("%d %b")
                            if tx["date"]
                            else "—"
                        ),
                        "Description": tx["description"],
                        "Category": tx["category"],
                        "Type": (
                            "🟢 Income"
                            if tx["type"] == "income"
                            else "🔴 Expense"
                            if tx["type"] == "expense"
                            else tx["type"].title()
                        ),
                        "Amount": _money(tx["amount"]),
                    }
                    for tx in recent
                ]
            )

            st.dataframe(
                activity_df,
                hide_index=True,
                use_container_width=True,
                height=252,
            )
        else:
            st.info(
                "No transactions yet. Use Smart Import to bring in "
                "your first finance activity."
            )

    st.markdown("<div style='height:0.95rem'></div>", unsafe_allow_html=True)

    # --------------------------------------------------
    # OPERATIONAL HEALTH
    # --------------------------------------------------

    _section_title(
        "Operational Health",
        "A compact snapshot of how the workspace is performing.",
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        _kpi_card(
            "Collection Rate",
            f"{collection_rate:.1f}%",
            "Collected vs invoiced",
            "success" if collection_rate >= 70 else "warning",
        )

    with s2:
        _kpi_card(
            "Clients",
            str(len(clients)),
            "Active records",
            "info",
        )

    with s3:
        open_invoice_count = sum(
            1
            for invoice in invoices
            if invoice["status"] not in {"paid", "cancelled"}
        )

        _kpi_card(
            "Open Invoices",
            str(open_invoice_count),
            f"{len(overdue_invoices)} overdue",
            "warning" if overdue_invoices else "violet",
        )

    with s4:
        _kpi_card(
            "Transactions",
            str(len(transactions)),
            "Recorded activity",
            "info",
        )