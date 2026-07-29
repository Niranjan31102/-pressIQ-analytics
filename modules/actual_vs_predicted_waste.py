from pathlib import Path
from textwrap import dedent
import html

import streamlit as st

from ui_theme import module_hero


# ============================================================
# FILE PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCT_MASTER_PATH = (
    PROJECT_ROOT
    / "backend_data"
    / "product_master.xlsx"
)

PREDICTION_MASTER_PATH = (
    PROJECT_ROOT
    / "backend_data"
    / "PressIQ_Prediction_Master_v1.xlsx"
)


# ============================================================
# MODULE-SPECIFIC CSS
# ============================================================

def add_actual_vs_predicted_css():
    """
    Add styles used only by the Actual vs Predicted Waste module.

    No sidebar radio styling is included here, so the existing
    PressIQ navigation will remain unchanged.
    """

    st.markdown(
        """
        <style>

        /* -----------------------------------------
           WORKFLOW
        ----------------------------------------- */

        .avp-workflow {
            display: grid;
            grid-template-columns: 1fr 42px 1fr 42px 1fr;
            align-items: center;
            gap: 8px;
            margin: 0.15rem 0 1.35rem 0;
        }

        .avp-step {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            text-align: center;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }

        .avp-step-active {
            border-color: #2563eb;
            background: linear-gradient(
                135deg,
                #eff6ff 0%,
                #ffffff 100%
            );
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.13);
        }

        .avp-step-number {
            width: 28px;
            height: 28px;
            margin: 0 auto 0.4rem auto;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 0.78rem;
            font-weight: 900;
        }

        .avp-step-active .avp-step-number {
            background: #2563eb;
            color: #ffffff;
        }

        .avp-step-title {
            color: #0f172a;
            font-size: 0.88rem;
            font-weight: 850;
        }

        .avp-arrow {
            text-align: center;
            color: #94a3b8;
            font-size: 1.25rem;
            font-weight: 900;
        }

        /* -----------------------------------------
           COMMON SECTION
        ----------------------------------------- */

        .avp-section {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.26);
            border-radius: 22px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
        }

        .avp-section-title {
            color: #0f172a;
            font-size: 1.08rem;
            font-weight: 900;
            margin-bottom: 0.2rem;
        }

        .avp-section-caption {
            color: #64748b;
            font-size: 0.86rem;
        }

        /* -----------------------------------------
           PRODUCTION TYPE CARDS
        ----------------------------------------- */

        .avp-production-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin: 0.8rem 0 0.45rem 0;
        }

        .avp-production-card {
            background: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 18px;
            padding: 1.05rem 1.1rem;
            min-height: 102px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }

        .avp-production-card-selected {
            border-color: #2563eb;
            background: linear-gradient(
                135deg,
                #eff6ff 0%,
                #ffffff 100%
            );
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.15);
        }

        .avp-production-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.7rem;
        }

        .avp-production-icon {
            width: 40px;
            height: 40px;
            border-radius: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            font-size: 1.1rem;
        }

        .avp-selection-mark {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #2563eb;
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 900;
        }

        .avp-production-name {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 900;
            margin-top: 0.72rem;
        }

        .avp-production-description {
            color: #64748b;
            font-size: 0.82rem;
            margin-top: 0.16rem;
        }

        /* -----------------------------------------
           UPLOAD AREA
        ----------------------------------------- */

        .avp-upload-heading {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .avp-upload-icon {
            width: 44px;
            height: 44px;
            min-width: 44px;
            border-radius: 14px;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #2563eb;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 900;
        }

        .avp-file-ready {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-left: 5px solid #10b981;
            border-radius: 14px;
            padding: 0.82rem 1rem;
            color: #065f46;
            font-size: 0.86rem;
            font-weight: 750;
            margin: 0.75rem 0 0.3rem 0;
            word-break: break-word;
        }

        .avp-placeholder {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-left: 5px solid #2563eb;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            color: #1e3a8a;
            font-size: 0.88rem;
            font-weight: 700;
        }

        .avp-footer {
            text-align: center;
            margin-top: 2rem;
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 600;
        }

        @media (max-width: 800px) {

            .avp-workflow {
                grid-template-columns: 1fr;
            }

            .avp-arrow {
                transform: rotate(90deg);
            }

            .avp-production-grid {
                grid-template-columns: 1fr;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SESSION STATE
# ============================================================

def initialize_actual_vs_predicted_state():
    """
    Create the session-state values required by this module.
    """

    defaults = {
        "avp_stage": "upload",
        "avp_report_type": "Main",
        "avp_uploaded_file_name": "",
        "avp_working_table": None,
        "avp_final_report_png": None,
        "avp_focus_mode": False,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# ============================================================
# SMALL HELPERS
# ============================================================

def safe_html_text(value):
    """
    Escape uploaded file names before showing them in HTML.
    """

    return html.escape(str(value).strip())


# ============================================================
# WORKFLOW
# ============================================================

def render_workflow():
    """
    Display Upload, Working Table and Final Report stages.
    """

    current_stage = st.session_state.avp_stage

    upload_class = (
        "avp-step avp-step-active"
        if current_stage == "upload"
        else "avp-step"
    )

    review_class = (
        "avp-step avp-step-active"
        if current_stage == "review"
        else "avp-step"
    )

    report_class = (
        "avp-step avp-step-active"
        if current_stage == "report"
        else "avp-step"
    )

    workflow_html = dedent(
        f"""
        <div class="avp-workflow">

            <div class="{upload_class}">
                <div class="avp-step-number">1</div>
                <div class="avp-step-title">Upload Report</div>
            </div>

            <div class="avp-arrow">→</div>

            <div class="{review_class}">
                <div class="avp-step-number">2</div>
                <div class="avp-step-title">Working Table</div>
            </div>

            <div class="avp-arrow">→</div>

            <div class="{report_class}">
                <div class="avp-step-number">3</div>
                <div class="avp-step-title">Final Report</div>
            </div>

        </div>
        """
    ).strip()

    st.markdown(
        workflow_html,
        unsafe_allow_html=True,
    )


# ============================================================
# PRODUCTION TYPE CARDS
# ============================================================

def render_production_type_cards():
    """
    Display Main and Supplement cards side by side.

    Streamlit buttons are used instead of a radio widget so
    sidebar navigation styling is never affected.
    """

    current_report_type = st.session_state.avp_report_type

    section_html = dedent(
        """
        <div class="avp-section">
            <div class="avp-section-title">
                Select Production Type
            </div>
            <div class="avp-section-caption">
                Choose the report you want to prepare.
            </div>
        </div>
        """
    ).strip()

    st.markdown(
        section_html,
        unsafe_allow_html=True,
    )

    main_selected_class = (
        "avp-production-card avp-production-card-selected"
        if current_report_type == "Main"
        else "avp-production-card"
    )

    supplement_selected_class = (
        "avp-production-card avp-production-card-selected"
        if current_report_type == "Supplement"
        else "avp-production-card"
    )

    main_mark = (
        '<div class="avp-selection-mark">✓</div>'
        if current_report_type == "Main"
        else ""
    )

    supplement_mark = (
        '<div class="avp-selection-mark">✓</div>'
        if current_report_type == "Supplement"
        else ""
    )

    main_column, supplement_column = st.columns(2)

    with main_column:
        main_card_html = dedent(
            f"""
            <div class="{main_selected_class}">
                <div class="avp-production-top">
                    <div class="avp-production-icon">M</div>
                    {main_mark}
                </div>

                <div class="avp-production-name">
                    Main Production
                </div>

                <div class="avp-production-description">
                    Main editions and integrated sections
                </div>
            </div>
            """
        ).strip()

        st.markdown(
            main_card_html,
            unsafe_allow_html=True,
        )

        if st.button(
            "Select Main Production",
            use_container_width=True,
            key="avp_select_main",
            disabled=current_report_type == "Main",
        ):
            st.session_state.avp_report_type = "Main"
            st.rerun()

    with supplement_column:
        supplement_card_html = dedent(
            f"""
            <div class="{supplement_selected_class}">
                <div class="avp-production-top">
                    <div class="avp-production-icon">S</div>
                    {supplement_mark}
                </div>

                <div class="avp-production-name">
                    Supplement Production
                </div>

                <div class="avp-production-description">
                    Supplement editions and pullouts
                </div>
            </div>
            """
        ).strip()

        st.markdown(
            supplement_card_html,
            unsafe_allow_html=True,
        )

        if st.button(
            "Select Supplement Production",
            use_container_width=True,
            key="avp_select_supplement",
            disabled=current_report_type == "Supplement",
        ):
            st.session_state.avp_report_type = "Supplement"
            st.rerun()


# ============================================================
# UPLOAD SCREEN
# ============================================================

def render_upload_screen():
    """
    Display production-type selection and file uploader.
    """

    render_production_type_cards()

    st.markdown("")

    upload_heading_html = dedent(
        """
        <div class="avp-section">

            <div class="avp-upload-heading">

                <div class="avp-upload-icon">
                    ↑
                </div>

                <div>
                    <div class="avp-section-title">
                        Upload Production Report
                    </div>

                    <div class="avp-section-caption">
                        Supported file format: Excel (.xlsx or .xls)
                    </div>
                </div>

            </div>

        </div>
        """
    ).strip()

    st.markdown(
        upload_heading_html,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Production Report",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
        key="avp_production_report_upload",
    )

    if uploaded_file is not None:
        st.session_state.avp_uploaded_file_name = uploaded_file.name

        safe_file_name = safe_html_text(uploaded_file.name)

        file_ready_html = dedent(
            f"""
            <div class="avp-file-ready">
                ✓ File ready: {safe_file_name}
            </div>
            """
        ).strip()

        st.markdown(
            file_ready_html,
            unsafe_allow_html=True,
        )

    st.markdown("")

    process_clicked = st.button(
        "Process Report",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
        key="avp_process_report_button",
    )

    if process_clicked:
        st.session_state.avp_uploaded_file_name = uploaded_file.name

        with st.spinner("Processing report. Please wait..."):
            pass

        st.success(
            "Upload screen is working correctly. "
            "The processing engine will be connected in the next step."
        )


# ============================================================
# TEMPORARY PLACEHOLDER SCREENS
# ============================================================

def render_review_placeholder():
    placeholder_html = dedent(
        """
        <div class="avp-placeholder">
            The Working Table will be connected in the next development step.
        </div>
        """
    ).strip()

    st.markdown(
        placeholder_html,
        unsafe_allow_html=True,
    )


def render_report_placeholder():
    placeholder_html = dedent(
        """
        <div class="avp-placeholder">
            The Final Management Report will be connected later.
        </div>
        """
    ).strip()

    st.markdown(
        placeholder_html,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

def render_module_footer():
    footer_html = dedent(
        """
        <div class="avp-footer">
            Powered by PressIQ AI · Designed for Production Intelligence
        </div>
        """
    ).strip()

    st.markdown(
        footer_html,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN MODULE
# ============================================================

def run_actual_vs_predicted_waste():
    """
    Main entry point called by app.py.
    """

    initialize_actual_vs_predicted_state()
    add_actual_vs_predicted_css()

    module_hero(
        title="Actual vs Predicted Waste",
        subtitle="",
    )

    render_workflow()

    if st.session_state.avp_stage == "upload":
        render_upload_screen()

    elif st.session_state.avp_stage == "review":
        render_review_placeholder()

    elif st.session_state.avp_stage == "report":
        render_report_placeholder()

    render_module_footer()
