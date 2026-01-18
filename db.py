import pyodbc
import streamlit as st

def get_connection():
    db = st.secrets["database"]
    return pyodbc.connect(
        f"DRIVER={{ {db['driver']} }};"
        f"SERVER={db['server']};"
        f"DATABASE={db['database']};"
        f"Trusted_Connection={db['trusted']};"
        f"TrustServerCertificate={db['trust_cert']};"
    )
