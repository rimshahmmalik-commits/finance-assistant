from database.database import (
    get_reminder_queue,
    get_reminder_events,
    add_reminder_event,
)

from email_service.sender import send_gmail


def build_automatic_message(item):
    client = item["client"]
    invoice_number = item["invoice_number"]
    remaining = item["remaining"]
    due_date = item["due_date"]
    reminder_type = item["reminder_type"]

    if reminder_type == "Overdue":
        subject = f"Overdue Invoice Reminder — {invoice_number}"

        message = (
            f"Hello {client},\n\n"
            f"This is a reminder that invoice {invoice_number} "
            f"with an outstanding balance of PKR {remaining:,.2f} "
            f"was due on {due_date}.\n\n"
            f"Please arrange payment at your earliest convenience.\n\n"
            f"Thank you."
        )

    elif reminder_type == "Due Today":
        subject = f"Invoice Due Today — {invoice_number}"

        message = (
            f"Hello {client},\n\n"
            f"This is a reminder that invoice {invoice_number} "
            f"with an outstanding balance of PKR {remaining:,.2f} "
            f"is due today.\n\n"
            f"Thank you."
        )

    else:
        subject = f"Upcoming Invoice Reminder — {invoice_number}"

        message = (
            f"Hello {client},\n\n"
            f"This is a friendly reminder that invoice {invoice_number} "
            f"with an outstanding balance of PKR {remaining:,.2f} "
            f"is due on {due_date}.\n\n"
            f"Thank you."
        )

    return subject, message


def reminder_already_sent(
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


def run_automatic_reminders():
    queue = get_reminder_queue()
    events = get_reminder_events()

    results = []

    for item in queue:

        invoice_number = item["invoice_number"]
        reminder_type = item["reminder_type"]
        email = item["email"]

        if reminder_already_sent(
            events,
            invoice_number,
            reminder_type
        ):
            results.append({
                "invoice": invoice_number,
                "status": "Skipped",
                "reason": "Reminder already sent"
            })
            continue

        if not email or "@" not in email:
            results.append({
                "invoice": invoice_number,
                "status": "Skipped",
                "reason": "Missing or invalid email"
            })
            continue

        subject, message = build_automatic_message(item)

        try:
            result = send_gmail(
                email,
                subject,
                message
            )

            if result.get("success"):

                add_reminder_event(
                    invoice_number,
                    reminder_type,
                    message,
                    "Sent"
                )

                results.append({
                    "invoice": invoice_number,
                    "status": "Sent",
                    "reason": email
                })

            else:
                results.append({
                    "invoice": invoice_number,
                    "status": "Failed",
                    "reason": "Gmail did not confirm delivery"
                })

        except Exception as error:
            results.append({
                "invoice": invoice_number,
                "status": "Failed",
                "reason": str(error)
            })

    return results