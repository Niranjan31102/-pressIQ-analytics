import streamlit as st


def initialize_avp_session():
    """
    Initialize all session state variables
    required by the Actual vs Predicted Waste module.
    """

    defaults = {

        # Navigation
        "avp_stage": "upload",

        # Upload
        "avp_uploaded_file": None,
        "avp_uploaded_filename": None,

        # Report Information
        "avp_issue_date": None,
        "avp_plant": None,
        "avp_total_editions": 0,

        # Production Type
        "avp_report_type": "Main",

        # Data
        "avp_general_df": None,
        "avp_book_df": None,
        "avp_innovation_df": None,

        # Product Matching
        "avp_product_master": None,

        # Prediction
        "avp_prediction_master": None,

        # Working Table
        "avp_working_df": None,

        # Machine Summary
        "avp_machine_summary": None,

        # Final Report
        "avp_final_report": None,

        # Validation
        "avp_validation_messages": [],

        # UI
        "avp_processing_complete": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def reset_avp_session():
    """
    Reset module state when
    user uploads a new report.
    """

    keys = [

        "avp_uploaded_file",
        "avp_uploaded_filename",

        "avp_issue_date",
        "avp_plant",
        "avp_total_editions",

        "avp_general_df",
        "avp_book_df",
        "avp_innovation_df",

        "avp_working_df",
        "avp_machine_summary",

        "avp_final_report",

        "avp_validation_messages",

        "avp_processing_complete",
    ]

    for key in keys:

        if key in st.session_state:

            if key == "avp_validation_messages":
                st.session_state[key] = []

            elif key == "avp_processing_complete":
                st.session_state[key] = False

            else:
                st.session_state[key] = None

    st.session_state["avp_stage"] = "upload"
    st.session_state["avp_report_type"] = "Main"
    st.session_state["avp_total_editions"] = 0


def goto_upload():

    st.session_state["avp_stage"] = "upload"


def goto_review():

    st.session_state["avp_stage"] = "review"


def goto_report():

    st.session_state["avp_stage"] = "report"
