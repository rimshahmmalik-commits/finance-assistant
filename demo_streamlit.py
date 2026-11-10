"""Community Cloud entry point. This never connects to the personal local database."""
import os
from pathlib import Path
import runpy
os.environ['DEMO_PUBLIC'] = '1'
import streamlit as st
from demo.cloud_database import start_database

@st.cache_resource
def demo_database():
    return start_database()

os.environ['DATABASE_URL'] = demo_database()
runpy.run_path(str(Path(__file__).parent / 'app.py'), run_name='__main__')
