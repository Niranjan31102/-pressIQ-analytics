import streamlit as st

from modules.waste_tracker import run_waste_tracker
from modules.adam_analyzer import run_adam_analyzer
from modules.downtime import run_downtime_analyzer
from modules.micro_stoppage import run_micro_stoppage_analyzer

st.set_page_config(
    page_title="PressIQ Analytics",
    page_icon="🏭",
    layout="wide"
)

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main-title {
    font-size: 44px;
    font-weight: 900;
    color: #0f172a;
}
.sub-title {
    font-size: 20px;
    color: #475569;
}
.card {
    background: #ffffff;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0px 4px 14px rgba(15, 23, 42, 0.06);
}
.insight-card {
    background: linear-gradient(90deg, #eff6ff, #f8fafc);
    padding: 18px;
    border-radius: 16px;
    border-left: 6px solid #2563eb;
    margin-bottom: 12px;
}
.warning-card {
    background: #fff7ed;
    padding: 18px;
    border-radius: 16px;
    border-left: 6px solid #f97316;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown('<div class="main-title">🏭 PressIQ Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI Powered Plant Performance Intelligence Platform</div>', unsafe_allow_html=True)

    st.write("### Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Please enter email and password")

    st.info("Demo login only. Real signup/authentication will be added later.")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("🏭 PressIQ Analytics")
st.sidebar.success("Logged in")

area = st.sidebar.selectbox(
    "Select Intelligence Area",
    ["Waste Intelligence", "Downtime Intelligence"]
)

if area == "Waste Intelligence":
    module = st.sidebar.radio(
        "Select Waste Tool",
        [
            "Pan India Waste Tracker Analyzer",
            "ADAM Production Report Analyzer"
        ]
    )
else:
    module = st.sidebar.radio(
        "Select Downtime Tool",
        [
            "Overall Downtime Analyzer",
            "0–4 Min Micro Stoppage Analyzer",
            "Web Break Downtime Analyzer"
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

elif module == "ADAM Production Report Analyzer":
    run_adam_analyzer()

elif module == "Overall Downtime Analyzer":
    run_downtime_analyzer()

elif module == "0–4 Min Micro Stoppage Analyzer":
    run_micro_stoppage_analyzer()

elif module == "Web Break Downtime Analyzer":
    st.info("🧵 Web Break Downtime Analyzer will be added later.")
