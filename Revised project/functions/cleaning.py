import numpy as np
import pandas as pd


def clean_column_names(df):
  """Standardizes column names by stripping whitespace,

  replacing spaces with underscores, and ensuring consistency.
  """
  df.columns = (
      df.columns.str.strip().str.replace(" ", "_").str.replace("-", "_")
  )
  return df


def clean_text_columns(df):
  """Strips leading and trailing whitespace from all string/object columns

  and handles messy text entries.
  """
  for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].astype(str).str.strip()
    # Safely convert literal string 'nan' back to true pandas missing values if needed
    df[col] = df[col].replace({"nan": np.nan, "NaN": np.nan, "": np.nan})
  return df


def fill_missing_numerics(df, fill_value=0):
  """Defensively fills missing numeric values with a default (like 0)

  to prevent calculations from returning NaN or crashing.
  """
  for col in df.select_dtypes(include=[np.number]).columns:
    df[col] = df[col].fillna(fill_value)
  return df


def master_clean(df):
  """A master wrapper function that runs all cleaning steps sequentially

  on any raw dataframe loaded from a CSV.
  """
  if df is None or df.empty:
    return df

  df = clean_column_names(df)
  df = clean_text_columns(df)
  df = fill_missing_numerics(df)
  return df