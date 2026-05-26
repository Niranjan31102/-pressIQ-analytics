import streamlit as st

def run_utility_performance_analyzer():

    st.header("Utility Performance Analyzer")
    st.caption("EMS Daily Utility Performance File Analysis")

    uploaded_file = st.file_uploader(
        "Upload EMS Daily Utility Performance File",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_file is not None:
        st.success("File uploaded successfully.")
