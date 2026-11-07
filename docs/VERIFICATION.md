# Verification notes

## Portfolio preparation — 8 November 2026

Completed checks:

- Installed `requirements.txt` in a fresh Python 3.12 virtual environment;
  `pip check` reported no broken requirements. All direct dependency imports
  succeeded, including the Gmail and Microsoft helper dependencies.
  Resolved versions included Streamlit 1.67.0, Pandas 2.3.3 and Psycopg 3.3.8.
- Parsed the synthetic CSV and confirmed its five-row structure and deliberate
  duplicate invoice example.
- Parsed all 21 Python source files and checked imports between local modules.
- Exercised invoice-review rules for duplicate invoices and missing clients,
  checking the resulting risk levels and review recommendations.
- Reviewed the current entry point to distinguish routed features from
  unconnected development modules.
- Scanned all 13 existing Git commits for common private-key, API-token and
  password-bearing database URL patterns. No matches were found. No credential,
  OAuth token or database files were present in the tracked file history.
  This is a basic heuristic check, not a security audit.

## Checks still required before deployment

No PostgreSQL server or Docker installation was available in the preparation
environment. Database creation, SQL queries, demo seeding and a complete
Streamlit interface walkthrough have **not** been integration-tested here.
The Compose configuration has not been executed. No email was sent, no OAuth
account was connected and no real financial records were used.

Use a new disposable database for the following manual checks:

1. Follow the README setup and run `seed_demo.py`.
2. Verify 5 clients, 8 invoices, 5 payments and 32 transactions were created.
3. Run the seeder again and check the same counts, rather than duplicate data.
4. Open each routed page and check for exceptions.
5. Upload `examples/invoice_import.csv`; verify the duplicate, missing client
   and negative amount are flagged before approving any records.
6. Add a new invoice, record a partial payment and verify its remaining balance.
7. Generate a PDF invoice and compare its values with the source record.
8. Export data from Settings and reconcile row counts and totals.
9. Test email separately with a dedicated test inbox and explicit sending
   consent. Keep the scheduler stopped during the portfolio walkthrough.

Screenshots should be captured from the actual running app with synthetic data;
none are fabricated or represented as verified interface output here.
