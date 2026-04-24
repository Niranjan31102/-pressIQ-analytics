import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(
    page_title="PressIQ Analytics",
    page_icon="🏭",
    layout="wide"
)

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #1f4e79;
}
.sub-title {
    font-size: 18px;
    color: #555;
}
.metric-card {
    background-color: #f5f7fa;
    padding: 18px;
    border-radius: 14px;
    border-left: 6px solid #1f4e79;
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.markdown('<div class="main-title">PressIQ Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI Powered Downtime Intelligence Platform</div>', unsafe_allow_html=True)

    st.write("")
    st.write("### Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            st.session_state.logged_in = True
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Please enter email and password")

    st.stop()

# ---------------- MAIN APP ----------------
st.sidebar.title("🏭 PressIQ Analytics")
st.sidebar.success("Logged in")

tool = st.sidebar.selectbox(
    "Select Analysis Tool",
    ["Downtime Analyzer"]
)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.markdown('<div class="main-title">PressIQ Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Downtime Analyzer Tool</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload downtime Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    st.success("File uploaded successfully")

    # Detect DT column
    if "Total Downtime" in df.columns:
        dt_col = "Total Downtime"
    elif "D.T." in df.columns:
        dt_col = "D.T."
    else:
        st.error("Downtime column not found. Expected 'Total Downtime' or 'D.T.'")
        st.stop()

    df["DT_min"] = pd.to_numeric(df[dt_col], errors="coerce")
    df = df[df["DT_min"].notna()].copy()

    for col in ["Reason", "Department", "Machine", "PRESS", "Main/Supplement"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    def dt_bucket(x):
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

    df["DT_Bucket"] = df["DT_min"].apply(dt_bucket)

    total_events = len(df)
    total_dt = df["DT_min"].sum()
    avg_dt = df["DT_min"].mean()

    st.write("## Executive Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Events", f"{total_events:,}")
    col2.metric("Total Downtime", f"{total_dt:,.0f} min")
    col3.metric("Average DT/Event", f"{avg_dt:.2f} min")

    st.write("---")

    # Bucket summary
    bucket_order = ["0-4", "5-15", "16-30", "31-45", "46-60", "60+"]
    bucket_summary = (
        df.groupby("DT_Bucket")["DT_min"]
        .agg(Events="count", Total_DT="sum", Avg_DT="mean")
        .reindex(bucket_order)
        .fillna(0)
        .reset_index()
    )
    bucket_summary["DT Share %"] = (bucket_summary["Total_DT"] / total_dt * 100).round(1)

    st.write("## Downtime Bucket Analysis")
    st.dataframe(bucket_summary, use_container_width=True)

    fig_bucket = px.bar(
        bucket_summary,
        x="DT_Bucket",
        y="Total_DT",
        text="Total_DT",
        title="Downtime by Duration Bucket"
    )
    st.plotly_chart(fig_bucket, use_container_width=True)

    # Department summary
    if "Department" in df.columns:
        dept_summary = (
            df.groupby("Department")["DT_min"]
            .agg(Events="count", Total_DT="sum", Avg_DT="mean")
            .sort_values("Total_DT", ascending=False)
            .reset_index()
        )
        dept_summary["DT Share %"] = (dept_summary["Total_DT"] / total_dt * 100).round(1)

        st.write("## Department-wise Downtime")
        st.dataframe(dept_summary, use_container_width=True)

        fig_dept = px.bar(
            dept_summary.head(10),
            x="Department",
            y="Total_DT",
            text="Total_DT",
            title="Top Departments by Downtime"
        )
        st.plotly_chart(fig_dept, use_container_width=True)

    # Reason summary
    if "Reason" in df.columns:
        reason_summary = (
            df.groupby("Reason")["DT_min"]
            .agg(Events="count", Total_DT="sum", Avg_DT="mean")
            .sort_values(["Total_DT", "Events"], ascending=False)
            .reset_index()
        )
        reason_summary["DT Share %"] = (reason_summary["Total_DT"] / total_dt * 100).round(1)

        st.write("## Top Downtime Reasons")
        st.dataframe(reason_summary.head(30), use_container_width=True)

        fig_reason = px.bar(
            reason_summary.head(15),
            x="Reason",
            y="Total_DT",
            text="Total_DT",
            title="Top 15 Downtime Reasons"
        )
        st.plotly_chart(fig_reason, use_container_width=True)

        repeated = reason_summary[reason_summary["Events"] >= 2]

        st.write("## Repeated Reasons")
        st.dataframe(repeated.head(30), use_container_width=True)

    # Machine / Press summary
    machine_col = None
    if "Machine" in df.columns:
        machine_col = "Machine"
    elif "PRESS" in df.columns:
        machine_col = "PRESS"

    if machine_col:
        machine_summary = (
            df.groupby(machine_col)["DT_min"]
            .agg(Events="count", Total_DT="sum", Avg_DT="mean")
            .sort_values("Total_DT", ascending=False)
            .reset_index()
        )
        machine_summary["DT Share %"] = (machine_summary["Total_DT"] / total_dt * 100).round(1)

        st.write("## Press / Machine-wise Downtime")
        st.dataframe(machine_summary, use_container_width=True)

        fig_machine = px.bar(
            machine_summary,
            x=machine_col,
            y="Total_DT",
            text="Total_DT",
            title="Downtime by Press / Machine"
        )
        st.plotly_chart(fig_machine, use_container_width=True)

    # Main vs Supplement
    if "Main/Supplement" in df.columns:
        ms_summary = (
            df.groupby("Main/Supplement")["DT_min"]
            .agg(Events="count", Total_DT="sum", Avg_DT="mean")
            .sort_values("Total_DT", ascending=False)
            .reset_index()
        )
        ms_summary["DT Share %"] = (ms_summary["Total_DT"] / total_dt * 100).round(1)

        st.write("## Main vs Supplement")
        st.dataframe(ms_summary, use_container_width=True)

        fig_ms = px.bar(
            ms_summary,
            x="Main/Supplement",
            y="Total_DT",
            text="Total_DT",
            title="Main vs Supplement Downtime"
        )
        st.plotly_chart(fig_ms, use_container_width=True)

    # AI Summary
    st.write("## PressIQ AI Management Summary")

    top_bucket = bucket_summary.sort_values("Total_DT", ascending=False).iloc[0]
    summary_lines = []

    summary_lines.append(
        f"The highest downtime bucket is **{top_bucket['DT_Bucket']}**, contributing **{top_bucket['Total_DT']:.0f} minutes**."
    )

    if "Department" in df.columns:
        top_dept = dept_summary.iloc[0]
        summary_lines.append(
            f"The highest loss department is **{top_dept['Department']}** with **{top_dept['Total_DT']:.0f} minutes**."
        )

    if "Reason" in df.columns:
        top_reason = reason_summary.iloc[0]
        summary_lines.append(
            f"The top downtime reason is **{top_reason['Reason']}**, causing **{top_reason['Total_DT']:.0f} minutes** across **{top_reason['Events']} events**."
        )

    if machine_col:
        top_machine = machine_summary.iloc[0]
        summary_lines.append(
            f"The highest downtime machine/press is **{top_machine[machine_col]}** with **{top_machine['Total_DT']:.0f} minutes**."
        )

    for line in summary_lines:
        st.markdown("- " + line)

    st.write("### Recommended Actions")
    st.markdown("""
1. Attack top 5 repeated downtime reasons first.  
2. Assign department-wise ownership for high-loss areas.  
3. Review worst press/machine daily.  
4. Reduce recovery time in the largest DT bucket.  
5. Track repeat issues until closure, not just reporting.
    """)

    # Excel download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        bucket_summary.to_excel(writer, index=False, sheet_name="Bucket Summary")

        if "Department" in df.columns:
            dept_summary.to_excel(writer, index=False, sheet_name="Department Summary")

        if "Reason" in df.columns:
            reason_summary.to_excel(writer, index=False, sheet_name="Reason Summary")
            repeated.to_excel(writer, index=False, sheet_name="Repeated Reasons")

        if machine_col:
            machine_summary.to_excel(writer, index=False, sheet_name="Machine Summary")

        if "Main/Supplement" in df.columns:
            ms_summary.to_excel(writer, index=False, sheet_name="Main vs Supplement")

    st.download_button(
        label="Download Excel Report",
        data=output.getvalue(),
        file_name="PressIQ_Downtime_Analyzer_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload an Excel file to start analysis.")
