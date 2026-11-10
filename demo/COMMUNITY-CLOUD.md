# Card-free deployment

Use Streamlit Community Cloud, signing in with GitHub. Choose this repository,
branch `live-demo`, entry file `demo_streamlit.py`, and Python 3.12.
No API keys, email accounts or paid database are needed for this demo.

The app starts a disposable, loopback-only PostgreSQL process from the Debian
`postgresql` dependency in `packages.txt`. Each visitor uses an isolated schema
and the real finance app's database functions. Synthetic data resets on host
restart. It is a portfolio demo, not durable accounting storage.

Visitors can create clients, invoices, transactions and payment records, inspect
analytics and export PDFs. Outbound mail and account connections are disabled.
Financial insights use rules, not a language model. Do not enter real client data.

Local testing: set DEMO_PUBLIC=1 and DATABASE_URL to a disposable test PostgreSQL
instance, then run `streamlit run demo_streamlit.py`. Never use a production DB.
