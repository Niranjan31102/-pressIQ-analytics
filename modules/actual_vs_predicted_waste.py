import os
import html
import pandas as pd
import streamlit as st


PRODUCT_MASTER_PATH = "backend_data/product_master.xlsx"


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def load_product_master():
    if not os.path.exists(PRODUCT_MASTER_PATH):
        st.error(
            "Product Master file not found. Please add this file:\n\n"
            "backend_data/product_master.xlsx"
        )
        return pd.DataFrame()

    try:
        master_df = pd.read_excel(
            PRODUCT_MASTER_PATH,
            sheet_name="Product_Master"
        )
    except Exception as e:
        st.error(f"Unable to read Product_Master sheet: {e}")
        return pd.DataFrame()

    required_cols = [
        "Priority",
        "Match Text",
        "Display Code",
        "Report Type",
        "Status"
    ]

    missing_cols = [c for c in required_cols if c not in master_df.columns]

    if missing_cols:
        st.error(f"Missing columns in Product Master: {missing_cols}")
        return pd.DataFrame()

    master_df = master_df.copy()

    master_df["Priority"] = pd.to_numeric(
        master_df["Priority"],
        errors="coerce"
    ).fillna(9999)

    master_df["Match Text Clean"] = master_df["Match Text"].apply(clean_text)
    master_df["Report Type Clean"] = master_df["Report Type"].apply(clean_text)
    master_df["Status Clean"] = master_df["Status"].apply(clean_text)

    master_df = master_df[
        master_df["Status Clean"].isin(["ACTIVE", "YES", "Y"])
    ].copy()

    master_df = master_df.sort_values("Priority")

    return master_df


def detect_product_code(product_name, edition_name, report_type, master_df):
    product_clean = clean_text(product_name)
    edition_clean = clean_text(edition_name)

    search_text = f"{product_clean} {edition_clean}".strip()

    report_type_clean = clean_text(report_type)

    filtered_master = master_df[
        master_df["Report Type Clean"] == report_type_clean
    ].copy()

    for _, row in filtered_master.iterrows():
        match_text = row["Match Text Clean"]

        if match_text and match_text in search_text:
            return {
                "auto_code": row["Display Code"],
                "final_code": row["Display Code"],
                "match_status": "🟢 Auto Matched",
                "matched_text": row["Match Text"],
            }

    fallback_name = product_name if str(product_name).strip() else edition_name

    return {
        "auto_code": fallback_name,
        "final_code": fallback_name,
        "match_status": "🟡 Review Required",
        "matched_text": "Not Found",
    }

def format_number(value):
    """
    Format production numbers using Indian-style comma grouping where possible.
    Example: 114850 becomes 1,14,850.
    """

    try:
        number = int(float(value))
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

    return f"-{formatted}" if negative else formatted


def format_report_date(value):
    """
    Convert report date to DD/MM/YYYY format.
    """

    if pd.isna(value):
        return "—"

    try:
        date_value = pd.to_datetime(value)
        return date_value.strftime("%d/%m/%Y")
    except Exception:
        return html.escape(str(value))


def render_premium_working_table(table_df, selected_report):
    """
    Display the Actual vs Predicted Waste working table
    using a custom PressIQ premium design.
    """

    if table_df.empty:
        st.warning(f"No {selected_report} records are available.")
        return

    st.markdown(
        """
        <style>
        .piq-working-section {
            margin-top: 18px;
            margin-bottom: 24px;
        }

        .piq-table-heading-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 14px;
        }

        .piq-table-title {
            font-size: 20px;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
        }

        .piq-table-subtitle {
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
        }

        .piq-report-badge {
            display: inline-flex;
            align-items: center;
            padding: 7px 12px;
            border-radius: 999px;
            background: #e8f0ff;
            color: #153e75;
            border: 1px solid #c9d8f5;
            font-size: 12px;
            font-weight: 800;
            white-space: nowrap;
        }

        .piq-table-shell {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 18px;
            overflow: hidden;
            box-shadow:
                0 12px 30px rgba(15, 23, 42, 0.07),
                0 2px 8px rgba(15, 23, 42, 0.04);
        }

        .piq-table-scroll {
            overflow-x: auto;
            overflow-y: auto;
            max-height: 560px;
        }

        .piq-premium-table {
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

        .piq-premium-table thead th {
            position: sticky;
            top: 0;
            z-index: 5;
            padding: 15px 12px;
            background: linear-gradient(135deg, #0b1f3a, #123866);
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.45px;
            line-height: 1.35;
            text-align: center;
            text-transform: uppercase;
            border-right: 1px solid rgba(255, 255, 255, 0.12);
            white-space: nowrap;
        }

        .piq-premium-table thead th:last-child {
            border-right: none;
        }

        .piq-premium-table tbody td {
            padding: 14px 12px;
            border-bottom: 1px solid #e9eef5;
            border-right: 1px solid #eef2f7;
            color: #263548;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            vertical-align: middle;
            background: #ffffff;
        }

        .piq-premium-table tbody tr:nth-child(even) td {
            background: #f8fafc;
        }

        .piq-premium-table tbody tr:hover td {
            background: #f0f6ff;
        }

        .piq-premium-table tbody tr:last-child td {
            border-bottom: none;
        }

        .piq-premium-table tbody td:last-child {
            border-right: none;
        }

        .piq-machine-badge {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            min-width: 34px;
            height: 28px;
            padding: 0 9px;
            border-radius: 8px;
            background: #dbeafe;
            border: 1px solid #bfdbfe;
            color: #1e40af;
            font-size: 12px;
            font-weight: 900;
        }

        .piq-publication-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 72px;
            padding: 7px 11px;
            border-radius: 9px;
            background: #eef2ff;
            border: 1px solid #d9ddff;
            color: #3730a3;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: 0.25px;
        }

        .piq-po-cell {
            color: #7c2d12 !important;
            background: #fff7ed !important;
            font-weight: 800 !important;
        }

        .piq-predicted-cell {
            color: #166534 !important;
            background: #f0fdf4 !important;
            font-weight: 800 !important;
        }

        .piq-actual-cell {
            color: #0f3d63 !important;
            background: #eff6ff !important;
            font-weight: 800 !important;
        }

        .piq-extra-cell {
            color: #9a3412 !important;
            background: #fff7ed !important;
            font-weight: 800 !important;
        }

        .piq-reason-cell {
            min-width: 280px;
            max-width: 340px;
            text-align: left !important;
            line-height: 1.45;
            white-space: normal;
            color: #475569 !important;
            font-weight: 500 !important;
        }

        .piq-empty-value {
            color: #94a3b8;
            font-weight: 700;
        }

        .piq-status-dot {
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            margin-right: 7px;
            background: #22c55e;
            vertical-align: middle;
        }

        @media (max-width: 900px) {
            .piq-table-heading-row {
                align-items: flex-start;
                flex-direction: column;
            }

            .piq-table-shell {
                border-radius: 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    table_rows = []

    for _, row in table_df.iterrows():
        edition_date = format_report_date(row.get("Issue Date"))
        machine = html.escape(str(row.get("Machine", "—")))
        incharge = html.escape(str(row.get("Machine In-charge", "—")))
        publication = html.escape(str(row.get("Final Code", "—")))

        po = format_number(row.get("PO"))
        actual_waste = format_number(row.get("Actual Waste"))

        predicted_waste = row.get("Predicted Waste")

        if pd.isna(predicted_waste) or str(predicted_waste).strip() == "":
            predicted_display = '<span class="piq-empty-value">—</span>'
            extra_display = '<span class="piq-empty-value">—</span>'
            reason_display = "NA"

        else:
            try:
                predicted_number = float(predicted_waste)
                actual_number = float(row.get("Actual Waste", 0))

                extra_number = max(
                    actual_number - predicted_number,
                    0
                )

                predicted_display = format_number(predicted_number)
                extra_display = format_number(extra_number)

                reason_value = row.get(
                    "Reason for Extra Waste",
                    "NA"
                )

                if extra_number <= 0:
                    reason_display = "NA"
                else:
                    reason_display = (
                        str(reason_value).strip()
                        if str(reason_value).strip()
                        else "Reason Required"
                    )

            except (TypeError, ValueError):
                predicted_display = '<span class="piq-empty-value">—</span>'
                extra_display = '<span class="piq-empty-value">—</span>'
                reason_display = "NA"

        reason_display = html.escape(str(reason_display))

        table_rows.append(
            f"""
            <tr>
                <td>{edition_date}</td>

                <td>
                    <span class="piq-machine-badge">
                        {machine}
                    </span>
                </td>

                <td>{incharge}</td>

                <td>
                    <span class="piq-publication-badge">
                        {publication}
                    </span>
                </td>

                <td class="piq-po-cell">
                    {po}
                </td>

                <td class="piq-predicted-cell">
                    {predicted_display}
                </td>

                <td class="piq-actual-cell">
                    {actual_waste}
                </td>

                <td class="piq-extra-cell">
                    {extra_display}
                </td>

                <td class="piq-reason-cell">
                    {reason_display}
                </td>
            </tr>
            """
        )

    table_html = f"""
    <div class="piq-working-section">

        <div class="piq-table-heading-row">

            <div>
                <div class="piq-table-title">
                    Production Working Table
                </div>

                <div class="piq-table-subtitle">
                    Review publication, production order and waste details before generating the final report.
                </div>
            </div>

            <div class="piq-report-badge">
                <span class="piq-status-dot"></span>
                {html.escape(selected_report)} Report
            </div>

        </div>

        <div class="piq-table-shell">
            <div class="piq-table-scroll">

                <table class="piq-premium-table">

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
                        {''.join(table_rows)}
                    </tbody>

                </table>

            </div>
        </div>

    </div>
    """

    st.markdown(
        table_html,
        unsafe_allow_html=True
    )
def run_actual_vs_predicted_waste():

    st.markdown("## Actual vs Predicted Waste")
    st.caption("Product Master Matching Engine")

    uploaded_file = st.file_uploader(
        "Upload Production Report",
        type=["xlsx", "xls"],
        key="actual_vs_predicted_waste_upload"
    )

    if uploaded_file is None:
        st.info("Please upload Production Report.")
        return

    master_df = load_product_master()

    if master_df.empty:
        return

    try:
        df = pd.read_excel(
            uploaded_file,
            sheet_name="General"
        )
    except Exception as e:
        st.error(f"Unable to read General sheet: {e}")
        return

    required_cols = [
        "Issue Date",
        "Products",
        "Edition",
        "Main/Supplement",
        "Machine",
        "Print Order",
        "Waste",
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]

    if missing_cols:
        st.error(f"Missing columns in Production Report: {missing_cols}")
        return

    df = df.copy()

    df["Main/Supplement Clean"] = df["Main/Supplement"].apply(clean_text)

    main_df = df[df["Main/Supplement Clean"] == "MAIN"].copy()
    supp_df = df[df["Main/Supplement Clean"] == "SUPPLEMENT"].copy()

    st.success("Production Report loaded successfully.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Main Editions", len(main_df))

    with col2:
        st.metric("Supplement Editions", len(supp_df))

    selected_report = st.radio(
        "Select Report Type",
        ["Main", "Supplement"],
        horizontal=True
    )

    if selected_report == "Main":
        work_df = main_df.copy()
    else:
        work_df = supp_df.copy()

    if work_df.empty:
        st.warning(f"No data found for {selected_report}.")
        return

    output_rows = []

    for _, row in work_df.iterrows():
        detected = detect_product_code(
            product_name=row["Products"],
            edition_name=row["Edition"],
            report_type=selected_report,
            master_df=master_df
        )

        output_rows.append({
            "Status": detected["match_status"],
            "Issue Date": row["Issue Date"],
            "Machine": row["Machine"],
            "Machine In-charge": row.get("In-Charge", "—"),
            "Product Name": row["Products"],
            "Edition": row["Edition"],
            "Auto Code": detected["auto_code"],
            "Final Code": detected["final_code"],
            "Matched Text": detected["matched_text"],
            "PO": row["Print Order"],
            "Actual Waste": row["Waste"],
        })

    result_df = pd.DataFrame(output_
    result_df["Predicted Waste"] = pd.NA
    result_df["Extra Waste"] = pd.NA
    result_df["Reason for Extra Waste"] = "NA"

    review_count = (result_df["Status"] == "🟡 Review Required").sum()

    if review_count > 0:
        st.warning(
            f"{review_count} product(s) not found in Product Master. "
            "Please review and edit Final Code before final report."
        )
    else:
        st.success("All products matched successfully from Product Master.")

    st.markdown("### Review Product Codes")

    edited_df = st.data_editor(
        result_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Final Code": st.column_config.TextColumn(
                "Final Code",
                help="Edit this if detected product code is wrong.",
                required=True,
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                disabled=True,
            ),
            "Auto Code": st.column_config.TextColumn(
                "Auto Code",
                disabled=True,
            ),
            "Matched Text": st.column_config.TextColumn(
                "Matched Text",
                disabled=True,
            ),
            "Product Name": st.column_config.TextColumn(
                "Product Name",
                disabled=True,
            ),
            "Edition": st.column_config.TextColumn(
                "Edition",
                disabled=True,
            ),
        },
        key=f"product_code_editor_{selected_report}"
    )

    edited_df["Final Code"] = edited_df["Final Code"].astype(str).str.strip()

    edited_df["Status"] = edited_df.apply(
        lambda r: "✏️ Edited"
        if str(r["Final Code"]).strip() != str(r["Auto Code"]).strip()
        else r["Status"],
        axis=1
    )

    premium_table_df = edited_df.copy()

    premium_table_df["Predicted Waste"] = pd.NA
    premium_table_df["Extra Waste"] = pd.NA
    premium_table_df["Reason for Extra Waste"] = "NA"

    render_premium_working_table(
        premium_table_df,
        selected_report
    )
