"""Isolated PostgreSQL schemas for a synthetic, resettable Streamlit demo."""
from contextvars import ContextVar
from datetime import datetime,timedelta,timezone
from contextlib import contextmanager
import os,re,uuid
from psycopg import sql

SCHEMA=ContextVar('finance_demo_schema',default=None)
def enabled():return os.getenv('DEMO_PUBLIC')=='1'
def valid_schema(name):return isinstance(name,str) and re.fullmatch(r'demo_[a-f0-9]{32}',name) is not None

@contextmanager
def scope(name):
    if not valid_schema(name):raise ValueError('Invalid synthetic session identifier.')
    token=SCHEMA.set(name)
    try:yield name
    finally:SCHEMA.reset(token)

def ensure_schema(name):
    if not valid_schema(name):raise ValueError('Invalid synthetic session identifier.')
    from database.database import POOL,_TABLES_READY
    created=False
    with POOL.connection() as conn,conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(77281143)')
        conn.execute('CREATE SCHEMA IF NOT EXISTS demo_control')
        conn.execute('CREATE TABLE IF NOT EXISTS demo_control.sessions (name TEXT PRIMARY KEY,last_seen TIMESTAMPTZ NOT NULL)')
        expired=conn.execute('SELECT name FROM demo_control.sessions WHERE last_seen < %s',(datetime.now(timezone.utc)-timedelta(hours=2),)).fetchall()
        for (old,) in expired:
            if valid_schema(old):
                conn.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(old)))
                conn.execute('DELETE FROM demo_control.sessions WHERE name=%s',(old,));_TABLES_READY.discard(old)
        exists=conn.execute('SELECT 1 FROM demo_control.sessions WHERE name=%s',(name,)).fetchone()
        if not exists:
            if conn.execute('SELECT count(*) FROM demo_control.sessions').fetchone()[0]>=40:
                raise RuntimeError('The demo is busy. Please try again later.')
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(name)));created=True
        conn.execute('INSERT INTO demo_control.sessions VALUES (%s,%s) ON CONFLICT(name) DO UPDATE SET last_seen=EXCLUDED.last_seen',(name,datetime.now(timezone.utc)))
    return created

def seed_current():
    from database.database import create_tables
    from seed_demo import seed_demo_data
    create_tables();seed_demo_data()

def reset_current():
    from database.database import POOL,_TABLES_READY
    name=SCHEMA.get()
    if not valid_schema(name):raise ValueError('Missing synthetic session.')
    with POOL.connection() as conn:
        conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(name)))
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(name)))
    _TABLES_READY.discard(name);seed_current()

def configure_session(st):
    name=st.session_state.setdefault('_demo_schema','demo_'+uuid.uuid4().hex)
    if not valid_schema(name):raise RuntimeError('Invalid demo session.')
    SCHEMA.set(name)
    try:
        fresh=ensure_schema(name)
        if fresh or not st.session_state.get('_demo_seeded'):
            seed_current();st.session_state['_demo_seeded']=True
    except RuntimeError as exc:st.error(str(exc));st.stop()
    st.info('Interactive public demo · Fictional financial records · Your changes are session-specific and temporary. Email sending is disabled. Analysis uses rules, not an LLM.')
    with st.sidebar:
        st.caption('PUBLIC SANDBOX · Synthetic data')
        if st.button('Reset my demo',key='_demo_reset'):
            reset_current();st.rerun()
        st.caption('Sessions expire after inactivity. This is not a production accounting service.')
