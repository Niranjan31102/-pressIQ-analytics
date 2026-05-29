import streamlit as st
import pandas as pd
import numpy as np
import html
from pathlib import Path
BASELINE_DIR = Path("baseline_data")

BASELINE_FILES = [
    BASELINE_DIR / "APR26_Utility_performance.xlsx",
    BASELINE_DIR / "MAY26_Utility_performance.xlsx",
]


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
        font-size: 13px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: .04em;
    }
    .kpi-value {
        font-size: 30px;
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
    @media (max-width: 900px) {
        .zone-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    </style>
    """, unsafe_allow_html=True)


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


def read_hourly_sheet(uploaded_file, sheet_name="Hourly"):
    uploaded_file.seek(0)
    xls = pd.ExcelFile(uploaded_file)

    if sheet_name not in xls.sheet_names:
        raise ValueError(f"'{sheet_name}' sheet not found.")

    uploaded_file.seek(0)
    raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)

    header_row = 2
    headers = raw_df.iloc[header_row].tolist()

    df = raw_df.iloc[header_row + 1:].copy()
    df.columns = headers
    df = df.dropna(how="all")

    df = df.rename(columns={
        df.columns[0]: "Sr No",
        df.columns[1]: "Feeder Name"
    })

    df = df[pd.notna(df["Feeder Name"])].copy()
    df = df.head(72)

    df["Sr No"] = df["Sr No"].astype(str).str.replace(".0", "", regex=False)
    df["Feeder Name"] = df["Feeder Name"].astype(str).str.strip()
    df["Feeder ID"] = df["Sr No"] + " - " + df["Feeder Name"]

    hour_source_cols = df.columns[2:-1]
    clean_map = {col: normalize_hour(col) for col in hour_source_cols}
    df = df.rename(columns=clean_map)

    hour_cols = [h for h in clean_map.values() if h in ZONE_MAP]

    for col in hour_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, hour_cols


def read_baseline_workbook(uploaded_file):
    uploaded_file.seek(0)
    xls = pd.ExcelFile(uploaded_file)
    all_days = []

    for sheet in xls.sheet_names:
        uploaded_file.seek(0)
        raw_df = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)

        if raw_df.shape[0] < 5:
            continue

        headers = raw_df.iloc[2].tolist()
        df = raw_df.iloc[3:].copy()
        df.columns = headers
        df = df.dropna(how="all")

        df = df.rename(columns={
            df.columns[0]: "Sr No",
            df.columns[1]: "Feeder Name"
        })

        df = df[pd.notna(df["Feeder Name"])].copy()
        df = df.head(72)

        df["Sr No"] = df["Sr No"].astype(str).str.replace(".0", "", regex=False)
        df["Feeder Name"] = df["Feeder Name"].astype(str).str.strip()
        df["Feeder ID"] = df["Sr No"] + " - " + df["Feeder Name"]
        df["Baseline Day"] = str(sheet)

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
            value_name="Consumption"
        )

        all_days.append(long_df)

    if not all_days:
        return pd.DataFrame()

    baseline_long = pd.concat(all_days, ignore_index=True)
    baseline_long["Zone"] = baseline_long["Hour"].map(ZONE_MAP)

    return baseline_long


def long_format(df, hour_cols):
    long_df = df.melt(
        id_vars=["Sr No", "Feeder Name", "Feeder ID"],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Consumption"
    )
    long_df["Zone"] = long_df["Hour"].map(ZONE_MAP)
    long_df["Consumption"] = pd.to_numeric(long_df["Consumption"], errors="coerce")
    return long_df


def clean_consumption_data(long_df):
    df = long_df.copy()

    df["Quality Status"] = "Valid"
    df["Clean Consumption"] = df["Consumption"]

    # Negative values are treated as EMS / meter data issue.
    # Positive high/low values are NOT treated as data error because production timing changes daily.
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
        issue_text.append(
            f"{row['Hour']} value {row['Consumption']:,.1f}"
        )

    return (
        "Negative consumption found: "
        + "; ".join(issue_text)
        + ". This may be EMS/meter data error. Kindly check source reading."
    )
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
        as_index=False
    )["Clean Consumption"].sum()

    baseline = daily_zone.groupby(
        ["Feeder ID", "Feeder Name", "Zone"],
        as_index=False
    )["Clean Consumption"].agg(
        baseline_median="median",
        baseline_mean="mean",
        baseline_p75=lambda x: x.quantile(0.75),
        baseline_p90=lambda x: x.quantile(0.90)
    )

    day_count = baseline_long["Baseline Day"].nunique()

    return baseline, day_count


def create_feeder_zone_summary(current_long, baseline):
    current_clean = clean_consumption_data(current_long)

    zone_summary = current_clean.groupby(
        ["Feeder ID", "Feeder Name", "Zone"],
        as_index=False
    ).agg(
        current_units=("Clean Consumption", "sum"),
        issue_count=("Quality Status", lambda x: (x != "Valid").sum())
    )

    if baseline is not None:
        zone_summary = zone_summary.merge(
            baseline,
            on=["Feeder ID", "Feeder Name", "Zone"],
            how="left"
        )
    else:
        zone_summary["baseline_median"] = np.nan
        zone_summary["baseline_mean"] = np.nan
        zone_summary["baseline_p75"] = np.nan
        zone_summary["baseline_p90"] = np.nan

    def zone_status(row):
        if row["issue_count"] > 0:
            return "Data Error Suspect"

        if pd.isna(row["baseline_median"]):
            return "Baseline Pending"

        if row["current_units"] > row["baseline_p90"]:
            return "Out Control"

        if row["current_units"] > row["baseline_p75"]:
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
    if all(s == "Baseline Pending" for s in statuses):
        return "Baseline Pending"

    return "In Control"


def status_class(status):
    if status == "In Control":
        return "status-in"
    if status == "Warning":
        return "status-warning"
    if status == "Out Control":
        return "status-out"
    if status == "Data Error Suspect":
        return "status-data"
    return "status-pending"


def format_units(value):
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}"


def create_remark(feeder_id, feeder_name, feeder_status, zone_rows, current_long):
    if feeder_status == "Baseline Pending":
        return "Baseline not uploaded yet. Upload April/May baseline files to activate control prediction."

    if feeder_status == "Data Error Suspect":
        return create_data_error_remark(feeder_id, current_long)

    out_zones = zone_rows[zone_rows["Zone Status"] == "Out Control"]["Zone"].tolist()
    warn_zones = zone_rows[zone_rows["Zone Status"] == "Warning"]["Zone"].tolist()

    if out_zones:
        zone_text = ", ".join([z.split("|")[0].strip() for z in out_zones])
        return f"Consumption is out of seasonal control in {zone_text}. Review this feeder for abnormal running, idle load, or production/load variation."

    if warn_zones:
        zone_text = ", ".join([z.split("|")[0].strip() for z in warn_zones])
        return f"Consumption is above normal range in {zone_text}. Keep under watch and compare with production activity."

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
    
def run_utility_performance_analyzer():
    add_utility_css()

    st.markdown("""
    <div class="utility-hero">
        <div class="utility-title">Utility Performance Analyzer</div>
        <div class="utility-subtitle">
            Feeder-wise Zone Control Dashboard | EMS Daily Utility Performance Analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

    current_file = st.file_uploader(
        "Upload EMS Daily Utility Performance File",
        type=["xls", "xlsx"],
        key="current_ems_file"
    )

    if current_file is None:
        st.info("Upload current EMS daily file to view feeder-wise zone control dashboard.")
        return

    try:
        feeder_df, hour_cols = read_hourly_sheet(current_file, sheet_name="Hourly")
        current_long = long_format(feeder_df, hour_cols)
    except Exception as e:
        st.error(f"Current EMS file reading failed: {e}")
        return

    baseline = None
    baseline_days = 0

    available_baseline_files = [str(file) for file in BASELINE_FILES if file.exists()]

    if available_baseline_files:
        with st.spinner("Loading seasonal baseline from app data..."):
            baseline, baseline_days = build_baseline(available_baseline_files)
    else:
        st.warning("Seasonal baseline files not found in baseline_data folder.")

    feeder_status_df = zone_summary.groupby(
        ["Feeder ID", "Feeder Name"],
        as_index=False
    )["Zone Status"].agg(lambda x: final_feeder_status(x))

    feeder_status_df = feeder_status_df.rename(columns={"Zone Status": "Feeder Status"})

    total_units = zone_summary["current_units"].sum()
    total_feeders = feeder_status_df["Feeder ID"].nunique()
    in_control = (feeder_status_df["Feeder Status"] == "In Control").sum()
    warning = (feeder_status_df["Feeder Status"] == "Warning").sum()
    out_control = (feeder_status_df["Feeder Status"] == "Out Control").sum()
    data_error = (feeder_status_df["Feeder Status"] == "Data Error Suspect").sum()

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Feeders</div>
        <div class="kpi-value">{total_feeders}</div>
    </div>
    """, unsafe_allow_html=True)

    k2.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Recorded Units</div>
        <div class="kpi-value">{total_units:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

    k3.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">In Control</div>
        <div class="kpi-value">{in_control}</div>
    </div>
    """, unsafe_allow_html=True)

    k4.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Warning</div>
        <div class="kpi-value">{warning}</div>
    </div>
    """, unsafe_allow_html=True)

    k5.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Out / Error</div>
        <div class="kpi-value">{out_control + data_error}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    if baseline is None:
        st.warning("Baseline not active. Please check baseline_data folder in GitHub.")
    else:
        st.success(f"Seasonal baseline active automatically: April–May 2026 | {baseline_days} historical days.")

    st.caption(
        "Note: Recorded Units means sum of all 72 feeder readings. "
        "It is shown for visibility, not as final plant net consumption."
    )

    st.markdown("### Feeder-wise Zone Control")

    f1, f2 = st.columns([1, 1])

    with f1:
        selected_status = st.selectbox(
            "Filter by status",
            ["All", "In Control", "Warning", "Out Control", "Data Error Suspect", "Baseline Pending"]
        )

    with f2:
        search_text = st.text_input("Search feeder", "")

    display_df = feeder_status_df.copy()

    if selected_status != "All":
        display_df = display_df[display_df["Feeder Status"] == selected_status]

    if search_text.strip():
        display_df = display_df[
            display_df["Feeder Name"].str.contains(search_text, case=False, na=False) |
            display_df["Feeder ID"].str.contains(search_text, case=False, na=False)
        ]

    status_rank = {
        "Data Error Suspect": 1,
        "Out Control": 2,
        "Warning": 3,
        "In Control": 4,
        "Baseline Pending": 5,
    }

    display_df["rank"] = display_df["Feeder Status"].map(status_rank).fillna(9)
    display_df = display_df.sort_values(["rank", "Feeder ID"])

    if display_df.empty:
        st.info("No feeder found for selected filter.")
        return

    for _, feeder in display_df.iterrows():
        feeder_id = feeder["Feeder ID"]
        feeder_name = feeder["Feeder Name"]
        feeder_status = feeder["Feeder Status"]

        zone_rows = zone_summary[zone_summary["Feeder ID"] == feeder_id].copy()

        render_feeder_card(
            feeder_id=feeder_id,
            feeder_name=feeder_name,
            zone_rows=zone_rows,
            feeder_status=feeder_status,
            current_long=current_long
        )
