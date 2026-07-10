import html
from pathlib import Path
from textwrap import dedent

import pandas as pd
import streamlit as st


# =========================================================
# FILE PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCT_MASTER_PATH = (
    PROJECT_ROOT
    / "backend_data"
    / "product_master.xlsx"
)


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(value):
    """
    Convert any value into clean uppercase text for matching.
    """

    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def safe_display_text(value, fallback="—"):
    """
    Convert a value into safe text for HTML display.
    """

    if pd.isna(value):
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return html.escape(text)


def find_column(df, possible_names):
    """
    Find a production-report column using a list of possible names.

    This protects the module from small differences such as:
    In-Charge / Incharge / Machine In-Charge.
    """

    normalized_columns = {
        clean_text(column): column
        for column in df.columns
    }

    for name in possible_names:
        normalized_name = clean_text(name)

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    return None


def format_indian_number(value):
    """
    Format numbers using Indian comma grouping.

    Examples:
    25090  -> 25,090
    114850 -> 1,14,850
    """

    if pd.isna(value):
        return "—"

    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return "—"

    negative = number < 0
    number = abs(number)

    number_text = str(number)

    if len(number_text) <= 3:
        formatted = number_text
    else:
        last_three = number_text[-3:]
        remaining = number_text[:-3]

        groups = []

        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        if remaining:
            groups.insert(0, remaining)

        formatted = ",".join(groups + [last_three])

    if negative:
        formatted = f"-{formatted}"

    return formatted


def format_report_date(value):
    """
    Format the issue date as DD/MM/YYYY.
    """

    if pd.isna(value):
        return "—"

    try:
        parsed_date = pd.to_datetime(value)
        return parsed_date.strftime("%d/%m/%Y")
    except Exception:
        return safe_display_text(value)


# =========================================================
# PRODUCT MASTER
# =========================================================

@st.cache_data(show_spinner=False)
def load_product_master(file_modified_time):
    """
    Read and prepare the Product Master file.

    file_modified_time is included so Streamlit reloads the
    master automatically whenever the Excel file changes.
    """

    if not PRODUCT_MASTER_PATH.exists():
        return pd.DataFrame(), (
            "Product Master file was not found at:\n\n"
            "backend_data/product_master.xlsx"
        )

    try:
        master_df = pd.read_excel(
            PRODUCT_MASTER_PATH,
            sheet_name="Product_Master"
        )
    except Exception as error:
        return pd.DataFrame(), (
            f"Unable to read the Product_Master sheet: {error}"
        )

    required_columns = [
        "Priority",
        "Match Text",
        "Display Code",
        "Report Type",
        "Status",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in master_df.columns
    ]

    if missing_columns:
        return pd.DataFrame(), (
            "Missing columns in Product Master: "
            + ", ".join(missing_columns)
        )

    master_df = master_df.copy()

    master_df["Priority"] = pd.to_numeric(
        master_df["Priority"],
        errors="coerce"
    ).fillna(9999)

    master_df["Match Text Clean"] = (
        master_df["Match Text"]
        .apply(clean_text)
    )

    master_df["Display Code Clean"] = (
        master_df["Display Code"]
        .apply(lambda value: str(value).strip() if not pd.isna(value) else "")
    )

    master_df["Report Type Clean"] = (
        master_df["Report Type"]
        .apply(clean_text)
    )

    master_df["Status Clean"] = (
        master_df["Status"]
        .apply(clean_text)
    )

    master_df = master_df[
        master_df["Status Clean"].isin(
            ["ACTIVE", "YES", "Y", "TRUE", "1"]
        )
    ].copy()

    master_df = master_df[
        master_df["Match Text Clean"] != ""
    ].copy()

    master_df = master_df[
        master_df["Display Code Clean"] != ""
    ].copy()

    master_df = master_df.sort_values(
        by=["Priority"],
        ascending=True
    ).reset_index(drop=True)

    return master_df, None


def get_product_master():
    """
    Load Product Master using its modification time.
    """

    if not PRODUCT_MASTER_PATH.exists():
        return pd.DataFrame(), (
            "Product Master file was not found at:\n\n"
            "backend_data/product_master.xlsx"
        )

    modified_time = PRODUCT_MASTER_PATH.stat().st_mtime

    return load_product_master(modified_time)


def detect_product_code(
    product_name,
    edition_name,
    report_type,
    master_df
):
    """
    Detect the product display code.

    Matching approach:
    1. Filter Product Master by Main or Supplement.
    2. Follow Priority order.
    3. Search in both Products and Edition.
    4. If no match is found, show the original full name.
    """

    product_text = clean_text(product_name)
    edition_text = clean_text(edition_name)

    combined_search_text = (
        f"{product_text} {edition_text}"
    ).strip()

    report_type_clean = clean_text(report_type)

    relevant_master = master_df[
        master_df["Report Type Clean"] == report_type_clean
    ].copy()

    for _, master_row in relevant_master.iterrows():
        match_text = master_row["Match Text Clean"]

        if match_text and match_text in combined_search_text:
            display_code = str(
                master_row["Display Code"]
            ).strip()

            return {
                "auto_code": display_code,
                "final_code": display_code,
                "match_status": "🟢 Auto Matched",
                "matched_text": str(
                    master_row["Match Text"]
                ).strip(),
            }

    product_fallback = (
        str(product_name).strip()
        if not pd.isna(product_name)
        and str(product_name).strip()
        else ""
    )

    edition_fallback = (
        str(edition_name).strip()
        if not pd.isna(edition_name)
        and str(edition_name).strip()
        else ""
    )

    fallback_name = (
        product_fallback
        or edition_fallback
        or "Unnamed Product"
    )

    return {
        "auto_code": fallback_name,
        "final_code": fallback_name,
        "match_status": "🟡 Review Required",
        "matched_text": "Not Found in Product Master",
    }


# =========================================================
# PREMIUM WORKING TABLE
# =========================================================

def render_premium_working_table(
    table_df,
    selected_report
):
    """
    Render the working table using custom HTML and CSS.

    This is the premium display table, not a generic
    Streamlit dataframe.
    """

    if table_df.empty:
        st.warning(
            f"No {selected_report} records are available."
        )
        return

    st.markdown(
        """
        <style>

        .avpw-section {
            margin-top: 24px;
            margin-bottom: 30px;
        }

        .avpw-heading-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            margin-bottom: 14px;
        }

        .avpw-heading-title {
            color: #0f172a;
            font-size: 21px;
            font-weight: 850;
            line-height: 1.2;
        }

        .avpw-heading-subtitle {
            color: #64748b;
            font-size: 13px;
            margin-top: 5px;
        }

        .avpw-report-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 13px;
            border-radius: 999px;
            background: #eaf2ff;
            border: 1px solid #cbdcf7;
            color: #173f70;
            font-size: 12px;
            font-weight: 800;
            white-space: nowrap;
        }

        .avpw-report-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12);
        }

        .avpw-table-card {
            background: #ffffff;
            border: 1px solid #d9e2ef;
            border-radius: 18px;
            overflow: hidden;
            box-shadow:
                0 14px 34px rgba(15, 23, 42, 0.07),
                0 3px 10px rgba(15, 23, 42, 0.04);
        }

        .avpw-table-scroll {
            width: 100%;
            max-height: 570px;
            overflow-x: auto;
            overflow-y: auto;
        }

        table.avpw-table {
            width: 100%;
            min-width: 1320px;
            border-collapse: separate;
            border-spacing: 0;
            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        table.avpw-table thead th {
            position: sticky;
            top: 0;
            z-index: 4;
            padding: 15px 12px;
            background: linear-gradient(
                135deg,
                #071a36 0%,
                #0b2c59 55%,
                #123f73 100%
            );
            color: #ffffff;
            border-right: 1px solid rgba(255, 255, 255, 0.14);
            text-align: center;
            vertical-align: middle;
            font-size: 11px;
            font-weight: 850;
            line-height: 1.35;
            letter-spacing: 0.38px;
            text-transform: uppercase;
            white-space: nowrap;
        }

        table.avpw-table thead th:last-child {
            border-right: none;
        }

        table.avpw-table tbody td {
            padding: 14px 12px;
            background: #ffffff;
            color: #263548;
            border-right: 1px solid #edf1f6;
            border-bottom: 1px solid #e7edf4;
            text-align: center;
            vertical-align: middle;
            font-size: 13px;
            font-weight: 600;
        }

        table.avpw-table tbody tr:nth-child(even) td {
            background: #f8fafc;
        }

        table.avpw-table tbody tr:hover td {
            background: #f0f6ff;
        }

        table.avpw-table tbody tr:last-child td {
            border-bottom: none;
        }

        table.avpw-table tbody td:last-child {
            border-right: none;
        }

        .avpw-machine-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 35px;
            height: 29px;
            padding: 0 10px;
            border-radius: 8px;
            background: #dbeafe;
            border: 1px solid #bfdbfe;
            color: #1e3a8a;
            font-size: 12px;
            font-weight: 900;
        }

        .avpw-publication-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 68px;
            padding: 7px 11px;
            border-radius: 9px;
            background: #eef2ff;
            border: 1px solid #d8ddff;
            color: #3730a3;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: 0.2px;
        }

        .avpw-po-cell {
            color: #7c2d12 !important;
            background: #fff7ed !important;
            font-weight: 850 !important;
        }

        .avpw-predicted-cell {
            color: #166534 !important;
            background: #f0fdf4 !important;
            font-weight: 850 !important;
        }

        .avpw-actual-cell {
            color: #075985 !important;
            background: #f0f9ff !important;
            font-weight: 850 !important;
        }

        .avpw-extra-cell {
            color: #9a3412 !important;
            background: #fff7ed !important;
            font-weight: 850 !important;
        }

        .avpw-reason-cell {
            min-width: 290px;
            max-width: 360px;
            text-align: left !important;
            white-space: normal;
            line-height: 1.45;
            color: #475569 !important;
            font-weight: 500 !important;
        }

        .avpw-empty-value {
            color: #94a3b8;
            font-weight: 750;
        }

        .avpw-review-note {
            margin-top: 12px;
            padding: 10px 13px;
            border-radius: 10px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 12px;
        }

        @media (max-width: 900px) {

            .avpw-heading-row {
                flex-direction: column;
                align-items: flex-start;
            }

            .avpw-table-card {
                border-radius: 14px;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    html_rows = []

    for _, row in table_df.iterrows():
        edition_date = format_report_date(
            row.get("Issue Date")
        )

        machine = safe_display_text(
            row.get("Machine")
        )

        machine_incharge = safe_display_text(
            row.get("Machine In-charge")
        )

        publication = safe_display_text(
            row.get("Final Code")
        )

        po = format_indian_number(
            row.get("PO")
        )

        actual_waste = format_indian_number(
            row.get("Actual Waste")
        )

        predicted_waste = row.get("Predicted Waste")

        if (
            pd.isna(predicted_waste)
            or str(predicted_waste).strip() == ""
        ):
            predicted_display = (
                '<span class="avpw-empty-value">—</span>'
            )

            extra_display = (
                '<span class="avpw-empty-value">—</span>'
            )

            reason_display = "NA"

        else:
            try:
                predicted_number = float(predicted_waste)

                actual_number = pd.to_numeric(
                    row.get("Actual Waste"),
                    errors="coerce"
                )

                if pd.isna(actual_number):
                    actual_number = 0

                extra_number = max(
                    float(actual_number) - predicted_number,
                    0
                )

                predicted_display = format_indian_number(
                    predicted_number
                )

                extra_display = format_indian_number(
                    extra_number
                )

                if extra_number <= 0:
                    reason_display = "NA"
                else:
                    entered_reason = str(
                        row.get(
                            "Reason for Extra Waste",
                            ""
                        )
                    ).strip()

                    reason_display = (
                        entered_reason
                        if entered_reason
                        and entered_reason.upper() != "NAN"
                        else "Reason Required"
                    )

            except (TypeError, ValueError):
                predicted_display = (
                    '<span class="avpw-empty-value">—</span>'
                )

                extra_display = (
                    '<span class="avpw-empty-value">—</span>'
                )

                reason_display = "NA"

        reason_display = safe_display_text(
            reason_display,
            fallback="NA"
        )

        html_rows.append(
            f"""
            <tr>
                <td>{edition_date}</td>

                <td>
                    <span class="avpw-machine-badge">
                        {machine}
                    </span>
                </td>

                <td>{machine_incharge}</td>

                <td>
                    <span class="avpw-publication-badge">
                        {publication}
                    </span>
                </td>

                <td class="avpw-po-cell">
                    {po}
                </td>

                <td class="avpw-predicted-cell">
                    {predicted_display}
                </td>

                <td class="avpw-actual-cell">
                    {actual_waste}
                </td>

                <td class="avpw-extra-cell">
                    {extra_display}
                </td>

                <td class="avpw-reason-cell">
                    {reason_display}
                </td>
            </tr>
            """
        )

    selected_report_safe = safe_display_text(
        selected_report
    )

   working_table_html = dedent(f"""
    <div class="avpw-section">

        <div class="avpw-heading-row">

            <div>
                <div class="avpw-heading-title">
                    Production Working Table
                </div>

                <div class="avpw-heading-subtitle">
                    Review production details before preparing the final report.
                </div>
            </div>

            <div class="avpw-report-badge">
                <span class="avpw-report-dot"></span>
                {selected_report_safe} Report
            </div>

        </div>

        <div class="avpw-table-card">

            <div class="avpw-table-scroll">

                <table class="avpw-table">

                    <thead>
                        <tr>
                            <th>Edition Date</th>
                            <th>Machine</th>
                            <th>Machine In-charge</th>
                            <th>Publication</th>
                            <th>PO</th>
                            <th>Predicted Waste</th>
                            <th>Actual Waste</th>
                            <th>Extra Waste</th>
                            <th>Reason for Extra Waste</th>
                        </tr>
                    </thead>

                    <tbody>
                        {''.join(html_rows)}
                    </tbody>

                </table>

            </div>

        </div>

        <div class="avpw-review-note">
            Predicted Waste is intentionally blank until the prediction criteria are finalized.
        </div>

    </div>
    """)

    st.markdown(
        working_table_html,
        unsafe_allow_html=True
    )


# =========================================================
# MAIN MODULE
# =========================================================

def run_actual_vs_predicted_waste():

    st.markdown(
        "## Actual vs Predicted Waste"
    )

    st.caption(
        "Product Master Matching Engine and Production Working Table"
    )

    uploaded_file = st.file_uploader(
        "Upload Production Report",
        type=["xlsx", "xls"],
        key="actual_vs_predicted_waste_upload"
    )

    if uploaded_file is None:
        st.info(
            "Please upload the Production Report."
        )
        return

    master_df, master_error = get_product_master()

    if master_error:
        st.error(master_error)
        return

    if master_df.empty:
        st.error(
            "Product Master contains no active matching rules."
        )
        return

    try:
        production_df = pd.read_excel(
            uploaded_file,
            sheet_name="General"
        )
    except Exception as error:
        st.error(
            f"Unable to read the General sheet: {error}"
        )
        return

    # -----------------------------------------------------
    # FIND REQUIRED PRODUCTION REPORT COLUMNS
    # -----------------------------------------------------

    issue_date_col = find_column(
        production_df,
        [
            "Issue Date",
            "Edition Date",
        ]
    )

    products_col = find_column(
        production_df,
        [
            "Products",
            "Product Name",
            "Product",
        ]
    )

    edition_col = find_column(
        production_df,
        [
            "Edition",
            "Edition Name",
        ]
    )

    report_type_col = find_column(
        production_df,
        [
            "Main/Supplement",
            "Main / Supplement",
            "Main Supplement",
        ]
    )

    machine_col = find_column(
        production_df,
        [
            "Machine",
            "Machine Name",
        ]
    )

    print_order_col = find_column(
        production_df,
        [
            "Print Order",
            "PO",
            "PrintOrder",
        ]
    )

    waste_col = find_column(
        production_df,
        [
            "Waste",
            "Actual Waste",
            "Total Waste",
        ]
    )

    incharge_col = find_column(
        production_df,
        [
            "In-Charge",
            "Incharge",
            "Machine In-Charge",
            "Machine Incharge",
            "Shift In-Charge",
        ]
    )

    required_column_map = {
        "Issue Date": issue_date_col,
        "Products": products_col,
        "Edition": edition_col,
        "Main/Supplement": report_type_col,
        "Machine": machine_col,
        "Print Order": print_order_col,
        "Waste": waste_col,
    }

    missing_columns = [
        expected_name
        for expected_name, actual_name
        in required_column_map.items()
        if actual_name is None
    ]

    if missing_columns:
        st.error(
            "Missing columns in Production Report: "
            + ", ".join(missing_columns)
        )

        with st.expander(
            "Show available General sheet columns"
        ):
            st.write(
                list(production_df.columns)
            )

        return

    production_df = production_df.copy()

    production_df["_Report Type Clean"] = (
        production_df[report_type_col]
        .apply(clean_text)
    )

    main_df = production_df[
        production_df["_Report Type Clean"] == "MAIN"
    ].copy()

    supplement_df = production_df[
        production_df["_Report Type Clean"] == "SUPPLEMENT"
    ].copy()

    st.success(
        "Production Report loaded successfully."
    )

    metric_col_1, metric_col_2 = st.columns(2)

    with metric_col_1:
        st.metric(
            "Main Editions",
            len(main_df)
        )

    with metric_col_2:
        st.metric(
            "Supplement Editions",
            len(supplement_df)
        )

    selected_report = st.radio(
        "Select Report Type",
        options=[
            "Main",
            "Supplement",
        ],
        horizontal=True,
        key="actual_vs_predicted_report_type"
    )

    if selected_report == "Main":
        selected_df = main_df.copy()
    else:
        selected_df = supplement_df.copy()

    if selected_df.empty:
        st.warning(
            f"No {selected_report} records were found."
        )
        return

    # -----------------------------------------------------
    # BUILD PRODUCT MATCHING RESULT
    # -----------------------------------------------------

    output_rows = []

    for source_index, row in selected_df.iterrows():
        product_name = row.get(
            products_col,
            ""
        )

        edition_name = row.get(
            edition_col,
            ""
        )

        detected_product = detect_product_code(
            product_name=product_name,
            edition_name=edition_name,
            report_type=selected_report,
            master_df=master_df
        )

        machine_incharge = (
            row.get(incharge_col, "—")
            if incharge_col
            else "—"
        )

        output_rows.append(
            {
                "Row ID": str(source_index),
                "Status": detected_product[
                    "match_status"
                ],
                "Issue Date": row.get(
                    issue_date_col
                ),
                "Machine": row.get(
                    machine_col
                ),
                "Machine In-charge": machine_incharge,
                "Product Name": product_name,
                "Edition": edition_name,
                "Auto Code": detected_product[
                    "auto_code"
                ],
                "Final Code": detected_product[
                    "final_code"
                ],
                "Matched Text": detected_product[
                    "matched_text"
                ],
                "PO": pd.to_numeric(
                    row.get(print_order_col),
                    errors="coerce"
                ),
                "Actual Waste": pd.to_numeric(
                    row.get(waste_col),
                    errors="coerce"
                ),
                "Predicted Waste": pd.NA,
                "Extra Waste": pd.NA,
                "Reason for Extra Waste": "NA",
            }
        )

    result_df = pd.DataFrame(
        output_rows
    )

    review_count = int(
        (
            result_df["Status"]
            == "🟡 Review Required"
        ).sum()
    )

    if review_count > 0:
        st.warning(
            f"{review_count} product(s) were not found in "
            "Product Master. Review the yellow rows and "
            "correct Final Code if required."
        )
    else:
        st.success(
            "All products matched successfully from Product Master."
        )

    # -----------------------------------------------------
    # PRODUCT CODE REVIEW
    # -----------------------------------------------------

    st.markdown(
        "### Product Code Review"
    )

    st.caption(
        "Only Final Code is editable. This review table will later "
        "be replaced by the row-level premium edit panel."
    )

    editor_columns = [
        "Status",
        "Issue Date",
        "Machine",
        "Product Name",
        "Edition",
        "Auto Code",
        "Final Code",
        "Matched Text",
    ]

    edited_code_df = st.data_editor(
        result_df[editor_columns],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=[
            "Status",
            "Issue Date",
            "Machine",
            "Product Name",
            "Edition",
            "Auto Code",
            "Matched Text",
        ],
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                width="medium"
            ),
            "Issue Date": st.column_config.DateColumn(
                "Issue Date",
                format="DD/MM/YYYY",
                disabled=True
            ),
            "Machine": st.column_config.TextColumn(
                "Machine",
                disabled=True
            ),
            "Product Name": st.column_config.TextColumn(
                "Product Name",
                width="large",
                disabled=True
            ),
            "Edition": st.column_config.TextColumn(
                "Edition",
                width="large",
                disabled=True
            ),
            "Auto Code": st.column_config.TextColumn(
                "Auto Code",
                disabled=True
            ),
            "Final Code": st.column_config.TextColumn(
                "Final Code",
                help=(
                    "Change this only when the automatic "
                    "publication code is incorrect."
                ),
                required=True
            ),
            "Matched Text": st.column_config.TextColumn(
                "Matched Text",
                width="large",
                disabled=True
            ),
        },
        key=f"product_code_review_{selected_report}"
    )

    # -----------------------------------------------------
    # COPY EDITED FINAL CODES BACK INTO RESULT
    # -----------------------------------------------------

    final_result_df = result_df.copy()

    final_result_df["Final Code"] = (
        edited_code_df["Final Code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .values
    )

    final_result_df["Status"] = final_result_df.apply(
        lambda row: (
            "✏️ Edited"
            if clean_text(row["Final Code"])
            != clean_text(row["Auto Code"])
            else row["Status"]
        ),
        axis=1
    )

    # -----------------------------------------------------
    # PREMIUM WORKING TABLE
    # -----------------------------------------------------

    render_premium_working_table(
        final_result_df,
        selected_report
    )
