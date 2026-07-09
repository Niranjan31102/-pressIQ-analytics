import os
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
        "Product Name",
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
            product_name=row["Product Name"],
            edition_name=row["Edition"],
            report_type=selected_report,
            master_df=master_df
        )

        output_rows.append({
            "Status": detected["match_status"],
            "Issue Date": row["Issue Date"],
            "Machine": row["Machine"],
            "Product Name": row["Product Name"],
            "Edition": row["Edition"],
            "Auto Code": detected["auto_code"],
            "Final Code": detected["final_code"],
            "Matched Text": detected["matched_text"],
            "PO": row["Print Order"],
            "Actual Waste": row["Waste"],
        })

    result_df = pd.DataFrame(output_rows)

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

    st.markdown("### Final Product Code Preview")

    st.dataframe(
        edited_df[
            [
                "Status",
                "Issue Date",
                "Machine",
                "Final Code",
                "PO",
                "Actual Waste",
            ]
        ],
        use_container_width=True,
        hide_index=True
    )
