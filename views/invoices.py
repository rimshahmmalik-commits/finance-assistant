import streamlit as st
from database.database import add_invoice, get_invoices, get_clients


def show_invoices_page():
    st.title("Invoices")
    st.caption("Create and manage invoices.")

    clients = get_clients()

    if not clients:
        st.warning("Add at least one client before creating an invoice.")
        return

    client_names = [client[1] for client in clients]

    st.subheader("Create Invoice")

    with st.form("invoice_form"):
        invoice_number = st.text_input("Invoice Number")

        client = st.selectbox(
            "Client",
            client_names
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        status = st.selectbox(
            "Status",
            ["Pending", "Paid", "Overdue"]
        )

        submitted = st.form_submit_button("Save Invoice")

        if submitted:
            if invoice_number.strip() == "":
                st.error("Invoice number is required.")
            else:
                add_invoice(
                    invoice_number,
                    client,
                    amount,
                    status
                )

                st.success("Invoice saved successfully.")
                st.rerun()

    st.divider()

    st.subheader("Invoice History")

    invoices = get_invoices()

    if invoices:
        data = []

        for invoice in invoices:
            data.append({
                "Invoice": invoice[0],
                "Client": invoice[1],
                "Amount": f"PKR {invoice[2]:,.2f}",
                "Status": invoice[3]
            })

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No invoices yet.")