import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

from utils.helpers import PLANT_NAMES, norm, safe_div, to_num, insight_box


def find_header_row(raw):
    keywords = [
        "date", "consumption", "cold", "warm", "planned", "unplanned",
        "running", "print", "reel", "tear", "sweep", "trial", "total waste"
    ]

    for i in range(min(25, len(raw))):
        row_text = " ".join([norm(v) for v in raw.iloc[i].values if pd.notna(v)])
        score = sum(k in row_text for k in keywords)

        if score >= 4:
            return i

    return 0


def find_col(df, must_terms=None, any_terms=None, exclude_terms=None):
    must_terms = must_terms or []
    any_terms = any_terms or []
    exclude_terms = exclude_terms or []

    for col in df.columns:
        c = norm(col)

        if any(ex in c for ex in exclude_terms):
            continue

        if all(t in c for t in must_terms):
            if not any_terms or any(t in c for t in any_terms):
                return col

    return None


def read_tracker_file(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)

    plant_sheets = [
        s for s in xls.sheet_names
        if norm(s) not in ["summary", "data dictionary", "dictionary"]
    ]

    daily_frames = []
    summary_rows = []

    for sheet in plant_sheets:
        raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        header_row = find_header_row(raw)

        df = pd.read_excel(xls, sheet_name=sheet, header=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all")

        plant_code = str(sheet).strip().upper()
        plant_name = PLANT_NAMES.get(plant_code, plant_code)

        date_col = find_col(df, must_terms=["date"])
        if date_col is None:
            date_col = df.columns[0]

        df["Date_Parsed"] = pd.to_datetime(df[date_col], errors="coerce")
        daily = df[df["Date_Parsed"].notna()].copy()

        if daily.empty:
            continue

        colmap = {
            "Consumption Kg": find_col(daily, must_terms=["consumption"]),
            "Cold Waste Kg": find_col(daily, must_terms=["cold"], any_terms=["waste"]),
            "Warm Planned Waste Kg": find_col(daily, must_terms=["warm", "planned"], exclude_terms=["unplanned"]),
            "Warm Unplanned Waste Kg": find_col(daily, must_terms=["warm", "unplanned"]),
            "Variance Waste Kg": find_col(daily, must_terms=["variance"]),
            "Running Waste Kg": find_col(daily, must_terms=["running"]),
            "Print Waste Kg": find_col(daily, must_terms=["print", "waste"]),
            "Reel End Waste Kg": find_col(daily, must_terms=["reel", "end"]),
            "Tear Off Waste Kg": find_col(daily, must_terms=["tear"]),
            "Sweep Waste Kg": find_col(daily, must_terms=["sweep"]),
            "Trial Waste Kg": find_col(daily, must_terms=["trial"]),
            "Total Waste Kg": find_col(daily, must_terms=["total", "waste"], exclude_terms=["print"]),
            "Cold Starts": find_col(daily, must_terms=["cold", "start"]),
            "Warm Starts": find_col(daily, must_terms=["warm", "start"]),
            "Makeready Starts": find_col(daily, must_terms=["makeready"]),
            "Warm Unplanned Stoppages": find_col(daily, must_terms=["unplanned"], any_terms=["stoppage", "stop"]),
            "GNP Count": find_col(daily, must_terms=["gnp"]),
            "Extra Folder": find_col(daily, must_terms=["extra", "folder"]),
            "Remarks": find_col(daily, must_terms=["remark"])
        }

        out = pd.DataFrame()
        out["Plant Code"] = plant_code
        out["Plant Name"] = plant_name
        out["Date"] = daily["Date_Parsed"]

        for k, col in colmap.items():
            if k == "Remarks":
                out[k] = daily[col].astype(str) if col else ""
            else:
                out[k] = to_num(daily[col]) if col else 0

        if out["Total Waste Kg"].sum() == 0:
            out["Total Waste Kg"] = (
                out["Print Waste Kg"]
                + out["Reel End Waste Kg"]
                + out["Tear Off Waste Kg"]
                + out["Sweep Waste Kg"]
                + out["Trial Waste Kg"]
            )

        if out["Print Waste Kg"].sum() == 0:
            out["Print Waste Kg"] = (
                out["Cold Waste Kg"]
                + out["Warm Planned Waste Kg"]
                + out["Warm Unplanned Waste Kg"]
                + out["Variance Waste Kg"]
                + out["Running Waste Kg"]
            )

        out["Non Print Waste Kg"] = (
            out["Reel End Waste Kg"]
            + out["Tear Off Waste Kg"]
            + out["Sweep Waste Kg"]
            + out["Trial Waste Kg"]
        )

        out["Waste %"] = out.apply(
            lambda r: safe_div(r["Total Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        daily_frames.append(out)

        total_consumption = out["Consumption Kg"].sum()
        total_waste = out["Total Waste Kg"].sum()

        summary_rows.append({
            "Plant Code": plant_code,
            "Plant Name": plant_name,
            "Days": out["Date"].nunique(),
            "Consumption Kg": total_consumption,
            "Consumption MT": total_consumption / 1000,
            "Total Waste Kg": total_waste,
            "Total Waste MT": total_waste / 1000,
            "Waste %": safe_div(total_waste, total_consumption) * 100,
            "Print Waste Kg": out["Print Waste Kg"].sum(),
            "Print Waste MT": out["Print Waste Kg"].sum() / 1000,
            "Non Print Waste Kg": out["Non Print Waste Kg"].sum(),
            "Non Print Waste MT": out["Non Print Waste Kg"].sum() / 1000,
            "Cold Waste Kg": out["Cold Waste Kg"].sum(),
            "Warm Planned Waste Kg": out["Warm Planned Waste Kg"].sum(),
            "Warm Unplanned Waste Kg": out["Warm Unplanned Waste Kg"].sum(),
            "Running Waste Kg": out["Running Waste Kg"].sum(),
            "Reel End Waste Kg": out["Reel End Waste Kg"].sum(),
            "Tear Off Waste Kg": out["Tear Off Waste Kg"].sum(),
            "Sweep Waste Kg": out["Sweep Waste Kg"].sum(),
            "Trial Waste Kg": out["Trial Waste Kg"].sum(),
            "Cold Starts": out["Cold Starts"].sum(),
            "Warm Starts": out["Warm Starts"].sum() if out["Warm Starts"].sum() else out["Makeready Starts"].sum(),
            "Warm Unplanned Stoppages": out["Warm Unplanned Stoppages"].sum(),
            "GNP Count": out["GNP Count"].sum(),
            "Extra Folder": out["Extra Folder"].sum(),
        })

    summary = pd.DataFrame(summary_rows)
    daily_all = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()

    if not summary.empty:
        summary["Waste per Cold Start Kg"] = summary.apply(
            lambda r: safe_div(r["Cold Waste Kg"], r["Cold Starts"]),
            axis=1
        )
        summary["Waste per Warm Start Kg"] = summary.apply(
            lambda r: safe_div(r["Warm Planned Waste Kg"] + r["Warm Unplanned Waste Kg"], r["Warm Starts"]),
            axis=1
        )
        summary["Waste per Unplanned Stop Kg"] = summary.apply(
            lambda r: safe_div(r["Warm Unplanned Waste Kg"], r["Warm Unplanned Stoppages"]),
            axis=1
        )
        summary["Waste per GNP Kg"] = summary.apply(
            lambda r: safe_div(r["Total Waste Kg"], r["GNP Count"]),
            axis=1
        )
        summary["Waste per Extra Folder Kg"] = summary.apply(
            lambda r: safe_div(r["Total Waste Kg"], r["Extra Folder"]),
            axis=1
        )

    return summary, daily_all


def run_waste_tracker():
    st.markdown("### Upload Pan India Waste Tracker File")
    uploaded_file = st.file_uploader("Upload Excel tracker file", type=["xlsx"])

    if not uploaded_file:
        st.info("Upload Pan India Waste Tracker Excel file to start analysis.")
        return

    with st.spinner("Reading all plant sheets and building Pan India waste intelligence..."):
        summary, daily_all = read_tracker_file(uploaded_file)

    if summary.empty:
        st.error("No plant data could be detected. Please check file format.")
        return

    total_consumption = summary["Consumption Kg"].sum()
    total_waste = summary["Total Waste Kg"].sum()
    pan_waste_pct = safe_div(total_waste, total_consumption) * 100

    best_plant = summary.sort_values("Waste %").iloc[0]
    worst_plant = summary.sort_values("Waste %", ascending=False).iloc[0]
    highest_abs = summary.sort_values("Total Waste MT", ascending=False).iloc[0]

    st.markdown("## Executive Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pan India Consumption", f"{total_consumption/1000:,.1f} MT")
    c2.metric("Total Waste", f"{total_waste/1000:,.1f} MT")
    c3.metric("Pan India Waste %", f"{pan_waste_pct:.2f}%")
    c4.metric("Plants Analyzed", f"{len(summary)}")

    st.markdown("## 🚨 Critical Insights")
    insight_box(f"<b>Best waste-rate plant:</b> {best_plant['Plant Name']} ({best_plant['Waste %']:.2f}%).")
    insight_box(f"<b>Worst waste-rate plant:</b> {worst_plant['Plant Name']} ({worst_plant['Waste %']:.2f}%).", "warning")
    insight_box(f"<b>Highest absolute waste:</b> {highest_abs['Plant Name']} with {highest_abs['Total Waste MT']:.1f} MT waste.")
    insight_box(f"<b>Pan India waste rate:</b> {pan_waste_pct:.2f}%. Plants above this need focused waste control.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "All India Ranking",
        "Single Plant vs Pan India",
        "Plant vs Plant",
        "Waste Category",
        "Daily Outliers",
        "Download Report"
    ])

    with tab1:
        st.markdown("## All India Plant Ranking")
        ranking = summary.sort_values("Waste %", ascending=False).copy()
        ranking["Rank"] = ranking["Waste %"].rank(ascending=True, method="min").astype(int)

        st.dataframe(ranking, use_container_width=True)

        fig_rank = px.bar(
            ranking.sort_values("Waste %"),
            x="Waste %",
            y="Plant Name",
            orientation="h",
            text="Waste %",
            title="Plant Ranking by Waste %"
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        fig_abs = px.bar(
            summary.sort_values("Total Waste MT", ascending=False),
            x="Plant Name",
            y="Total Waste MT",
            text="Total Waste MT",
            title="Plant Ranking by Absolute Waste MT"
        )
        st.plotly_chart(fig_abs, use_container_width=True)

    with tab2:
        st.markdown("## Single Plant vs Pan India")
        plant = st.selectbox("Select Plant", summary["Plant Name"].tolist(), key="single_plant")
        plant_row = summary[summary["Plant Name"] == plant].iloc[0]

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Plant Waste %", f"{plant_row['Waste %']:.2f}%")
        p2.metric("Pan India Waste %", f"{pan_waste_pct:.2f}%")
        p3.metric("Gap vs Pan India", f"{plant_row['Waste %'] - pan_waste_pct:+.2f}%")
        p4.metric("Total Waste", f"{plant_row['Total Waste MT']:.1f} MT")

        plant_daily = daily_all[daily_all["Plant Name"] == plant]
        fig_daily = px.line(
            plant_daily,
            x="Date",
            y="Waste %",
            markers=True,
            title=f"{plant} Daily Waste % Trend"
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        if plant_row["Waste %"] > pan_waste_pct:
            gap_waste = (plant_row["Waste %"] - pan_waste_pct) / 100 * plant_row["Consumption Kg"]
            insight_box(
                f"<b>{plant} is above Pan India average.</b> Approx saving opportunity if it reaches Pan India average: {gap_waste/1000:.1f} MT.",
                "warning"
            )
        else:
            insight_box(f"<b>{plant} is performing better than Pan India average.</b> It can be used as a benchmark plant.")

    with tab3:
        st.markdown("## Plant vs Plant Comparison")

        plants = summary["Plant Name"].tolist()
        col_a, col_b = st.columns(2)

        with col_a:
            plant_a = st.selectbox("Select Plant 1", plants, key="plant_a")

        with col_b:
            plant_b = st.selectbox("Select Plant 2", plants, index=1 if len(plants) > 1 else 0, key="plant_b")

        a = summary[summary["Plant Name"] == plant_a].iloc[0]
        b = summary[summary["Plant Name"] == plant_b].iloc[0]

        comp = pd.DataFrame({
            "KPI": [
                "Consumption MT", "Total Waste MT", "Waste %",
                "Print Waste MT", "Non Print Waste MT",
                "Cold Waste Kg", "Warm Planned Waste Kg", "Warm Unplanned Waste Kg",
                "Running Waste Kg", "Reel End Waste Kg", "Tear Off Waste Kg",
                "Sweep Waste Kg", "Trial Waste Kg",
                "Cold Starts", "Warm Starts", "Warm Unplanned Stoppages",
                "GNP Count", "Extra Folder",
                "Waste per Cold Start Kg", "Waste per Warm Start Kg",
                "Waste per Unplanned Stop Kg", "Waste per GNP Kg",
                "Waste per Extra Folder Kg"
            ],
            plant_a: [
                a["Consumption MT"], a["Total Waste MT"], a["Waste %"],
                a["Print Waste MT"], a["Non Print Waste MT"],
                a["Cold Waste Kg"], a["Warm Planned Waste Kg"], a["Warm Unplanned Waste Kg"],
                a["Running Waste Kg"], a["Reel End Waste Kg"], a["Tear Off Waste Kg"],
                a["Sweep Waste Kg"], a["Trial Waste Kg"],
                a["Cold Starts"], a["Warm Starts"], a["Warm Unplanned Stoppages"],
                a["GNP Count"], a["Extra Folder"],
                a["Waste per Cold Start Kg"], a["Waste per Warm Start Kg"],
                a["Waste per Unplanned Stop Kg"], a["Waste per GNP Kg"],
                a["Waste per Extra Folder Kg"]
            ],
            plant_b: [
                b["Consumption MT"], b["Total Waste MT"], b["Waste %"],
                b["Print Waste MT"], b["Non Print Waste MT"],
                b["Cold Waste Kg"], b["Warm Planned Waste Kg"], b["Warm Unplanned Waste Kg"],
                b["Running Waste Kg"], b["Reel End Waste Kg"], b["Tear Off Waste Kg"],
                b["Sweep Waste Kg"], b["Trial Waste Kg"],
                b["Cold Starts"], b["Warm Starts"], b["Warm Unplanned Stoppages"],
                b["GNP Count"], b["Extra Folder"],
                b["Waste per Cold Start Kg"], b["Waste per Warm Start Kg"],
                b["Waste per Unplanned Stop Kg"], b["Waste per GNP Kg"],
                b["Waste per Extra Folder Kg"]
            ]
        })

        comp["Better"] = comp.apply(lambda r: plant_a if r[plant_a] < r[plant_b] else plant_b, axis=1)
        st.dataframe(comp, use_container_width=True)

        trend_two = daily_all[daily_all["Plant Name"].isin([plant_a, plant_b])]
        fig_two = px.line(
            trend_two,
            x="Date",
            y="Waste %",
            color="Plant Name",
            markers=True,
            title=f"Daily Waste % Trend: {plant_a} vs {plant_b}"
        )
        st.plotly_chart(fig_two, use_container_width=True)

    with tab4:
        st.markdown("## Waste Category Analysis")

        cat = pd.DataFrame({
            "Category": ["Print Waste", "Reel End", "Tear Off", "Sweep", "Trial"],
            "Waste MT": [
                summary["Print Waste MT"].sum(),
                summary["Reel End Waste Kg"].sum() / 1000,
                summary["Tear Off Waste Kg"].sum() / 1000,
                summary["Sweep Waste Kg"].sum() / 1000,
                summary["Trial Waste Kg"].sum() / 1000,
            ]
        })

        st.dataframe(cat, use_container_width=True)

        fig_cat = px.pie(cat, values="Waste MT", names="Category", hole=0.45, title="Pan India Waste Category Share")
        st.plotly_chart(fig_cat, use_container_width=True)

        fig_cat_bar = px.bar(cat, x="Category", y="Waste MT", text="Waste MT", title="Waste by Category")
        st.plotly_chart(fig_cat_bar, use_container_width=True)

    with tab5:
        st.markdown("## Daily Outlier Detection")

        outliers = daily_all[
            (daily_all["Waste %"] > pan_waste_pct)
            & (daily_all["Consumption Kg"] > 0)
        ].sort_values("Waste %", ascending=False)

        st.write(f"Days above Pan India average waste rate: {len(outliers)}")
        st.dataframe(outliers.head(50), use_container_width=True)

        top_outlier = outliers.head(20)

        if not top_outlier.empty:
            fig_out = px.bar(
                top_outlier,
                x="Date",
                y="Waste %",
                color="Plant Name",
                text="Waste %",
                title="Top Daily Waste % Outliers"
            )
            st.plotly_chart(fig_out, use_container_width=True)

    with tab6:
        st.markdown("## Download Report")
        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            summary.to_excel(writer, index=False, sheet_name="Plant Summary")
            daily_all.to_excel(writer, index=False, sheet_name="Daily Data")
            ranking.to_excel(writer, index=False, sheet_name="Ranking")
            cat.to_excel(writer, index=False, sheet_name="Category Summary")
            outliers.to_excel(writer, index=False, sheet_name="Outliers")

        st.download_button(
            "📥 Download Pan India Waste Tracker Report",
            data=output.getvalue(),
            file_name="PressIQ_Pan_India_Waste_Tracker_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
