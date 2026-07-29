from pathlib import Path

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
# MODULE CSS
# ============================================================

def add_actual_vs_predicted_css():
    st.markdown(
        """
        <style>

        /* =========================================
           MODULE WORKFLOW
        ========================================= */

        .avp-workflow {
            display: grid;
            grid-template-columns: 1fr 44px 1fr 44px 1fr;
            align-items: center;
            gap: 8px;
            margin: 0.2rem 0 1.4rem 0;
        }

        .avp-step {
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            text-align: center;
        }

        .avp-step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #dbeafe;
            color: #1d4ed8;
            font-size: 0.78rem;
            font-weight: 900;
            margin-bottom: 0.4rem;
        }

        .avp-step-title {
            color: #0f172a;
            font-size: 0.88rem;
            font-weight: 850;
        }

        .avp-step-active {
            border-color: #2563eb;
            background: linear-gradient(
                135deg,
                #eff6ff 0%,
                #ffffff 100%
            );
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.12);
        }

        .avp-step-active .avp-step-number {
            background: #2563eb;
            color: #ffffff;
        }

        .avp-arrow {
            text-align: center;
            color: #94a3b8;
            font-size: 1.3rem;
            font-weight: 900;
        }

        /* =========================================
           PRODUCTION TYPE SECTION
        ========================================= */

        .avp-section-card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.26);
            border-radius: 22px;
            padding: 1.25rem;
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.07);
            margin-bottom: 1.1rem;
        }

        .avp-section-title {
            color: #0f172a;
            font-size: 1.08rem;
            font-weight: 900;
            margin-bottom: 0.25rem;
        }

        .avp-section-caption {
            color: #64748b;
            font-size: 0.86rem;
            margin-bottom: 0.85rem;
        }

        /* Convert horizontal radio options into cards */

        div[data-testid="stRadio"] div[role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 1rem !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] label {
            background: #ffffff !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 18px !important;
            padding: 1rem 1.1rem !important;
            min-height: 86px !important;
            display: flex !important;
            align-items: center !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06) !important;
            transition: all 0.2s ease !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
            border-color: #2563eb !important;
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(37, 99, 235, 0.12) !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] label:has(
            input:checked
        ) {
            border-color: #2563eb !important;
            background: linear-gradient(
                135deg,
                #eff6ff 0%,
                #ffffff 100%
            ) !important;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.16) !important;
        }

        div[data-testid="stRadio"] div[role="radiogroup"] label p {
            color: #0f172a !important;
            font-size: 0.98rem !important;
            font-weight: 850 !important;
        }

        /* =========================================
           UPLOAD AREA
        ========================================= */

        .avp-upload-heading {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.8rem;
        }

        .avp-upload-icon {
            width: 42px;
            height: 42px;
            border-radius: 13px;
            background: #eff6ff;
            color: #2563eb;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            border: 1px solid #bfdbfe;
        }

        .avp-upload-title {
            color: #0f172a;
            font-size: 1.05rem;
            font-weight: 900;
        }

        .avp-upload-caption {
            color: #64748b;
            font-size: 0.82rem;
            margin-top: 0.12rem;
        }

        .avp-file-ready {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-left: 5px solid #10b981;
            border-radius: 14px;
            padding: 0.85rem 1rem;
            color: #065f46;
            font-size: 0.88rem;
            font-weight: 750;
            margin-top: 0.8rem;
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

            div[data-testid="stRadio"] div[role="radiogroup"] {
                grid-template-columns: 1fr !important;
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
    defaults = {
        "avp_stage": "upload",
        "avp_report_type": "Main Production",
        "avp_uploaded_file_name": "",
        "avp_working_table": None,
        "avp_final_report_png": None,
        "avp_focus_mode": False,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# ============================================================
# UI COMPONENTS
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

    st.markdown(
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
        """,
        unsafe_allow_html=True,
    )


def render_upload_screen():
    st.markdown(
        """
        <div class="avp-section-card">
            <div class="avp-section-title">
                Select Production Type
            </div>
            <div class="avp-section-caption">
                Choose the report you want to prepare.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_report_type = st.radio(
        "Production Type",
        options=[
            "🌙 Main Production",
            "🌆 Supplement Production",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="avp_report_type_selector",
    )

    if "Main" in selected_report_type:
        st.session_state.avp_report_type = "Main Production"
    else:
        st.session_state.avp_report_type = "Supplement Production"

    st.markdown("")

    st.markdown(
        """
        <div class="avp-section-card">

            <div class="avp-upload-heading">

                <div class="avp-upload-icon">
                    ↑
                </div>

                <div>
                    <div class="avp-upload-title">
                        Upload Production Report
                    </div>

                    <div class="avp-upload-caption">
                        Supported file format: Excel (.xlsx or .xls)
                    </div>
                </div>

            </div>

        </div>
        """,
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

        st.markdown(
            f"""
            <div class="avp-file-ready">
                ✓ File ready: {uploaded_file.name}
            </div>
            """,
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
        with st.spinner("Processing report. Please wait..."):
            st.session_state.avp_uploaded_file_name = uploaded_file.name

        st.success(
            "Upload screen is working correctly. "
            "The processing engine will be connected in the next step."
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
        st.info("Working Table will be connected in the next development step.")

    elif st.session_state.avp_stage == "report":
        st.info("Final Management Report will be connected later.")

    st.markdown(
        """
        <div class="avp-footer">
            Powered by PressIQ AI · Designed for Production Intelligence
        </div>
        """,
        unsafe_allow_html=True,
    )
