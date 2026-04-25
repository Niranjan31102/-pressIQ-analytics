import pandas as pd
import streamlit as st

PLANT_NAMES = {
    "AIR": "Airoli",
    "KAN": "Kandivali",
    "KND": "Kandivali",
    "BAN": "Bangalore",
    "CHE": "Chennai",
    "KOL": "Kolkata",
    "PUN": "Pune",
    "SAH": "Sahibabad",
    "SHD": "Sahibabad",
    "AHM": "Ahmedabad",
    "BAR": "Baroda",
    "MAN": "Manesar",
    "HYD": "Hyderabad",
    "LUC": "Lucknow",
    "NAG": "Nagpur",
    "TVM": "Trivandrum"
}

def norm(x):
    return str(x).strip().lower().replace("\n", " ")

def safe_div(a, b):
    return a / b if b not in [0, None] and pd.notna(b) else 0

def to_num(s):
    return pd.to_numeric(
        s.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False),
        errors="coerce"
    ).fillna(0)

def insight_box(text, kind="info"):
    css = "insight-card" if kind == "info" else "warning-card"
    st.markdown(f'<div class="{css}">{text}</div>', unsafe_allow_html=True)

def detect_dt_column(df):
    if "Total Downtime" in df.columns:
        return "Total Downtime"
    if "D.T." in df.columns:
        return "D.T."
    return None

def create_dt_bucket(x):
    if x <= 4:
        return "0-4"
    elif x <= 15:
        return "5-15"
    elif x <= 30:
        return "16-30"
    elif x <= 45:
        return "31-45"
    elif x <= 60:
        return "46-60"
    else:
        return "60+"

def clean_common_columns(df):
    df.columns = df.columns.str.strip()
    for col in [
        "Reason", "Department", "Related", "Machine", "PRESS",
        "Main/Supplement", "Edition", "GNP/SNP", "Folder"
    ]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df
