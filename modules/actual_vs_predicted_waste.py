import streamlit as st

from modules.avp_session import (
    initialize_avp_session,
)

from modules.avp_ui import (
    render_upload_screen,
    render_review_placeholder,
    render_report_placeholder,
)


def run_actual_vs_predicted_waste():
    """
    Main controller for
    Actual vs Predicted Waste Module
    """

    initialize_avp_session()

    stage = st.session_state.avp_stage

    if stage == "upload":
        render_upload_screen()

    elif stage == "review":
        render_review_placeholder()

    elif stage == "report":
        render_report_placeholder()

    else:
        st.error("Unknown application stage.")
