import streamlit as st


def show_pf_delay_report():
    st.markdown("## PF Delay Report")

    st.info("PF Delay Report module will be built here.")

    uploaded_file = st.file_uploader(
        "Upload PF Delay Report file",
        type=["xlsx", "xls", "csv"],
        key="pf_delay_report_uploader"
    )

    if uploaded_file is not None:
        st.success("File uploaded successfully.")

        st.write("Next, we will build PF Delay Report logic here.")
