import streamlit as st
import pandas as pd


REQUIRED_SHEETS = [
    "General",
    "Down Time",
    "Book Wise Details",
]


def find_column(df, possible_names):
    """
    Finds a column from dataframe using possible column names.
    This helps because Excel column names may slightly vary.
    """
    df_columns_clean = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for name in possible_names:
        clean_name = name.strip().lower()
        if clean_name in df_columns_clean:
            return df_columns_clean[clean_name]

    return None


def format_time(value):
    """
    Converts Excel time/date value into HH:MM hrs format.
    """
    if pd.isna(value):
        return ""

    try:
        value = pd.to_datetime(value)
        return value.strftime("%H:%M hrs")
    except Exception:
        return str(value)


def format_minutes(value):
    """
    Converts downtime value into mins format.
    """
    if pd.isna(value):
        return "0 mins"

    try:
        value = float(value)
        return f"{int(round(value))} mins"
    except Exception:
        return f"{value} mins"


def identify_last_finished_main_edition(general_df):
    """
    Step 2 logic:
    - Filter Main editions
    - Find latest Last Production End / Production End
    - Return all rows matching latest finish time
    """

    main_supp_col = find_column(
        general_df,
        ["Main/Supplement", "Main Supplement", "Main_Supplement"]
    )

    production_end_col = find_column(
        general_df,
        ["Last Production End", "Production End"]
    )

    product_name_col = find_column(
        general_df,
        ["Product Name", "Products", "Product"]
    )

    machine_col = find_column(
        general_df,
        ["Machine", "Machine Name"]
    )

    downtime_col = find_column(
        general_df,
        ["Total Downtime", "Total DownTime", "Downtime"]
    )

    runid_col = find_column(
        general_df,
        ["Runid", "Run ID", "RunId"]
    )

    required_columns = {
        "Main/Supplement": main_supp_col,
        "Last Production End / Production End": production_end_col,
        "Product Name": product_name_col,
        "Machine": machine_col,
        "Total Downtime": downtime_col,
        "Runid": runid_col,
    }

    missing_columns = [
        name for name, col in required_columns.items()
        if col is None
    ]

    if missing_columns:
        return None, missing_columns

    main_df = general_df[
        general_df[main_supp_col].astype(str).str.strip().str.lower() == "main"
    ].copy()

    if main_df.empty:
        return pd.DataFrame(), []

    main_df[production_end_col] = pd.to_datetime(
        main_df[production_end_col],
        errors="coerce"
    )

    main_df = main_df.dropna(subset=[production_end_col])

    if main_df.empty:
        return pd.DataFrame(), []

    latest_finish_time = main_df[production_end_col].max()

    last_finished_df = main_df[
        main_df[production_end_col] == latest_finish_time
    ].copy()

    return last_finished_df, []


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

        st.success("File uploaded successfully.")

        last_finished_df, missing_columns = identify_last_finished_main_edition(general_df)

        if missing_columns:
            st.error("Required column missing in General sheet.")
            st.write("Missing column(s):")
            st.write(missing_columns)
            return

        if last_finished_df is None or last_finished_df.empty:
            st.warning("No Main edition records found with valid print finish time.")
            return

        product_name_col = find_column(last_finished_df, ["Product Name", "Products", "Product"])
        machine_col = find_column(last_finished_df, ["Machine", "Machine Name"])
        downtime_col = find_column(last_finished_df, ["Total Downtime", "Total DownTime", "Downtime"])
        production_end_col = find_column(last_finished_df, ["Last Production End", "Production End"])

        st.markdown("### PF Delay Report Preview")

        report_lines = []
        report_lines.append("Last-finished Main Edition identified successfully.")
        report_lines.append("")

        for _, row in last_finished_df.iterrows():
            report_lines.append(f"Last Edition: {row[product_name_col]}")
            report_lines.append(f"Print Finish: {format_time(row[production_end_col])}")
            report_lines.append(f"Machine: {row[machine_col]}")
            report_lines.append(f"Total Downtime: {format_minutes(row[downtime_col])}")
            report_lines.append("")

        report_text = "\n".join(report_lines)

        st.text_area(
            "Generated Report Text",
            value=report_text,
            height=300,
            key="pf_delay_report_text_preview"
        )

    except Exception as e:
        st.error("Unable to read uploaded Excel file.")
        st.exception(e)
