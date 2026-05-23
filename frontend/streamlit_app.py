"""Optional Streamlit demo UI.

Install streamlit separately with `pip install streamlit requests`, run the FastAPI
server, then execute:

    streamlit run frontend/streamlit_app.py
"""

import json
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(page_title="EY Audit AI", layout="wide")
st.title("EY AI Enterprise Audit & Invoice Compliance")

payload_path = Path("data/demo_payloads/invoice_workflow_request.json")
payload = st.text_area("Workflow request JSON", payload_path.read_text(), height=500)

if st.button("Run invoice audit workflow"):
    response = requests.post("http://localhost:8000/workflows/invoice-audit/run", json=json.loads(payload), timeout=30)
    st.write(response.status_code)
    st.json(response.json())
