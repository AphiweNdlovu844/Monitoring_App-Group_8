from pathlib import Path
import pandas as pd

# Define path lookup for your data folder
FOLDERS = [Path("data"), Path("../data"), Path("."), Path("..")]

def load(name):
    for f in FOLDERS:
        if (f / f"{name}.csv").exists():
            return pd.read_csv(f / f"{name}.csv")
    return pd.DataFrame()

def find(df, *keys):
    for k in keys:
        for c in df.columns:
            if k in str(c).lower().replace(" ", "_"):
                return c

BANDS = [(4, "Low"), (9, "Medium"), (16, "High"), (25, "Critical")]

def calculate_risk(likelihood, consequence):
    l, c = int(likelihood), int(consequence)
    if not (1 <= l <= 5 and 1 <= c <= 5):
        raise ValueError("Likelihood and consequence must be between 1 and 5.")
    score = l * c
    for top, name in BANDS:
        if score <= top:
            return score, name

def risk_warning(level):
    if level in ("High", "Critical"):
        return f"WARNING: {level.upper()} RISK - stop work and escalate to the manager."
    return "CAUTION: put controls in place." if level == "Medium" else "Low risk - keep monitoring."

# Alert rules and functions (Cell 6 & 7 logic)
ORDER = {"CRITICAL": 0, "WARNING": 1}
ACTION = {
    "CRITICAL": "Inspect immediately and start the appropriate maintenance/safety procedure.",
    "WARNING": "Monitor closely and schedule a check."
}

NUM_RULES = [
    (("temperature", "temp"), "Temperature", "C", 80, 100, False),
    (("vibration",), "Vibration", "mm/s", 5, 8, False),
    (("availability",), "Availability", "%", 85, 70, True),
    (("downtime",), "Downtime", "h", 40, 80, False),
    (("ppe",), "PPE compliance", "%", 80, 50, True),
    (("fatigue",), "Fatigue level", "/10", 6, 8, False)
]

TXT_RULES = [
    (("severity",), "Incident severity", {"critical": "CRITICAL", "high": "WARNING", "major": "WARNING"}),
    (("risk_level", "risk_class", "classification"), "Risk level", {"critical": "CRITICAL", "high": "WARNING"}),
    (("maintenance_status", "status"), "Maintenance status", {"overdue": "WARNING"}),
    (("ppe",), "PPE status", {"no": "WARNING", "partial": "WARNING", "non-compliant": "CRITICAL"}),
    (("fatigue",), "Fatigue", {"high": "WARNING", "very high": "CRITICAL"})
]

def grade(value, warn, crit, low_is_bad=False):
    if low_is_bad:
        return "CRITICAL" if value < crit else "WARNING" if value < warn else None
    return "CRITICAL" if value > crit else "WARNING" if value >= warn else None

def mk(name, df, idc, lv, label, value, status):
    hit = lv.notna()
    return pd.DataFrame({
        "Level": lv[hit], "Source": name, "ID": df.loc[hit, idc].astype(str), 
        "Parameter": label, "Value": value[hit], "Status": status[hit], 
        "Action": lv[hit].map(ACTION)
    })

def scan(name, df):
    parts = []
    if df.empty:
        return parts
    idc = next((find(df, k) for k in ("equipment_id", "worker_id", "incident_id", "id") if find(df, k)), df.columns[0])
    for keys, label, unit, warn, crit, low in NUM_RULES:
        col = find(df, *keys)
        if not col:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        if low and unit == "%" and s.max() <= 1:
            s = s * 100
        lv = s.apply(grade, args=(warn, crit, low))
        parts.append(mk(name, df, idc, lv, label, s.astype(str) + " " + unit,
                        ("Below " if low else "Above ") + lv.fillna("").str.lower() + " threshold"))
    for keys, label, mp in TXT_RULES:
        col = find(df, *keys)
        if not col:
            continue
        lv = df[col].astype(str).str.strip().str.lower().map(mp)
        parts.append(mk(name, df, idc, lv, label, df[col].astype(str), label + ": " + df[col].astype(str)))
    return parts

def generate_alerts(data):
    parts = [p for n, d in data.items() for p in scan(n, d)]
    if not parts:
        return pd.DataFrame(columns=["Level", "Source", "ID", "Parameter", "Value", "Status", "Action"])
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values("Level", key=lambda s: s.map(ORDER), kind="stable")
    return out.drop_duplicates(["Source", "ID", "Parameter"]).reset_index(drop=True)