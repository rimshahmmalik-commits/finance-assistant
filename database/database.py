import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_NAME = BASE_DIR / "invoice_ai.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_tables():
    create_invoice_table()
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


def add_client(company, email, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO clients (company, email, phone) VALUES (?, ?, ?)",
        (company, email, phone)
    )

    conn.commit()
    conn.close()


def get_clients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, company, email, phone FROM clients ORDER BY company"
    )

    clients = cursor.fetchall()
    conn.close()

    return clients
def create_invoice_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT,
        client TEXT,
        amount REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_invoice(invoice_number, client, amount, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO invoices
        (invoice_number, client, amount, status)
        VALUES (?, ?, ?, ?)
        """,
        (invoice_number, client, amount, status)
    )

    conn.commit()
    conn.close()


def get_invoices():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT invoice_number, client, amount, status
    FROM invoices
    ORDER BY id DESC
    """)

    invoices = cursor.fetchall()

    conn.close()

    return invoices