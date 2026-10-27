import streamlit as st
import pandas as pd
import os

def render(DATA_FOLDER):
    st.title("Safety Incidents")

    incidents_file = os.path.join(DATA_FOLDER, "incidents.csv")

    # Load or initialize dataset
    if os.path.exists(incidents_file):
        try:
            incidents = pd.read_csv(incidents_file)
            incidents.columns = incidents.columns.str.strip()
        except Exception as e:
            st.error(f"Error reading incidents dataset: {e}")
            return
    else:
        # Create empty DataFrame with required fields if file does not exist
        columns = [
            "Incident_ID", "Date", "Time", "Shift", "Location", "Department",
            "Incident_Type", "Severity", "Injury_Status", "Lost_Time_Injury",
            "Cause", "Corrective_Action", "Incident_Status"
        ]
        incidents = pd.DataFrame(columns=columns)

    # Ensure all required columns are present in case the CSV is missing any
    required_cols = [
        "Incident_ID", "Date", "Time", "Shift", "Location", "Department",
        "Incident_Type", "Severity", "Injury_Status", "Lost_Time_Injury",
        "Cause", "Corrective_Action", "Incident_Status"
    ]
    for col in required_cols:
        if col not in incidents.columns:
            incidents[col] = "N/A"

    # --- Summary Metrics ---
    st.markdown("### Safety Summary")
    total_incidents = len(incidents)

    open_statuses = ["open", "under investigation", "pending"]
    open_incidents = incidents[
        incidents["Incident_Status"].astype(str).str.strip().str.lower().isin(open_statuses)
    ].shape[0]

    lost_time_count = incidents[
        incidents["Lost_Time_Injury"].astype(str).str.strip().str.lower().isin(["yes", "true", "1"])
    ].shape[0]

    critical_count = incidents[
        incidents["Severity"].astype(str).str.strip().str.lower().isin(["critical", "high", "major"])
    ].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Incidents", total_incidents)
    col2.metric("Open / Investigating", open_incidents)
    col3.metric("Lost-Time Injuries", lost_time_count)
    col4.metric("High / Critical Severity", critical_count)

    st.divider()

    # --- Search & Filtering ---
    st.markdown("### Filter Incident Repository")
    col_search, col_dept, col_sev = st.columns(3)

    with col_search:
        search_query = st.text_input("Search ID, Location, or Cause", placeholder="e.g. INC-001 or Underground")

    with col_dept:
        dept_options = ["All"] + sorted([d for d in incidents["Department"].dropna().unique() if d != "N/A"])
        selected_dept = st.selectbox("Department", dept_options)

    with col_sev:
        sev_options = ["All"] + sorted([s for s in incidents["Severity"].dropna().unique() if s != "N/A"])
        selected_sev = st.selectbox("Severity", sev_options)

    # Apply filters
    filtered_df = incidents.copy()

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["Incident_ID"].astype(str).str.lower().str.contains(q) |
            filtered_df["Location"].astype(str).str.lower().str.contains(q) |
            filtered_df["Cause"].astype(str).str.lower().str.contains(q)
        ]

    if selected_dept != "All":
        filtered_df = filtered_df[filtered_df["Department"] == selected_dept]

    if selected_sev != "All":
        filtered_df = filtered_df[filtered_df["Severity"] == selected_sev]

    st.write(f"**Records Found:** {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- Form to Log New Incident ---
    with st.expander("➕ Log New Safety Incident"):
        with st.form("add_incident_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)

            with f1:
                inc_id = st.text_input("Incident ID", f"INC-{total_incidents + 1:03d}")
                inc_date = st.date_input("Date")
                inc_time = st.time_input("Time")
                shift = st.selectbox("Shift", ["Day", "Night", "Afternoon"])

            with f2:
                location = st.text_input("Location", placeholder="e.g. Underground Shaft 3")
                department = st.selectbox(
                    "Department",
                    ["Mining Operations", "Engineering", "Processing", "Health & Safety", "Logistics", "Maintenance"]
                )
                inc_type = st.selectbox(
                    "Incident Type",
                    ["Near Miss", "Minor Injury", "Medical Treatment", "Equipment Damage", "Lost-Time Injury", "Environmental"]
                )
                severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])

            with f3:
                injury_status = st.selectbox("Injury Status", ["None", "First Aid Applied", "Medical Treatment", "Hospitalized", "Fatal"])
                lost_time = st.radio("Lost-Time Injury Status?", ["No", "Yes"])
                inc_status = st.selectbox("Incident Status", ["Open", "Under Investigation", "Closed"])

            cause = st.text_area("Root Cause Description", placeholder="Describe how the incident occurred...")
            corrective_action = st.text_area("Corrective Action", placeholder="Describe actions taken or proposed...")

            submitted = st.form_submit_button("Submit Incident Record")

            if submitted:
                new_record = {
                    "Incident_ID": inc_id,
                    "Date": str(inc_date),
                    "Time": str(inc_time),
                    "Shift": shift,
                    "Location": location,
                    "Department": department,
                    "Incident_Type": inc_type,
                    "Severity": severity,
                    "Injury_Status": injury_status,
                    "Lost_Time_Injury": lost_time,
                    "Cause": cause,
                    "Corrective_Action": corrective_action,
                    "Incident_Status": inc_status
                }

                updated_incidents = pd.concat([incidents, pd.DataFrame([new_record])], ignore_index=True)
                updated_incidents.to_csv(incidents_file, index=False)
                st.success(f"Incident {inc_id} saved successfully!")
                st.rerun()