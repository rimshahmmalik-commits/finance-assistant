import streamlit as st
from database.database import add_client, get_clients


def show_clients_page():
    st.title("Clients")

    st.subheader("Add New Client")

    company = st.text_input("Company Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")

    if st.button("Save Client"):
        if company:
            add_client(company, email, phone)
            st.success("Client added successfully!")
            st.rerun()
        else:
            st.error("Company name is required.")

    st.divider()

    st.subheader("Saved Clients")

    clients = get_clients()

    if clients:
        for client in clients:
            st.write(f"🏢 {client[1]}")
            st.write(f"📧 {client[2]}")
            st.write(f"📞 {client[3]}")
            st.write("---")
    else:
        st.info("No clients added yet.")