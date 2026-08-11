import streamlit as st

from database.database import (
    get_reminder_queue,
    add_reminder_event,
    get_reminder_events,
)

from email_service.sender import send_gmail


def build_reminder_message(item):
    client = item["client"]
    invoice_number = item["invoice_number"]
    remaining = item["remaining"]
    due_date = item["due_date"]
    reminder_type = item["reminder_type"]

    if reminder_type == "Overdue":
        return (
            f"Hello {client},\n\n"
            f"This is a reminder that invoice {invoice_number} "
            f"with an outstanding balance of PKR {remaining:,.2f} "
            f"was due on {due_date}.\n\n"
            f"Please arrange payment at your earliest convenience.\n\n"
            f"Thank you."
        )

    if reminder_type == "Due Today":
        return (
            f"Hello {client},\n\n"
            f"This is a reminder that invoice {invoice_number} "
            f"with an outstanding balance of PKR {remaining:,.2f} "
            f"is due today.\n\n"
            f"Thank you."
        )

    return (
        f"Hello {client},\n\n"
        f"This is a friendly reminder that invoice {invoice_number} "
        f"with an outstanding balance of PKR {remaining:,.2f} "
        f"is due on {due_date}.\n\n"
        f"Thank you."
    )


def build_subject(item):
    invoice_number = item["invoice_number"]
    reminder_type = item["reminder_type"]

    if reminder_type == "Overdue":
        return f"Overdue Invoice Reminder — {invoice_number}"

    if reminder_type == "Due Today":
        return f"Invoice Due Today — {invoice_number}"

    return f"Upcoming Invoice Reminder — {invoice_number}"


def already_sent(
    events,
    invoice_number,
    reminder_type
):
    for event in events:
        if (
            event[0] == invoice_number
            and event[1] == reminder_type
            and event[3] == "Sent"
        ):
            return True

    return False


def show_reminders_page():

    st.title("Reminder Center")

    st.caption(
        "Review and send upcoming or overdue invoice reminders."
    )

    queue = get_reminder_queue()
    events = get_reminder_events()

    # --------------------------------------------------
    # EMPTY QUEUE
    # --------------------------------------------------

    if not queue:

        st.success(
            "No payment reminders need attention right now."
        )

    else:

        overdue_count = sum(
            1
            for item in queue
            if item["reminder_type"] == "Overdue"
        )

        due_today_count = sum(
            1
            for item in queue
            if item["reminder_type"] == "Due Today"
        )

        due_soon_count = sum(
            1
            for item in queue
            if item["reminder_type"] == "Due Soon"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Overdue",
                overdue_count
            )

        with col2:
            st.metric(
                "Due Today",
                due_today_count
            )

        with col3:
            st.metric(
                "Due Soon",
                due_soon_count
            )

        st.divider()

        # --------------------------------------------------
        # REMINDER QUEUE
        # --------------------------------------------------

        for index, item in enumerate(queue):

            label = (
                f"{item['invoice_number']} — "
                f"{item['client']} — "
                f"{item['reminder_type']}"
            )

            with st.expander(label):

                st.write(
                    f"**Client:** {item['client']}"
                )

                st.write(
                    f"**Email:** "
                    f"{item['email'] or 'No email saved'}"
                )

                st.write(
                    f"**Due Date:** {item['due_date']}"
                )

                st.write(
                    f"**Outstanding:** "
                    f"PKR {item['remaining']:,.2f}"
                )

                # ------------------------------------------
                # DUPLICATE SEND PROTECTION
                # ------------------------------------------

                if already_sent(
                    events,
                    item["invoice_number"],
                    item["reminder_type"]
                ):

                    st.success(
                        "A reminder of this type has already been sent."
                    )

                    continue

                # ------------------------------------------
                # SUBJECT
                # ------------------------------------------

                default_subject = build_subject(
                    item
                )

                subject = st.text_input(
                    "Email Subject",
                    value=default_subject,
                    key=(
                        f"subject_"
                        f"{index}_"
                        f"{item['invoice_number']}"
                    )
                )

                # ------------------------------------------
                # MESSAGE
                # ------------------------------------------

                message_key = (
                    f"reminder_message_"
                    f"{index}_"
                    f"{item['invoice_number']}"
                )

                if message_key not in st.session_state:

                    st.session_state[
                        message_key
                    ] = build_reminder_message(
                        item
                    )

                edited_message = st.text_area(
                    "Reminder Message",
                    value=st.session_state[
                        message_key
                    ],
                    height=180,
                    key=(
                        f"message_editor_"
                        f"{index}_"
                        f"{item['invoice_number']}"
                    )
                )

                # ------------------------------------------
                # ACTIONS
                # ------------------------------------------

                col_prepare, col_send = st.columns(2)

                with col_prepare:

                    if st.button(
                        "Prepare Reminder",
                        key=(
                            f"prepare_"
                            f"{index}_"
                            f"{item['invoice_number']}"
                        )
                    ):

                        add_reminder_event(
                            item["invoice_number"],
                            item["reminder_type"],
                            edited_message,
                            "Prepared"
                        )

                        st.success(
                            "Reminder prepared and logged."
                        )

                with col_send:

                    if st.button(
                        "Send Email",
                        type="primary",
                        key=(
                            f"send_"
                            f"{index}_"
                            f"{item['invoice_number']}"
                        )
                    ):

                        # ----------------------------------
                        # VALIDATION
                        # ----------------------------------

                        if not item["email"]:

                            st.error(
                                "No client email is saved."
                            )

                        elif (
                            "@" not in item["email"]
                            or "." not in item["email"]
                        ):

                            st.error(
                                "The saved client email is invalid."
                            )

                        elif not subject.strip():

                            st.error(
                                "Email subject cannot be empty."
                            )

                        elif not edited_message.strip():

                            st.error(
                                "Reminder message cannot be empty."
                            )

                        else:

                            # ----------------------------------
                            # REAL GMAIL SEND
                            # ----------------------------------

                            try:

                                with st.spinner(
                                    "Sending reminder..."
                                ):

                                    result = send_gmail(
                                        item["email"],
                                        subject.strip(),
                                        edited_message.strip()
                                    )

                                if result.get("success"):

                                    # ONLY log Sent after Gmail
                                    # confirms the API request worked.

                                    add_reminder_event(
                                        item["invoice_number"],
                                        item["reminder_type"],
                                        edited_message.strip(),
                                        "Sent"
                                    )

                                    st.success(
                                        f"Reminder sent successfully "
                                        f"to {item['email']}."
                                    )

                                    st.balloons()

                                    st.rerun()

                                else:

                                    st.error(
                                        "Gmail did not confirm "
                                        "the email was sent."
                                    )

                            except Exception as error:

                                st.error(
                                    f"Email could not be sent: {error}"
                                )

    # --------------------------------------------------
    # REMINDER HISTORY
    # --------------------------------------------------

    st.divider()

    st.subheader(
        "Reminder History"
    )

    events = get_reminder_events()

    if not events:

        st.info(
            "No reminder events recorded yet."
        )

    else:

        rows = []

        for event in events:

            rows.append({
                "Invoice": event[0],
                "Type": event[1],
                "Status": event[3],
                "Recorded": event[4],
                "Message": event[2],
            })

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )