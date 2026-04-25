import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(
    page_title="PressIQ Analytics",
    page_icon="🏭",
    layout="wide"
)

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #1f4e79;
}
.sub-title {
    font-size: 20px;
    color: #555;
    margin-bottom: 20px;
}
.info-box {
    background-color: #f5f7fa;
    padding: 18px;
    border-radius: 14px;
    border-left: 6px solid #1f4e79;
    margin-bottom: 15px;
}
.warning-box {
    background-color: #fff7ed;
    padding: 18px;
    border-radius: 14px;
    border-left: 6px solid #f97316;
    margin-bottom: 15px;
}
.success-box {
    background-color: #f0fdf4;
    padding: 18px;
    border-radius: 14px;
    border-left: 6px solid #16a34a;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🏭 PressIQ Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI Powered Plant Performance Intelligence Platform</div>', unsafe_allow_html=True)

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

    st.info("Note: This is temporary demo login. Real signup/authentication will be added later.")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("🏭 PressIQ Analytics")
st.sidebar.success("Logged in")

st.sidebar.markdown("## 📊 Downtime Intelligence")

dt_module = st.sidebar.radio(
    "Select Downtime Tool",
    [
        "Overall Downtime Analyzer",
        "0–4 Min Micro Stoppage Analyzer",
        "Web Break Downtime Analyzer",
        "Main vs Supplement DT Analyzer",
        "Press Health / Repeated Reason Analyzer"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("## ♻️ Waste Intelligence")

waste_module = st.sidebar.radio(
    "Select Waste Tool",
    [
        "ADAM Production Report Analyzer",
        "Pan India Waste Tracker Analyzer"
    ]
)

st.sidebar.markdown("---")

module_group = st.sidebar.selectbox(
    "Active Intelligence Area",
    [
        "Downtime Intelligence",
        "Waste Intelligence"
    ]
)

if module_group == "Downtime Intelligence":
    selected_module = dt_module
else:
    selected_module = waste_module

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ---------------- HEADER ----------------
st.markdown('<div class="main-title">PressIQ Analytics</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{selected_module}</div>', unsafe_allow_html=True)


# ---------------- COMMON FUNCTIONS ----------------
def detect_dt_column(df):
    if "Total Downtime" in df.columns:
        return "Total Downtime"
    elif "D.T." in df.columns:
        return "D.T."
    else:
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
        "Reason",
        "Department",
        "Related",
        "Machine",
        "PRESS",
        "Main/Supplement",
        "Edition",
        "GNP/SNP",
        "Folder"
    ]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def ask_pressiq_ai_box(context_name):
    st.write("---")
    st.write("## 🤖 Ask PressIQ AI")
    st.caption(f"Ask questions based on this uploaded {context_name}. No need to upload again.")

    suggested = st.columns(4)

    with suggested[0]:
        if st.button("Top 5 Issues"):
            st.session_state.ai_question = "What are the top 5 issues?"
    with suggested[1]:
        if st.button("Action Plan"):
            st.session_state.ai_question = "Give me an action plan."
    with suggested[2]:
        if st.button("Worst Area"):
            st.session_state.ai_question = "Which area is worst and why?"
    with suggested[3]:
        if st.button("Saving Scope"):
            st.session_state.ai_question = "What is the saving opportunity?"

    question = st.text_input(
        "Type your question",
        value=st.session_state.get("ai_question", "")
    )

    if st.button("Ask PressIQ AI"):
        if question:
            st.info(
                "AI chat engine will be connected in the next phase. "
                "For now, this box is ready for module-wise AI questions."
            )
        else:
            st.warning("Please type a question.")


# ---------------- MODULE 1: OVERALL DOWNTIME ANALYZER ----------------
if selected_module == "Overall Downtime Analyzer":

    uploaded_file = st.file_uploader("Upload downtime Excel file", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df = clean_common_columns(df)

        st.success("File uploaded successfully")

        dt_col = detect_dt_column(df)

        if dt_col is None:
            st.error("Downtime column not found. Expected 'Total Downtime' or 'D.T.'")
            st.stop()

        df["DT_min"] = pd.to_numeric(df[dt_col], errors="coerce")
        df = df[df["DT_min"].notna()].copy()
        df["DT_Bucket"] = df["DT_min"].apply(create_dt_bucket)

        total_events = len(df)
        total_dt = df["DT_min"].sum()
        avg_dt = df["DT_min"].mean()

        if df["DT_min"].max() <= 4:
            st.markdown(
                """
                <div class="warning-box">
                ⚠️ This uploaded file contains only 0–4 minute downtime events.
                Overall downtime analysis may be limited. For full DT performance, upload complete downtime data.
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("## Executive Dashboard")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events", f"{total_events:,}")
        col2.metric("Total Downtime", f"{total_dt:,.0f} min")
        col3.metric("Average DT/Event", f"{avg_dt:.2f} min")

        st.write("---")

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

        dept_summary = None
        reason_summary = None
        machine_summary = None
        ms_summary = None
        repeated = None
        machine_col = None

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
            fig_reason.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_reason, use_container_width=True)

            repeated = reason_summary[reason_summary["Events"] >= 2]

            st.write("## Repeated Reasons")
            st.dataframe(repeated.head(30), use_container_width=True)

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

        st.write("## 🚨 Key Insights")

        top_bucket = bucket_summary.sort_values("Total_DT", ascending=False).iloc[0]

        st.markdown(
            f"""
            <div class="info-box">
            <b>Biggest DT bucket:</b> {top_bucket['DT_Bucket']} with {top_bucket['Total_DT']:.0f} minutes.
            </div>
            """,
            unsafe_allow_html=True
        )

        if dept_summary is not None and len(dept_summary) > 0:
            top_dept = dept_summary.iloc[0]
            st.markdown(
                f"""
                <div class="info-box">
                <b>Highest loss department:</b> {top_dept['Department']} with {top_dept['Total_DT']:.0f} minutes.
                </div>
                """,
                unsafe_allow_html=True
            )

        if reason_summary is not None and len(reason_summary) > 0:
            top_reason = reason_summary.iloc[0]
            st.markdown(
                f"""
                <div class="info-box">
                <b>Top downtime reason:</b> {top_reason['Reason']} caused {top_reason['Total_DT']:.0f} minutes across {int(top_reason['Events'])} events.
                </div>
                """,
                unsafe_allow_html=True
            )

        if machine_summary is not None and len(machine_summary) > 0:
            top_machine = machine_summary.iloc[0]
            st.markdown(
                f"""
                <div class="info-box">
                <b>Worst press/machine:</b> {top_machine[machine_col]} with {top_machine['Total_DT']:.0f} minutes.
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write("## PressIQ AI Management Summary")

        st.markdown("""
        ### Recommended Actions
        1. Focus first on the highest DT bucket and repeated reasons.
        2. Assign department-wise owners for top loss areas.
        3. Review worst press/machine daily.
        4. Convert repeated medium-duration stoppages into controlled short stops.
        5. Track repeat issues until closure, not only reporting.
        """)

        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            bucket_summary.to_excel(writer, index=False, sheet_name="Bucket Summary")

            if dept_summary is not None:
                dept_summary.to_excel(writer, index=False, sheet_name="Department Summary")

            if reason_summary is not None:
                reason_summary.to_excel(writer, index=False, sheet_name="Reason Summary")
                repeated.to_excel(writer, index=False, sheet_name="Repeated Reasons")

            if machine_summary is not None:
                machine_summary.to_excel(writer, index=False, sheet_name="Machine Summary")

            if ms_summary is not None:
                ms_summary.to_excel(writer, index=False, sheet_name="Main vs Supplement")

        st.download_button(
            label="📥 Download Excel Report",
            data=output.getvalue(),
            file_name="PressIQ_Downtime_Analyzer_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        ask_pressiq_ai_box("downtime file")

    else:
        st.info("Upload an Excel file to start Overall Downtime Analysis.")


# ---------------- MODULE 2: 0-4 MIN MICRO STOPPAGE ANALYZER ----------------
elif selected_module == "0–4 Min Micro Stoppage Analyzer":

    uploaded_file = st.file_uploader("Upload 0–4 min downtime Excel file", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df = clean_common_columns(df)

        dt_col = detect_dt_column(df)

        if dt_col is None:
            st.error("Downtime column not found. Expected 'Total Downtime' or 'D.T.'")
            st.stop()

        df["DT_min"] = pd.to_numeric(df[dt_col], errors="coerce")
        df = df[df["DT_min"].notna()].copy()

        micro_df = df[df["DT_min"] <= 4].copy()

        st.success("0–4 min file uploaded successfully")

        total_events = len(micro_df)
        total_dt = micro_df["DT_min"].sum()
        avg_dt = micro_df["DT_min"].mean()

        st.write("## 0–4 Min Micro Stoppage Dashboard")

        col1, col2, col3 = st.columns(3)
        col1.metric("Micro Events", f"{total_events:,}")
        col2.metric("Micro DT", f"{total_dt:,.0f} min")
        col3.metric("Avg Micro DT/Event", f"{avg_dt:.2f} min" if total_events else "0")

        if len(micro_df) == 0:
            st.warning("No 0–4 min downtime events found.")
            st.stop()

        if "Reason" in micro_df.columns:
            micro_reason = (
                micro_df.groupby(["DT_min", "Reason"])["DT_min"]
                .agg(Events="count", Total_DT="sum")
                .sort_values(["DT_min", "Events"], ascending=[False, False])
                .reset_index()
            )

            st.write("## Exact Minute-wise Reason Breakdown")
            st.dataframe(micro_reason, use_container_width=True)

            reason_summary = (
                micro_df.groupby("Reason")["DT_min"]
                .agg(Events="count", Total_DT="sum", Avg_DT="mean")
                .sort_values(["Events", "Total_DT"], ascending=False)
                .reset_index()
            )

            st.write("## Top Repeated Micro Stoppage Reasons")
            st.dataframe(reason_summary.head(30), use_container_width=True)

            fig_micro = px.bar(
                reason_summary.head(15),
                x="Reason",
                y="Events",
                text="Events",
                title="Top 15 Repeated Micro Stoppage Reasons"
            )
            fig_micro.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_micro, use_container_width=True)

        if "Department" in micro_df.columns:
            dept_summary = (
                micro_df.groupby("Department")["DT_min"]
                .agg(Events="count", Total_DT="sum", Avg_DT="mean")
                .sort_values(["Events", "Total_DT"], ascending=False)
                .reset_index()
            )

            st.write("## Department-wise Micro Stoppages")
            st.dataframe(dept_summary, use_container_width=True)

        if "Main/Supplement" in micro_df.columns:
            ms_summary = (
                micro_df.groupby("Main/Supplement")["DT_min"]
                .agg(Events="count", Total_DT="sum", Avg_DT="mean")
                .sort_values("Events", ascending=False)
                .reset_index()
            )

            st.write("## Main vs Supplement Micro Stoppages")
            st.dataframe(ms_summary, use_container_width=True)

        st.write("## 🔬 Micro Stoppage Intelligence")

        st.markdown("""
        <div class="info-box">
        0–4 min stoppages are usually hidden losses. They may look small individually,
        but repeated nuisance stops create major productivity loss across the month.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        ### Recommended Actions
        1. Focus on repeated micro-stoppage reasons with high event count.
        2. Identify nuisance trips, sensor false trips, paper jam detector issues, and operator reset delays.
        3. Convert top 10 micro issues into a daily closure tracker.
        4. Set target to reduce repeated 0–4 min events by 30–40%.
        """)

        ask_pressiq_ai_box("0–4 min micro stoppage file")

    else:
        st.info("Upload a 0–4 min downtime Excel file to start analysis.")


# ---------------- MODULE 3: WEB BREAK DOWNTIME ANALYZER ----------------
elif selected_module == "Web Break Downtime Analyzer":
    st.info("🧵 Web Break Downtime Analyzer will be built in Phase 2.")


# ---------------- MODULE 4: MAIN VS SUPPLEMENT DT ANALYZER ----------------
elif selected_module == "Main vs Supplement DT Analyzer":
    st.info("📘 Main vs Supplement DT Analyzer will be built in Phase 2.")


# ---------------- MODULE 5: PRESS HEALTH ANALYZER ----------------
elif selected_module == "Press Health / Repeated Reason Analyzer":
    st.info("🏭 Press Health / Repeated Reason Analyzer will be built in Phase 2.")


# ---------------- MODULE 6: ADAM PRODUCTION REPORT ANALYZER ----------------
elif selected_module == "ADAM Production Report Analyzer":
    st.info("📄 ADAM Production Report Analyzer will be built next under Waste Intelligence.")


# ---------------- MODULE 7: PAN INDIA WASTE TRACKER ANALYZER ----------------
elif selected_module == "Pan India Waste Tracker Analyzer":
    st.info("🌍 Pan India Waste Tracker Analyzer will be built next under Waste Intelligence.")
