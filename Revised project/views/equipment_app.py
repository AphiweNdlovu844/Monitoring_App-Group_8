#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Load all your data files cleanly
equipment = pd.read_csv(os.path.join(script_dir, '..', 'data', 'equipment.csv'))
maintenance = pd.read_csv(os.path.join(script_dir, '..', 'data', 'maintenance.csv'))
equipment_readings = pd.read_csv(os.path.join(script_dir, '..', 'data', 'equipment_readings.csv'))




def temperature_status(temperature):
    if temperature < 80:
        return "NORMAL"
    elif temperature <= 100:
        return "WARNING"
    else:
        return "CRITICAL"


def vibration_status(vibration):
    if vibration < 5:
        return "NORMAL"
    elif vibration <= 8:
        return "WARNING"
    else:
        return "CRITICAL"


def overall_condition(temperature, vibration):
    if temperature == "CRITICAL" or vibration == "CRITICAL":
        return "CRITICAL"
    elif temperature == "WARNING" or vibration == "WARNING":
        return "WARNING"
    else:
        return "NORMAL"


equipment["Temperature Status"] = equipment["Temperature_C"].apply(temperature_status)
equipment["Vibration Status"] = equipment["Vibration_mm_s"].apply(vibration_status)
equipment["Overall Equipment Condition"] = equipment.apply(lambda row: overall_condition(row["Temperature Status"],row["Vibration Status"]), axis = 1)


critical_id = equipment[equipment["Overall Equipment Condition"] == "CRITICAL"]["Equipment_ID"].tolist()
warning_id = equipment[equipment["Overall Equipment Condition"] == "WARNING"]["Equipment_ID"].tolist()


def equipment_condition_alert(row):

    if row["Overall Equipment Condition"] == "CRITICAL":
        return "Equipment requires immediate inspection."

    elif row["Overall Equipment Condition"] == "WARNING":
        return "Equipment is approaching predefined thresholds."

    else:
        return "Equipment is operating within predefined limits."

equipment["Condition Alert"] = equipment.apply(equipment_condition_alert,axis=1)

def calculate_availability(operating_time, downtime):
    total_time = operating_time + downtime
    if total_time == 0:
        return 0
    availability = (operating_time / total_time) * 100
    return round(availability, 1)

equipment["Calculated Availability"] = equipment.apply(lambda row: calculate_availability(row["Operating_Time_90d_h"],row["Downtime_90d_h"]),axis=1)


def availability_status(availability):
    if availability < 80:
        return "LOW"
    else:
        return "ACCEPTABLE"

equipment["Availability Status"] = equipment["Calculated Availability"].apply(availability_status)

low_availability = equipment[equipment["Calculated Availability"] < 80]["Equipment_ID"].tolist()


def downtime_status(downtime):
    if downtime > 300:   #300 hours is an arbitrary threshold chosen for educational purposes
        return "Excessive Downtime"
    else:
        return "Acceptable"

equipment["Downtime Status"] = equipment["Downtime_90d_h"].apply(downtime_status)

excessive_downtime = equipment[equipment["Downtime_90d_h"]> 300]["Equipment_ID"].tolist()

def repeated_alerts(alert_count):
    if alert_count >= 5:
        return "Repeated Alerts"
    else:
        return "No Repeated Alerts"

equipment["Alert Status"] = equipment["Alert_Count_30d"].apply(repeated_alerts)


def equipment_due(equipment):
    due = []
    for index, row in equipment.iterrows():
        if row["Maintenance_Status"] == "Due":due.append(row["Equipment_ID"])
    return due


def equipment_overdue(equipment):
    overdue = []
    for index, row in equipment.iterrows():
        if row["Maintenance_Status"] == "Overdue":overdue.append(row["Equipment_ID"])
    return overdue


def equipment_under_maintenance(equipment):
    under_maintenance = []
    for index, row in equipment.iterrows():
        if row["Maintenance_Status"] == "Under Maintenance":
            under_maintenance.append(row["Equipment_ID"])
    return under_maintenance


def maintenance_priority(row):
    if row["Overall Equipment Condition"] == "CRITICAL":
        return "Critical"

    elif row["Maintenance_Status"] == "Overdue":
        return "High"

    elif row["Availability Status"] == "LOW":
        return "High"

    elif row["Downtime Status"] == "Excessive Downtime":
        return "High"

    elif row["Critical_Alert_Count_30d"] > 0:
        return "High"

    elif row["Maintenance_Status"] == "Due":
        return "Medium"

    elif row["Alert Status"] == "Repeated Alerts":
        return "Medium"

    elif row["Maintenance_Status"] == "Under Maintenance":
        return "Medium"

    else:
        return "Low"

equipment["Maintenance Priority"] = equipment.apply(maintenance_priority,axis=1)

st.set_page_config(page_title="Khwezi Mining | Equipment Monitoring", layout="wide")
st.sidebar.title("Khwezi Mining")
page = st.sidebar.radio("Monitoring section", ["Overview", "Equipment Condition", "Maintenance Monitoring","Equipment Performance"])
equipment_id = st.sidebar.selectbox("Select equipment", equipment["Equipment_ID"].tolist())
selected = equipment.loc[equipment["Equipment_ID"] == equipment_id].iloc[0]


history = equipment_readings.loc[equipment_readings["Equipment_ID"] == equipment_id].copy()
history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
history = history.dropna(subset=["Date"]).sort_values("Date")

if page == "Overview":
    st.title("Equipment Monitoring")
    st.caption("Overview of the existing equipment dataset")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total equipment", len(equipment))
    c2.metric("Normal", int((equipment["Overall Equipment Condition"] == "NORMAL").sum()))
    c3.metric("Warning", len(warning_id))
    c4.metric("Critical", len(critical_id))
    st.metric("Average availability", f"{equipment['Calculated Availability'].mean():.1f}%")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Equipment condition distribution")
        condition_counts = equipment["Overall Equipment Condition"].value_counts().reindex(["NORMAL", "WARNING", "CRITICAL"], fill_value=0)
        st.bar_chart(condition_counts)
    with c2:
        st.subheader("Maintenance status distribution")
        maintenance_counts = equipment["Maintenance_Status"].value_counts()
        st.bar_chart(maintenance_counts)
    st.subheader("Machines requiring attention")
    attention_required = equipment[equipment["Maintenance Priority"].isin(["Critical", "High"])]
    st.dataframe(attention_required[["Equipment_ID", "Equipment_Type", "Overall Equipment Condition", "Maintenance_Status", "Calculated Availability", "Downtime_90d_h", "Maintenance Priority"]], hide_index=True, width= 'stretch')
    st.subheader("Equipment highlights")
    c1, c2 = st.columns(2)
    with c1:
        highest_temperature = equipment.loc[equipment["Temperature_C"].idxmax()]
        highest_vibration = equipment.loc[equipment["Vibration_mm_s"].idxmax()]
        st.write(f"Highest temperature: {highest_temperature['Equipment_ID']} — {highest_temperature['Temperature_C']:.1f} °C")
        st.write(f"Highest vibration: {highest_vibration['Equipment_ID']} — {highest_vibration['Vibration_mm_s']:.1f} mm/s")
    with c2:
        lowest_availability = equipment.loc[equipment["Calculated Availability"].idxmin()]
        highest_downtime = equipment.loc[equipment["Downtime_90d_h"].idxmax()]
        st.write(f"Lowest availability: {lowest_availability['Equipment_ID']} — {lowest_availability['Calculated Availability']:.1f}%")
        st.write(f"Highest downtime: {highest_downtime['Equipment_ID']} — {highest_downtime['Downtime_90d_h']:.1f} h")

elif page == "Equipment Condition":
    st.title("Equipment Condition Monitoring")
    st.caption("Thresholds are educational prototypes, not manufacturer specifications")
    st.subheader(f"Selected equipment: {equipment_id}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperature", f"{selected['Temperature_C']:.1f} °C")
    c2.metric("Vibration", f"{selected['Vibration_mm_s']:.1f} mm/s")
    c3.metric("Availability", f"{selected['Calculated Availability']:.1f}%")
    st.write("Temperature status:", selected["Temperature Status"])
    st.write("Vibration status:", selected["Vibration Status"])
    st.write("Overall condition:", selected["Overall Equipment Condition"])
    condition = selected["Overall Equipment Condition"]
    if condition == "CRITICAL":
        st.error(selected["Condition Alert"])
    elif condition == "WARNING":
        st.warning(selected["Condition Alert"])
    else:
        st.success(selected["Condition Alert"])
    st.subheader("Temperature trend (historical readings)")
    st.line_chart(history.set_index("Date")["Temperature_C"])
    st.subheader("Vibration trend (historical readings)")
    st.line_chart(history.set_index("Date")["Vibration_mm_s"])
    st.subheader("All equipment conditions")
    status_filter = st.selectbox("Filter equipment by condition", ["All", "NORMAL", "WARNING", "CRITICAL"])
    condition_table = equipment
    if status_filter != "All":
        condition_table = condition_table.loc[condition_table["Overall Equipment Condition"] == status_filter]
    st.dataframe(condition_table[["Equipment_ID", "Temperature_C", "Temperature Status", "Vibration_mm_s", "Vibration Status", "Overall Equipment Condition", "Condition Alert"]], hide_index=True, width= 'stretch')
    st.write("Critical machines:", ", ".join(critical_id) if critical_id else "None")
    st.write("Warning machines:", ", ".join(warning_id) if warning_id else "None")

elif page == "Maintenance Monitoring":
    st.title("Equipment Maintenance Monitoring")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total equipment", len(equipment))
    c2.metric("Due", len(equipment_due(equipment)))
    c3.metric("Overdue", len(equipment_overdue(equipment)))
    c4.metric("Under maintenance", len(equipment_under_maintenance(equipment)))
    st.subheader(f"Maintenance details: {equipment_id}")
    st.write("Maintenance status:", selected["Maintenance_Status"])
    st.write("Maintenance priority:", selected["Maintenance Priority"])
    st.write("Availability:", f"{selected['Calculated Availability']:.1f}%", "—", selected["Availability Status"])
    st.write("Downtime (90 days):", f"{selected['Downtime_90d_h']:.1f} hours", "—", selected["Downtime Status"])
    st.write("Alerts (30 days):", int(selected["Alert_Count_30d"]), "—", selected["Alert Status"])
    st.subheader("Maintenance priority table")
    priority = st.selectbox("Filter by maintenance priority", ["All", "Critical", "High", "Medium", "Low"])
    priority_table = equipment[["Equipment_ID", "Equipment_Type", "Overall Equipment Condition", "Maintenance_Status", "Calculated Availability", "Downtime_90d_h", "Alert_Count_30d", "Alert Status", "Maintenance Priority"]]
    if priority != "All":
        priority_table = priority_table.loc[priority_table["Maintenance Priority"] == priority]
    st.dataframe(priority_table, hide_index=True, width= 'stretch')
    st.subheader("Top 10 equipment by downtime")
    equipment_sorted = equipment.sort_values("Downtime_90d_h", ascending=False).head(10)
    st.bar_chart(equipment_sorted.set_index("Equipment_ID")["Downtime_90d_h"])
    st.subheader("Average downtime by equipment type")
    downtime_by_type = equipment.groupby("Equipment_Type")["Downtime_90d_h"].mean()
    st.bar_chart(downtime_by_type)
    st.subheader("Equipment requiring maintenance attention")
    maintenance_filter = st.selectbox("Filter maintenance status", ["All", "Due", "Overdue", "Under Maintenance"])
    maintenance_table = equipment
    if maintenance_filter != "All":
        maintenance_table = maintenance_table.loc[maintenance_table["Maintenance_Status"] == maintenance_filter]
    st.dataframe(maintenance_table[["Equipment_ID", "Equipment_Type", "Maintenance_Status", "Maintenance Priority", "Calculated Availability", "Downtime_90d_h"]], hide_index=True, width= 'stretch')
    st.subheader(f"Maintenance work orders: {equipment_id}")
    st.dataframe(maintenance.loc[maintenance["Equipment_ID"] == equipment_id], hide_index=True, width= 'stretch')

# SECTION 4: EQUIPMENT PERFORMANCE QUESTIONS

elif page == "Equipment Performance":

    st.title("Equipment Performance")

    # 1. Equipment with the highest downtime
    highest_downtime = equipment.loc[equipment["Downtime_90d_h"].idxmax()]

    st.subheader("Equipment with the highest downtime")
    st.write(
        highest_downtime["Equipment_ID"],
        "—", highest_downtime["Downtime_90d_h"], "hours"
    )

    # 2. Equipment with the lowest availability
    lowest_availability = equipment.loc[equipment["Calculated Availability"].idxmin()]

    st.subheader("Equipment with the lowest availability")
    st.write(
        lowest_availability["Equipment_ID"],
        "—", lowest_availability["Calculated Availability"], "%"
    )

    # 3. Equipment with the highest vibration
    highest_vibration = equipment.loc[equipment["Vibration_mm_s"].idxmax()]

    st.subheader("Equipment with the highest vibration")
    st.write(
        highest_vibration["Equipment_ID"],
        "—", highest_vibration["Vibration_mm_s"], "mm/s")

    # 4. Equipment with the highest temperature
    highest_temperature = equipment.loc[equipment["Temperature_C"].idxmax()]

    st.subheader("Equipment with the highest operating temperature")
    st.write(
        highest_temperature["Equipment_ID"],
        "—", highest_temperature["Temperature_C"], "°C")

    # 5. Equipment with the most alerts
    most_alerts = equipment.loc[equipment["Alert_Count_30d"].idxmax()]

    st.subheader("Equipment that has generated the most alerts")
    st.write(
        most_alerts["Equipment_ID"],
        "—", most_alerts["Alert_Count_30d"], "alerts in 30 days"
    )

    # 6. Equipment requiring maintenance
    requires_maintenance = equipment[
        equipment["Maintenance_Status"].isin(
            ["Due", "Overdue", "Under Maintenance"]
        )
    ]

    st.subheader("Equipment that requires maintenance")
    st.dataframe(
        requires_maintenance[
            ["Equipment_ID", "Maintenance_Status", "Maintenance Priority"]
        ],
        hide_index=True
    )

    # 7. Equipment overdue for maintenance
    overdue_equipment = equipment_overdue(equipment)

    st.subheader("Equipment overdue for maintenance")
    st.write(", ".join(overdue_equipment) if overdue_equipment else "None")

    # 8. Average equipment availability
    average_availability = equipment["Calculated Availability"].mean()

    st.subheader("Average equipment availability")
    st.write(f"{average_availability:.1f}%")

    # 9. Equipment type with the highest average downtime
    downtime_by_type = equipment.groupby("Equipment_Type")["Downtime_90d_h"].mean()

    highest_downtime_type = downtime_by_type.idxmax()

    st.subheader("Equipment type that has the highest downtime")
    st.write(
        highest_downtime_type,
        "—", f"{downtime_by_type.max():.1f}", "hours average downtime"
    )

    # 10. Equipment requiring immediate inspection
    immediate_inspection = equipment[
        equipment["Overall Equipment Condition"] == "CRITICAL"
    ]

    st.subheader("Equipment that requires immediate inspection")
    st.dataframe(
        immediate_inspection[
            ["Equipment_ID", "Temperature_C", "Vibration_mm_s",
             "Overall Equipment Condition", "Condition Alert"]
        ],
        hide_index=True
    )

