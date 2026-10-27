import os
import sqlite3
import pandas as pd
from functions.cleaning import master_clean  # 1. Import at the very top

DB_PATH = "mine_monitoring.db"


def get_connection():
  """Returns a SQLite connection object with foreign keys enabled."""
  conn = sqlite3.connect(DB_PATH, check_same_thread=False)
  conn.execute("PRAGMA foreign_keys = ON;")
  return conn


def initialize_database():
  """Reads CSVs from the data folder, cleans them using master_clean,

  and writes them to SQLite.
  """
  conn = get_connection()

  csv_files = {
      "users.csv": "users",
      "permissions.csv": "permissions",
      "workers.csv": "workers",
      "equipment.csv": "equipment",
      "equipment_readings.csv": "equipment_readings",
      "maintenance.csv": "maintenance",
      "incidents.csv": "incidents",
      "risk_assessments.csv": "risk_assessments",
  }

  for file_name, table_name in csv_files.items():
    file_path = os.path.join("data", file_name)
    if os.path.exists(file_path):
      df = pd.read_csv(file_path)

      # 2. Pass the dataframe through your master cleaning module!
      df = master_clean(df)

      # 3. Push the clean data to SQLite
      df.to_sql(table_name, conn, if_exists="replace", index=False)
      print(
          f"Successfully loaded and cleaned {file_name} into table"
          f" '{table_name}'."
      )
    else:
      print(f"Warning: {file_path} not found.")

  conn.close()


if __name__ == "__main__":
  initialize_database()