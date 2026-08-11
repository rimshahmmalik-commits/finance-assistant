import sqlite3
from pathlib import Path
from datetime import datetime, date


BASE_DIR = Path(__file__).resolve().parent.parent
DB_NAME = BASE_DIR / "invoice_ai.db"


# --------------------------------------------------
# CONNECTION
# --------------------------------------------------

def get_connection():
    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


# --------------------------------------------------
# INITIAL SETUP
# --------------------------------------------------

def create_tables():
    create_clients_table()
    create_invoice_table()
    create_review_decisions_table()
    create_payment_events_table()
    create_reminder_events_table()

    migrate_invoice_columns()


def create_clients_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            email TEXT,
            phone TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_invoice_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            client TEXT,
            amount REAL,
            status TEXT,
            invoice_date TEXT,
            due_date TEXT
        )
    """)

    conn.commit()
    conn.close()


def migrate_invoice_columns():
    """
    Adds new columns to older databases without deleting data.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "PRAGMA table_info(invoices)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "invoice_date" not in columns:
        cursor.execute(
            """
            ALTER TABLE invoices
            ADD COLUMN invoice_date TEXT
            """
        )

    if "due_date" not in columns:
        cursor.execute(
            """
            ALTER TABLE invoices
            ADD COLUMN due_date TEXT
            """
        )

    conn.commit()
    conn.close()


def create_review_decisions_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            client TEXT,
            amount REAL,
            risk_score INTEGER,
            detected_issue TEXT,
            ai_summary TEXT,
            ai_recommendation TEXT,
            decision TEXT NOT NULL,
            decision_reason TEXT,
            decided_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_payment_events_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            amount_paid REAL DEFAULT 0,
            note TEXT,
            recorded_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_reminder_events_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminder_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            reminder_type TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            sent_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# CLIENTS
# --------------------------------------------------

def add_client(company, email, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO clients
        (company, email, phone)
        VALUES (?, ?, ?)
        """,
        (
            company,
            email,
            phone
        )
    )

    conn.commit()
    conn.close()


def get_clients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, company, email, phone
        FROM clients
        ORDER BY company
    """)

    clients = cursor.fetchall()

    conn.close()

    return clients


# --------------------------------------------------
# INVOICES
# --------------------------------------------------

def add_invoice(
    invoice_number,
    client,
    amount,
    status,
    invoice_date=None,
    due_date=None
):
    conn = get_connection()
    cursor = conn.cursor()

    if invoice_date is None:
        invoice_date = date.today().isoformat()

    cursor.execute(
        """
        INSERT INTO invoices(
            invoice_number,
            client,
            amount,
            status,
            invoice_date,
            due_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            client,
            amount,
            status,
            invoice_date,
            due_date
        )
    )

    conn.commit()
    conn.close()


def get_invoices():
    """
    Keep existing 4-column structure so Dashboard,
    Smart Import and current invoice code do not break.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            client,
            amount,
            status
        FROM invoices
        ORDER BY id DESC
    """)

    invoices = cursor.fetchall()

    conn.close()

    return invoices


def get_invoice_details():
    """
    Extended invoice data for new features.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            client,
            amount,
            status,
            invoice_date,
            due_date
        FROM invoices
        ORDER BY id DESC
    """)

    invoices = cursor.fetchall()

    conn.close()

    return invoices


def update_invoice_status(
    invoice_number,
    status
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET status = ?
        WHERE invoice_number = ?
        """,
        (
            status,
            invoice_number
        )
    )

    conn.commit()
    conn.close()


def update_invoice_dates(
    invoice_number,
    invoice_date,
    due_date
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET invoice_date = ?,
            due_date = ?
        WHERE invoice_number = ?
        """,
        (
            invoice_date,
            due_date,
            invoice_number
        )
    )

    conn.commit()
    conn.close()


def invoice_exists(invoice_number):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM invoices
        WHERE LOWER(invoice_number) = LOWER(?)
        LIMIT 1
        """,
        (invoice_number,)
    )

    exists = cursor.fetchone() is not None

    conn.close()

    return exists


def update_overdue_invoices():
    """
    Automatically marks unpaid invoices overdue
    once their due date has passed.
    """

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute(
        """
        UPDATE invoices
        SET status = 'Overdue'
        WHERE due_date IS NOT NULL
        AND due_date != ''
        AND due_date < ?
        AND status NOT IN (
            'Paid',
            'Rejected',
            'Hold'
        )
        """,
        (today,)
    )

    conn.commit()
    conn.close()


def get_overdue_invoices():
    update_overdue_invoices()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            client,
            amount,
            status,
            invoice_date,
            due_date
        FROM invoices
        WHERE status = 'Overdue'
        ORDER BY due_date ASC
    """)

    invoices = cursor.fetchall()

    conn.close()

    return invoices


# --------------------------------------------------
# REVIEW DECISIONS
# --------------------------------------------------

def add_review_decision(
    invoice_number,
    client,
    amount,
    risk_score,
    detected_issue,
    ai_summary,
    ai_recommendation,
    decision,
    decision_reason
):
    conn = get_connection()
    cursor = conn.cursor()

    decided_at = datetime.now().isoformat(
        timespec="seconds"
    )

    cursor.execute(
        """
        INSERT INTO review_decisions(
            invoice_number,
            client,
            amount,
            risk_score,
            detected_issue,
            ai_summary,
            ai_recommendation,
            decision,
            decision_reason,
            decided_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            client,
            amount,
            risk_score,
            detected_issue,
            ai_summary,
            ai_recommendation,
            decision,
            decision_reason,
            decided_at
        )
    )

    conn.commit()
    conn.close()


def get_review_decisions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            client,
            amount,
            risk_score,
            detected_issue,
            ai_summary,
            ai_recommendation,
            decision,
            decision_reason,
            decided_at
        FROM review_decisions
        ORDER BY id DESC
    """)

    decisions = cursor.fetchall()

    conn.close()

    return decisions


def get_review_decision_for_invoice(
    invoice_number
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            invoice_number,
            client,
            amount,
            risk_score,
            detected_issue,
            ai_summary,
            ai_recommendation,
            decision,
            decision_reason,
            decided_at
        FROM review_decisions
        WHERE invoice_number = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (invoice_number,)
    )

    decision = cursor.fetchone()

    conn.close()

    return decision


# --------------------------------------------------
# PAYMENT TRACKING
# --------------------------------------------------

def add_payment_event(
    invoice_number,
    payment_status,
    amount_paid,
    note
):
    conn = get_connection()
    cursor = conn.cursor()

    recorded_at = datetime.now().isoformat(
        timespec="seconds"
    )

    cursor.execute(
        """
        INSERT INTO payment_events(
            invoice_number,
            payment_status,
            amount_paid,
            note,
            recorded_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            payment_status,
            amount_paid,
            note,
            recorded_at
        )
    )

    conn.commit()
    conn.close()


def get_payment_events(
    invoice_number=None
):
    conn = get_connection()
    cursor = conn.cursor()

    if invoice_number:

        cursor.execute(
            """
            SELECT
                invoice_number,
                payment_status,
                amount_paid,
                note,
                recorded_at
            FROM payment_events
            WHERE invoice_number = ?
            ORDER BY id DESC
            """,
            (invoice_number,)
        )

    else:

        cursor.execute("""
            SELECT
                invoice_number,
                payment_status,
                amount_paid,
                note,
                recorded_at
            FROM payment_events
            ORDER BY id DESC
        """)

    events = cursor.fetchall()

    conn.close()

    return events


def get_total_paid_for_invoice(
    invoice_number
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COALESCE(
            SUM(amount_paid),
            0
        )
        FROM payment_events
        WHERE invoice_number = ?
        """,
        (invoice_number,)
    )

    total_paid = cursor.fetchone()[0]

    conn.close()

    return total_paid
# --------------------------------------------------
# PAYMENT REMINDERS
# --------------------------------------------------

def create_reminder_events_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminder_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            reminder_type TEXT NOT NULL,
            message TEXT,
            status TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_reminder_queue():
    """
    Returns unpaid invoices that are overdue
    or due within the next 7 days.
    """

    update_overdue_invoices()

    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()

    cursor.execute("""
        SELECT
            i.invoice_number,
            i.client,
            i.amount,
            i.status,
            i.due_date,
            c.email
        FROM invoices i
        LEFT JOIN clients c
            ON LOWER(i.client) = LOWER(c.company)
        WHERE i.status NOT IN (
            'Paid',
            'Rejected',
            'Hold'
        )
        AND i.due_date IS NOT NULL
        AND i.due_date != ''
        ORDER BY i.due_date ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    queue = []

    for row in rows:

        invoice_number = row[0]
        client = row[1]
        amount = row[2]
        status = row[3]
        due_date_text = row[4]
        email = row[5]

        try:
            due = datetime.strptime(
                due_date_text,
                "%Y-%m-%d"
            ).date()

        except (ValueError, TypeError):
            continue

        days_until_due = (
            due - today
        ).days

        total_paid = (
            get_total_paid_for_invoice(
                invoice_number
            )
        )

        remaining = max(
            amount - total_paid,
            0
        )

        if remaining <= 0:
            continue

        if days_until_due < 0:

            reminder_type = "Overdue"

        elif days_until_due == 0:

            reminder_type = "Due Today"

        elif days_until_due <= 7:

            reminder_type = "Due Soon"

        else:
            continue

        queue.append({
            "invoice_number": invoice_number,
            "client": client,
            "email": email or "",
            "amount": amount,
            "paid": total_paid,
            "remaining": remaining,
            "status": status,
            "due_date": due_date_text,
            "days_until_due": days_until_due,
            "reminder_type": reminder_type
        })

    return queue


def add_reminder_event(
    invoice_number,
    reminder_type,
    message,
    status="Prepared"
):
    conn = get_connection()
    cursor = conn.cursor()

    recorded_at = datetime.now().isoformat(
        timespec="seconds"
    )

    cursor.execute(
        """
        INSERT INTO reminder_events(
            invoice_number,
            reminder_type,
            message,
            status,
            recorded_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            reminder_type,
            message,
            status,
            recorded_at
        )
    )

    conn.commit()
    conn.close()


def get_reminder_events():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            reminder_type,
            message,
            status,
            recorded_at
        FROM reminder_events
        ORDER BY id DESC
    """)

    events = cursor.fetchall()

    conn.close()

    return events
def update_client(
    client_id,
    company,
    email,
    phone
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE clients
        SET company = ?,
            email = ?,
            phone = ?
        WHERE id = ?
        """,
        (
            company,
            email,
            phone,
            client_id
        )
    )

    conn.commit()
    conn.close()