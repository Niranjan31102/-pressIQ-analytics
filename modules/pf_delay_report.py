import streamlit as st
import pandas as pd


REQUIRED_SHEETS = [
    "General",
    "Down Time",
    "Book Wise Details",
]


def show_pf_delay_report():
    st.markdown("## PF Delay Report")
    st.caption("Generate Director-level Print Finished delay report from Production Excel file.")

    uploaded_file = st.file_uploader(
        "Upload Production Report Excel File",
        type=["xlsx", "xls"],
        key="pf_delay_report_uploader"
    )

    if uploaded_file is None:
        st.info("Upload the daily production Excel file to generate PF Delay Report.")
        return

    try:
        excel_file = pd.ExcelFile(uploaded_file)
        available_sheets = excel_file.sheet_names

        missing_sheets = [
            sheet for sheet in REQUIRED_SHEETS
            if sheet not in available_sheets
        ]

        if missing_sheets:
            st.error("Required sheet missing in uploaded file.")
            st.write("Missing sheet(s):")
            st.write(missing_sheets)
            return

        general_df = pd.read_excel(uploaded_file, sheet_name="General")
        downtime_df = pd.read_excel(uploaded_file, sheet_name="Down Time")
        bookwise_df = pd.read_excel(uploaded_file, sheet_name="Book Wise Details")

        st.success("File uploaded and required sheets found successfully.")

        with st.expander("Preview loaded data"):
            st.write("### General")
            st.dataframe(general_df.head(10), use_container_width=True)

            st.write("### Down Time")
            st.dataframe(downtime_df.head(10), use_container_width=True)

            st.write("### Book Wise Details")
            st.dataframe(bookwise_df.head(10), use_container_width=True)

        st.info("Next step: we will add logic to identify the last-finished Main edition.")

    except Exception as e:
        st.error("Unable to read uploaded Excel file.")
        st.exception(e)
