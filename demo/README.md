# Public Finance Assistant demo

This uses the existing Streamlit interface and PostgreSQL queries. Each Streamlit session receives a server-generated isolated PostgreSQL schema with synthetic records. Reset affects only that schema. Idle sessions expire after two hours; the demo caps active schemas. Reminders can be prepared but all provider send functions are blocked.

Dockerfile.demo starts a disposable, loopback-only PostgreSQL server inside the demo container. It contains no real data and uses local trust authentication; PostgreSQL is not exposed as a public service. This avoids relying on a separately expiring free database. Container restarts delete all demo data. This setup is for a synthetic evaluation sandbox, not production hosting.

Deploy branch live-demo, Dockerfile.demo, on a free Render web service. The app port follows PORT. No personal .env, credentials, OAuth tokens or local databases enter the Docker context. No email provider should be configured. Financial analysis remains rule-based.
