import os
from datetime import datetime
import pandas as pd
import streamlit as st

def render(data_folder):
    st.subheader("Risk Assessment")
    # Store risk assessments inside the application's data folder.
    risk_file = os.path.join(data_folder, "risk_assessments.csv")
    # Display the risk assessment interface.
    show_risk_page(risk_file)
# ====================== (g) RISK ASSESSMENT ======================
RISK_FILE = "risk_assessments.csv" # where assessments are saved
BANDS = [(4, "Low"), (9, "Medium"), (16, "High"), (25, "Critical")] # (highest score, class)


def calculate_risk(likelihood, consequence):
    """Return (score, level) for 1-5 inputs; raise ValueError for bad input."""
    try:
        l, c = int(likelihood), int(consequence) # make sure they are whole numbers
    except (TypeError, ValueError):
        raise ValueError("Likelihood and consequence must be whole numbers.")
    if not (1 <= l <= 5 and 1 <= c <= 5): # error prevention (brief, section 5)
        raise ValueError("Likelihood and consequence must be between 1 and 5.")
    score = l * c # RiskScore = Likelihood x Consequence
    for top, name in BANDS: # first band whose upper limit fits
        if score <= top:
            return score, name


def show_risk_page(path=RISK_FILE):
    """Streamlit page: enter a hazard, score it, warn the user, save it."""
    import streamlit as st
    st.header("Risk Assessment")
    item = st.text_input("Hazard / safety observation")
    area = st.text_input("Department or area")
    l = st.slider("Likelihood (1 = rare ... 5 = almost certain)", 1, 5, 1) # sliders stop invalid input
    c = st.slider("Consequence (1 = minor ... 5 = catastrophic)", 1, 5, 1)
    if st.button("Assess risk"):
        if not item.strip():
            st.error("Please describe the hazard first.")
        else:
            score, level = calculate_risk(l, c)
            if level in ("High", "Critical"): # required warning for high/critical
                st.error(f"{level.upper()} RISK (score {score}): stop work, escalate to the manager.")
            elif level == "Medium":
                st.warning(f"MEDIUM RISK (score {score}): put controls in place.")
            else:
                st.success(f"LOW RISK (score {score}): keep monitoring.")
            row = pd.DataFrame([{"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "description": item,
                                 "department": area, "likelihood": l, "consequence": c,
                                 "risk_score": score, "risk_level": level}])
            row.to_csv(path, mode="a", header=not os.path.exists(path), index=False) # append to CSV
            st.success("Assessment saved.")
    if os.path.exists(path): # show history + chart of risk classes
        df = pd.read_csv(path)
        st.dataframe(df)
        if "risk_level" in df.columns:
            st.bar_chart(df["risk_level"].value_counts())


# ====================== (h) ALERTS AND NOTIFICATIONS ======================
ORDER = {"CRITICAL": 0, "WARNING": 1} # sort order: critical first
ACTION = {"CRITICAL": "Inspect immediately and start the appropriate maintenance/safety procedure.",
          "WARNING": "Monitor closely and schedule a check."}
ALERT_COLS = ["Level", "Source", "ID", "Parameter", "Value", "Status", "Action"]

# Numeric rules: (column, label, unit, warning limit, critical limit, low_is_bad)
# Educational prototype thresholds only. Change the column names to match your team's CSVs.
EQUIPMENT_RULES = [("temperature", "Temperature", "C", 80, 100, False),
                   ("vibration", "Vibration", "mm/s", 5, 8, False),
                   ("availability", "Availability", "%", 85, 70, True),
                   ("downtime", "Downtime", "h", 40, 80, False)]
WORKER_RULES = [("ppe_compliance", "PPE compliance", "%", 80, 50, True),
                ("fatigue_level", "Fatigue level", "/10", 6, 8, False)]
# Text rules: (data key, id column, column, label, {value: level})
CATEGORY_RULES = [("equipment", "equipment_id", "maintenance_status", "Maintenance status", {"Overdue": "WARNING"}),
                  ("incidents", "incident_id", "severity", "Incident severity", {"Critical": "CRITICAL", "High": "WARNING"}),
                  ("risks", "description", "risk_level", "Risk level", {"Critical": "CRITICAL", "High": "WARNING"})]


def grade(value, warn, crit, low_is_bad=False):
    """Return 'CRITICAL', 'WARNING' or None for one value."""
    if low_is_bad: # e.g. availability: small = bad
        return "CRITICAL" if value < crit else "WARNING" if value < warn else None
    return "CRITICAL" if value > crit else "WARNING" if value >= warn else None # e.g. temperature


def make_alert(level, source, item_id, parameter, value, status):
    """Build one alert as a dictionary."""
    return {"Level": level, "Source": source, "ID": item_id, "Parameter": parameter,
            "Value": value, "Status": status, "Action": ACTION[level]}


def scan_ranges(df, id_col, source, rules):
    """Check numeric columns against warning/critical limits; return list of alerts."""
    alerts = []
    for col, label, unit, warn, crit, low_bad in rules:
        if col not in df.columns: # skip missing columns instead of crashing
            continue
        levels = df[col].apply(grade, args=(warn, crit, low_bad)) # grade every row at once
        for i in levels[levels.notna()].index: # only rows that were flagged
            side = "Below" if low_bad else "Above"
            alerts.append(make_alert(levels[i], source, df.at[i, id_col], label,
                                     f"{df.at[i, col]} {unit}", f"{side} {levels[i].lower()} threshold"))
    return alerts


def scan_categories(df, id_col, source, col, label, mapping):
    """Turn text values (e.g. 'Overdue', 'Critical') into alerts using a dictionary."""
    if col not in df.columns:
        return []
    levels = df[col].map(mapping) # unknown values become NaN = no alert
    return [make_alert(levels[i], source, df.at[i, id_col], label, df.at[i, col], f"{label}: {df.at[i, col]}")
            for i in levels[levels.notna()].index]


def generate_alerts(data):
    """data = {'equipment': df, 'workers': df, 'incidents': df, 'risks': df}; returns sorted DataFrame."""
    alerts = []
    for key, id_col, rules in (("equipment", "equipment_id", EQUIPMENT_RULES), ("workers", "worker_id", WORKER_RULES)):
        if key in data:
            alerts += scan_ranges(data[key], id_col, key.capitalize(), rules)
    for key, id_col, col, label, mapping in CATEGORY_RULES:
        if key in data:
            alerts += scan_categories(data[key], id_col, key.capitalize(), col, label, mapping)
    out = pd.DataFrame(alerts, columns=ALERT_COLS)
    return out.sort_values("Level", key=lambda s: s.map(ORDER), kind="stable").reset_index(drop=True)


def format_alert(a):
    """Text version of one alert, laid out like Figure 1 in the brief."""
    line = "=" * 50
    return (f"{line}\nMINING MONITORING ALERT\n{line}\n[{a['Level']}]\n{a['Source']} ID: {a['ID']}\n"
            f"Parameter: {a['Parameter']}\nValue: {a['Value']}\nStatus: {a['Status']}\n"
            f"Recommended Action:\n {a['Action']}\n{line}")


def show_alerts_page(data):
    """Streamlit page: counts, filter, alert messages, CSV download."""
    import streamlit as st
    st.header("Alerts and Notifications")
    alerts = generate_alerts(data)
    if alerts.empty:
        st.success("No active alerts. All monitored values are within limits.")
        return
    c1, c2 = st.columns(2)
    c1.metric("Critical alerts", int((alerts["Level"] == "CRITICAL").sum()))
    c2.metric("Warnings", int((alerts["Level"] == "WARNING").sum()))
    pick = st.multiselect("Show levels", ["CRITICAL", "WARNING"], default=["CRITICAL", "WARNING"])
    shown = alerts[alerts["Level"].isin(pick)]
    for _, a in shown.head(20).iterrows(): # first 20 only, keeps the page light
        msg = f"**[{a['Level']}] {a['Source']} {a['ID']}** - {a['Parameter']}: {a['Value']} ({a['Status']}). {a['Action']}"
        (st.error if a["Level"] == "CRITICAL" else st.warning)(msg)
    st.dataframe(shown)
    st.download_button("Download alerts (CSV)", shown.to_csv(index=False), "alerts.csv")


if __name__ == "__main__": # quick terminal test with tiny sample data
    demo = {"equipment": pd.DataFrame({"equipment_id": ["TRK-012", "LDR-003"], "temperature": [105, 85],
                                       "vibration": [9.2, 3], "availability": [95, 60], "downtime": [10, 90],
                                       "maintenance_status": ["OK", "Overdue"]}),
            "workers": pd.DataFrame({"worker_id": ["W1", "W2"], "ppe_compliance": [40, 95], "fatigue_level": [9, 3]}),
            "incidents": pd.DataFrame({"incident_id": ["INC-1"], "severity": ["Critical"]})}
    print(calculate_risk(4, 5), calculate_risk(2, 2), calculate_risk(3, 3))
    result = generate_alerts(demo)
    print(result[["Level", "Source", "ID", "Parameter", "Value"]].to_string())
    print(format_alert(result.iloc[0]))