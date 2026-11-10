#!/usr/bin/env bash
set -euo pipefail
PG_BIN="$(find /usr/lib/postgresql -type f -name initdb -printf '%h\n' | head -n 1)"
if [ ! -f "$PGDATA/PG_VERSION" ]; then
  "$PG_BIN/initdb" -D "$PGDATA" -U demo -A trust --no-locale -E UTF8 >/dev/null
fi
"$PG_BIN/pg_ctl" -D "$PGDATA" -o "-c listen_addresses=127.0.0.1 -c max_connections=12 -c shared_buffers=16MB -c work_mem=2MB -c maintenance_work_mem=8MB -p 5432" -w start
if ! "$PG_BIN/psql" -U demo -h 127.0.0.1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='finance_demo'" | grep -q 1; then
  "$PG_BIN/createdb" -U demo -h 127.0.0.1 finance_demo
fi
exec streamlit run app.py --server.address=0.0.0.0 --server.port="${PORT:-10000}" --server.headless=true --browser.gatherUsageStats=false
