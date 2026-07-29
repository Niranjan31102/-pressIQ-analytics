from pathlib import Path
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
# HTML HELPER
# ============================================================

def compact_html(html_text):
    """
    Remove indentation and line breaks from HTML.

    This prevents Streamlit Markdown from displaying HTML
    as visible code blocks.
    """

    return "".join(
        line.strip()
        for line in str(html_text).splitlines()
        if line.strip()
    )


# ============================================================
# MODULE-SPECIFIC CSS
# ============================================================

def add_actual_vs_predicted_css():
    css = """
    <style>

    .avp-workflow {
        display: grid;
        grid-template-columns: 1fr 42px 1fr 42px 1fr;
        align-items: center;
        gap: 8px;
        margin: 0.15rem 0 1.35rem 0;
    }

    .avp-step {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(148, 163, 184, 0.30);
        border-radius: 16px;
        padding: 0.9rem 1rem;
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
        box-shadow: 0 12px 28px rgba(37, 99, 235, 0.14);
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

    .avp-section-heading {
        margin: 0.2rem 0 0.75rem 0;
    }

    .avp-section-title {
        color: #0f172a;
        font-size: 1.1rem;
        font-weight: 900;
        margin-bottom: 0.18rem;
    }

    .avp-section-caption {
        color: #64748b;
        font-size: 0.85rem;
    }

    .avp-production-card {
        background: rgba(255, 255, 255, 0.96);
        border: 1.5px solid #cbd5e1;
        border-radius: 20px;
        padding: 1.15rem 1.2rem;
        min-height: 116px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
        margin-bottom: 0.55rem;
    }

    .avp-production-card-selected {
        border-color: #2563eb;
        background: linear-gradient(
            135deg,
            #eff6ff 0%,
            #ffffff 100%
        );
        box-shadow: 0 15px 32px rgba(37, 99, 235, 0.16);
    }

    .avp-production-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
    }

    .avp-production-icon {
        width: 42px;
        height: 42px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        font-size: 0.95rem;
        font-weight: 900;
    }

    .avp-selection-mark {
        width: 25px;
        height: 25px;
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
        font-size: 1.02rem;
        font-weight: 900;
        margin-top: 0.75rem;
    }

    .avp-production-description {
        color: #64748b;
        font-size: 0.83rem;
        margin-top: 0.18rem;
    }

    .avp-upload-card {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 22px;
        padding: 1.25rem;
        box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
        margin: 1rem 0 0.8rem 0;
    }

    .avp-upload-heading {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    .avp-upload-icon {
        width: 46px;
        height: 46px;
        min-width: 46px;
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
        padding: 0.85rem 1rem;
        color: #065f46;
        font-size: 0.86rem;
        font-weight: 750;
        margin: 0.75rem 0 0.35rem 0;
        word-break: break-word;
    }

    .avp-placeholder {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 5px solid #2563eb;
        border-radius: 14px;
        padding: 1rem;
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
    }

    </style>
    """

    st.markdown(
        compact_html(css),
        unsafe_allow_html=True,
    )


# ============================================================
# SESSION STATE
# ============================================================

def initialize_actual_vs_predicted_state():
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
    return html.escape(str(value).strip())


# ============================================================
# WORKFLOW
# ============================================================

def render_workflow():
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

    workflow_html = f"""
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

    st.markdown(
        compact_html(workflow_html),
        unsafe_allow_html=True,
    )


# ============================================================
# PRODUCTION TYPE
# ============================================================

def render_production_type_cards():
    heading_html = """
    <div class="avp-section-heading">
        <div class="avp-section-title">
            Select Production Type
        </div>
        <div class="avp-section-caption">
            Choose the report you want to prepare.
        </div>
    </div>
    """

    st.markdown(
        compact_html(heading_html),
        unsafe_allow_html=True,
    )

    current_report_type = st.session_state.avp_report_type

    main_class = (
        "avp-production-card avp-production-card-selected"
        if current_report_type == "Main"
        else "avp-production-card"
    )

    supplement_class = (
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
        main_html = f"""
        <div class="{main_class}">
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

        st.markdown(
            compact_html(main_html),
            unsafe_allow_html=True,
        )

        if st.button(
            "Select Main Production",
            use_container_width=True,
            disabled=current_report_type == "Main",
            key="avp_select_main",
        ):
            st.session_state.avp_report_type = "Main"
            st.rerun()

    with supplement_column:
        supplement_html = f"""
        <div class="{supplement_class}">
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

        st.markdown(
            compact_html(supplement_html),
            unsafe_allow_html=True,
        )

        if st.button(
            "Select Supplement Production",
            use_container_width=True,
            disabled=current_report_type == "Supplement",
            key="avp_select_supplement",
        ):
            st.session_state.avp_report_type = "Supplement"
            st.rerun()


# ============================================================
# UPLOAD SCREEN
# ============================================================

def render_upload_screen():
    render_production_type_cards()

    upload_heading_html = """
    <div class="avp-upload-card">
        <div class="avp-upload-heading">
            <div class="avp-upload-icon">↑</div>

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

    st.markdown(
        compact_html(upload_heading_html),
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

        file_ready_html = f"""
        <div class="avp-file-ready">
            ✓ File ready: {safe_file_name}
        </div>
        """

        st.markdown(
            compact_html(file_ready_html),
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
# PLACEHOLDER SCREENS
# ============================================================

def render_review_placeholder():
    placeholder_html = """
    <div class="avp-placeholder">
        The Working Table will be connected in the next development step.
    </div>
    """

    st.markdown(
        compact_html(placeholder_html),
        unsafe_allow_html=True,
    )


def render_report_placeholder():
    placeholder_html = """
    <div class="avp-placeholder">
        The Final Management Report will be connected later.
    </div>
    """

    st.markdown(
        compact_html(placeholder_html),
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

def render_module_footer():
    footer_html = """
    <div class="avp-footer">
        Powered by PressIQ AI · Designed for Production Intelligence
    </div>
    """

    st.markdown(
        compact_html(footer_html),
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN MODULE
# ============================================================

def run_actual_vs_predicted_waste():
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
