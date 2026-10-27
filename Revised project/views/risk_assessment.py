import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# 1. Fix path so we can import from the root folder
sys.path.append(str(Path(__file__).resolve().parents[1]))

# 2. Import your SQLite database connection and your groupmate's backend logic
from database import get_connection
from functions.risk_alerts_backend import generate_alerts

st.set_page_config(page_title="Alerts", page_icon="")
st.title("Alerts & Notifications")

# 3. Load data from SQLite (and the risk CSV) into the dictionary format expected
@st.cache_data
def load_all_data():
    conn = get_connection()
    data = {}
    
    # Load from SQLite Database safely
    tables = ["equipment", "workers", "incidents"]
    for t in tables:
        try:
            data[t] = pd.read_sql(f"SELECT * FROM {t}", conn)
        except Exception:
            data[t] = pd.DataFrame() # Empty fallback if table is missing
            
    conn.close()
    
    # Load the Risk assessments (saved as CSV by the other page)
    risk_path = Path("risk_assessments.csv")
    data["risks"] = pd.read_csv(risk_path) if risk_path.exists() else pd.DataFrame()
    
    return data

# 4. Generate Alerts
data = load_all_data()
alerts = generate_alerts(data)

# 5. Display the UI
if alerts.empty:
    st.success("No active alerts. All monitored values are within limits.")
else:
    # KPI Metrics
    col1, col2 = st.columns(2)
    col1.metric("Critical Alerts", int((alerts["Level"] == "CRITICAL").sum()))
    col2.metric("Warnings", int((alerts["Level"] == "WARNING").sum()))

    st.divider()

    # Filtering
    levels = st.multiselect("Filter by Level", ["CRITICAL", "WARNING"], default=["CRITICAL", "WARNING"])
    filtered_alerts = alerts[alerts["Level"].isin(levels)]

    # Display alerts as colored boxes
    st.subheader("Active Alerts")
    for _, a in filtered_alerts.head(20).iterrows():
        msg = f"**[{a['Level']}] {a['Source']} {a['ID']}** - {a['Parameter']}: {a['Value']} ({a['Status']}). \n\n*Action:* {a['Action']}"
        if a["Level"] == "CRITICAL":
            st.error(msg)
        else:
            st.warning(msg)

    # Data Table & Download
    st.subheader("Alert Data Table")
    st.dataframe(filtered_alerts, use_container_width=True)
    st.download_button("Download alerts (CSV)", filtered_alerts.to_csv(index=False), "alerts.csv")