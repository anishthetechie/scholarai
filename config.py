import os

try:
    import streamlit as st
    _secret_url = st.secrets.get("API_URL", None)
except Exception:
    _secret_url = None

API_URL = os.environ.get("API_URL") or _secret_url or "http://127.0.0.1:8000"
API_URL = API_URL.rstrip("/")
