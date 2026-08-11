from datetime import date, timedelta

from database.database import (
    get_connection,
    add_client,
    add_invoice,
    add_payment_event,
    add_transaction,
)


DEMO_CLIENTS = [
    ("Atlas Traders", "accounts@atlastraders.pk", "+92 300 1112233"),
    ("Nexa Retail", "finance@nexaretail.pk", "+92 301 2223344"),
    ("Urban Mart", "payments@urbanmart.pk", "+92 302 3334455"),
    ("PakCraft Supplies", "accounts@pakcraft.pk", "+92 303 4445566"),
    ("Vertex Distribution", "finance@vertexdist.pk", "+92 304 5556677"),
]


def demo_invoice_number(n):
    return f"DEMO-INV-{n:03d}"


def demo_reference(n):
    return f"DEMO-TXN-{n:03d}"


def clear_demo_data():
    """
    Remove only records created by this demo seeder.
    Existing user/client data is left untouched.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM reminder_events
                WHERE invoice_number LIKE 'DEMO-INV-%'
            """)

            cursor.execute("""
                DELETE FROM review_decisions
                WHERE invoice_number LIKE 'DEMO-INV-%'
            """)

            cursor.execute("""
                DELETE FROM payment_events
                WHERE invoice_number LIKE 'DEMO-INV-%'
            """)

            cursor.execute("""
                DELETE FROM invoices
                WHERE invoice_number LIKE 'DEMO-INV-%'
            """)

            cursor.execute("""
                DELETE FROM transactions
                WHERE source = 'Demo Seed'
                OR reference LIKE 'DEMO-TXN-%'
            """)

            cursor.execute("""
                DELETE FROM clients
                WHERE company IN (
                    'Atlas Traders',
                    'Nexa Retail',
                    'Urban Mart',
                    'PakCraft Supplies',
                    'Vertex Distribution'
                )
            """)


def seed_clients():
    for company, email, phone in DEMO_CLIENTS:
        add_client(
            company,
            email,
            phone
        )


def seed_invoices(today):
    invoices = [
        # number, client, amount, status, invoice_date offset, due_date offset
        (1, "Atlas Traders", 420000, "Pending", -52, -22),
        (2, "Nexa Retail", 285000, "Pending", -39, -9),
        (3, "Urban Mart", 190000, "Pending", -20, 10),
        (4, "PakCraft Supplies", 345000, "Pending", -14, 16),
        (5, "Vertex Distribution", 225000, "Paid", -61, -31),
        (6, "Atlas Traders", 160000, "Paid", -44, -14),
        (7, "Urban Mart", 125000, "Pending", -7, 23),
        (8, "Nexa Retail", 310000, "Pending", -3, 27),
    ]

    for (
        number,
        client,
        amount,
        status,
        invoice_offset,
        due_offset
    ) in invoices:
        add_invoice(
            demo_invoice_number(number),
            client,
            amount,
            status,
            (today + timedelta(days=invoice_offset)).isoformat(),
            (today + timedelta(days=due_offset)).isoformat(),
        )

    # Fully paid invoices
    add_payment_event(
        demo_invoice_number(5),
        "Paid",
        225000,
        "Demo payment received in full",
    )

    add_payment_event(
        demo_invoice_number(6),
        "Paid",
        160000,
        "Demo payment received in full",
    )

    # Partial payments
    add_payment_event(
        demo_invoice_number(1),
        "Partial",
        120000,
        "Demo partial payment",
    )

    add_payment_event(
        demo_invoice_number(2),
        "Partial",
        85000,
        "Demo partial payment",
    )

    add_payment_event(
        demo_invoice_number(3),
        "Partial",
        50000,
        "Demo advance payment",
    )


def seed_transactions(today):
    """
    Seed ~3 months of realistic SMB cash activity.
    Enough history for reports and forecasting.
    """
    transactions = [
        # days ago, type, description, amount, category, account
        (86, "Income", "Customer payment Atlas Traders", 180000, "Sales", "HBL Business"),
        (83, "Expense", "Warehouse rent", 85000, "Rent", "HBL Business"),
        (80, "Expense", "LESCO electricity bill", 22000, "Utilities", "HBL Business"),
        (78, "Expense", "Wholesale inventory purchase", 140000, "Inventory", "HBL Business"),
        (75, "Expense", "Meta ads campaign", 28000, "Marketing", "Bank Alfalah"),
        (72, "Expense", "Staff payroll", 110000, "Payroll", "HBL Business"),
        (69, "Income", "Customer payment Vertex Distribution", 225000, "Sales", "HBL Business"),
        (65, "Expense", "Fuel and delivery expense", 18000, "Transport", "JazzCash"),
        (62, "Expense", "Office stationery", 12000, "Office Supplies", "Cash"),
        (59, "Income", "Customer payment Nexa Retail", 200000, "Sales", "HBL Business"),
        (57, "Expense", "Warehouse rent", 85000, "Rent", "HBL Business"),
        (54, "Expense", "LESCO electricity bill", 24000, "Utilities", "HBL Business"),
        (51, "Expense", "Supplier stock purchase", 165000, "Inventory", "HBL Business"),
        (48, "Expense", "Google ads", 32000, "Marketing", "Bank Alfalah"),
        (45, "Expense", "Staff payroll", 110000, "Payroll", "HBL Business"),
        (41, "Income", "Customer payment Atlas Traders", 160000, "Sales", "HBL Business"),
        (38, "Expense", "Courier and transport", 21000, "Transport", "JazzCash"),
        (34, "Expense", "Bank service charges", 6500, "Bank Fees", "HBL Business"),
        (31, "Income", "Customer payment Urban Mart", 140000, "Sales", "HBL Business"),
        (29, "Expense", "Warehouse rent", 85000, "Rent", "HBL Business"),
        (27, "Expense", "LESCO electricity bill", 26000, "Utilities", "HBL Business"),
        (24, "Expense", "Wholesale inventory purchase", 190000, "Inventory", "HBL Business"),
        (21, "Expense", "Meta ads campaign", 36000, "Marketing", "Bank Alfalah"),
        (18, "Expense", "Staff payroll", 115000, "Payroll", "HBL Business"),
        (15, "Income", "Customer payment Nexa Retail", 85000, "Sales", "HBL Business"),
        (12, "Expense", "Fuel and delivery expense", 23000, "Transport", "JazzCash"),
        (10, "Expense", "Printer supplies", 14500, "Office Supplies", "Cash"),
        (8, "Income", "Customer payment Atlas Traders", 120000, "Sales", "HBL Business"),
        (6, "Expense", "Supplier stock purchase", 125000, "Inventory", "HBL Business"),
        (4, "Expense", "Google ads campaign", 18000, "Marketing", "Bank Alfalah"),
        (2, "Income", "Walk-in cash sales", 65000, "Sales", "Cash"),
        (1, "Expense", "Internet and utilities", 9000, "Utilities", "HBL Business"),
    ]

    for index, (
        days_ago,
        transaction_type,
        description,
        amount,
        category,
        account
    ) in enumerate(transactions, start=1):
        transaction_date = (
            today - timedelta(days=days_ago)
        ).isoformat()

        add_transaction(
            transaction_date,
            transaction_type,
            description,
            amount,
            category,
            account,
            demo_reference(index),
            "Demo Seed",
        )


def seed_demo_data():
    today = date.today()

    print("Clearing previous demo-only records...")
    clear_demo_data()

    print("Adding demo clients...")
    seed_clients()

    print("Adding demo invoices and payments...")
    seed_invoices(today)

    print("Adding demo transactions...")
    seed_transactions(today)

    print("")
    print("DEMO DATA READY")
    print("5 clients")
    print("8 invoices")
    print("5 payment events")
    print("32 transactions")
    print("")
    print("Only DEMO-prefixed / Demo Seed records were replaced.")


if __name__ == "__main__":
    seed_demo_data()