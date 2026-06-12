import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta


REQUIRED_SHEETS = [
    "General",
    "Down Time",
    "Book Wise Details",
]


LPRS_RULES = {
    "TOIM_MP_1": "00:00",
    "MTM_MP_1": "23:15",
    "TOITH_MP_1": "00:30",
    "TOIVP_MP_1": "00:15",
}


def find_column(df, possible_names):
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
    if pd.isna(value):
        return ""

    try:
        value = pd.to_datetime(value)
        return value.strftime("%H:%M hrs")
    except Exception:
        return str(value)


def format_minutes(value):
    if pd.isna(value):
        return "0 mins"

    try:
        value = float(value)
        return f"{int(round(value))} mins"
    except Exception:
        return f"{value} mins"


def clean_complexity(value):
    """
    Example:
    C4-High Pagination (SNP) + Multiple Innovations
    becomes:
    High Pagination (SNP) + Multiple Innovations
    """
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if "-" in text:
        return text.split("-", 1)[1].strip()

    return text


def parse_time_to_minutes(value):
    """
    Converts time value to minutes from midnight.
    """
    if pd.isna(value):
        return None

    try:
        dt = pd.to_datetime(value)
        return dt.hour * 60 + dt.minute
    except Exception:
        pass

    try:
        text = str(value).strip().replace("hrs", "").strip()
        parts = text.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        return hour * 60 + minute
    except Exception:
        return None


def calculate_page_release_delay(product_name, lpr_value):
    """
    Calculates delay based on product-wise LPRS rule.
    Handles midnight crossing also.
    """
    product_text = str(product_name).strip()

    if product_text not in LPRS_RULES:
        return "", "", ""

    lprs_text = LPRS_RULES[product_text]

    lpr_minutes = parse_time_to_minutes(lpr_value)
    lprs_minutes = parse_time_to_minutes(lprs_text)

    if lpr_minutes is None or lprs_minutes is None:
        return format_time(lpr_value), f"{lprs_text} hrs", ""

    delay = lpr_minutes - lprs_minutes

    if delay < 0:
        delay += 24 * 60

    return format_time(lpr_value), f"{lprs_text} hrs", f"{delay} mins"


def identify_last_finished_main_edition(general_df):
    main_supp_col = find_column(
        general_df,
        ["Main/Supplement", "Main Supplement", "Main_Supplement"]
    )

    production_end_col = find_column(
        general_df,
        ["Last Production End", "Production End"]
    )

    production_end_date_col = find_column(
        general_df,
        ["Production End Date", "Last Production End Date"]
    )

    product_name_col = find_column(
        general_df,
        ["Product Name", "Edition", "Products", "Product"]
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
        "Production End": production_end_col,
        "Production End Date": production_end_date_col,
        "Product Name / Products": product_name_col,
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

    main_df["_production_end_datetime"] = pd.to_datetime(
        main_df[production_end_date_col].astype(str).str.strip()
        + " "
        + main_df[production_end_col].astype(str).str.strip(),
        errors="coerce",
        dayfirst=True
    )

    main_df = main_df.dropna(subset=["_production_end_datetime"])

    if main_df.empty:
        return pd.DataFrame(), []

    latest_finish_datetime = main_df["_production_end_datetime"].max()

    last_finished_df = main_df[
        main_df["_production_end_datetime"] == latest_finish_datetime
    ].copy()

    return last_finished_df, []


def get_bookwise_info(bookwise_df, runid):
    runid_col = find_column(
        bookwise_df,
        ["Runid", "Run ID", "RunId"]
    )

    edition_col = find_column(
        bookwise_df,
        ["Edition", "Edition Name"]
    )

    last_tiff_col = find_column(
        bookwise_df,
        ["Last Tiff", "Last Tiff Edition", "LPR"]
    )

    complexity_col = find_column(
        bookwise_df,
        ["Complexities", "Complexity"]
    )

    required_columns = {
        "Runid": runid_col,
        "Edition": edition_col,
        "Last Tiff Edition": last_tiff_col,
        "Complexities": complexity_col,
    }

    missing_columns = [
        name for name, col in required_columns.items()
        if col is None
    ]

    if missing_columns:
        return None, missing_columns

    matched_df = bookwise_df[
        bookwise_df[runid_col].astype(str).str.strip() == str(runid).strip()
    ]

    if matched_df.empty:
        return None, []

    row = matched_df.iloc[0]

    return {
        "edition": row[edition_col],
        "last_tiff": row[last_tiff_col],
        "complexity": clean_complexity(row[complexity_col]),
    }, []


def get_issue_date(last_finished_df):
    production_end_date_col = find_column(
        last_finished_df,
        ["Production End Date", "Last Production End Date"]
    )

    if production_end_date_col is None:
        return ""

    try:
        latest_date = pd.to_datetime(
            last_finished_df[production_end_date_col].iloc[0],
            dayfirst=True
        )
        return latest_date.strftime("%d-%m-%Y")
    except Exception:
        return ""


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

        product_name_col = find_column(
            last_finished_df,
            ["Product Name", "Edition", "Products", "Product"]
        )

        machine_col = find_column(
            last_finished_df,
            ["Machine", "Machine Name"]
        )

        downtime_col = find_column(
            last_finished_df,
            ["Total Downtime", "Total DownTime", "Downtime"]
        )

        production_end_col = find_column(
            last_finished_df,
            ["Last Production End", "Production End"]
        )

        runid_col = find_column(
            last_finished_df,
            ["Runid", "Run ID", "RunId"]
        )

        issue_date = get_issue_date(last_finished_df)

        report_lines = []
        report_lines.append(f"Airoli Plant Issue Dated: {issue_date}")
        report_lines.append("")

        first_lpr = ""
        first_lprs = ""
        first_delay = ""

        for _, row in last_finished_df.iterrows():
            runid = row[runid_col]
            product_name = row[product_name_col]

            book_info, book_missing_columns = get_bookwise_info(bookwise_df, runid)

            if book_missing_columns:
                st.error("Required column missing in Book Wise Details sheet.")
                st.write("Missing column(s):")
                st.write(book_missing_columns)
                return

            if book_info is None:
                edition_name = str(row[product_name_col])
                complexity = "Bookwise Details missing"
                lpr = ""
                lprs = ""
                delay = ""
            else:
                edition_name = book_info["edition"]
                complexity = book_info["complexity"]
                lpr, lprs, delay = calculate_page_release_delay(
                    product_name,
                    book_info["last_tiff"]
                )

            if first_lpr == "":
                first_lpr = lpr
                first_lprs = lprs
                first_delay = delay

            report_lines.append(f"Last Edition: {edition_name}")
            report_lines.append(f"Print Finish: {format_time(row[production_end_col])}")
            report_lines.append(f"Machine: {row[machine_col]}")
            report_lines.append(f"Total Downtime: {format_minutes(row[downtime_col])}")
            report_lines.append(f"Complexity: {complexity}")
            report_lines.append("")

        report_lines.append("Page Release Delay:")
        report_lines.append(f"LPR: {first_lpr}")
        report_lines.append(f"LPRS: {first_lprs}")
        report_lines.append(f"Delay: {first_delay}")
        report_lines.append("")

        report_text = "\n".join(report_lines)

        st.markdown("### PF Delay Report Preview")

        st.text_area(
            "Generated Report Text",
            value=report_text,
            height=450,
            key="pf_delay_report_text_preview"
        )

    except Exception as e:
        st.error("Unable to read uploaded Excel file.")
        st.exception(e)
