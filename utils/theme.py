import streamlit as st


def apply_midnight_pro_theme():
    """
    Shared Midnight Pro design system for Finance Assistant.
    Apply once near the top of app.py.
    """
    st.markdown(
        """
        <style>
        :root {
            --bg: #0b1020;
            --bg-soft: #111827;
            --panel: #131c2f;
            --panel-2: #172036;
            --border: #26324a;
            --text: #f8fafc;
            --muted: #94a3b8;
            --accent: #6d7cff;
            --accent-2: #8b5cf6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --cyan: #38bdf8;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top right, rgba(109,124,255,0.08), transparent 28%),
                linear-gradient(180deg, #0b1020 0%, #0a0f1b 100%);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"] {
            right: 0.75rem;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1500px;
            padding-top: 1.6rem;
            padding-bottom: 2.5rem;
            padding-left: 2.1rem;
            padding-right: 2.1rem;
        }

        /* Typography */
        h1, h2, h3, h4 {
            color: var(--text) !important;
            letter-spacing: -0.025em;
        }

        h1 {
            font-size: 2.5rem !important;
            font-weight: 760 !important;
            margin-bottom: 0.25rem !important;
        }

        h2 {
            font-weight: 720 !important;
        }

        .stCaption,
        [data-testid="stCaptionContainer"] {
            color: var(--muted) !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, #10182a 0%, #0e1626 100%);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 0.85rem;
        }

        [data-testid="stSidebar"] h2 {
            font-size: 1.15rem !important;
            margin-bottom: 0.05rem !important;
        }

        [data-testid="stSidebar"] .stCaption {
            font-size: 0.69rem !important;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #74829b !important;
            margin-bottom: 0.25rem !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: var(--border);
            margin: 0.6rem 0;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.22rem;
        }

        [data-testid="stSidebar"] .stButton {
            margin-bottom: 0.02rem;
        }

        [data-testid="stSidebar"] .stButton > button {
            min-height: 2.1rem;
            border-radius: 9px;
            border: 1px solid transparent;
            background: transparent;
            color: #cbd5e1;
            justify-content: flex-start;
            padding: 0.34rem 0.72rem;
            font-size: 0.84rem;
            font-weight: 560;
            box-shadow: none;
            transition: 0.15s ease;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(255,255,255,0.05);
            border-color: #2b3954;
            color: #ffffff;
            transform: translateX(2px);
        }

        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background:
                linear-gradient(90deg, rgba(109,124,255,0.22), rgba(139,92,246,0.14));
            border-color: rgba(109,124,255,0.50);
            color: #ffffff;
            box-shadow:
                inset 3px 0 0 var(--accent),
                0 8px 22px rgba(109,124,255,0.08);
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background:
                linear-gradient(180deg, rgba(23,32,54,0.97), rgba(17,24,39,0.97));
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            min-height: 112px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.14);
            transition: 0.18s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: #3b4c6d;
            box-shadow: 0 16px 36px rgba(0,0,0,0.18);
        }

        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 0.8rem !important;
        }

        [data-testid="stMetricValue"] {
            color: #f8fafc !important;
            font-weight: 740 !important;
            font-size: clamp(1.55rem, 2vw, 2.25rem) !important;
            line-height: 1.05 !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.76rem !important;
        }

        /* Containers / borders */
        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: rgba(19,28,47,0.72);
            overflow: hidden;
        }

        [data-testid="stForm"] {
            background: rgba(19,28,47,0.72);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1rem 0.25rem 1rem;
        }

        /* Inputs */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] > div,
        .stDateInput input {
            background: #111827 !important;
            color: #f8fafc !important;
            border-color: #2a3750 !important;
            border-radius: 10px !important;
        }

        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px rgba(109,124,255,0.35) !important;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            border-radius: 10px;
            border: 1px solid #2a3750;
            background: #172036;
            color: #f8fafc;
            font-weight: 620;
            box-shadow: none;
            transition: 0.16s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: #526990;
            background: #1b2742;
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(0,0,0,0.12);
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            border-color: transparent;
            color: white;
            box-shadow: 0 10px 22px rgba(109,124,255,0.20);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            border-bottom: 1px solid var(--border);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 9px 9px 0 0;
            color: #94a3b8;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
        }

        .stTabs [aria-selected="true"] {
            color: #ffffff !important;
            background: rgba(109,124,255,0.10);
        }

        /* Dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
            background: #111827;
        }

        [data-testid="stDataFrame"] [role="columnheader"] {
            background: #172036 !important;
        }

        /* Alerts */
        [data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid var(--border);
        }

        hr {
            border-color: var(--border) !important;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        /* Reusable helpers */
        .fa-page-header {
            margin-bottom: 1.15rem;
        }

        .fa-eyebrow {
            color: #7f8ca5;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .fa-card {
            background:
                linear-gradient(180deg, rgba(23,32,54,0.97), rgba(17,24,39,0.97));
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.05rem 1.1rem;
            box-shadow: 0 12px 30px rgba(0,0,0,0.14);
            transition: 0.18s ease;
        }

        .fa-card:hover {
            transform: translateY(-1px);
            border-color: #3b4c6d;
        }

        .fa-card-title {
            color: #f8fafc;
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .fa-muted {
            color: var(--muted);
        }

        .fa-badge {
            display: inline-block;
            padding: 0.24rem 0.52rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid #334155;
            background: rgba(255,255,255,0.03);
        }

        .fa-kpi {
            border-radius: 16px;
            padding: 1rem 1.05rem;
            background: linear-gradient(180deg, rgba(23,32,54,0.97), rgba(17,24,39,0.97));
            border: 1px solid var(--border);
            min-height: 114px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.14);
        }

        .fa-kpi.success { border-top: 2px solid rgba(34,197,94,0.8); }
        .fa-kpi.violet  { border-top: 2px solid rgba(139,92,246,0.85); }
        .fa-kpi.warning { border-top: 2px solid rgba(245,158,11,0.85); }
        .fa-kpi.danger  { border-top: 2px solid rgba(239,68,68,0.9); }
        .fa-kpi.info    { border-top: 2px solid rgba(56,189,248,0.85); }

        .fa-kpi-label {
            color: var(--muted);
            font-size: 0.78rem;
            margin-bottom: 0.42rem;
        }

        .fa-kpi-value {
            color: var(--text);
            font-size: clamp(1.45rem, 2vw, 2.1rem);
            font-weight: 760;
            line-height: 1.05;
        }

        .fa-kpi-note {
            color: #8090aa;
            font-size: 0.72rem;
            margin-top: 0.45rem;
        }

        .fa-positive { color: var(--success); }
        .fa-negative { color: #fb7185; }
        .fa-warning-text { color: #fbbf24; }

        .fa-progress-track {
            height: 5px;
            background: #202c43;
            border-radius: 999px;
            overflow: hidden;
        }

        .fa-progress-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--accent), var(--accent-2));
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title, subtitle=None, eyebrow=None):
    eyebrow_html = (
        f'<div class="fa-eyebrow">{eyebrow}</div>'
        if eyebrow
        else ""
    )

    subtitle_html = (
        f'<div class="fa-muted">{subtitle}</div>'
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="fa-page-header">
            {eyebrow_html}
            <h1>{title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title, body):
    st.markdown(
        f"""
        <div class="fa-card">
            <div class="fa-card-title">{title}</div>
            <div class="fa-muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )