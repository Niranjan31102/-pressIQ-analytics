import html
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from modules.drive_loader import (
    expected_ems_filename,
    find_file_in_drive,
    download_drive_file,
)


# ============================================================
# BASELINE FILES
# ============================================================

BASELINE_DIR = Path("baseline_data")

# Keep only the real baseline files in baseline_data folder.
# This auto-detects common file names to avoid file-name mismatch issues.
BASELINE_FILE_CANDIDATES = [
    "APR26_Utility_performance.xlsx",
    "APR_26_Utility_performance.xlsx",
    "APR_26 Utility performance.xlsx",
    "MAY26_Utility_performance.xlsx",
    "May26_Utility_performance.xlsx",
    "May_26_Utility_performance.xlsx",
    "May_26 Utility performance.xlsx",
]

BASELINE_FILES = [
    BASELINE_DIR / file_name
    for file_name in BASELINE_FILE_CANDIDATES
    if (BASELINE_DIR / file_name).exists()
]


# ============================================================
# ZONE LOGIC
# ============================================================

ZONE_ORDER = [
    "Zone 1 | 06:00-08:00",
    "Zone 2 | 09:00-16:00",
    "Zone 3 | 17:00-23:00",
    "Zone 4 | 00:00-05:00",
]

ZONE_MAP = {
    "06:00": "Zone 1 | 06:00-08:00",
    "07:00": "Zone 1 | 06:00-08:00",
    "08:00": "Zone 1 | 06:00-08:00",

    "09:00": "Zone 2 | 09:00-16:00",
    "10:00": "Zone 2 | 09:00-16:00",
    "11:00": "Zone 2 | 09:00-16:00",
    "12:00": "Zone 2 | 09:00-16:00",
    "13:00": "Zone 2 | 09:00-16:00",
    "14:00": "Zone 2 | 09:00-16:00",
    "15:00": "Zone 2 | 09:00-16:00",
    "16:00": "Zone 2 | 09:00-16:00",

    "17:00": "Zone 3 | 17:00-23:00",
    "18:00": "Zone 3 | 17:00-23:00",
    "19:00": "Zone 3 | 17:00-23:00",
    "20:00": "Zone 3 | 17:00-23:00",
    "21:00": "Zone 3 | 17:00-23:00",
    "22:00": "Zone 3 | 17:00-23:00",
    "23:00": "Zone 3 | 17:00-23:00",

    "00:00": "Zone 4 | 00:00-05:00",
    "01:00": "Zone 4 | 00:00-05:00",
    "02:00": "Zone 4 | 00:00-05:00",
    "03:00": "Zone 4 | 00:00-05:00",
    "04:00": "Zone 4 | 00:00-05:00",
    "05:00": "Zone 4 | 00:00-05:00",
}


# ============================================================
# EVENT-BASED FEEDER LOGIC
# ============================================================

# Feeders that run only during special production, trial, or GNP/glossy jobs.
# Add more keywords here later when you share the feeder mapping.
EVENT_BASED_KEYWORDS = [
    "UV",
    "UV TOWER",
    "PU15",
    "PU5",
    "GNP",
]

# For event feeders, daily zone consumption is classified as:
# <= 5 units       = Idle / no use
# > 5 and <= 25    = Test / Trial
# > 25             = Production Active
EVENT_IDLE_THRESHOLD = 5
EVENT_TRIAL_THRESHOLD = 25
EVENT_ZERO_RATIO_THRESHOLD = 0.70
MIN_EVENT_ACTIVE_DAYS = 2


# ============================================================
# CSS
# ============================================================

def add_utility_css():
    st.markdown("""
    <style>
    .utility-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 45%, #2563eb 100%);
        padding: 26px 30px;
        border-radius: 24px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.20);
    }
    .utility-title {
        font-size: 34px;
        font-weight: 900;
        margin-bottom: 4px;
    }
    .utility-subtitle {
        font-size: 16px;
        color: #dbeafe;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        min-height: 112px;
    }
    .kpi-label {
        font-size: 12px;
        font-weight: 800;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 900;
        color: #0f172a;
        margin-top: 8px;
    }
    .feeder-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }
    .feeder-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 15px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 12px;
    }
    .feeder-name {
        font-size: 20px;
        font-weight: 900;
        color: #0f172a;
    }
    .feeder-meta {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
    }
    .status-pill {
        padding: 8px 13px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 900;
        white-space: nowrap;
    }
    .status-in {
        background: #dcfce7;
        color: #166534;
    }
    .status-warning {
        background: #fef3c7;
        color: #92400e;
    }
    .status-out {
        background: #fee2e2;
        color: #991b1b;
    }
    .status-data {
        background: #f3e8ff;
        color: #6b21a8;
    }
    .status-pending {
        background: #e2e8f0;
        color: #334155;
    }
    .status-minor {
        background: #e0f2fe;
        color: #075985;
    }
    .status-event {
        background: #ede9fe;
        color: #5b21b6;
    }
    .status-idle {
        background: #f1f5f9;
        color: #475569;
    }
    .zone-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
    }
    .zone-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 14px;
    }
    .zone-title {
        font-size: 12px;
        font-weight: 900;
        color: #475569;
        margin-bottom: 6px;
    }
    .zone-value {
        font-size: 24px;
        font-weight: 900;
        color: #0f172a;
    }
    .zone-base {
        font-size: 12px;
        color: #64748b;
        margin-top: 5px;
    }
    .zone-status {
        font-size: 12px;
        font-weight: 900;
        margin-top: 8px;
    }
    .remark-box {
        background: #f8fafc;
        border-left: 5px solid #2563eb;
        border-radius: 14px;
        padding: 12px 14px;
        margin-top: 14px;
        color: #334155;
        font-size: 14px;
    }
    .mode-note {
        background: #eff6ff;
        border-left: 5px solid #2563eb;
        padding: 14px 16px;
        border-radius: 14px;
        color: #1e3a8a;
        margin-top: 12px;
        margin-bottom: 18px;
    }
    @media (max-width: 900px) {
        .zone-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def get_date_list(start_date, end_date):
    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current = current + timedelta(days=1)

    return dates


def normalize_hour(col):
    try:
        dt = pd.to_datetime(col)
        return dt.strftime("%H:00")
    except Exception:
        text = str(col).strip()
        if ":" in text:
            try:
                return pd.to_datetime(text).strftime("%H:00")
            except Exception:
                return text
        return text


def safe_seek(file_obj):
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)


def format_units(value):
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}"


def status_class(status):
    if status == "In Control":
        return "status-in"
    if status == "Warning":
        return "status-warning"
    if status == "Out Control":
        return "status-out"
    if status == "Data Error Suspect":
        return "status-data"
    if status == "Minor Variation":
        return "status-minor"
    if status in ["Test / Trial", "Event Baseline Pending"]:
        return "status-event"
    if status == "Idle":
        return "status-idle"
    return "status-pending"


def is_event_keyword_feeder(feeder_name):
    text = str(feeder_name).upper()
    return any(keyword in text for keyword in EVENT_BASED_KEYWORDS)


def classify_event_activity(units):
    if pd.isna(units) or units <= EVENT_IDLE_THRESHOLD:
        return "Idle"
    if units <= EVENT_TRIAL_THRESHOLD:
        return "Test / Trial"
    return "Production Active"


# ============================================================
# READ CURRENT EMS DAILY FILE
# ============================================================

def read_hourly_sheet(uploaded_file, sheet_name="Hourly"):
    safe_seek(uploaded_file)
    raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
    header_row = next((i for i in range(min(12, len(raw)))
                       if str(raw.iloc[i, 1]).strip().lower() == "feeder name"), None)
    if header_row is None:
        raise ValueError("Hourly sheet: Feeder Name header not found.")
    hours = [(i, normalize_hour(raw.iloc[header_row, i])) for i in range(2, raw.shape[1])]
    hours = [(i, h) for i, h in hours if h in ZONE_MAP]
    hour_cols = [h for _, h in hours]
    if len(hour_cols) != 24 or len(set(hour_cols)) != 24:
        raise ValueError("Hourly sheet requires 24 unique hourly columns (06:00 through 05:00).")
    df = raw.iloc[header_row + 1:, [0, 1] + [i for i, _ in hours]].copy()
    df.columns = ["Sr No", "Feeder Name"] + hour_cols
    serial = pd.to_numeric(df["Sr No"], errors="coerce")
    df = df[serial.notna() & serial.gt(0) & serial.mod(1).eq(0)].copy()
    if df.empty or df["Feeder Name"].isna().any():
        raise ValueError("Hourly sheet contains no usable feeder rows or a missing feeder name.")
    df["Sr No"] = pd.to_numeric(df["Sr No"]).astype(int).astype(str)
    if df["Sr No"].duplicated().any():
        raise ValueError("Duplicate EMS serial numbers. Correct the workbook before analysis.")
    df["Feeder Name"] = df["Feeder Name"].astype(str).str.strip()
    df["Feeder ID"] = df["Sr No"] + " - " + df["Feeder Name"]
    for col in hour_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Missing data remains missing, never replaced by zero.
    if header_row > 0:
        try:
            issue = pd.to_datetime(raw.iloc[header_row - 1, 1])
            if pd.notna(issue):
                df.attrs["issue_date"] = issue.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return df, hour_cols


def long_format(df, hour_cols):
    long_df = df.melt(
        id_vars=["Sr No", "Feeder Name", "Feeder ID"],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Consumption",
    )

    long_df["Consumption"] = pd.to_numeric(long_df["Consumption"], errors="coerce")
    long_df["Zone"] = long_df["Hour"].map(ZONE_MAP)

    return long_df


# ============================================================
# CLEANING LOGIC
# ============================================================

def clean_consumption_data(long_df):
    df = long_df.copy()

    df["Quality Status"] = "Valid"
    df["Clean Consumption"] = df["Consumption"]

    # Important:
    # Only negative values are treated as data quality issue.
    # Positive high/low jumps are NOT treated as data error because print timing changes daily.
    negative_mask = df["Consumption"] < 0

    df.loc[negative_mask, "Quality Status"] = "Data Error Suspect"
    df.loc[negative_mask, "Clean Consumption"] = np.nan

    return df


def create_data_error_remark(feeder_id, current_long):
    feeder_issues = current_long[
        (current_long["Feeder ID"] == feeder_id) &
        (current_long["Consumption"] < 0)
    ].copy()

    if feeder_issues.empty:
        return "EMS data issue found. Kindly verify source reading."

    issue_text = []

    for _, row in feeder_issues.iterrows():
        date_part = ""
        if "Analysis Date" in feeder_issues.columns:
            date_part = f"{row.get('Analysis Date', '')} "
        issue_text.append(
            f"{date_part}{row['Hour']} value {row['Consumption']:,.1f}"
        )

    return (
        "Negative consumption found: "
        + "; ".join(issue_text)
        + ". This may be EMS/meter data error. Kindly check source reading."
    )


# ============================================================
# BASELINE READING
# ============================================================

def read_baseline_workbook(baseline_file):
    xls = pd.ExcelFile(baseline_file)
    all_days = []

    for sheet in xls.sheet_names:
        raw_df = pd.read_excel(baseline_file, sheet_name=sheet, header=None)

        if raw_df.shape[0] < 5:
            continue

        headers = raw_df.iloc[2].tolist()
        df = raw_df.iloc[3:].copy()
        df.columns = headers
        df = df.dropna(how="all")

        df = df.rename(columns={
            df.columns[0]: "Sr No",
            df.columns[1]: "Feeder Name",
        })

        df = df[pd.notna(df["Feeder Name"])].copy()
        df = df.head(72)

        df["Sr No"] = df["Sr No"].astype(str).str.replace(".0", "", regex=False)
        df["Feeder Name"] = df["Feeder Name"].astype(str).str.strip()
        df["Feeder ID"] = df["Sr No"] + " - " + df["Feeder Name"]

        file_label = Path(str(baseline_file)).stem
        df["Baseline Day"] = file_label + " | " + str(sheet)

        hour_source_cols = df.columns[2:-2]
        clean_map = {col: normalize_hour(col) for col in hour_source_cols}
        df = df.rename(columns=clean_map)

        hour_cols = [h for h in clean_map.values() if h in ZONE_MAP]

        for col in hour_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        long_df = df.melt(
            id_vars=["Baseline Day", "Sr No", "Feeder Name", "Feeder ID"],
            value_vars=hour_cols,
            var_name="Hour",
            value_name="Consumption",
        )

        all_days.append(long_df)

    if not all_days:
        return pd.DataFrame()

    baseline_long = pd.concat(all_days, ignore_index=True)
    baseline_long["Zone"] = baseline_long["Hour"].map(ZONE_MAP)

    return baseline_long


def build_baseline(baseline_files):
    if not baseline_files:
        return None, 0

    baseline_frames = []

    for file in baseline_files:
        try:
            base_long = read_baseline_workbook(file)
            if not base_long.empty:
                baseline_frames.append(base_long)
        except Exception as e:
            st.warning(f"Baseline file skipped: {file}. Error: {e}")

    if not baseline_frames:
        return None, 0

    baseline_long = pd.concat(baseline_frames, ignore_index=True)
    baseline_clean = clean_consumption_data(baseline_long)

    valid_base = baseline_clean[baseline_clean["Quality Status"] == "Valid"].copy()

    daily_zone = valid_base.groupby(
        ["Baseline Day", "Feeder ID", "Feeder Name", "Zone"],
        as_index=False,
    )["Clean Consumption"].sum()

    # Regular baseline: uses all valid historical days.
    regular_baseline = daily_zone.groupby(
        ["Feeder ID", "Feeder Name", "Zone"],
        as_index=False,
    )["Clean Consumption"].agg(
        regular_median="median",
        regular_mean="mean",
        regular_p75=lambda x: x.quantile(0.75),
        regular_p90=lambda x: x.quantile(0.90),
    )

    # Event feeder detection and active-day baseline.
    activity = daily_zone.copy()
    activity["Event Activity"] = activity["Clean Consumption"].apply(classify_event_activity)

    activity_summary = activity.groupby(
        ["Feeder ID", "Feeder Name", "Zone"],
        as_index=False,
    ).agg(
        baseline_total_days=("Baseline Day", "nunique"),
        baseline_idle_days=("Event Activity", lambda x: (x == "Idle").sum()),
        baseline_trial_days=("Event Activity", lambda x: (x == "Test / Trial").sum()),
        baseline_active_days=("Event Activity", lambda x: (x == "Production Active").sum()),
    )

    activity_summary["baseline_idle_ratio"] = (
        activity_summary["baseline_idle_days"] / activity_summary["baseline_total_days"].replace(0, np.nan)
    )

    activity_summary["keyword_event_feeder"] = activity_summary["Feeder Name"].apply(is_event_keyword_feeder)
    activity_summary["auto_event_feeder"] = activity_summary["baseline_idle_ratio"] >= EVENT_ZERO_RATIO_THRESHOLD
    activity_summary["is_event_based"] = (
        activity_summary["keyword_event_feeder"] | activity_summary["auto_event_feeder"]
    )

    active_days = activity[activity["Event Activity"] == "Production Active"].copy()

    if active_days.empty:
        active_baseline = pd.DataFrame(
            columns=[
                "Feeder ID", "Feeder Name", "Zone",
                "active_median", "active_mean", "active_p75", "active_p90",
            ]
        )
    else:
        active_baseline = active_days.groupby(
            ["Feeder ID", "Feeder Name", "Zone"],
            as_index=False,
        )["Clean Consumption"].agg(
            active_median="median",
            active_mean="mean",
            active_p75=lambda x: x.quantile(0.75),
            active_p90=lambda x: x.quantile(0.90),
        )

    baseline = regular_baseline.merge(
        activity_summary,
        on=["Feeder ID", "Feeder Name", "Zone"],
        how="left",
    ).merge(
        active_baseline,
        on=["Feeder ID", "Feeder Name", "Zone"],
        how="left",
    )

    # Final baseline columns used by the dashboard.
    # Regular feeders use all-day baseline.
    # Event feeders use production-active-day baseline when available.
    baseline["baseline_median"] = baseline["regular_median"]
    baseline["baseline_mean"] = baseline["regular_mean"]
    baseline["baseline_p75"] = baseline["regular_p75"]
    baseline["baseline_p90"] = baseline["regular_p90"]

    event_mask = baseline["is_event_based"].fillna(False) & baseline["active_median"].notna()

    baseline.loc[event_mask, "baseline_median"] = baseline.loc[event_mask, "active_median"]
    baseline.loc[event_mask, "baseline_mean"] = baseline.loc[event_mask, "active_mean"]
    baseline.loc[event_mask, "baseline_p75"] = baseline.loc[event_mask, "active_p75"]
    baseline.loc[event_mask, "baseline_p90"] = baseline.loc[event_mask, "active_p90"]

    day_count = baseline_long["Baseline Day"].nunique()

    return baseline, day_count


# ============================================================
# CONTROL STATUS LOGIC
# ============================================================

def minimum_impact_required(baseline_median):
    if pd.isna(baseline_median):
        return 0

    if baseline_median < 50:
        return 25

    if baseline_median < 500:
        return 50

    return baseline_median * 0.10


def create_feeder_zone_summary(current_long, baseline, baseline_multiplier=1):
    current_clean = clean_consumption_data(current_long)

    zone_summary = current_clean.groupby(
        ["Feeder ID", "Feeder Name", "Zone"],
        as_index=False,
    ).agg(
        current_units=("Clean Consumption", "sum"),
        issue_count=("Quality Status", lambda x: (x != "Valid").sum()),
    )

    # Current selected-range daily activity classification.
    if "Analysis Date" in current_clean.columns:
        daily_keys = ["Analysis Date", "Feeder ID", "Feeder Name", "Zone"]
    else:
        current_clean = current_clean.copy()
        current_clean["Analysis Date"] = "Current"
        daily_keys = ["Analysis Date", "Feeder ID", "Feeder Name", "Zone"]

    current_daily_zone = current_clean.groupby(
        daily_keys,
        as_index=False,
    )["Clean Consumption"].sum()

    current_daily_zone["Current Event Activity"] = current_daily_zone["Clean Consumption"].apply(
        classify_event_activity
    )

    current_activity = current_daily_zone.groupby(
        ["Feeder ID", "Feeder Name", "Zone"],
        as_index=False,
    ).agg(
        current_idle_days=("Current Event Activity", lambda x: (x == "Idle").sum()),
        current_trial_days=("Current Event Activity", lambda x: (x == "Test / Trial").sum()),
        current_active_days=("Current Event Activity", lambda x: (x == "Production Active").sum()),
    )

    zone_summary = zone_summary.merge(
        current_activity,
        on=["Feeder ID", "Feeder Name", "Zone"],
        how="left",
    )

    for col in ["current_idle_days", "current_trial_days", "current_active_days"]:
        zone_summary[col] = zone_summary[col].fillna(0).astype(int)

    if baseline is not None:
        zone_summary = zone_summary.merge(
            baseline,
            on=["Feeder ID", "Feeder Name", "Zone"],
            how="left",
        )

        zone_summary["is_event_based"] = zone_summary["is_event_based"].fillna(False)

        # Regular feeders compare N-day actual with daily baseline x N days.
        # Event feeders compare production-active actual with active baseline x active days.
        zone_summary["effective_baseline_multiplier"] = baseline_multiplier
        event_mask = zone_summary["is_event_based"] == True
        zone_summary.loc[event_mask, "effective_baseline_multiplier"] = zone_summary.loc[
            event_mask, "current_active_days"
        ]

        for col in ["baseline_median", "baseline_mean", "baseline_p75", "baseline_p90"]:
            zone_summary[col] = zone_summary[col] * zone_summary["effective_baseline_multiplier"]

    else:
        zone_summary["baseline_median"] = np.nan
        zone_summary["baseline_mean"] = np.nan
        zone_summary["baseline_p75"] = np.nan
        zone_summary["baseline_p90"] = np.nan
        zone_summary["is_event_based"] = False
        zone_summary["baseline_active_days"] = np.nan
        zone_summary["effective_baseline_multiplier"] = baseline_multiplier

    def zone_status(row):
        if row["issue_count"] > 0:
            return "Data Error Suspect"

        is_event = bool(row.get("is_event_based", False))

        if is_event:
            current_active_days = int(row.get("current_active_days", 0))
            current_trial_days = int(row.get("current_trial_days", 0))
            baseline_active_days = row.get("baseline_active_days", np.nan)

            if current_active_days == 0 and current_trial_days > 0:
                return "Test / Trial"

            if current_active_days == 0:
                return "Idle"

            if pd.isna(row["baseline_median"]) or pd.isna(baseline_active_days) or baseline_active_days < MIN_EVENT_ACTIVE_DAYS:
                return "Event Baseline Pending"

        else:
            if pd.isna(row["baseline_median"]):
                return "Baseline Pending"

        current_value = row["current_units"]
        median_value = row["baseline_median"]
        p75_value = row["baseline_p75"]
        p90_value = row["baseline_p90"]

        difference = current_value - median_value
        minimum_impact = minimum_impact_required(median_value)

        if current_value > p90_value:
            if difference < minimum_impact:
                return "Minor Variation"
            return "Out Control"

        if current_value > p75_value:
            if difference < minimum_impact:
                return "Minor Variation"
            return "Warning"

        return "In Control"

    zone_summary["Zone Status"] = zone_summary.apply(zone_status, axis=1)

    return zone_summary


def final_feeder_status(statuses):
    statuses = list(statuses)

    if "Data Error Suspect" in statuses:
        return "Data Error Suspect"

    if "Out Control" in statuses:
        return "Out Control"

    if "Warning" in statuses:
        return "Warning"

    if "Event Baseline Pending" in statuses:
        return "Event Baseline Pending"

    if "Test / Trial" in statuses:
        return "Test / Trial"

    if "Minor Variation" in statuses:
        return "Minor Variation"

    if all(s == "Idle" for s in statuses):
        return "Idle"

    if all(s == "Baseline Pending" for s in statuses):
        return "Baseline Pending"

    return "In Control"


# ============================================================
# REMARKS AND CARD RENDERING
# ============================================================

def create_remark(feeder_id, feeder_name, feeder_status, zone_rows, current_long):
    if feeder_status == "Baseline Pending":
        return "Baseline not available. Please check seasonal baseline files."

    if feeder_status == "Event Baseline Pending":
        return (
            "This appears to be an event-based feeder. It has production-active use today, "
            "but not enough previous active-use days are available to build a reliable active baseline."
        )

    if feeder_status == "Data Error Suspect":
        return create_data_error_remark(feeder_id, current_long)

    if feeder_status == "Idle":
        return "This event-based feeder is idle in the selected period. No production use detected."

    if feeder_status == "Test / Trial":
        return (
            "Small consumption found. This looks like testing/trial/warm-up, "
            "not actual production use. No action required unless repeated unexpectedly."
        )

    if feeder_status == "Minor Variation":
        return (
            "Consumption is above the statistical limit, but the unit difference is very small. "
            "Marked as minor variation to avoid unnecessary false alarm."
        )

    out_zones = zone_rows[zone_rows["Zone Status"] == "Out Control"]["Zone"].tolist()
    warn_zones = zone_rows[zone_rows["Zone Status"] == "Warning"]["Zone"].tolist()

    if out_zones:
        zone_text = ", ".join([z.split("|")[0].strip() for z in out_zones])
        event_note = ""
        if zone_rows.get("is_event_based", pd.Series([False])).fillna(False).any():
            event_note = " This is event-based logic, compared with previous production-active days only."
        return (
            f"Consumption is out of seasonal control in {zone_text}. "
            "Review this feeder for abnormal running, idle load, production variation, or utility support load."
            + event_note
        )

    if warn_zones:
        zone_text = ", ".join([z.split("|")[0].strip() for z in warn_zones])
        event_note = ""
        if zone_rows.get("is_event_based", pd.Series([False])).fillna(False).any():
            event_note = " This is event-based logic, compared with previous production-active days only."
        return (
            f"Consumption is above normal range in {zone_text}. "
            "Keep under watch and compare with production activity."
            + event_note
        )

    if zone_rows.get("is_event_based", pd.Series([False])).fillna(False).any():
        return (
            "Event-based feeder logic applied. Idle and test/trial days are not used as production baseline. "
            "Current production-active consumption is within active-use control range."
        )

    return "Consumption is within seasonal control range for all zones."


def render_feeder_card(feeder_id, feeder_name, zone_rows, feeder_status, current_long):
    status_css = status_class(feeder_status)
    remark = create_remark(feeder_id, feeder_name, feeder_status, zone_rows, current_long)

    safe_feeder_id = html.escape(str(feeder_id))
    safe_feeder_name = html.escape(str(feeder_name))
    safe_remark = html.escape(str(remark))

    zone_html_parts = []

    for zone in ZONE_ORDER:
        row = zone_rows[zone_rows["Zone"] == zone]

        if row.empty:
            current = 0
            median = np.nan
            zstatus = "Baseline Pending"
        else:
            row = row.iloc[0]
            current = row["current_units"]
            median = row["baseline_median"]
            zstatus = row["Zone Status"]

        z_color = {
            "In Control": "#166534",
            "Warning": "#92400e",
            "Out Control": "#991b1b",
            "Data Error Suspect": "#6b21a8",
            "Minor Variation": "#075985",
            "Test / Trial": "#5b21b6",
            "Event Baseline Pending": "#5b21b6",
            "Idle": "#475569",
            "Baseline Pending": "#334155",
        }.get(zstatus, "#334155")

        zone_html_parts.append(
            f'<div class="zone-box">'
            f'<div class="zone-title">{html.escape(zone)}</div>'
            f'<div class="zone-value">{format_units(current)}</div>'
            f'<div class="zone-base">Baseline median: {format_units(median)}</div>'
            f'<div class="zone-status" style="color:{z_color};">{html.escape(zstatus)}</div>'
            f'</div>'
        )

    zone_html = "".join(zone_html_parts)

    card_html = (
        f'<div class="feeder-card">'
        f'<div class="feeder-head">'
        f'<div>'
        f'<div class="feeder-name">{safe_feeder_name}</div>'
        f'<div class="feeder-meta">{safe_feeder_id}</div>'
        f'</div>'
        f'<div class="status-pill {status_css}">{html.escape(feeder_status)}</div>'
        f'</div>'
        f'<div class="zone-grid">{zone_html}</div>'
        f'<div class="remark-box"><b>Remark:</b> {safe_remark}</div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


# ============================================================
# MAIN MODULE
# ============================================================

# Phase 1.1 mapping is embedded for a one-file deployment.
# feeder_mapping.json in the delivery package is its reviewable companion.
# Enable DG only after the electrical team confirms non-overlapping source meters.
PHASE_MAPPING = {'version': '1.1', 'evidence': 'Uploaded Utility Tree structure(1).pptx, slides 1–2; EMS sample serial numbers and names. Physical hierarchy is not a source-energy balance.', 'dg_source_ids': [], 'dg_mapping_confirmed': False, 'solar_accounting_confirmed': False, 'nodes': {'1': {'name': 'HT INCOMER-1', 'parent': None, 'meter': True}, '2': {'name': 'HT INCOMER-2', 'parent': None, 'meter': True}, '3': {'name': 'TRANSFORMER 2 INCOMER', 'parent': '2', 'meter': True}, '4': {'name': 'TRANSFORMER 1 INCOMER', 'parent': '1', 'meter': True}, '5': {'name': 'OLD PCC 9F2 INCOMER', 'parent': '4', 'meter': True}, '6': {'name': 'DG POWER 9F', 'parent': 'dg_distribution', 'meter': True}, '7': {'name': 'DG POWER 3F', 'parent': 'dg_distribution', 'meter': True}, '8': {'name': 'EB POWER 6F', 'parent': 'unmapped', 'meter': True}, '9': {'name': 'DM PLANT PDB', 'parent': 'dm', 'meter': True}, '10': {'name': 'STP', 'parent': 'dm', 'meter': True}, '11': {'name': 'ETP', 'parent': 'dm', 'meter': True}, '12': {'name': 'WATER PUMP PANEL', 'parent': 'dm', 'meter': True}, '13': {'name': 'DRIVER CANTEEN', 'parent': 'dm', 'meter': True}, '14': {'name': 'DM PLANT MCC', 'parent': 'dm', 'meter': True}, '15': {'name': 'DG1', 'parent': 'dg', 'meter': True}, '16': {'name': 'DG2', 'parent': 'dg', 'meter': True}, '17': {'name': 'DG4', 'parent': 'dg', 'meter': True}, '18': {'name': 'UTILITY PANEL', 'parent': '5', 'meter': True}, '19': {'name': 'ADMIN BUILDING MAIN PANEL', 'parent': '5', 'meter': True}, '20': {'name': 'CANTEEN PDB', 'parent': '19', 'meter': True}, '21': {'name': 'AC PLANT MAIN PANEL', 'parent': '5', 'meter': True}, '22': {'name': 'CHILLER 1', 'parent': '21', 'meter': True}, '23': {'name': 'CHILLER 2', 'parent': '21', 'meter': True}, '24': {'name': 'CHILLER 3', 'parent': '21', 'meter': True}, '25': {'name': 'CHILLER 4', 'parent': '21', 'meter': True}, '26': {'name': 'OSCI COOLING SKID PRI PUMP', 'parent': '21', 'meter': True}, '27': {'name': 'OSCI COOLING SKID SEC PUMP', 'parent': '21', 'meter': True}, '28': {'name': 'MOTOR SKID PRI PUMP', 'parent': '21', 'meter': True}, '29': {'name': 'MOTOR SKID SEC PUMP', 'parent': '21', 'meter': True}, '30': {'name': 'COMPRESSOR MAIN', 'parent': '35', 'meter': True}, '31': {'name': 'COMPRESSOR 1', 'parent': '30', 'meter': True}, '32': {'name': 'COMPRESSOR 2', 'parent': '30', 'meter': True}, '33': {'name': 'COMPRESSOR 3', 'parent': '30', 'meter': True}, '34': {'name': 'COMPRESSOR 4', 'parent': '30', 'meter': True}, '35': {'name': 'PRESS 1 INCOMER', 'parent': '5', 'meter': True}, '36': {'name': 'PRESS 2 INCOMER', 'parent': '5', 'meter': True}, '37': {'name': 'PRESS 1 FEEDER (3200 A)', 'parent': '35', 'meter': True}, '38': {'name': 'PRESS 2 FEEDER (3200 A)', 'parent': '36', 'meter': True}, '39': {'name': 'UPS 1', 'parent': '35', 'meter': True}, '40': {'name': 'UPS 2', 'parent': '36', 'meter': True}, '41': {'name': 'UV TOWER PU5', 'parent': '36', 'meter': True}, '42': {'name': 'SPARE', 'parent': '36', 'meter': True}, '43': {'name': 'UV TOWER PU15', 'parent': '36', 'meter': True}, '44': {'name': 'SPARE', 'parent': '36', 'meter': True}, '45': {'name': 'MAIL ROOM DB MAIN', 'parent': '35', 'meter': True}, '46': {'name': 'PLANT POWER PANEL MAIN', 'parent': '5', 'meter': True}, '47': {'name': 'INCOMER NEW PDB WORKSHOP', 'parent': '46', 'meter': True}, '48': {'name': 'SPLIT AC DB MAIN', 'parent': '46', 'meter': True}, '49': {'name': 'NP GODOWN MAIN', 'parent': '46', 'meter': True}, '50': {'name': 'AC DB1 MAIN', 'parent': '46', 'meter': True}, '51': {'name': 'AHU DB 2', 'parent': '46', 'meter': True}, '52': {'name': 'AHU DB 1 MAIN', 'parent': '46', 'meter': True}, '53': {'name': 'INCOMER MAIN LDB PANEL', 'parent': '5', 'meter': True}, '54': {'name': 'MLDB 1', 'parent': '53', 'meter': True}, '55': {'name': 'MLDB 2', 'parent': '53', 'meter': True}, '56': {'name': 'MLDB 3', 'parent': '53', 'meter': True}, '57': {'name': 'MLDB 4', 'parent': '53', 'meter': True}, '58': {'name': 'NP GODOWN LDB MAIN', 'parent': '53', 'meter': True}, '59': {'name': 'AUROSYS 2 DB', 'parent': '40', 'meter': True}, '60': {'name': 'CTP UPS DB', 'parent': '40', 'meter': True}, '61': {'name': 'CROMOMAN MSEB', 'parent': '3', 'meter': True}, '62': {'name': 'CROMOMAN DG', 'parent': 'dg_distribution', 'meter': True}, '63': {'name': 'CROMOMAN RELATED', 'parent': '61', 'meter': True}, '64': {'name': 'CROMOMAN MACHINE', 'parent': '61', 'meter': True}, '65': {'name': 'CROMOMAN HVAC', 'parent': '61', 'meter': True}, '66': {'name': 'RMD STAFF', 'parent': '46', 'meter': True}, '67': {'name': 'Colorman A APL', 'parent': '46', 'meter': True}, '68': {'name': 'Colorman B APL', 'parent': '46', 'meter': True}, '69': {'name': 'Solar PCC', 'parent': '5', 'meter': True}, '70': {'name': 'Solar NP Godown', 'parent': '49', 'meter': True}, '71': {'name': 'Cromoman UV', 'parent': '64', 'meter': True}, '72': {'name': 'Cromoman Spare', 'parent': '64', 'meter': True}, 'dm': {'name': 'DM / ETP / STP', 'parent': '5', 'meter': False}, 'dg': {'name': 'DG Panel — mapping pending', 'parent': None, 'meter': False}, 'dg_distribution': {'name': 'DG distribution — not additional generation', 'parent': 'dg', 'meter': False}, 'unmapped': {'name': 'Mapping review', 'parent': None, 'meter': False}}, 'notes': ['DG1/DG2/DG4 are candidate source meters. Electrical confirmation required before combining them.', 'PPT DG Power 6F does not match EMS EB POWER 6F (8). Left unresolved.', 'Solar readings are visible but excluded from HT + DG accounting until meter direction and boundary are established.', 'DM / ETP / STP has no standalone matching meter in this workbook. No inferred group total.', 'CTP UPS DB and AUROSYS 2 DB appear below UPS-2 in the diagram.', 'Duplicate SPARE labels mapped by EMS IDs 42 and 44 under Press-2.']}


def phase_name(value):
    return " ".join(str(value).strip().upper().split())


def phase_meter_values(current_long):
    """A usable total requires every hourly reading for every analyzed day."""
    data = current_long.copy()
    days = data["Analysis Date"].nunique()
    values = {}
    for serial, rows in data.groupby("Sr No", sort=False):
        serial = str(serial)
        numbers = pd.to_numeric(rows["Consumption"], errors="coerce")
        expected = PHASE_MAPPING["nodes"].get(serial)
        names = rows["Feeder Name"].map(phase_name).unique()
        mismatch = expected is not None and (len(names) != 1 or names[0] != phase_name(expected["name"]))
        good = np.isfinite(numbers) & numbers.ge(0)
        complete = (len(rows) == days * 24 and good.all()
                    and not rows.duplicated(["Analysis Date", "Hour"]).any()
                    and all(set(g["Hour"]) == set(ZONE_MAP) for _, g in rows.groupby("Analysis Date")))
        reason = "Name differs from mapping" if mismatch else ("Complete" if complete else "Incomplete / invalid readings")
        values[serial] = {"units":float(numbers.sum()) if complete and not mismatch else None,
                          "name":str(rows.iloc[0]["Feeder Name"]), "quality":reason,
                          "valid_hours":int(good.sum()), "expected_hours":days * 24}
    return values


def phase_source_totals(values):
    def total(ids):
        readings = [values.get(i, {}).get("units") for i in ids]
        return sum(readings) if readings and all(v is not None for v in readings) else None
    ht = total(["1", "2"])
    ids = PHASE_MAPPING["dg_source_ids"]
    # Only the three candidate source meters are supported after explicit confirmation.
    # Distribution meters must never enter this sum.
    configured = (PHASE_MAPPING["dg_mapping_confirmed"] and bool(ids)
                  and len(ids) == len(set(ids)) and set(ids).issubset({"15", "16", "17"}))
    dg = total(ids) if configured else None
    return {"ht":ht, "dg":dg, "ht_dg":ht + dg if ht is not None and dg is not None else None}


def phase_path(key):
    nodes = PHASE_MAPPING["nodes"]
    path, seen = [], set()
    while key in nodes and key not in seen:
        seen.add(key)
        path.append(nodes[key]["name"])
        key = nodes[key]["parent"]
    return " / ".join(reversed(path))


def phase_descendants(key):
    children = [k for k, n in PHASE_MAPPING["nodes"].items() if n["parent"] == key]
    result = [key]
    for child in children:
        result.extend(phase_descendants(child))
    return result


def phase_kwh(value):
    return "Pending" if value is None else f"{value:,.1f}"


def phase_card(label, value, note, featured=False):
    cls = "piq-source piq-featured" if featured else "piq-source"
    st.markdown(f'<div class="{cls}"><div class="piq-eyebrow">{html.escape(label)}</div>'
                f'<div class="piq-energy">{phase_kwh(value)}</div>'
                f'<div class="piq-unit">kWh</div><div class="piq-note">{html.escape(note)}</div></div>',
                unsafe_allow_html=True)


def phase_detail(key, values, current_long, zone_summary, statuses):
    nodes = PHASE_MAPPING["nodes"]
    node = nodes[key]
    st.caption(phase_path(key))
    if node["meter"]:
        value = values.get(key, {})
        st.metric(node["name"], (phase_kwh(value.get("units")) + " kWh") if value.get("units") is not None else "Unavailable")
        quality = value.get("quality", "Meter absent from selected files")
        if quality != "Complete":
            st.warning(quality + ". Consumption control status is withheld for this meter.")
        else:
            match = current_long[current_long["Sr No"].astype(str) == key]
            feeder_id = match.iloc[0]["Feeder ID"]
            zr = zone_summary[zone_summary["Feeder ID"] == feeder_id]
            status = statuses.get(feeder_id, "Baseline Pending")
            render_feeder_card(feeder_id, node["name"], zr, status, current_long)
            with st.expander("Hourly readings"):
                pivot = match.pivot(index="Hour", columns="Analysis Date", values="Consumption")
                pivot = pivot.reindex(list(ZONE_MAP))
                st.dataframe(pivot, use_container_width=True)
    else:
        st.info("Diagram group only. No standalone meter total is assigned to this group.")

    children = [k for k,n in nodes.items() if n["parent"] == key]
    if children:
        records = []
        for child in children:
            n = nodes[child]; v = values.get(child, {})
            records.append({"EMS ID": child if n["meter"] else "—", "Connected feeder": n["name"],
                            "kWh": v.get("units"),
                            "Reading": v.get("quality", "Meter absent") if n["meter"] else "Diagram group"})
        st.markdown("#### Directly connected feeders")
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        st.caption("Each row is its own meter reading. Parent and child readings are not added together.")


def render_phase_dashboard(current_long, zone_summary, feeder_status_df, calculated_days, baseline_days, baseline_active):
    st.markdown('''<style>
    .piq-source{background:#fff;border:1px solid #dce5ef;border-radius:18px;padding:24px 20px;
      min-height:204px;margin:8px 0 16px;box-shadow:0 6px 24px #102d5010;}
    .piq-eyebrow{font-size:12px;letter-spacing:1px;font-weight:700;text-transform:uppercase;color:#546a84;}
    .piq-energy{font-size:clamp(24px,3vw,38px);font-weight:800;letter-spacing:-1px;color:#102b4c;margin-top:12px;}
    .piq-unit{font-size:13px;color:#60758c;}.piq-note{font-size:12px;line-height:1.5;color:#60758c;margin-top:12px;}
    .piq-featured{background:linear-gradient(125deg,#10233f,#174a78);border:0;}
    .piq-featured .piq-energy{color:#fff;}.piq-featured .piq-eyebrow,.piq-featured .piq-unit,.piq-featured .piq-note{color:#cee1f4;}
    </style>''', unsafe_allow_html=True)
    values = phase_meter_values(current_long)
    totals = phase_source_totals(values)
    dates = sorted(current_long["Analysis Date"].astype(str).unique())
    st.caption(f"ANALYZED DATA: {dates[0]} to {dates[-1]} · {calculated_days} file(s) · Hourly sheet · 06:00–05:00")
    title = "Utility Performance"
    if len(dates) == 1:
        parsed_date = pd.to_datetime(dates[0], errors="coerce")
        if pd.notna(parsed_date):
            title += "- " + parsed_date.strftime("%d/%m/%Y")
    st.markdown("### " + title)
    cols = st.columns([1, 1, 1, 1.3])
    for col, key, label in zip(cols[:2], ["1", "2"], ["HT Incomer-1", "HT Incomer-2"]):
        with col:
            phase_card(label, values.get(key, {}).get("units"), "")
    with cols[2]:
        # Requested test-dashboard placeholder; not a verified DG measurement.
        # Keep unresolved DG out of the verified source calculation.
        displayed_dg = totals["dg"] if totals["dg"] is not None else 0.0
        phase_card("DG energy", displayed_dg, "")
    with cols[3]:
        if totals["ht_dg"] is not None:
            phase_card("HT + DG supply", totals["ht_dg"], "", True)
        else:
            phase_card("HT subtotal", totals["ht"], "", True)



def run_utility_performance_analyzer():
    add_utility_css()

    st.markdown("""
    <div class="utility-hero">
        <div class="utility-title">Utility Performance Analyzer</div>
        <div class="utility-subtitle">
            Plant Energy Overview · Phase 1.1 · Source meters and feeder hierarchy
        </div>
    </div>
    """, unsafe_allow_html=True)

    data_source = st.radio(
        "Select Data Source",
        ["Google Drive Folder", "Manual Upload"],
        horizontal=True,
    )

    if st.session_state.get("utility_source_p11") != data_source:
        st.session_state.utility_current_long_p11 = None
        st.session_state.utility_calculated_days_p11 = 0
        st.session_state.utility_found_files_p11 = []
        st.session_state.utility_missing_files_p11 = []
        st.session_state.utility_source_p11 = data_source

    current_long = None
    calculated_days = 0
    
    if "utility_current_long_p11" not in st.session_state:
        st.session_state.utility_current_long_p11 = None

    if "utility_calculated_days_p11" not in st.session_state:
        st.session_state.utility_calculated_days_p11 = 0

    if "utility_found_files_p11" not in st.session_state:
        st.session_state.utility_found_files_p11 = []

    if "utility_missing_files_p11" not in st.session_state:
        st.session_state.utility_missing_files_p11 = []

    # ---------------- GOOGLE DRIVE DATE RANGE MODE ----------------
    if data_source == "Google Drive Folder":
        st.markdown("### Analyze from Google Drive")

        col_start, col_end = st.columns(2)

        with col_start:
            start_date = st.date_input(
                "Start Date",
                value=date.today(),
                key="utility_start_date",
            )

        with col_end:
            end_date = st.date_input(
                "End Date",
                value=date.today(),
                key="utility_end_date",
            )

        if end_date < start_date:
            st.error("End Date cannot be before Start Date.")
            return

        st.markdown(
            '<div class="mode-note">'
            'For one-day analysis, select the same start and end date. '
            'For weekly or multi-day analysis, select a date range.'
            '</div>',
            unsafe_allow_html=True,
        )
            
        if st.button("Analyze Date Range"):
            st.session_state.utility_current_long_p11 = None
            st.session_state.utility_found_files_p11 = []
            st.session_state.utility_missing_files_p11 = []
            st.session_state.utility_calculated_days_p11 = 0
            try:
                folder_id = st.secrets["UTILITY_DRIVE_FOLDER_ID"]
            except Exception:
                st.error(
                    "UTILITY_DRIVE_FOLDER_ID is missing in Streamlit secrets. "
                    "Add it above [gcp_service_account] in secrets."
                )
                return

            selected_dates = get_date_list(start_date, end_date)

            all_day_data = []
            missing_files = []
            found_files = []

            with st.spinner("Searching and reading EMS files from Google Drive..."):
                for selected_day in selected_dates:
                    file_name = expected_ems_filename(selected_day)
                    try:
                        file_info = find_file_in_drive(folder_id, file_name)
                    except Exception as exc:
                        missing_files.append(f"{file_name} | lookup failed: {exc}")
                        continue

                    if file_info is None:
                        missing_files.append(file_name)
                        continue

                    try:
                        drive_file = download_drive_file(file_info["id"])

                        feeder_df, hour_cols = read_hourly_sheet(
                            drive_file,
                            sheet_name="Hourly",
                        )

                        day_long = long_format(feeder_df, hour_cols)
                        day_long["Analysis Date"] = selected_day.strftime("%Y-%m-%d")

                        all_day_data.append(day_long)
                        found_files.append(file_name)

                    except Exception as e:
                        missing_files.append(f"{file_name} | reading failed: {e}")

            if not all_day_data:
                st.error("No EMS files found/read for selected date range.")

                if missing_files:
                    st.warning("Missing or unread files: " + ", ".join(missing_files))

                return

            current_long = pd.concat(all_day_data, ignore_index=True)
            calculated_days = len(found_files)

            st.session_state.utility_current_long_p11 = current_long
            st.session_state.utility_calculated_days_p11 = calculated_days
            st.session_state.utility_found_files_p11 = found_files
            st.session_state.utility_missing_files_p11 = missing_files

            st.success(f"Files analyzed: {calculated_days} / {len(selected_dates)}")

            if missing_files:
                st.warning("Missing or unread files: " + ", ".join(missing_files))

        else:
            if st.session_state.utility_current_long_p11 is None:
                st.info("Select start date and end date, then click Analyze Date Range.")
                return

            current_long = st.session_state.utility_current_long_p11
            calculated_days = st.session_state.utility_calculated_days_p11

            if st.session_state.utility_found_files_p11:
                total_selected = calculated_days + len(st.session_state.utility_missing_files_p11)
                st.success(f"Files analyzed: {calculated_days} / {total_selected}")

            if st.session_state.utility_missing_files_p11:
                st.warning(
                    "Missing or unread files: "
                    + ", ".join(st.session_state.utility_missing_files_p11)
                )

    # ---------------- MANUAL UPLOAD BACKUP MODE ----------------
    else:
        current_file = st.file_uploader(
            "Upload EMS Daily Utility Performance File",
            type=["xls", "xlsx"],
            key="current_ems_file",
        )

        if current_file is None:
            st.info("Upload current EMS daily file to view feeder-wise zone control dashboard.")
            return

        try:
            feeder_df, hour_cols = read_hourly_sheet(
                current_file,
                sheet_name="Hourly",
            )

            current_long = long_format(feeder_df, hour_cols)
            current_long["Analysis Date"] = feeder_df.attrs.get("issue_date", "Manual Upload")
            calculated_days = 1

            st.session_state.utility_current_long_p11 = current_long
            st.session_state.utility_calculated_days_p11 = calculated_days
            st.session_state.utility_found_files_p11 = ["Manual Upload"]
            st.session_state.utility_missing_files_p11 = []

        except Exception as e:
            st.error(f"Current EMS file reading failed: {e}")
            return

    # ---------------- BASELINE LOADING ----------------
    baseline = None
    baseline_days = 0

    available_baseline_files = [str(file) for file in BASELINE_FILES if file.exists()]

    if available_baseline_files:
        with st.spinner("Loading seasonal baseline from app data..."):
            try:
                baseline, baseline_days = build_baseline(available_baseline_files)
            except Exception as exc:
                st.warning(f"Baseline could not be loaded: {exc}. Consumption view remains available.")
    else:
        st.warning("Seasonal baseline files not found in baseline_data folder.")

    # ---------------- FEEDER ZONE SUMMARY ----------------
    zone_summary = create_feeder_zone_summary(
        current_long,
        baseline,
        baseline_multiplier=calculated_days,
    )

    feeder_status_df = zone_summary.groupby(
        ["Feeder ID", "Feeder Name"],
        as_index=False,
    )["Zone Status"].agg(lambda x: final_feeder_status(x))

    feeder_status_df = feeder_status_df.rename(
        columns={"Zone Status": "Feeder Status"}
    )

    render_phase_dashboard(current_long, zone_summary, feeder_status_df, calculated_days,
                           baseline_days, baseline is not None)
