import streamlit as st

from database.database import (
    get_transactions,
    get_invoice_management_data,
)

from ai.finance_ai import generate_cash_flow_forecast


def show_forecast_page():
    st.title("Cash Flow Forecast")

    st.caption(
        "See upcoming cash-flow risk, expected collections "
        "and the invoices that need your attention."
    )

    # --------------------------------------------------
    # GET DATA
    # --------------------------------------------------

    transactions = get_transactions()
    invoices = get_invoice_management_data()

    forecast = generate_cash_flow_forecast(
        transactions,
        invoices,
        forecast_days=30
    )

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    st.subheader("30-Day Outlook")

    confidence = forecast["confidence"]
    forecast_available = forecast["forecast_available"]

    if confidence == "High":
        st.success("Forecast Confidence: High")

    elif confidence == "Medium":
        st.warning("Forecast Confidence: Medium")

    else:
        st.warning("Forecast Confidence: Low")

    # --------------------------------------------------
    # DATA QUALITY
    # --------------------------------------------------

    data1, data2 = st.columns(2)

    with data1:
        st.metric(
            "History Available",
            f"{forecast['history_days']} days"
        )

    with data2:
        st.metric(
            "Transactions Analysed",
            forecast["transaction_count"]
        )

    st.divider()

    # --------------------------------------------------
    # LIMITED DATA MODE
    # --------------------------------------------------

    if not forecast_available:

        st.subheader("Operating Forecast")

        st.info(
            "There isn't enough transaction history yet "
            "to produce a reliable operating cash-flow forecast."
        )

        for warning in forecast["warnings"]:
            st.warning(warning)

    # --------------------------------------------------
    # FULL FORECAST MODE
    # --------------------------------------------------

    else:

        st.subheader("Projected Cash Movement")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Projected Inflows",
                (
                    f"PKR "
                    f"{forecast['projected_inflows']:,.2f}"
                )
            )

        with col2:
            st.metric(
                "Projected Outflows",
                (
                    f"PKR "
                    f"{forecast['projected_outflows']:,.2f}"
                )
            )

        with col3:
            net_change = forecast[
                "projected_net_change"
            ]

            st.metric(
                "Projected Net Change",
                f"PKR {net_change:,.2f}"
            )

        risk_level = forecast["risk_level"]

        if risk_level == "High":
            st.error(
                "Cash-flow risk is currently HIGH."
            )

        elif risk_level == "Medium":
            st.warning(
                "Cash-flow risk is currently MEDIUM."
            )

        else:
            st.success(
                "Cash-flow risk is currently LOW."
            )

    st.divider()

    # --------------------------------------------------
    # COLLECTION OPPORTUNITY
    # --------------------------------------------------

    st.subheader("Potential Collections")

    potential_collections = forecast[
        "expected_invoice_collections"
    ]

    priority_collections = forecast[
        "priority_collections"
    ]

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Potential Collections",
            f"PKR {potential_collections:,.2f}"
        )

    with col2:
        st.metric(
            "Priority Invoices",
            len(priority_collections)
        )

    st.caption(
        "Potential collections are outstanding invoices "
        "due within the forecast period. They are not "
        "treated as guaranteed cash receipts."
    )

    # --------------------------------------------------
    # PRIORITY COLLECTIONS
    # --------------------------------------------------

    if priority_collections:

        st.subheader("Collection Priorities")

        for item in priority_collections:

            with st.container(border=True):

                st.markdown(
                    f"### {item['invoice']} — "
                    f"{item['client']}"
                )

                c1, c2 = st.columns(2)

                with c1:
                    st.metric(
                        "Outstanding",
                        f"PKR {item['amount']:,.2f}"
                    )

                with c2:
                    st.write("**Due Date**")
                    st.write(
                        item["due_date"].strftime(
                            "%d %b %Y"
                        )
                    )

                st.write(
                    "**Recommended action:** "
                    "Prioritize collection and follow up "
                    "with this customer."
                )

    else:

        st.success(
            "No outstanding invoices require collection "
            "within the forecast period."
        )

    # --------------------------------------------------
    # ASSUMPTIONS
    # --------------------------------------------------

    st.divider()

    with st.expander(
        "How this forecast works"
    ):

        for assumption in forecast[
            "assumptions"
        ]:
            st.write(
                f"• {assumption}"
            )