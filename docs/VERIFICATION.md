# Verification notes

## Portfolio preparation — 8 November 2026

Completed checks:

- Installed `requirements.txt` in a fresh Python 3.12 virtual environment;
  `pip check` reported no broken requirements. All direct dependency imports
  succeeded, including the Gmail and Microsoft helper dependencies.
  Resolved versions included Streamlit 1.67.0, Pandas 2.3.3 and Psycopg 3.3.8.
- Parsed all 21 Python source files and checked imports between local modules.
- Exercised invoice-review rules for duplicate invoices and missing clients,
  checking the resulting risk levels and review recommendations.
- Reviewed the entry point to distinguish routed features from development modules.
- Scanned all 13 original Git commits for common private-key, API-token and
  password-bearing database URL patterns. No matches were found. No credential,
  OAuth token or database files were present in the tracked file history.
  This is a basic heuristic check, not a security audit.

## Running demo and integration checks — 8 November 2026

Used PostgreSQL 16.15 in an isolated, disposable local database and ran the app
with Streamlit 1.67.0. The database and app were bound to loopback. No real client
records, account credentials or financial data were used.

Passed checks:

- Created the schema and ran `seed_demo.py` twice. Counts remained 5 clients,
  8 invoices, 5 payment events and 32 transactions, with no duplicate seed data.
- Reconciled transaction totals: PKR 1,175,000 income, PKR 1,500,000 expenses
  and PKR -325,000 net cash flow.
- Confirmed seeded partial-payment balances and paid-invoice state.
- Created a temporary test invoice for PKR 1,000 through the database layer,
  recorded PKR 250 and verified PKR 750 remained, then recorded PKR 750 and
  verified the paid state. Removed only this test invoice and its payments.
- Generated a nonempty PDF invoice with a valid PDF header. This was a
  generation smoke check, not a visual comparison of the PDF contents.
- Built the complete Settings export and parsed its four CSV files; client,
  invoice, payment and transaction row counts matched the database.
- Used headless Chrome at 1680 × 1120 to open Dashboard, Invoices, Transactions,
  Clients, Analytics, Reminders, Settings, AI Advisor and Smart Import. No
  Streamlit exception panels appeared. AI Advisor remains a placeholder.
- Uploaded `examples/invoice_import.csv` in the actual interface. Its five rows
  produced two ready rows and three blocked rows. The review queue correctly
  identified a duplicate invoice, a missing client and a negative amount.
  No import records were approved or saved during this check.
- Captured and visually reviewed five real app screenshots in
  `docs/screenshots/` using only synthetic demo data.

The page walkthrough checks rendering and initial page execution; it does not
exercise every control, editing operation or error path. Payment writes were
checked through the database layer, rather than the browser form.

## Checks still required before deployment

- Docker Compose configuration was not executed; the demo used a portable local
  PostgreSQL server instead.
- No email was sent, no OAuth account was connected and the scheduler was not
  started. Gmail and Microsoft sending need separate tests with a dedicated inbox.
- Authentication, tenant isolation, production hosting, concurrency, access
  controls and financial precision need further work and validation.
- PDF layout, Excel-file import variants and every create/edit/delete interface
  flow were not exhaustively tested.

These checks support a portfolio demonstration, not a production-readiness claim.
