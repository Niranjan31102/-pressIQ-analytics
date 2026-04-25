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


def get_col(df, index):
    if index < len(df.columns):
        return df.iloc[:, index]
    return pd.Series([0] * len(df))


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

        # Date assumed in column A
        date_series = pd.to_datetime(get_col(df, 0), errors="coerce")
        daily = df[date_series.notna()].copy()
        daily["Date_Parsed"] = date_series[date_series.notna()].values

        if daily.empty:
            continue

        out = pd.DataFrame()
        out["Plant Code"] = plant_code
        out["Plant Name"] = plant_name
        out["Date"] = daily["Date_Parsed"]

        # Fixed tracker mapping by Excel column
        # C = Total Consumption
        # M = Total Printed Waste
        # O = No. of Makeready Starts
        # P = No. of Warm Unplanned Stoppages
        # Q = No. of GNPs
        # R = Extra Folder
        # S = Reel End Waste
        # U = Tear Off Waste
        # W = Sweep Waste
        # Y = Trial Waste
        # AA = Total Waste
        out["Consumption Kg"] = to_num(get_col(daily, 1))
        out["Total Printed Waste Kg"] = to_num(get_col(daily, 12))

        out["Makeready Starts"] = to_num(get_col(daily, 14))
        out["Warm Unplanned Stoppages"] = to_num(get_col(daily, 15))
        out["GNP Count"] = to_num(get_col(daily, 16))
        out["Extra Folder"] = to_num(get_col(daily, 17))

        out["Reel End Waste Kg"] = to_num(get_col(daily, 18))
        out["Tear Off Waste Kg"] = to_num(get_col(daily, 20))
        out["Sweep Waste Kg"] = to_num(get_col(daily, 22))
        out["Trial Waste Kg"] = to_num(get_col(daily, 24))
        out["Total Waste Kg"] = to_num(get_col(daily, 26))

        # Fallback if total waste is missing
        if out["Total Waste Kg"].sum() == 0:
            out["Total Waste Kg"] = (
                out["Total Printed Waste Kg"]
                + out["Reel End Waste Kg"]
                + out["Tear Off Waste Kg"]
                + out["Sweep Waste Kg"]
                + out["Trial Waste Kg"]
            )

        out["Total Waste %"] = out.apply(
            lambda r: safe_div(r["Total Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        out["Printed Waste %"] = out.apply(
            lambda r: safe_div(r["Total Printed Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        out["Reel End Waste %"] = out.apply(
            lambda r: safe_div(r["Reel End Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        out["Tear Off Waste %"] = out.apply(
            lambda r: safe_div(r["Tear Off Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        out["Sweep Waste %"] = out.apply(
            lambda r: safe_div(r["Sweep Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        out["Trial Waste %"] = out.apply(
            lambda r: safe_div(r["Trial Waste Kg"], r["Consumption Kg"]) * 100,
            axis=1
        )

        daily_frames.append(out)

        total_consumption = out["Consumption Kg"].sum()
        total_waste = out["Total Waste Kg"].sum()
        printed_waste = out["Total Printed Waste Kg"].sum()
        reel_waste = out["Reel End Waste Kg"].sum()
        tear_waste = out["Tear Off Waste Kg"].sum()
        sweep_waste = out["Sweep Waste Kg"].sum()
        trial_waste = out["Trial Waste Kg"].sum()

        summary_rows.append({
            "Plant Code": plant_code,
            "Plant Name": plant_name,

            "Total Consumption MT": total_consumption / 1000,
            "Total Waste MT": total_waste / 1000,
            "Total Waste %": safe_div(total_waste, total_consumption) * 100,

            "Total Printed Waste MT": printed_waste / 1000,
            "Printed Waste %": safe_div(printed_waste, total_consumption) * 100,

            "Reel End Waste MT": reel_waste / 1000,
            "Reel End Waste %": safe_div(reel_waste, total_consumption) * 100,

            "Tear Off Waste MT": tear_waste / 1000,
            "Tear Off Waste %": safe_div(tear_waste, total_consumption) * 100,

            "Sweep Waste MT": sweep_waste / 1000,
            "Sweep Waste %": safe_div(sweep_waste, total_consumption) * 100,

            "Trial Waste MT": trial_waste / 1000,
            "Trial Waste %": safe_div(trial_waste, total_consumption) * 100,

            "Total No. of Starts": out["Makeready Starts"].sum(),
            "Total No. of Warm Unplanned Stoppages": out["Warm Unplanned Stoppages"].sum(),
            "No. of GNPs": out["GNP Count"].sum(),
            "No. of Extra Folder": out["Extra Folder"].sum(),
        })

    summary = pd.DataFrame(summary_rows)
    daily_all = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()

    if not summary.empty:
        summary["Waste per Start Kg"] = summary.apply(
            lambda r: safe_div(r["Total Waste MT"] * 1000, r["Total No. of Starts"]),
            axis=1
        )
        summary["Waste per Warm Unplanned Stop Kg"] = summary.apply(
            lambda r: safe_div(r["Total Waste MT"] * 1000, r["Total No. of Warm Unplanned Stoppages"]),
            axis=1
        )
        summary["Waste per GNP Kg"] = summary.apply(
            lambda r: safe_div(r["Total Waste MT"] * 1000, r["No. of GNPs"]),
            axis=1
        )
        summary["Waste per Extra Folder Kg"] = summary.apply(
            lambda r: safe_div(r["Total Waste MT"] * 1000, r["No. of Extra Folder"]),
            axis=1
        )

    return summary, daily_all


def round_display(df):
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            if "%" in col:
                out[col] = out[col].round(2)
            elif "MT" in col:
                out[col] = out[col].round(2)
            elif "Kg" in col:
                out[col] = out[col].round(1)
            else:
                out[col] = out[col].round(0)
    return out


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

    total_consumption_mt = summary["Total Consumption MT"].sum()
    total_waste_mt = summary["Total Waste MT"].sum()
    pan_waste_pct = safe_div(total_waste_mt, total_consumption_mt) * 100

    best_plant = summary.sort_values("Total Waste %").iloc[0]
    worst_plant = summary.sort_values("Total Waste %", ascending=False).iloc[0]
    highest_abs = summary.sort_values("Total Waste MT", ascending=False).iloc[0]

    st.markdown("## Executive Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pan India Consumption", f"{total_consumption_mt:,.1f} MT")
    c2.metric("Total Waste", f"{total_waste_mt:,.1f} MT")
    c3.metric("Pan India Waste %", f"{pan_waste_pct:.2f}%")
    c4.metric("Plants Analyzed", f"{len(summary)}")

    st.markdown("## 🚨 Critical Insights")
    insight_box(f"<b>Best waste-rate plant:</b> {best_plant['Plant Name']} ({best_plant['Total Waste %']:.2f}%).")
    insight_box(f"<b>Worst waste-rate plant:</b> {worst_plant['Plant Name']} ({worst_plant['Total Waste %']:.2f}%).", "warning")
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

    # ---------------- TAB 1 ----------------
    with tab1:
        st.markdown("## All India Plant Ranking")

        waste_table = summary[[
            "Plant Name",
            "Total Consumption MT",
            "Total Waste MT",
            "Total Waste %",
            "Total Printed Waste MT",
            "Printed Waste %",
            "Reel End Waste MT",
            "Reel End Waste %",
            "Tear Off Waste MT",
            "Tear Off Waste %",
            "Sweep Waste MT",
            "Sweep Waste %",
            "Trial Waste MT",
            "Trial Waste %"
        ]].sort_values("Total Waste %", ascending=True)

        driver_table = summary[[
            "Plant Name",
            "Total Consumption MT",
            "Total No. of Starts",
            "Total No. of Warm Unplanned Stoppages",
            "No. of GNPs",
            "No. of Extra Folder"
        ]].sort_values("Total Consumption MT", ascending=False)

        st.markdown("### Waste Performance Table")
        st.dataframe(round_display(waste_table), use_container_width=True, hide_index=True)

        st.markdown("### Operational Driver Table")
        st.dataframe(round_display(driver_table), use_container_width=True, hide_index=True)

        fig_rank = px.bar(
            waste_table,
            x="Total Waste %",
            y="Plant Name",
            orientation="h",
            text="Total Waste %",
            title="Plant Ranking by Total Waste % - Best to Worst"
        )
        fig_rank.update_traces(texttemplate="%{text:.2f}%")
        fig_rank.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_rank, use_container_width=True)

        fig_abs = px.bar(
            waste_table.sort_values("Total Waste MT", ascending=False),
            x="Plant Name",
            y="Total Waste MT",
            text="Total Waste MT",
            title="Plant Ranking by Absolute Waste MT"
        )
        fig_abs.update_traces(texttemplate="%{text:.1f}")
        st.plotly_chart(fig_abs, use_container_width=True)

    # ---------------- TAB 2 ----------------
    with tab2:
        st.markdown("## Single Plant vs Pan India")

        plant = st.selectbox("Select Plant", summary["Plant Name"].tolist(), key="single_plant")
        plant_row = summary[summary["Plant Name"] == plant].iloc[0]

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Plant Waste %", f"{plant_row['Total Waste %']:.2f}%")
        p2.metric("Pan India Waste %", f"{pan_waste_pct:.2f}%")
        p3.metric("Gap vs Pan India", f"{plant_row['Total Waste %'] - pan_waste_pct:+.2f}%")
        p4.metric("Total Waste", f"{plant_row['Total Waste MT']:.1f} MT")

        compare_df = pd.DataFrame({
            "KPI": [
                "Total Consumption MT",
                "Total Waste MT",
                "Total Waste %",
                "Total Printed Waste MT",
                "Printed Waste %",
                "Reel End Waste MT",
                "Reel End Waste %",
                "Tear Off Waste MT",
                "Tear Off Waste %",
                "Sweep Waste MT",
                "Sweep Waste %",
                "Trial Waste MT",
                "Trial Waste %",
                "Total No. of Starts",
                "Total No. of Warm Unplanned Stoppages",
                "No. of GNPs",
                "No. of Extra Folder",
            ],
            plant: [
                plant_row["Total Consumption MT"],
                plant_row["Total Waste MT"],
                plant_row["Total Waste %"],
                plant_row["Total Printed Waste MT"],
                plant_row["Printed Waste %"],
                plant_row["Reel End Waste MT"],
                plant_row["Reel End Waste %"],
                plant_row["Tear Off Waste MT"],
                plant_row["Tear Off Waste %"],
                plant_row["Sweep Waste MT"],
                plant_row["Sweep Waste %"],
                plant_row["Trial Waste MT"],
                plant_row["Trial Waste %"],
                plant_row["Total No. of Starts"],
                plant_row["Total No. of Warm Unplanned Stoppages"],
                plant_row["No. of GNPs"],
                plant_row["No. of Extra Folder"],
            ],
            "Pan India": [
                total_consumption_mt,
                total_waste_mt,
                pan_waste_pct,
                summary["Total Printed Waste MT"].sum(),
                safe_div(summary["Total Printed Waste MT"].sum(), total_consumption_mt) * 100,
                summary["Reel End Waste MT"].sum(),
                safe_div(summary["Reel End Waste MT"].sum(), total_consumption_mt) * 100,
                summary["Tear Off Waste MT"].sum(),
                safe_div(summary["Tear Off Waste MT"].sum(), total_consumption_mt) * 100,
                summary["Sweep Waste MT"].sum(),
                safe_div(summary["Sweep Waste MT"].sum(), total_consumption_mt) * 100,
                summary["Trial Waste MT"].sum(),
                safe_div(summary["Trial Waste MT"].sum(), total_consumption_mt) * 100,
                summary["Total No. of Starts"].sum(),
                summary["Total No. of Warm Unplanned Stoppages"].sum(),
                summary["No. of GNPs"].sum(),
                summary["No. of Extra Folder"].sum(),
            ]
        })

        st.dataframe(round_display(compare_df), use_container_width=True, hide_index=True)

        plant_daily = daily_all[daily_all["Plant Name"] == plant]
        fig_daily = px.line(
            plant_daily,
            x="Date",
            y="Total Waste %",
            markers=True,
            title=f"{plant} Daily Total Waste % Trend"
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        if plant_row["Total Waste %"] > pan_waste_pct:
            gap_waste = (plant_row["Total Waste %"] - pan_waste_pct) / 100 * (plant_row["Total Consumption MT"] * 1000)
            insight_box(
                f"<b>{plant} is above Pan India average.</b> Approx saving opportunity if it reaches Pan India average: {gap_waste/1000:.1f} MT.",
                "warning"
            )
        else:
            insight_box(f"<b>{plant} is performing better than Pan India average.</b> It can be used as a benchmark plant.")

    # ---------------- TAB 3 ----------------
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
                "Total Consumption MT",
                "Total Waste MT",
                "Total Waste %",
                "Total Printed Waste MT",
                "Printed Waste %",
                "Reel End Waste MT",
                "Reel End Waste %",
                "Tear Off Waste MT",
                "Tear Off Waste %",
                "Sweep Waste MT",
                "Sweep Waste %",
                "Trial Waste MT",
                "Trial Waste %",
                "Total No. of Starts",
                "Total No. of Warm Unplanned Stoppages",
                "No. of GNPs",
                "No. of Extra Folder",
                "Waste per Start Kg",
                "Waste per Warm Unplanned Stop Kg",
                "Waste per GNP Kg",
                "Waste per Extra Folder Kg",
            ],
            plant_a: [
                a["Total Consumption MT"],
                a["Total Waste MT"],
                a["Total Waste %"],
                a["Total Printed Waste MT"],
                a["Printed Waste %"],
                a["Reel End Waste MT"],
                a["Reel End Waste %"],
                a["Tear Off Waste MT"],
                a["Tear Off Waste %"],
                a["Sweep Waste MT"],
                a["Sweep Waste %"],
                a["Trial Waste MT"],
                a["Trial Waste %"],
                a["Total No. of Starts"],
                a["Total No. of Warm Unplanned Stoppages"],
                a["No. of GNPs"],
                a["No. of Extra Folder"],
                a["Waste per Start Kg"],
                a["Waste per Warm Unplanned Stop Kg"],
                a["Waste per GNP Kg"],
                a["Waste per Extra Folder Kg"],
            ],
            plant_b: [
                b["Total Consumption MT"],
                b["Total Waste MT"],
                b["Total Waste %"],
                b["Total Printed Waste MT"],
                b["Printed Waste %"],
                b["Reel End Waste MT"],
                b["Reel End Waste %"],
                b["Tear Off Waste MT"],
                b["Tear Off Waste %"],
                b["Sweep Waste MT"],
                b["Sweep Waste %"],
                b["Trial Waste MT"],
                b["Trial Waste %"],
                b["Total No. of Starts"],
                b["Total No. of Warm Unplanned Stoppages"],
                b["No. of GNPs"],
                b["No. of Extra Folder"],
                b["Waste per Start Kg"],
                b["Waste per Warm Unplanned Stop Kg"],
                b["Waste per GNP Kg"],
                b["Waste per Extra Folder Kg"],
            ]
        })

        comp["Better"] = comp.apply(
            lambda r: plant_a if r[plant_a] < r[plant_b] else plant_b,
            axis=1
        )

        st.dataframe(round_display(comp), use_container_width=True, hide_index=True)

        trend_two = daily_all[daily_all["Plant Name"].isin([plant_a, plant_b])]
        fig_two = px.line(
            trend_two,
            x="Date",
            y="Total Waste %",
            color="Plant Name",
            markers=True,
            title=f"Daily Waste % Trend: {plant_a} vs {plant_b}"
        )
        st.plotly_chart(fig_two, use_container_width=True)

        if a["Total Waste %"] > b["Total Waste %"]:
            saving_gap = (a["Total Waste %"] - b["Total Waste %"]) / 100 * (a["Total Consumption MT"] * 1000)
            insight_box(f"If {plant_a} reaches {plant_b}'s waste %, saving opportunity is approx {saving_gap/1000:.1f} MT.", "warning")
        elif b["Total Waste %"] > a["Total Waste %"]:
            saving_gap = (b["Total Waste %"] - a["Total Waste %"]) / 100 * (b["Total Consumption MT"] * 1000)
            insight_box(f"If {plant_b} reaches {plant_a}'s waste %, saving opportunity is approx {saving_gap/1000:.1f} MT.", "warning")
        else:
            insight_box("Both plants have similar total waste percentage.")

    # ---------------- TAB 4 ----------------
    with tab4:
        st.markdown("## Waste Category Analysis")

        cat = pd.DataFrame({
            "Category": [
                "Total Printed Waste",
                "Reel End Waste",
                "Tear Off Waste",
                "Sweep Waste",
                "Trial Waste"
            ],
            "Waste MT": [
                summary["Total Printed Waste MT"].sum(),
                summary["Reel End Waste MT"].sum(),
                summary["Tear Off Waste MT"].sum(),
                summary["Sweep Waste MT"].sum(),
                summary["Trial Waste MT"].sum(),
            ]
        })

        st.dataframe(round_display(cat), use_container_width=True, hide_index=True)

        fig_cat = px.pie(
            cat,
            values="Waste MT",
            names="Category",
            hole=0.45,
            title="Pan India Waste Category Share"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

        fig_cat_bar = px.bar(
            cat,
            x="Category",
            y="Waste MT",
            text="Waste MT",
            title="Waste by Category"
        )
        fig_cat_bar.update_traces(texttemplate="%{text:.1f}")
        st.plotly_chart(fig_cat_bar, use_container_width=True)

    # ---------------- TAB 5 ----------------
    with tab5:
        st.markdown("## Daily Outlier Detection")

        outliers = daily_all[
            (daily_all["Total Waste %"] > pan_waste_pct)
            & (daily_all["Consumption Kg"] > 0)
        ].sort_values("Total Waste %", ascending=False)

        st.write(f"Days above Pan India average waste rate: {len(outliers)}")
        st.dataframe(round_display(outliers.head(50)), use_container_width=True, hide_index=True)

        top_outlier = outliers.head(20)

        if not top_outlier.empty:
            fig_out = px.bar(
                top_outlier,
                x="Date",
                y="Total Waste %",
                color="Plant Name",
                text="Total Waste %",
                title="Top Daily Waste % Outliers"
            )
            fig_out.update_traces(texttemplate="%{text:.2f}%")
            st.plotly_chart(fig_out, use_container_width=True)

    # ---------------- TAB 6 ----------------
    with tab6:
        st.markdown("## Download Report")

        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            round_display(waste_table).to_excel(writer, index=False, sheet_name="Waste Performance")
            round_display(driver_table).to_excel(writer, index=False, sheet_name="Operational Drivers")
            round_display(summary).to_excel(writer, index=False, sheet_name="Full Summary")
            round_display(daily_all).to_excel(writer, index=False, sheet_name="Daily Data")
            round_display(cat).to_excel(writer, index=False, sheet_name="Category Summary")
            round_display(outliers).to_excel(writer, index=False, sheet_name="Outliers")

        st.download_button(
            "📥 Download Pan India Waste Tracker Report",
            data=output.getvalue(),
            file_name="PressIQ_Pan_India_Waste_Tracker_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
