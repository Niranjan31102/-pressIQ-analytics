import streamlit as st
import pandas as pd


def run_actual_vs_predicted_waste():

    st.markdown("## 📊 Actual vs Predicted Waste")
    st.caption("Phase 1 - Production Report Reader")

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload Production Report",
        type=["xlsx", "xls"],
        key="actual_vs_predicted_waste_upload"
    )

    if uploaded_file is None:
        st.info("Please upload today's Production Report.")
        return

    # -----------------------------
    # Read General Sheet
    # -----------------------------
    try:
        df = pd.read_excel(
            uploaded_file,
            sheet_name="General"
        )

    except Exception as e:
        st.error(f"Unable to read 'General' sheet.\n\n{e}")
        return

    # -----------------------------
    # Basic validation
    # -----------------------------
    if len(df.columns) < 6:
        st.error("General sheet format is not correct.")
        return

    # Column F = Main/Supplement
    shift_col = df.columns[5]

    df[shift_col] = (
        df[shift_col]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    main_df = df[df[shift_col] == "main"].copy()
    supp_df = df[df[shift_col] == "supplement"].copy()

    st.success("Production Report Loaded Successfully")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "📰 Main Editions",
            len(main_df)
        )

    with col2:
        st.metric(
            "📚 Supplement Editions",
            len(supp_df)
        )

    st.divider()

    selected_shift = st.radio(
        "Select Report",
        [
            "Main",
            "Supplement"
        ],
        horizontal=True
    )

    st.divider()

    if selected_shift == "Main":

        st.subheader("Main Editions")

        st.dataframe(
            main_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.subheader("Supplement Editions")

        st.dataframe(
            supp_df,
            use_container_width=True,
            hide_index=True
        )
