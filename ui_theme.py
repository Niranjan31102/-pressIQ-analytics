import streamlit as st


def apply_premium_theme():
    st.markdown(
        """
        <style>
        /* =========================
           GLOBAL APP BACKGROUND
        ========================= */
        .stApp {
            background: linear-gradient(135deg, #f6f8fb 0%, #eef2f7 45%, #f8fafc 100%);
            color: #0f172a;
        }

        /* Hide Streamlit default noise */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Main content spacing */
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1440px;
        }

        /* =========================
           SIDEBAR MAIN STYLE
        ========================= */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e293b 0%, #243044 55%, #182235 100%);
            border-right: 1px solid rgba(255,255,255,0.10);
        }

        section[data-testid="stSidebar"] * {
            color: #e5e7eb !important;
        }

        /* =========================
           SIDEBAR BRAND / LOGO
        ========================= */
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.95rem;
            padding: 0.14rem 0.2rem 1.0rem 0.2rem;
        }
         
       .sidebar-simple-logo {
            width: 58px;
            height: 58px;
            min-width: 58px;
            border-radius: 18px;
            background: linear-gradient(135deg, #38bdf8 0%, #2563eb 55%, #1e3a8a 100%);
            color: #ffffff !important;
            font-weight: 950;
            font-size: 1.05rem;
            letter-spacing: -0.04em;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 16px 32px rgba(37,99,235,0.38);
            border: 1px solid rgba(147,197,253,0.55);
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.95rem;
            padding: 0.9rem 0.2rem 1.5rem 0.2rem;
        }

        .sidebar-title {
            color: #ffffff !important;
            font-size: 1.65rem;
            font-weight: 950;
            line-height: 1.05;
            letter-spacing: -0.04em;
        }   

        .sidebar-title {
            color: #ffffff !important;
            font-size: 1.65rem;
            font-weight: 950;
            line-height: 1.05;
            letter-spacing: -0.04em;
        }

        /* =========================
           SIDEBAR LOGIN CARD
        ========================= */
        section[data-testid="stSidebar"] .stAlert {
            background: rgba(20, 83, 85, 0.55) !important;
            border: 1px solid rgba(45, 212, 191, 0.16) !important;
            border-radius: 16px !important;
            padding: 1rem !important;
        }

        section[data-testid="stSidebar"] .stAlert p {
            font-size: 1rem !important;
            font-weight: 700 !important;
            line-height: 1.5 !important;
        }

        /* =========================
           SIDEBAR HEADINGS
        ========================= */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            font-weight: 900 !important;
        }

        section[data-testid="stSidebar"] h3 {
            font-size: 1.2rem !important;
            margin-top: 1.2rem !important;
            margin-bottom: 0.8rem !important;
        }

        /* Select Intelligence / Select Tool label */
        section[data-testid="stSidebar"] .stRadio > label {
            color: #dbeafe !important;
            font-size: 0.95rem !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 900;
            margin-bottom: 0.55rem;
        }

        /* Radio option cards */
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.65rem;
            transition: all 0.2s ease;
            min-width: 250px;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(59,130,246,0.20);
            border-color: rgba(96,165,250,0.55);
            transform: translateY(-1px);
        }

        /* Radio option text */
        section[data-testid="stSidebar"] div[role="radiogroup"] label p {
            font-size: 1.03rem !important;
            font-weight: 850 !important;
            line-height: 1.35 !important;
        }

        /* Selected radio dot */
        section[data-testid="stSidebar"] input[type="radio"] {
            transform: scale(1.12);
        }

        /* Sidebar logout button */
        section[data-testid="stSidebar"] .stButton > button {
            margin-top: 1rem;
            width: 100%;
            border-radius: 16px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff !important;
            border: 1px solid rgba(147,197,253,0.35);
            font-weight: 850;
            padding: 0.7rem 1rem;
            box-shadow: 0 12px 26px rgba(37,99,235,0.28);
        }

        /* =========================
           PREMIUM CARDS
        ========================= */
        .premium-card {
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 22px;
            padding: 1.2rem 1.25rem;
            box-shadow: 0 18px 45px rgba(15,23,42,0.08);
            backdrop-filter: blur(14px);
            margin-bottom: 1rem;
        }

        .hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%);
            border-radius: 28px;
            padding: 2rem;
            color: white;
            box-shadow: 0 24px 60px rgba(15,23,42,0.28);
            margin-bottom: 1.2rem;
            position: relative;
            overflow: hidden;
        }

        .hero-card:after {
            content: "";
            position: absolute;
            right: -90px;
            top: -90px;
            width: 240px;
            height: 240px;
            background: radial-gradient(circle, rgba(59,130,246,0.45), transparent 70%);
        }

        .hero-eyebrow {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #93c5fd;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            line-height: 1.15;
        }

        .hero-subtitle {
            color: #cbd5e1;
            font-size: 0.98rem;
            max-width: 780px;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }

        .module-card {
            background: #ffffff;
            border: 1px solid rgba(148,163,184,0.28);
            border-radius: 22px;
            padding: 1.2rem;
            box-shadow: 0 14px 32px rgba(15,23,42,0.06);
            min-height: 160px;
        }

        .module-card h3 {
            font-size: 1.05rem;
            margin: 0 0 0.35rem 0;
            color: #0f172a;
        }

        .module-card p {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 0.8rem;
        }

        .pill {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid #bfdbfe;
        }

        /* =========================
           KPI CARDS
        ========================= */
        .kpi-card {
            background: #ffffff;
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: 0 12px 28px rgba(15,23,42,0.06);
        }

        .kpi-label {
            font-size: 0.75rem;
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .kpi-value {
            font-size: 1.75rem;
            font-weight: 850;
            color: #0f172a;
            line-height: 1.1;
        }

        .kpi-delta-good {
            color: #059669;
            font-size: 0.82rem;
            font-weight: 700;
            margin-top: 0.4rem;
        }

        .kpi-delta-bad {
            color: #dc2626;
            font-size: 0.82rem;
            font-weight: 700;
            margin-top: 0.4rem;
        }

        .kpi-delta-neutral {
            color: #64748b;
            font-size: 0.82rem;
            font-weight: 700;
            margin-top: 0.4rem;
        }

        /* =========================
           UPLOAD BOX
        ========================= */
        .upload-shell {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px dashed #93c5fd;
            border-radius: 24px;
            padding: 1.2rem;
            box-shadow: 0 14px 30px rgba(37,99,235,0.07);
            margin-bottom: 1rem;
        }

        div[data-testid="stFileUploader"] {
            background: #ffffff;
            border-radius: 18px;
            padding: 0.8rem;
            border: 1px solid rgba(148,163,184,0.25);
        }

        /* =========================
           TABS
        ========================= */
        button[data-baseweb="tab"] {
            background: #ffffff;
            border-radius: 14px !important;
            margin-right: 0.35rem;
            border: 1px solid rgba(148,163,184,0.24);
            padding: 0.5rem 1rem;
            font-weight: 700;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: #0f172a;
            color: white;
        }

        /* =========================
           BUTTONS
        ========================= */
        .stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(37,99,235,0.25);
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            font-weight: 800;
            padding: 0.6rem 1rem;
            box-shadow: 0 10px 24px rgba(37,99,235,0.22);
        }

        .stButton > button:hover {
            border-color: #1d4ed8;
            transform: translateY(-1px);
        }

        /* =========================
           DATAFRAME / TABLE
        ========================= */
        div[data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(148,163,184,0.25);
            box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        }

        div[data-testid="stDataFrame"] table {
            text-align: center !important;
        }

        div[data-testid="stDataFrame"] th {
            text-align: center !important;
            font-weight: 600 !important;
        }

        div[data-testid="stDataFrame"] td {
            text-align: center !important;
        }

        /* =========================
           LOGIN
        ========================= */
        .login-wrapper {
            max-width: 460px;
            margin: 5vh auto 0 auto;
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 30px;
            padding: 2rem;
            box-shadow: 0 26px 70px rgba(15,23,42,0.16);
            backdrop-filter: blur(16px);
        }

        .login-logo {
            width: 58px;
            height: 58px;
            border-radius: 18px;
            background: linear-gradient(135deg, #2563eb, #0f172a);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 900;
            font-size: 1.25rem;
            margin-bottom: 1rem;
        }

        .login-title {
            font-size: 1.7rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }

        .login-subtitle {
            color: #64748b;
            font-size: 0.92rem;
            margin-bottom: 1.4rem;
        }

        /* =========================
           SMALL UTILITY
        ========================= */
        .muted {
            color: #64748b;
            font-size: 0.88rem;
        }

        .divider {
            height: 1px;
            background: rgba(148,163,184,0.25);
            margin: 1rem 0;
        }

        .success-chip {
            display: inline-block;
            background: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 800;
        }

        .warning-chip {
            display: inline-block;
            background: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 800;
        }

        .danger-chip {
            display: inline-block;
            background: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle, eyebrow="PRESSIQ ANALYTICS"):
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None):
    subtitle_html = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div>
            <div class="section-title">{title}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, delta=None, status="neutral"):
    delta_class = {
        "good": "kpi-delta-good",
        "bad": "kpi-delta-bad",
        "neutral": "kpi-delta-neutral",
    }.get(status, "kpi-delta-neutral")

    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def module_card(title, description, tag="Active Module"):
    st.markdown(
        f"""
        <div class="module-card">
            <span class="pill">{tag}</span>
            <h3 style="margin-top:0.9rem;">{title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def upload_box_title(title, subtitle):
    st.markdown(
        f"""
        <div class="upload-shell">
            <div class="section-title">{title}</div>
            <div class="section-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_card(title, body, chip=None, chip_type="success"):
    chip_class = {
        "success": "success-chip",
        "warning": "warning-chip",
        "danger": "danger-chip",
    }.get(chip_type, "success-chip")

    chip_html = f'<span class="{chip_class}">{chip}</span>' if chip else ""

    st.markdown(
        f"""
        <div class="premium-card">
            {chip_html}
            <div class="section-title" style="margin-top:0.75rem;">{title}</div>
            <div class="muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
