import streamlit as st

from ui_theme import apply_premium_theme

from modules.waste_tracker import run_waste_tracker
from modules.edition_waste import run_edition_waste_analyzer
from modules.adam_analyzer import run_adam_analyzer
from modules.downtime import run_downtime_analyzer
from modules.micro_stoppage import run_micro_stoppage_analyzer
from modules.utility_performance import run_utility_performance_analyzer

st.set_page_config(
    page_title="PressIQ Analytics",
    page_icon="🏭",
    layout="wide"
)
apply_premium_theme()

st.set_option("client.toolbarMode", "viewer")

# ---------------- STYLE ----------------
st.markdown("""
<style>

/* ----------- HEADER ----------- */
.main-title {
    font-size: 44px;
    font-weight: 900;
    color: #0f172a;
}

.sub-title {
    font-size: 20px;
    color: #475569;
}

/* ----------- KPI CARD (Power BI style) ----------- */
.card {
    background: #ffffff;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0px 6px 18px rgba(15, 23, 42, 0.08);
    margin-bottom: 10px;
}

/* ----------- INSIGHT CARD ----------- */
.insight-card {
    background: linear-gradient(90deg, #eff6ff, #f8fafc);
    padding: 18px;
    border-radius: 16px;
    border-left: 6px solid #2563eb;
    margin-bottom: 12px;
    font-size: 15px;
}

/* ----------- WARNING CARD ----------- */
.warning-card {
    background: #fff7ed;
    padding: 18px;
    border-radius: 16px;
    border-left: 6px solid #f97316;
    margin-bottom: 12px;
    font-size: 15px;
}

/* ----------- TABLE IMPROVEMENT ----------- */

/* Center align all table data */
div[data-testid="stDataFrame"] table {
    text-align: center !important;
}

/* Center header */
div[data-testid="stDataFrame"] th {
    text-align: center !important;
    font-weight: 600 !important;
}

/* Center values */
div[data-testid="stDataFrame"] td {
    text-align: center !important;
}

/* Slightly better spacing */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* ----------- TAB IMPROVEMENT ----------- */
button[role="tab"] {
    font-size: 14px !important;
    padding: 6px 12px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
COMMON_PASSWORD = "BCCL123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="login-brand-row">
            <div class="login-simple-logo">PIQ</div>
            <div class="login-main-title">PressIQ Analytics</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="sub-title">AI Powered Plant Performance Intelligence Platform</div>', unsafe_allow_html=True)

    st.write("### Login")

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if not email:
            st.error("Please enter email.")
        elif password != COMMON_PASSWORD:
            st.error("Invalid password.")
        else:
            st.session_state.logged_in = True
            st.session_state.user_email = email

            try:
                import gspread
                from oauth2client.service_account import ServiceAccountCredentials
                from datetime import datetime

                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive",
                ]

                creds = ServiceAccountCredentials.from_json_keyfile_dict(
                    st.secrets["gcp_service_account"],
                    scope,
                )

                client = gspread.authorize(creds)

                sheet = client.open("PressIQ User Logs").worksheet("Logs")

                sheet.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    email,
                    "Login",
                    "",
                    "",
                ])

            except Exception as e:
                st.warning(f"Login logging failed: {e}")
    
            st.rerun()

    st.stop()
# ---------------- SIDEBAR ----------------
st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-simple-logo">PIQ</div>
        <div>
            <div class="sidebar-title">PressIQ Analytics</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.success(f"Logged in: {st.session_state.user_email}")

st.sidebar.markdown("### Main Intelligence")

main_intelligence = st.sidebar.radio(
    "Select Intelligence",
    [
        "Waste Intelligence",
        "Utility Intelligence",
    ]
)

if main_intelligence == "Waste Intelligence":
    st.sidebar.markdown("### Waste Intelligence")

    module = st.sidebar.radio(
        "Select Tool",
        [
            "Edition Wise Wastage Analyzer",
        ]
    )

elif main_intelligence == "Utility Intelligence":
    st.sidebar.markdown("### Utility Intelligence")

    module = st.sidebar.radio(
        "Select Tool",
        [
            "Utility Performance Analyzer",
        ]
    )

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ---------------- HEADER ----------------
st.markdown('<div class="main-title">PressIQ Analytics</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{module}</div>', unsafe_allow_html=True)

# ---------------- ROUTER ----------------
if module == "Pan India Waste Tracker Analyzer":
    run_waste_tracker()
elif module == "Edition Wise Wastage Analyzer":
    run_edition_waste_analyzer()

elif module == "ADAM Production Report Analyzer":
    run_adam_analyzer()

elif module == "Overall Downtime Analyzer":
    run_downtime_analyzer()

elif module == "0–4 Min Micro Stoppage Analyzer":
    run_micro_stoppage_analyzer()

elif module == "Web Break Downtime Analyzer":
    st.info("🧵 Web Break Downtime Analyzer will be added later.")
    
elif module == "Utility Performance Analyzer":
    run_utility_performance_analyzer()
    
