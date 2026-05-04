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

    kg_cols = [
        "White Kg",
        "Scum Kg",
        "Cut-off Kg",
        "Registration Kg",
        "Density Variation Kg",
        "Other Kg",
        "Pasting Kg",
        "Total Waste Kg",
        "Print Order",
    ]

    for col in kg_cols:
        out[col] = to_num(out[col])

    # MT conversion for display/reporting
    out["White MT"] = out["White Kg"] / 1000
    out["Scum MT"] = out["Scum Kg"] / 1000
    out["Cut-off MT"] = out["Cut-off Kg"] / 1000
    out["Registration MT"] = out["Registration Kg"] / 1000
    out["Density Variation MT"] = out["Density Variation Kg"] / 1000
    out["Other MT"] = out["Other Kg"] / 1000
    out["Pasting MT"] = out["Pasting Kg"] / 1000
    out["Total Waste MT"] = out["Total Waste Kg"] / 1000

    return out


def round_display(df):
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            if "MT" in col:
                out[col] = out[col].round(3)
            elif "%" in col:
                out[col] = out[col].round(2)
            else:
                out[col] = out[col].round(0)
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

    default_index = available_sheets.index("AIR") if "AIR" in available_sheets else 0

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
        start_date = st.date_input(
            "From Date",
            min_date,
            min_value=min_date,
            max_value=max_date
        )

    with col2:
        end_date = st.date_input(
            "To Date",
            max_date,
            min_value=min_date,
            max_value=max_date
        )

    filtered = df[
        (df["Edition Date"].dt.date >= start_date) &
        (df["Edition Date"].dt.date <= end_date)
    ].copy()

    if filtered.empty:
        st.warning("No data found for selected date range.")
        return

    total_waste_mt = filtered["Total Waste MT"].sum()
    total_print_order = filtered["Print Order"].sum()
    total_editions = len(filtered)
    avg_waste_mt = total_waste_mt / total_editions if total_editions else 0

    st.markdown("## Executive Dashboard")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Editions", f"{total_editions:,}")
    k2.metric("Total Waste", f"{total_waste_mt:,.3f} MT")
    k3.metric("Total Print Order", f"{total_print_order:,.0f}")
    k4.metric("Avg Waste / Edition", f"{avg_waste_mt:,.3f} MT")

    st.markdown("## Key Insight")

    top_segment = {
        "White MT": filtered["White MT"].sum(),
        "Scum MT": filtered["Scum MT"].sum(),
        "Cut-off MT": filtered["Cut-off MT"].sum(),
        "Registration MT": filtered["Registration MT"].sum(),
        "Density Variation MT": filtered["Density Variation MT"].sum(),
        "Other MT": filtered["Other MT"].sum(),
        "Pasting MT": filtered["Pasting MT"].sum(),
    }

    top_segment_name = max(top_segment, key=top_segment.get)
    st.info(
        f"Highest waste segment is **{top_segment_name}** with "
        f"**{top_segment[top_segment_name]:,.3f} MT**."
    )

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
            "Waste MT": list(top_segment.values())
        }).sort_values("Waste MT", ascending=False)

        st.dataframe(round_display(segment_df), use_container_width=True, hide_index=True)

        fig_seg = px.bar(
            segment_df,
            x="Waste Segment",
            y="Waste MT",
            text="Waste MT",
            title="Waste by Segment (MT)"
        )
        fig_seg.update_traces(texttemplate="%{text:.3f}")
        st.plotly_chart(fig_seg, use_container_width=True)

        fig_pie = px.pie(
            segment_df,
            values="Waste MT",
            names="Waste Segment",
            hole=0.45,
            title="Waste Segment Share"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.markdown("## Edition Wise Waste Performance")

        edition_summary = (
            filtered.groupby(["Edition", "Edition Name"], dropna=False)["Total Waste MT"]
            .sum()
            .reset_index()
            .sort_values("Total Waste MT", ascending=False)
        )

        st.dataframe(round_display(edition_summary.head(50)), use_container_width=True, hide_index=True)

        fig_edition = px.bar(
            edition_summary.head(20),
            x="Total Waste MT",
            y="Edition Name",
            orientation="h",
            text="Total Waste MT",
            title="Top 20 Editions by Waste MT"
        )
        fig_edition.update_traces(texttemplate="%{text:.3f}")
        st.plotly_chart(fig_edition, use_container_width=True)

    with tab3:
        st.markdown("## Machine / Start Type Analysis")

        machine_summary = (
            filtered.groupby("Machine", dropna=False)["Total Waste MT"]
            .sum()
            .reset_index()
            .sort_values("Total Waste MT", ascending=False)
        )

        start_summary = (
            filtered.groupby("Type of Start", dropna=False)["Total Waste MT"]
            .sum()
            .reset_index()
            .sort_values("Total Waste MT", ascending=False)
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### Machine Wise Waste")
            st.dataframe(round_display(machine_summary), use_container_width=True, hide_index=True)

        with c2:
            st.markdown("### Start Type Wise Waste")
            st.dataframe(round_display(start_summary), use_container_width=True, hide_index=True)

        fig_machine = px.bar(
            machine_summary,
            x="Machine",
            y="Total Waste MT",
            text="Total Waste MT",
            title="Machine Wise Waste MT"
        )
        fig_machine.update_traces(texttemplate="%{text:.3f}")
        st.plotly_chart(fig_machine, use_container_width=True)

        fig_start = px.bar(
            start_summary,
            x="Type of Start",
            y="Total Waste MT",
            text="Total Waste MT",
            title="Start Type Wise Waste MT"
        )
        fig_start.update_traces(texttemplate="%{text:.3f}")
        st.plotly_chart(fig_start, use_container_width=True)

    with tab4:
        st.markdown("## GNP/SNP and Complexity Analysis")

        gnp_summary = (
            filtered.groupby("GNP/SNP", dropna=False)["Total Waste MT"]
            .sum()
            .reset_index()
            .sort_values("Total Waste MT", ascending=False)
        )

        complexity_summary = (
            filtered.groupby("Complexity", dropna=False)["Total Waste MT"]
            .sum()
            .reset_index()
            .sort_values("Total Waste MT", ascending=False)
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### GNP/SNP Wise Waste")
            st.dataframe(round_display(gnp_summary), use_container_width=True, hide_index=True)

        with c2:
            st.markdown("### Complexity Wise Waste")
            st.dataframe(round_display(complexity_summary), use_container_width=True, hide_index=True)

        fig_gnp = px.bar(
            gnp_summary,
            x="GNP/SNP",
            y="Total Waste MT",
            text="Total Waste MT",
            title="GNP/SNP Wise Waste MT"
        )
        fig_gnp.update_traces(texttemplate="%{text:.3f}")
        st.plotly_chart(fig_gnp, use_container_width=True)

        fig_complexity = px.bar(
            complexity_summary,
            x="Complexity",
            y="Total Waste MT",
            text="Total Waste MT",
            title="Complexity Wise Waste MT"
        )
        fig_complexity.update_traces(texttemplate="%{text:.3f}")
        st.plotly_chart(fig_complexity, use_container_width=True)

    with tab5:
        st.markdown("## Download Report")

        output = BytesIO()

        export_cols = [
            "Edition Date",
            "Edition",
            "Edition Name",
            "Print Order",
            "Main/Supplement",
            "Machine",
            "Folder",
            "GNP/SNP",
            "Complexity",
            "Type of Start",
            "White MT",
            "Scum MT",
            "Cut-off MT",
            "Registration MT",
            "Density Variation MT",
            "Other MT",
            "Pasting MT",
            "Total Waste MT",
        ]

        export_data = filtered[export_cols].copy()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            round_display(export_data).to_excel(writer, index=False, sheet_name="Filtered Data")
            round_display(segment_df).to_excel(writer, index=False, sheet_name="Waste Segment")
            round_display(edition_summary).to_excel(writer, index=False, sheet_name="Edition Summary")
            round_display(machine_summary).to_excel(writer, index=False, sheet_name="Machine Summary")
            round_display(start_summary).to_excel(writer, index=False, sheet_name="Start Type Summary")
            round_display(gnp_summary).to_excel(writer, index=False, sheet_name="GNP SNP Summary")
            round_display(complexity_summary).to_excel(writer, index=False, sheet_name="Complexity Summary")

        st.download_button(
            "📥 Download Edition Wise Wastage Report",
            data=output.getvalue(),
            file_name="PressIQ_Edition_Wise_Wastage_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
