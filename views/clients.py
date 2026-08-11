import streamlit as st

from database.database import (
    add_client,
    get_clients,
    update_client,
)


def show_clients_page():
    st.title("Clients")

    st.subheader("Add New Client")

    with st.form("add_client_form"):

        company = st.text_input(
            "Company Name"
        )

        email = st.text_input(
            "Email"
        )

        phone = st.text_input(
            "Phone Number"
        )

        submitted = st.form_submit_button(
            "Save Client",
            type="primary"
        )

        if submitted:

            if not company.strip():

                st.error(
                    "Company name is required."
                )

            else:

                add_client(
                    company.strip(),
                    email.strip(),
                    phone.strip()
                )

                st.success(
                    "Client added successfully."
                )

                st.balloons()

                st.rerun()

    st.divider()

    st.subheader("Saved Clients")

    clients = get_clients()

    if not clients:

        st.info(
            "No clients added yet."
        )

        return

    for index, client in enumerate(clients):

        client_id = client[0]
        company = client[1]
        email = client[2] or ""
        phone = client[3] or ""

        with st.expander(
            f"{company}",
            expanded=False
        ):

            st.write(
                f"**Email:** {email or 'Not provided'}"
            )

            st.write(
                f"**Phone:** {phone or 'Not provided'}"
            )

            st.divider()

            st.markdown(
                "### Edit Client"
            )

            with st.form(
                f"edit_client_{client_id}_{index}"
            ):

                edited_company = st.text_input(
                    "Company Name",
                    value=company,
                    key=f"company_{client_id}_{index}"
                )

                edited_email = st.text_input(
                    "Email",
                    value=email,
                    key=f"email_{client_id}_{index}"
                )

                edited_phone = st.text_input(
                    "Phone Number",
                    value=phone,
                    key=f"phone_{client_id}_{index}"
                )

                update_submitted = (
                    st.form_submit_button(
                        "Save Changes"
                    )
                )

                if update_submitted:

                    if not edited_company.strip():

                        st.error(
                            "Company name is required."
                        )

                    else:

                        update_client(
                            client_id,
                            edited_company.strip(),
                            edited_email.strip(),
                            edited_phone.strip()
                        )

                        st.success(
                            "Client updated successfully."
                        )

                        st.rerun()