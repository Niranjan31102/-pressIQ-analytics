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

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        div[data-testid="stToolbar"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }

        div[data-testid="stDecoration"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }

        div[data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }

        .block-container {
            padding-top: 0.4rem;
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

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0rem 0.1rem 0.8rem 0.1rem;
        }

        .sidebar-simple-logo {
            width: 50px;
            height: 50px;
            min-width: 50px;
            border-radius: 16px;
            background: linear-gradient(135deg, #38bdf8 0%, #2563eb 55%, #1e3a8a 100%);
            color: #ffffff !important;
            font-weight: 950;
            font-size: 0.95rem;
            letter-spacing: -0.04em;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 14px 28px rgba(37,99,235,0.35);
            border: 1px solid rgba(147,197,253,0.55);
        }

        .sidebar-title {
            color: #ffffff !important;
            font-size: 1.35rem;
            font-weight: 950;
            line-height: 1.05;
            letter-spacing: -0.04em;
            white-space: nowrap;
        }

        section[data-testid="stSidebar"] .stAlert {
            background: rgba(20, 83, 85, 0.42) !important;
            border: 1px solid rgba(45, 212, 191, 0.14) !important;
            border-radius: 12px !important;
            padding: 0.45rem 0.55rem !important;
            margin-bottom: 0.75rem !important;
        }

        section[data-testid="stSidebar"] .stAlert p {
            font-size: 0.72rem !important;
            font-weight: 650 !important;
            line-height: 1.25 !important;
            word-break: break-word !important;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #ffffff !important;
            font-weight: 900 !important;
        }

        section[data-testid="stSidebar"] h3 {
            font-size: 1rem !important;
            margin-top: 0.65rem !important;
            margin-bottom: 0.45rem !important;
        }

        section[data-testid="stSidebar"] .stRadio > label {
            color: #dbeafe !important;
            font-size: 0.72rem !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 900;
            margin-bottom: 0.25rem;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 13px;
            padding: 0.55rem 0.65rem;
            margin-bottom: 0.4rem;
            transition: all 0.2s ease;
            min-width: 210px;
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(59,130,246,0.20);
            border-color: rgba(96,165,250,0.55);
            transform: translateY(-1px);
        }

        section[data-testid="stSidebar"] div[role="radiogroup"] label p {
            font-size: 0.86rem !important;
            font-weight: 800 !important;
            line-height: 1.15 !important;
        }

        section[data-testid="stSidebar"] input[type="radio"] {
            transform: scale(1.05);
        }

        section[data-testid="stSidebar"] .stButton > button {
            margin-top: 0.45rem;
            width: 100%;
            border-radius: 13px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff !important;
            border: 1px solid rgba(147,197,253,0.35);
            font-weight: 800;
            padding: 0.45rem 0.75rem;
            box-shadow: 0 10px 20px rgba(37,99,235,0.24);
        }

        /* =========================
           LOGIN PAGE BRAND
        ========================= */
        .login-brand-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.7rem;
        }

        .login-simple-logo {
            width: 62px;
            height: 62px;
            min-width: 62px;
            border-radius: 19px;
            background: linear-gradient(135deg, #38bdf8 0%, #2563eb 55%, #1e3a8a 100%);
            color: #ffffff !important;
            font-weight: 950;
            font-size: 1.15rem;
            letter-spacing: -0.04em;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 16px 32px rgba(37,99,235,0.30);
            border: 1px solid rgba(147,197,253,0.55);
        }

        .login-main-title {
            color: #0f172a !important;
            font-size: 2.7rem;
            font-weight: 950;
            line-height: 1.05;
            letter-spacing: -0.05em;
        }

        .sub-title {
            font-size: 1.05rem;
            color: #334155;
            margin-bottom: 1rem;
        }

        .login-support-footer {
            margin-top: 2.2rem;
            text-align: center;
            color: #64748b;
            font-size: 0.82rem;
            font-weight: 500;
            line-height: 1.6;
        }

        .login-support-footer .support-highlight {
            color: #2563eb;
            font-weight: 800;
        }

        .login-support-footer .support-link {
            color: #2563eb;
            font-weight: 700;
        }

        .login-copyright {
            margin-top: 0.35rem;
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 500;
        }

        /* =========================
           INPUT BOX VISIBILITY
        ========================= */
        div[data-baseweb="input"] {
            background: #ffffff !important;
            border: 1.8px solid #94a3b8 !important;
            border-radius: 14px !important;
            box-shadow: 0 6px 16px rgba(15,23,42,0.06) !important;
        }

        div[data-baseweb="input"] input {
            background: #ffffff !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        div[data-baseweb="input"]:hover {
            border-color: #2563eb !important;
            box-shadow: 0 8px 20px rgba(37,99,235,0.12) !important;
        }

        div[data-baseweb="input"]:focus-within {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.16) !important;
        }

        textarea {
            background: #ffffff !important;
            border: 1.8px solid #94a3b8 !important;
            border-radius: 14px !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        div[data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1.8px solid #94a3b8 !important;
            border-radius: 14px !important;
            box-shadow: 0 6px 16px rgba(15,23,42,0.06) !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: #2563eb !important;
        }

        label,
        .stTextInput label,
        .stSelectbox label,
        .stNumberInput label,
        .stTextArea label,
        .stDateInput label {
            color: #0f172a !important;
            font-weight: 700 !important;
        }

        /* =========================
           COMMON MODULE HERO
        ========================= */
        .module-hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 48%, #2563eb 100%);
            border-radius: 24px;
            padding: 2rem 2.2rem;
            color: #ffffff;
            box-shadow: 0 24px 55px rgba(37,99,235,0.20);
            margin: 1.4rem 0 1.6rem 0;
        }

        .module-hero-title {
            font-size: 2rem;
            font-weight: 950;
            line-height: 1.1;
            margin-bottom: 0.55rem;
            letter-spacing: -0.04em;
            color: #ffffff !important;
        }

        .module-hero-subtitle {
            font-size: 1rem;
            font-weight: 500;
            color: #dbeafe !important;
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
            background: #ffffff !important;
            border-radius: 18px !important;
            padding: 0.8rem !important;
            border: 1.8px solid #94a3b8 !important;
            box-shadow: 0 8px 22px rgba(15,23,42,0.07) !important;
        }

        /* =========================
           INFO / ALERT BOXES
        ========================= */
        .stAlert {
            border-radius: 14px !important;
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
        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            border-radius: 14px;
            border: 1px solid rgba(37,99,235,0.25);
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white !important;
            font-weight: 800;
            padding: 0.6rem 1rem;
            box-shadow: 0 10px 24px rgba(37,99,235,0.22);
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover {
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

        @media (max-width: 768px) {
            .login-main-title {
                font-size: 2rem;
            }

            .login-brand-row {
                gap: 0.75rem;
            }

            .module-hero-title {
                font-size: 1.45rem;
            }

            .module-hero-card {
                padding: 1.4rem;
            }
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


def module_hero(title, subtitle):
    st.markdown(
        f"""
        <div class="module-hero-card">
            <div class="module-hero-title">{title}</div>
            <div class="module-hero-subtitle">{subtitle}</div>
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
