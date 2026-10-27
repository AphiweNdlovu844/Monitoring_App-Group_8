import pandas as pd
import numpy as np


def availability_percent(operating_time, downtime):
    denominator = operating_time + downtime
    return np.where(denominator > 0, (operating_time / denominator) * 100, 0)


def downtime_percent(downtime, operating_time):
    denominator = downtime + operating_time
    return np.where(denominator > 0, (downtime / denominator) * 100, 0)


def low_productivity(ratio, equipment_id):
    if pd.isna(ratio):
        return f"Unknown production {equipment_id}"
    if ratio < 80:
        return f"Low production {equipment_id}"
    return f"Normal production {equipment_id}"


def temperature_status(temp):
    if pd.isna(temp):
        return "Unknown"
    if temp > 100:
        return "Critical"
    if temp >= 80:
        return "Warning"
    return "Normal"


def vibration_status(vibr):
    if pd.isna(vibr):
        return "Unknown"
    if vibr > 8:
        return "Critical"
    if vibr >= 5:
        return "Warning"
    return "Normal"


def count_alerts(temp, vibr):
    if pd.isna(temp) or pd.isna(vibr):
        return 0
    alerts = 0
    if temp > 100 or temp >= 80:
        alerts += 1
    if vibr > 8 or vibr >= 5:
        alerts += 1
    return alerts


def overdue_equipment(df):
    return df[df["Maintenance_Status"].str.lower().str.contains("overdue", na=False)]


def under_maintenance(df):
    return df[df["Maintenance_Status"].str.lower().str.contains("under", na=False)]


def low_availability(df, threshold=80):
    return df[df["availability_percent"] < threshold]


def excessive_downtime(df, threshold=10):
    return df[df["downtime_percent"] > threshold]


def repeated_alerts(df, min_alerts=2):
    return df[df["alert_count"] >= min_alerts]


def equipment_kpis(df):
    return {
        "Total Equipment": len(df),
        "Overdue": len(overdue_equipment(df)),
        "Under Maintenance": len(under_maintenance(df)),
        "Low Availability": len(low_availability(df)),
        "Repeated Alerts": len(repeated_alerts(df)),
        "Avg Availability": f"{df['availability_percent'].mean():.1f}%",
    }

def ensure_availability(df):
  # 1. If lowercase version already exists, use it
  if (
      "availability_percent" in df.columns
      and not df["availability_percent"].isna().all()
  ):
    return df

  # 2. If uppercase version exists from database/CSV, copy it to lowercase
  if (
      "Availability_Pct" in df.columns
      and not df["Availability_Pct"].isna().all()
  ):
    df["availability_percent"] = df["Availability_Pct"]
    return df

  # 3. Otherwise, calculate it and store it as lowercase 'availability_percent'
  op_col = (
      "Operating_Time_90d_h"
      if "Operating_Time_90d_h" in df.columns
      else "Operating_Hours"
  )
  down_col = (
      "Downtime_90d_h" if "Downtime_90d_h" in df.columns else "Downtime_Hours"
  )

  if op_col in df.columns and down_col in df.columns:
    df["availability_percent"] = availability_percent(df[op_col], df[down_col])
  else:
    df["availability_percent"] = 0.0

  return df

def ensure_downtime(df):
  """Defensively ensures 'downtime_percent' exists,

  calculating it using downtime and operating hours if missing.
  """
  if "downtime_percent" in df.columns and not df["downtime_percent"].isna().all():
    return df

  if "Downtime_Pct" in df.columns and not df["Downtime_Pct"].isna().all():
    df["downtime_percent"] = df["Downtime_Pct"]
    return df

  op_col = "Operating_Time_90d_h"
  down_col = "Downtime_90d_h"

  if op_col in df.columns and down_col in df.columns:
    df["downtime_percent"] = downtime_percent(df[down_col], df[op_col])
  else:
    df["downtime_percent"] = 0.0

  return df

def highest_downtime(df, n=10):
  return df.sort_values("downtime_percent", ascending=False).head(n)[
      ["Equipment_ID", "Equipment_Type", "downtime_percent"]
  ]


def lowest_availability(df, n=10):
  return df.sort_values("availability_percent").head(n)[
      ["Equipment_ID", "Equipment_Type", "availability_percent"]
  ]


def highest_vibration(df, n=10):
  return df.sort_values("Vibration_mm_s", ascending=False).head(n)[
      ["Equipment_ID", "Equipment_Type", "Vibration_mm_s", "vib_status"]
  ]


def highest_temperature(df, n=10):
  return df.sort_values("Temperature_C", ascending=False).head(n)[
      ["Equipment_ID", "Equipment_Type", "Temperature_C", "temp_status"]
  ]


def most_alerts(df, n=10):
  return df.sort_values("alert_count", ascending=False).head(n)[
      ["Equipment_ID", "Equipment_Type", "alert_count"]
  ]


def downtime_by_type(df):
  return (
      df.groupby("Equipment_Type")["downtime_percent"]
      .mean()
      .round(2)
      .reset_index()
      .sort_values("downtime_percent", ascending=False)
  )


def availability_by_type(df):
  return (
      df.groupby("Equipment_Type")["availability_percent"]
      .mean()
      .round(2)
      .reset_index()
      .sort_values("availability_percent", ascending=False)
  )


def average_availability(df):
  return round(df["availability_percent"].mean(), 2)


def average_downtime(df):
  return round(df["downtime_percent"].mean(), 2)


def requires_immediate_inspection(df):
  mask = (df["temp_status"] == "Critical") | (df["vib_status"] == "Critical")
  return df[mask][
      [
          "Equipment_ID",
          "Equipment_Type",
          "Temperature_C",
          "temp_status",
          "Vibration_mm_s",
          "vib_status",
      ]
  ]


def equipment_count_by_type(df):
  return (
      df.groupby("Equipment_Type")
      .size()
      .reset_index(name="count")
      .sort_values("count", ascending=False)
  )


def rank_equipment(df, column, ascending=False, n=10, cols=None):
  if cols is None:
    cols = ["Equipment_ID", "Equipment_Type", column]
  cols = [c for c in cols if c in df.columns]
  return df.sort_values(column, ascending=ascending).head(n)[cols].reset_index(drop=True)


def equipment_requiring_maintenance(df):
  if "Maintenance_Status" not in df.columns or "alert_count" not in df.columns:
    return pd.DataFrame()
  mask = (
      df["Maintenance_Status"].str.lower().str.contains("overdue", na=False)
      | df["Maintenance_Status"].str.lower().str.contains("due", na=False)
      | (df["alert_count"] >= 2)
  )
  cols = ["Equipment_ID", "Equipment_Type", "Maintenance_Status", "alert_count"]
  cols = [c for c in cols if c in df.columns]
  return df[mask][cols]


def overdue_equipment(df):
  return df[df["Maintenance_Status"].str.lower().str.contains("overdue", na=False)]


def under_maintenance(df):
  return df[df["Maintenance_Status"].str.lower().str.contains("under", na=False)]


def low_availability(df, threshold=80):
  return df[df["availability_percent"] < threshold]


def excessive_downtime(df, threshold=10):
  return df[df["downtime_percent"] > threshold]


def repeated_alerts(df, min_alerts=2):
  return df[df["alert_count"] >= min_alerts]


def equipment_kpis(df):
  return {
      "Total Equipment": len(df),
      "Overdue": len(overdue_equipment(df)),
      "Under Maintenance": len(under_maintenance(df)),
      "Low Availability": len(low_availability(df)),
      "Repeated Alerts": len(repeated_alerts(df)),
      "Avg Availability": f"{df['availability_percent'].mean():.1f}%",
  }