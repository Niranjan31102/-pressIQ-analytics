import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO


def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def find_col(df, possible_names):
    cols = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        key = name.strip().lower()
        if key in cols:
            return cols[key]
    return None


def read_edition_file(uploaded_file, sheet_name):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    colmap = {
        "Edition Date": find_col(df, ["Edition Date (DD-MM-YYYY)", "Edition Date"]),
        "Edition": find_col(df, ["Edition"]),
        "Edition Name": find_col(df, ["Edition Name"]),
        "Print Order": find_col(df, ["Print Order"]),
        "Main/Supplement": find_col(df, ["Edition (Main/Supl)", "Main/Supplement"]),
        "Machine": find_col(df, ["Machine"]),
        "Folder": find_col(df, ["Folder"]),
        "GNP/SNP": find_col(df, ["GNP", "SNP/GNP"]),
        "Complexity": find_col(df, ["Complexity"]),
        "Type of Start": find_col(df, ["Type of Start"]),

        "White Kg": find_col(df, ["White copies in Kg"]),
        "Scum Kg": find_col(df, ["Scum Copies in Kg"]),
        "Cut-off Kg": find_col(df, ["Cut-off Copies in Kg"]),
        "Registration Kg": find_col(df, ["Registration Copies in Kg"]),
        "Density Variation Kg": find_col(df, ["Density Variation Copies in Kg"]),
        "Other Kg": find_col(df, ["Other waste copies in Kg"]),
        "Pasting Kg": find_col(df, ["Total pasting copies in Kg"]),
        "Total Waste Kg": find_col(df, ["Total waste in KG", "Total Waste in KG"]),
    }

    out = pd.DataFrame()

    for new_col, old_col in colmap.items():
        if old_col is None:
            out[new_col] = 0 if "Kg" in new_col or new_col == "Print Order" else ""
        else:
            out[new_col] = df[old_col]

    out["Edition Date"] = pd.to_datetime(out["Edition Date"], errors="coerce", dayfirst=True)
    out = out[out["Edition Date"].notna()].copy()

    for col in [
        "Print Order",
        "White Kg",
        "Scum Kg",
        "Cut-off Kg",
        "Registration Kg",
        "Density Variation Kg",
        "Other Kg",
        "Pasting Kg",
        "Total Waste Kg",
    ]:
        out[col] = to_num(out[col])

    return out


def run_edition_waste_analyzer():
    st.markdown("### Upload Edition Wise Wastage File")

    uploaded_file = st.file_uploader(
        "Upload Edition Wise Wastage Excel file",
        type=["xlsx"],
        key="edition_waste_upload"
    )

    if not uploaded_file:
        st.info("Upload edition-wise wastage tracker file to start analysis.")
        return

    xls = pd.ExcelFile(uploaded_file)

    available_sheets = [
        s for s in xls.sheet_names
        if str(s).strip().upper() not in ["MASTER", "SHEET1"]
    ]

    if "AIR" in xls.sheet_names:
        default_index = available_sheets.index("AIR") if "AIR" in available_sheets else 0
    else:
        default_index = 0

    sheet_name = st.selectbox(
        "Select Plant Sheet",
        available_sheets,
        index=default_index
    )

    df = read_edition_file(uploaded_file, sheet_name)

    if df.empty:
        st.error("No valid edition-wise data found in selected sheet.")
        return

    min_date = df["Edition Date"].min().date()
    max_date = df["Edition Date"].max().date()

    st.markdown("### Select Date Range")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("From Date", min_date, min_value=min_date, max_value=max_date)

    with col2:
        end_date = st.date_input("To Date", max_date, min_value=min_date, max_value=max_date)

    filtered = df[
        (df["Edition Date"].dt.date >= start_date) &
        (df["Edition Date"].dt.date <= end_date)
    ].copy()

    if filtered.empty:
        st.warning("No data found for selected date range.")
        return

    total_waste = filtered["Total Waste Kg"].sum()
    total_print_order = filtered["Print Order"].sum()
    total_editions = len(filtered)
    avg_waste = total_waste / total_editions if total_editions else 0

    st.markdown("## Executive Dashboard")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Editions", f"{total_editions:,}")
    k2.metric("Total Waste", f"{total_waste:,.1f} kg")
    k3.metric("Total Print Order", f"{total_print_order:,.0f}")
    k4.metric("Avg Waste / Edition", f"{avg_waste:,.1f} kg")

    st.markdown("## Key Insight")
    top_segment = {
        "White Kg": filtered["White Kg"].sum(),
        "Scum Kg": filtered["Scum Kg"].sum(),
        "Cut-off Kg": filtered["Cut-off Kg"].sum(),
        "Registration Kg": filtered["Registration Kg"].sum(),
        "Density Variation Kg": filtered["Density Variation Kg"].sum(),
        "Other Kg": filtered["Other Kg"].sum(),
        "Pasting Kg": filtered["Pasting Kg"].sum(),
    }

    top_segment_name = max(top_segment, key=top_segment.get)
    st.info(f"Highest waste segment is **{top_segment_name}** with **{top_segment[top_segment_name]:,.1f} kg**.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Waste Segment",
        "Edition Performance",
        "Machine / Start Type",
        "GNP-SNP / Complexity",
        "Download Report"
    ])

    with tab1:
        st.markdown("## Waste Segment Breakdown")

        segment_df = pd.DataFrame({
            "Waste Segment": list(top_segment.keys()),
            "Waste Kg": list(top_segment.values())
        }).sort_values("Waste Kg", ascending=False)

        st.dataframe(segment_df, use_container_width=True, hide_index=True)

        fig_seg = px.bar(
            segment_df,
            x="Waste Segment",
            y="Waste Kg",
            text="Waste Kg",
            title="Waste by Segment"
        )
        fig_seg.update_traces(texttemplate="%{text:.1f}")
        st.plotly_chart(fig_seg, use_container_width=True)

        fig_pie = px.pie(
            segment_df,
            values="Waste Kg",
            names="Waste Segment",
            hole=0.45,
            title="Waste Segment Share"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.markdown("## Edition Wise Waste Performance")

        edition_summary = (
            filtered.groupby(["Edition", "Edition Name"], dropna=False)["Total Waste Kg"]
            .sum()
            .reset_index()
            .sort_values("Total Waste Kg", ascending=False)
        )

        st.dataframe(edition_summary.head(50), use_container_width=True, hide_index=True)

        fig_edition = px.bar(
            edition_summary.head(20),
            x="Total Waste Kg",
            y="Edition Name",
            orientation="h",
            text="Total Waste Kg",
            title="Top 20 Editions by Waste Kg"
        )
        fig_edition.update_traces(texttemplate="%{text:.1f}")
        st.plotly_chart(fig_edition, use_container_width=True)

    with tab3:
        st.markdown("## Machine / Start Type Analysis")

        machine_summary = (
            filtered.groupby("Machine", dropna=False)["Total Waste Kg"]
            .sum()
            .reset_index()
            .sort_values("Total Waste Kg", ascending=False)
        )

        start_summary = (
            filtered.groupby("Type of Start", dropna=False)["Total Waste Kg"]
            .sum()
            .reset_index()
            .sort_values("Total Waste Kg", ascending=False)
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### Machine Wise Waste")
            st.dataframe(machine_summary, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("### Start Type Wise Waste")
            st.dataframe(start_summary, use_container_width=True, hide_index=True)

        fig_machine = px.bar(machine_summary, x="Machine", y="Total Waste Kg", text="Total Waste Kg")
        st.plotly_chart(fig_machine, use_container_width=True)

        fig_start = px.bar(start_summary, x="Type of Start", y="Total Waste Kg", text="Total Waste Kg")
        st.plotly_chart(fig_start, use_container_width=True)

    with tab4:
        st.markdown("## GNP/SNP and Complexity Analysis")

        gnp_summary = (
            filtered.groupby("GNP/SNP", dropna=False)["Total Waste Kg"]
            .sum()
            .reset_index()
            .sort_values("Total Waste Kg", ascending=False)
        )

        complexity_summary = (
            filtered.groupby("Complexity", dropna=False)["Total Waste Kg"]
            .sum()
            .reset_index()
            .sort_values("Total Waste Kg", ascending=False)
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### GNP/SNP Wise Waste")
            st.dataframe(gnp_summary, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("### Complexity Wise Waste")
            st.dataframe(complexity_summary, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown("## Download Report")

        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            filtered.to_excel(writer, index=False, sheet_name="Filtered Data")
            segment_df.to_excel(writer, index=False, sheet_name="Waste Segment")
            edition_summary.to_excel(writer, index=False, sheet_name="Edition Summary")
            machine_summary.to_excel(writer, index=False, sheet_name="Machine Summary")
            start_summary.to_excel(writer, index=False, sheet_name="Start Type Summary")
            gnp_summary.to_excel(writer, index=False, sheet_name="GNP SNP Summary")
            complexity_summary.to_excel(writer, index=False, sheet_name="Complexity Summary")

        st.download_button(
            "📥 Download Edition Wise Wastage Report",
            data=output.getvalue(),
            file_name="PressIQ_Edition_Wise_Wastage_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
