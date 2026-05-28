import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


ZONE_MAP = {
    "06:00": "Zone 1 | 06:00-08:00 | Low Load",
    "07:00": "Zone 1 | 06:00-08:00 | Low Load",
    "08:00": "Zone 1 | 06:00-08:00 | Low Load",

    "09:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "10:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "11:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "12:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "13:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "14:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "15:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",
    "16:00": "Zone 2 | 09:00-16:00 | Maintenance + Office",

    "17:00": "Zone 3 | 17:00-23:00 | Supplement Printing",
    "18:00": "Zone 3 | 17:00-23:00 | Supplement Printing",
    "19:00": "Zone 3 | 17:00-23:00 | Supplement Printing",
    "20:00": "Zone 3 | 17:00-23:00 | Supplement Printing",
    "21:00": "Zone 3 | 17:00-23:00 | Supplement Printing",
    "22:00": "Zone 3 | 17:00-23:00 | Supplement Printing",
    "23:00": "Zone 3 | 17:00-23:00 | Supplement Printing",

    "00:00": "Zone 4 | 00:00-05:00 | Main Book Printing",
    "01:00": "Zone 4 | 00:00-05:00 | Main Book Printing",
    "02:00": "Zone 4 | 00:00-05:00 | Main Book Printing",
    "03:00": "Zone 4 | 00:00-05:00 | Main Book Printing",
    "04:00": "Zone 4 | 00:00-05:00 | Main Book Printing",
    "05:00": "Zone 4 | 00:00-05:00 | Main Book Printing",
}


def normalize_hour(col):
    """
    Converts EMS hourly column names into HH:00 format.
    Handles datetime, timestamp, and text style headers.
    """
    try:
        dt = pd.to_datetime(col)
        return dt.strftime("%H:00")
    except Exception:
        pass

    text = str(col).strip()

    if ":" in text:
        try:
            return pd.to_datetime(text).strftime("%H:00")
        except Exception:
            return text

    return text


def read_hourly_sheet(uploaded_file):
    """
    Reads EMS Hourly sheet.
    Expected structure:
    Row 1: title
    Row 2: date
    Row 3: headers
    Row 4 onward: feeder data
    """
    xls = pd.ExcelFile(uploaded_file)

    if "Hourly" not in xls.sheet_names:
        st.error("Hourly sheet not found in uploaded EMS file.")
        st.stop()

    raw_df = pd.read_excel(uploaded_file, sheet_name="Hourly", header=None)

    # Header row is row index 2 based on studied EMS file
    header_row = 2
    headers = raw_df.iloc[header_row].tolist()

    df = raw_df.iloc[header_row + 1:].copy()
    df.columns = headers

    # Remove completely blank rows
    df = df.dropna(how="all")

    # First two columns are Sr No and Feeder Name
    df = df.rename(columns={
        df.columns[0]: "Sr No",
        df.columns[1]: "Feeder Name"
    })

    df = df[pd.notna(df["Feeder Name"])].copy()

    # Keep only 72 feeder rows if extra rows exist
    df = df.head(72)

    # Create feeder identity because SPARE is repeated
    df["Sr No"] = df["Sr No"].astype(str).str.replace(".0", "", regex=False)
    df["Feeder ID"] = df["Sr No"] + " - " + df["Feeder Name"].astype(str)

    hour_cols = df.columns[2:-1]

    clean_hour_map = {}
    for col in hour_cols:
        clean_hour_map[col] = normalize_hour(col)

    df = df.rename(columns=clean_hour_map)

    hour_cols_clean = list(clean_hour_map.values())

    # Convert hourly values to numeric
    for col in hour_cols_clean:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, hour_cols_clean


def create_long_data(df, hour_cols):
    long_df = df.melt(
        id_vars=["Sr No", "Feeder Name", "Feeder ID"],
        value_vars=hour_cols,
        var_name="Hour",
        value_name="Consumption"
    )

    long_df["Consumption"] = pd.to_numeric(long_df["Consumption"], errors="coerce")
    long_df["Zone"] = long_df["Hour"].map(ZONE_MAP)

    return long_df


def classify_data_quality(long_df):
    """
    First version data quality logic:
    - Negative values are invalid and excluded.
    - Very high positive spikes are only flagged if extremely unusual inside same feeder.
    """
    df = long_df.copy()

    df["Quality Status"] = "Valid"
    df["Clean Consumption"] = df["Consumption"]

    # Negative values
    negative_mask = df["Consumption"] < 0
    df.loc[negative_mask, "Quality Status"] = "Invalid Negative"
    df.loc[negative_mask, "Clean Consumption"] = np.nan

    # Positive spike detection feeder-wise
    valid_positive = df[df["Consumption"] >= 0].copy()

    feeder_stats = valid_positive.groupby("Feeder ID")["Consumption"].agg(
        feeder_median="median",
        feeder_p95=lambda x: x.quantile(0.95)
    ).reset_index()

    df = df.merge(feeder_stats, on="Feeder ID", how="left")

    suspect_mask = (
        (df["Consumption"] > 100) &
        (df["feeder_median"] > 0) &
        (
            (df["Consumption"] > df["feeder_median"] * 8) |
            (df["Consumption"] > df["feeder_p95"] * 2)
        )
    )

    df.loc[suspect_mask, "Quality Status"] = "Data Quality Suspect"
    df.loc[suspect_mask, "Clean Consumption"] = np.nan

    return df


def run_utility_performance_analyzer():
    st.header("Utility Performance Analyzer")
    st.caption("EMS Daily Utility Performance File Analysis")

    uploaded_file = st.file_uploader(
        "Upload EMS Daily Utility Performance File",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is None:
        st.info("Upload EMS daily utility file to start analysis.")
        return

    try:
        feeder_df, hour_cols = read_hourly_sheet(uploaded_file)
        long_df = create_long_data(feeder_df, hour_cols)
        analyzed_df = classify_data_quality(long_df)

    except Exception as e:
        st.error(f"File reading failed: {e}")
        return

    valid_df = analyzed_df[analyzed_df["Quality Status"] == "Valid"].copy()

    st.success("File uploaded and hourly feeder data processed successfully.")

    # ---------------- KPI SUMMARY ----------------
    total_feeders = feeder_df["Feeder ID"].nunique()
    total_recorded_units = valid_df["Clean Consumption"].sum()
    negative_count = (analyzed_df["Quality Status"] == "Invalid Negative").sum()
    suspect_count = (analyzed_df["Quality Status"] == "Data Quality Suspect").sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Feeders", total_feeders)
    col2.metric("Total Recorded Feeder Units", f"{total_recorded_units:,.1f}")
    col3.metric("Negative Values Ignored", negative_count)
    col4.metric("Suspect Spikes Ignored", suspect_count)

    st.info(
        "Note: Total Recorded Feeder Units is the sum of all 72 feeder readings. "
        "It is not treated as final plant total because parent and child feeders may overlap."
    )

    # ---------------- DATA QUALITY ALERTS ----------------
    st.subheader("Data Quality Alerts")

    dq_alerts = analyzed_df[analyzed_df["Quality Status"] != "Valid"][
        ["Feeder ID", "Feeder Name", "Hour", "Zone", "Consumption", "Quality Status"]
    ].copy()

    if dq_alerts.empty:
        st.success("No negative values or suspect positive spikes found.")
    else:
        st.warning("Some values are ignored from analysis because they look like EMS/data quality issues.")
        st.dataframe(dq_alerts, use_container_width=True, hide_index=True)

    # ---------------- ZONE SUMMARY ----------------
    st.subheader("Zone-wise Consumption Summary")

    zone_summary = valid_df.groupby("Zone", as_index=False)["Clean Consumption"].sum()
    zone_summary = zone_summary.rename(columns={"Clean Consumption": "Units"})
    zone_summary["Share %"] = zone_summary["Units"] / zone_summary["Units"].sum() * 100

    st.dataframe(
        zone_summary.sort_values("Zone"),
        use_container_width=True,
        hide_index=True
    )

    fig_zone = px.bar(
        zone_summary,
        x="Zone",
        y="Units",
        text="Units",
        title="Zone-wise Recorded Feeder Consumption"
    )
    fig_zone.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    st.plotly_chart(fig_zone, use_container_width=True)

    # ---------------- HOURLY TREND ----------------
    st.subheader("Hourly Consumption Pattern")

    hourly_summary = valid_df.groupby("Hour", as_index=False)["Clean Consumption"].sum()
    hourly_summary = hourly_summary.rename(columns={"Clean Consumption": "Units"})

    fig_hour = px.line(
        hourly_summary,
        x="Hour",
        y="Units",
        markers=True,
        title="Hourly Recorded Feeder Consumption Trend"
    )
    st.plotly_chart(fig_hour, use_container_width=True)

    # ---------------- TOP FEEDERS ----------------
    st.subheader("Top Consuming Feeders")

    feeder_summary = valid_df.groupby(
        ["Feeder ID", "Feeder Name"],
        as_index=False
    )["Clean Consumption"].sum()

    feeder_summary = feeder_summary.rename(columns={"Clean Consumption": "Units"})
    feeder_summary = feeder_summary.sort_values("Units", ascending=False)

    st.dataframe(feeder_summary, use_container_width=True, hide_index=True)

    top10 = feeder_summary.head(10)

    fig_top = px.bar(
        top10,
        x="Units",
        y="Feeder ID",
        orientation="h",
        text="Units",
        title="Top 10 Feeders by Recorded Consumption"
    )
    fig_top.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_top, use_container_width=True)

    # ---------------- HEATMAP ----------------
    st.subheader("Feeder × Hour Heatmap")

    heatmap_data = valid_df.pivot_table(
        index="Feeder ID",
        columns="Hour",
        values="Clean Consumption",
        aggfunc="sum"
    ).fillna(0)

    fig_heatmap = px.imshow(
        heatmap_data,
        aspect="auto",
        title="Hourly Consumption Heatmap - All 72 Feeders"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # ---------------- FEEDER ZONE HEATMAP ----------------
    st.subheader("Feeder × Zone Heatmap")

    zone_heatmap_data = valid_df.pivot_table(
        index="Feeder ID",
        columns="Zone",
        values="Clean Consumption",
        aggfunc="sum"
    ).fillna(0)

    fig_zone_heatmap = px.imshow(
        zone_heatmap_data,
        aspect="auto",
        title="Zone-wise Consumption Heatmap - All 72 Feeders"
    )
    st.plotly_chart(fig_zone_heatmap, use_container_width=True)

    # ---------------- INTERPRETATION ----------------
    st.subheader("Production-aware Interpretation")

    st.markdown("""
    - **Zone 1** is low/no production period. High consumption here needs review for idle load, AC, compressor, pump, lighting, or machines left ON.
    - **Zone 2** is maintenance and office activity period. Consumption should be compared with maintenance baseline.
    - **Zone 3** is supplement printing period. Higher load is expected due to printing activity.
    - **Zone 4** is main book/newspaper printing period. Highest load is expected here, so it should be judged against Zone 4 baseline, not simply marked abnormal.
    """)
