import streamlit as st

from ui_theme import (
    module_hero,
    upload_box_title,
)

from modules.avp_helpers import (
    card_title,
    success_box,
)

from modules.avp_session import (
    goto_review,
)


def render_workflow():

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("① Upload Report")

    with col2:
        st.info("② Working Table")

    with col3:
        st.info("③ Final Report")


def render_upload_screen():

    module_hero(
        title="Actual vs Predicted Waste",
        subtitle="Compare actual production waste against intelligent predicted waste."
    )

    render_workflow()

    st.write("")

    upload_box_title(
        "Upload Production Report",
        "Upload today's production report (.xlsx)"
    )

    uploaded_file = st.file_uploader(
        "Production Report",
        type=["xlsx", "xls"],
        label_visibility="collapsed"
    )

    if uploaded_file:

        st.session_state.avp_uploaded_file = uploaded_file
        st.session_state.avp_uploaded_filename = uploaded_file.name

        success_box("Production report uploaded successfully.")

        st.write("")

        col1, col2 = st.columns(2)

        with col1:

            st.text_input(
                "File Name",
                value=uploaded_file.name,
                disabled=True,
            )

        with col2:

            production_type = st.radio(
                "Production Type",
                ["Main", "Supplement"],
                horizontal=True,
            )

            st.session_state.avp_report_type = production_type

        st.write("")

        if st.button(
            "Process Report",
            use_container_width=True,
            type="primary",
        ):

            goto_review()

            st.rerun()


def render_review_placeholder():

    module_hero(
        title="Working Table",
        subtitle="Prediction engine will populate this screen."
    )

    st.info("Working Table under development.")


def render_report_placeholder():

    module_hero(
        title="Final Management Report",
        subtitle="Final report will appear here."
    )

    st.info("Management Report under development.")
