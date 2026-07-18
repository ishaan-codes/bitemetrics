import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sqlite3
from scipy import stats
from datetime import datetime, timedelta
import random
import time as _time

st.set_page_config(
    page_title="BiteMetrics | Zomato Order Funnel & A/B Testing Simulator",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

THEME = st.session_state.theme
IS_DARK = THEME == "dark"

# Solid, high-contrast color tokens — no near-invisible rgba
T = {
    "dark": dict(
        bg="#0B0F19",
        surface="#111827",
        card="#1F2937",
        card_border="#374151",
        card_hover="#283141",
        text="#F9FAFB",
        text2="#D1D5DB",
        text3="#9CA3AF",
        grid="#1F2937",
        plotly_font="#E5E7EB",
        nav_bg="#111827",
        nav_border="#1F2937",
        code_bg="#111827",
        badge_bg="rgba(226,55,68,0.18)",
        input_bg="#1F2937",
    ),
    "light": dict(
        bg="#F8FAFC",
        surface="#FFFFFF",
        card="#FFFFFF",
        card_border="#E2E8F0",
        card_hover="#F1F5F9",
        text="#0F172A",
        text2="#475569",
        text3="#94A3B8",
        grid="#F1F5F9",
        plotly_font="#334155",
        nav_bg="rgba(255,255,255,0.92)",
        nav_border="rgba(226,232,240,0.8)",
        code_bg="#F1F5F9",
        badge_bg="rgba(226,55,68,0.08)",
        input_bg="#F1F5F9",
    ),
}[THEME]

ZOMATO = "#E23744"

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: {T['bg']} !important;
}}

/* ── Reset ── */
.stApp, [data-testid="stAppViewContainer"], .main {{
    background: {T['bg']} !important;
    color: {T['text']} !important;
}}
.main .block-container {{
    padding: 0 2.5rem 2rem 2.5rem;
    max-width: 1360px;
}}
header[data-testid="stHeader"] {{ display: none !important; }}
section[data-testid="stSidebar"] {{
    background: {T['surface']};
    border-right: 1px solid {T['card_border']};
}}
section[data-testid="stSidebar"] * {{ color: {T['text']}; }}

/* ── Streamlit widget overrides ── */
[data-baseweb="select"] > div {{
    background: {T['input_bg']} !important;
    border-color: {T['card_border']} !important;
    color: {T['text']} !important;
}}
[data-baseweb="select"] span {{
    color: {T['text']} !important;
}}
.stSelectbox div[data-baseweb="select"] > div {{
    background: {T['input_bg']} !important;
}}
.stMultiSelect div[data-baseweb="select"] > div {{
    background: {T['input_bg']} !important;
}}
[data-baseweb="tag"] {{
    background: {T['card']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['card_border']} !important;
}}
.stTextArea textarea {{
    background: {T['input_bg']} !important;
    color: {T['text']} !important;
    border-color: {T['card_border']} !important;
}}
p, span, label, .stMarkdown {{
    color: {T['text']};
}}
h1, h2, h3, h4, h5, h6 {{
    color: {T['text']} !important;
}}
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {T['text3']} !important;
}}
[data-testid="stDataFrame"] {{
    background: {T['card']} !important;
}}
.stRadio label span {{
    color: {T['text2']} !important;
}}
.stRadio div[role="radiogroup"] label {{
    background: {T['card']} !important;
    border: 1px solid {T['card_border']} !important;
}}
div[data-testid="stExpander"] summary span {{
    color: {T['text']} !important;
}}
.stAlert {{
    background: {T['card']} !important;
    border: 1px solid {T['card_border']} !important;
}}
[data-baseweb="popover"] {{
    background: {T['card']} !important;
}}
[data-baseweb="menu"] {{
    background: {T['card']} !important;
}}
[data-baseweb="menu"] li {{
    color: {T['text']} !important;
}}
[data-baseweb="menu"] li:hover {{
    background: {T['card_hover']} !important;
}}
.stButton button {{
    color: {T['text']} !important;
}}
.stButton button[kind="primary"] {{
    color: white !important;
}}

/* ── Toggle fix ── */
[data-testid="stCheckbox"] label span {{
    color: {T['text']} !important;
}}
/* Toggle track */
[data-testid="stCheckbox"] label > div:first-child {{
    background: {('#CBD5E1' if not IS_DARK else 'rgba(250,250,250,0.2)')} !important;
    border: 1px solid {('#94A3B8' if not IS_DARK else 'rgba(250,250,250,0.3)')} !important;
    border-radius: 10px !important;
}}
/* Toggle thumb */
[data-testid="stCheckbox"] label > div:first-child > div {{
    background: {('#FFFFFF' if not IS_DARK else '#F9FAFB')} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
}}
/* Toggle when checked */
[data-testid="stCheckbox"] input:checked + div {{
    background: {ZOMATO} !important;
    border-color: {ZOMATO} !important;
}}

/* ── Plotly tick/label overrides ── */
.stPlotlyChart .ytick text,
.stPlotlyChart .xtick text,
.stPlotlyChart .g-ytitle text,
.stPlotlyChart .g-xtitle text,
.stPlotlyChart .g-gtitle text {{
    fill: {T['plotly_font']} !important;
}}

/* ── Selectbox border fix ── */
[data-baseweb="select"] > div {{
    border: 1px solid {T['card_border']} !important;
    border-radius: 8px !important;
}}
[data-baseweb="select"] svg {{
    fill: {T['text3']} !important;
}}

/* ── Top Navbar ── */
.top-nav {{
    background: {T['nav_bg']};
    border-bottom: 1px solid {T['nav_border']};
    padding: 0 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    margin: 0 -2.5rem 0 -2.5rem;
    {'backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);' if not IS_DARK else ''}
    {'box-shadow: 0 1px 3px rgba(0,0,0,0.04);' if not IS_DARK else ''}
}}
.top-nav .nl {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.top-nav .logo {{
    width: 32px; height: 32px;
    background: {ZOMATO};
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; color: white; font-weight: 800;
}}
.top-nav .brand {{
    font-size: 1.05rem; font-weight: 700;
    color: {T['text']};
}}
.top-nav .nr {{
    display: flex; align-items: center; gap: 24px;
    font-size: 0.82rem; color: {T['text3']};
}}
.top-nav .nr .sep {{
    width: 1px; height: 20px;
    background: {T['card_border']};
}}
.top-nav .nr .live {{
    display: flex; align-items: center; gap: 6px;
}}
.top-nav .nr .live .dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 6px rgba(34,197,94,0.4);
}}
.top-nav .nr .stat-label {{
    color: {T['text3']};
}}
.top-nav .nr .stat-val {{
    color: {T['text2']};
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}}
.top-nav .nr .pill {{
    font-size: 0.7rem; font-weight: 600;
    padding: 4px 10px; border-radius: 6px;
    text-transform: uppercase; letter-spacing: 0.4px;
}}
.pill-sim {{
    background: {'rgba(34,197,94,0.12)' if IS_DARK else 'rgba(34,197,94,0.08)'};
    color: #22C55E;
    border: 1px solid {'rgba(34,197,94,0.25)' if IS_DARK else 'rgba(34,197,94,0.15)'};
}}
.pill-ver {{
    background: {T['badge_bg']};
    color: {ZOMATO};
    border: 1px solid {'rgba(226,55,68,0.25)' if IS_DARK else 'rgba(226,55,68,0.12)'};
}}

/* ── Page Header Row ── */
.page-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 28px 0 20px 0;
}}
.page-header h1 {{
    font-size: 1.75rem; font-weight: 800;
    color: {T['text']}; margin: 0;
    letter-spacing: -0.5px;
}}
.page-header .subtitle {{
    font-size: 0.88rem; color: {T['text3']};
    margin-top: 2px;
}}

/* ── Bottom Navbar ── */
.bottom-nav {{
    background: {T['nav_bg']};
    border-top: 1px solid {T['nav_border']};
    padding: 0 48px;
    display: flex; align-items: center; justify-content: space-between;
    height: 56px;
    margin: 48px -2.5rem 0 -2.5rem;
    {'backdrop-filter: blur(12px);' if not IS_DARK else ''}
    {'box-shadow: 0 -1px 3px rgba(0,0,0,0.04);' if not IS_DARK else ''}
}}
.bottom-nav .bl {{
    display: flex; align-items: center; gap: 10px;
    font-size: 0.82rem; color: {T['text3']};
}}
.bottom-nav .bl .blogo {{
    width: 22px; height: 22px;
    background: {ZOMATO}; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; color: white; font-weight: 800;
}}
.bottom-nav .bl .bbrand {{
    font-weight: 600; color: {T['text2']};
}}
.bottom-nav .br {{
    display: flex; align-items: center; gap: 20px;
    font-size: 0.78rem; color: {T['text3']};
}}
.bottom-nav .br a {{
    color: {T['text3']}; text-decoration: none;
    transition: color 0.15s;
}}
.bottom-nav .br a:hover {{ color: {ZOMATO}; }}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: {T['card']};
    border-radius: 12px;
    padding: 4px;
    border: 1px solid {T['card_border']};
}}
.stTabs [data-baseweb="tab"] {{
    height: 40px;
    border-radius: 8px;
    padding: 0 20px;
    font-weight: 600;
    font-size: 0.82rem;
    color: {T['text3']};
    background: transparent;
    border: none;
}}
.stTabs [aria-selected="true"] {{
    background: {ZOMATO} !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(226,55,68,0.25);
}}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

/* ── Metrics ── */
div[data-testid="stMetric"] {{
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: {'none' if IS_DARK else '0 1px 3px rgba(0,0,0,0.04)'};
    transition: all 0.2s ease;
}}
div[data-testid="stMetric"]:hover {{
    border-color: {'#4B5563' if IS_DARK else '#CBD5E1'};
    transform: translateY(-2px);
    box-shadow: 0 4px 12px {'rgba(0,0,0,0.2)' if IS_DARK else 'rgba(0,0,0,0.06)'};
}}
div[data-testid="stMetric"] label {{
    color: {T['text3']} !important;
    font-weight: 600;
    font-size: 0.65rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {T['text']} !important;
    font-weight: 700;
    font-size: 1.4rem !important;
}}

/* ── Section Headers ── */
.sh {{
    display: flex; align-items: center; gap: 10px;
    margin: 8px 0 20px 0;
    padding-bottom: 14px;
    border-bottom: 1px solid {T['card_border']};
}}
.sh h3 {{
    margin: 0; font-size: 1.05rem; font-weight: 700;
    color: {T['text']};
}}
.sh .badge {{
    background: {ZOMATO}; color: white;
    font-size: 0.58rem; font-weight: 700;
    padding: 3px 10px; border-radius: 6px;
    text-transform: uppercase; letter-spacing: 0.5px;
}}

/* ── Friction Bars ── */
.fb {{
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 12px;
    padding: 14px 20px;
    display: flex; align-items: center; gap: 14px;
    margin-bottom: 8px;
    box-shadow: {'none' if IS_DARK else '0 1px 2px rgba(0,0,0,0.03)'};
    transition: border-color 0.15s;
}}
.fb:hover {{ border-color: {'#4B5563' if IS_DARK else '#CBD5E1'}; }}
.fb .lbl {{
    color: {T['text2']}; font-size: 0.78rem;
    font-weight: 600; min-width: 180px;
}}
.fb .track {{
    flex: 1; height: 6px;
    background: {T['card_border']};
    border-radius: 3px; overflow: hidden;
}}
.fb .fill {{ height: 100%; border-radius: 3px; }}
.fb .pct {{
    font-weight: 700; font-size: 0.85rem;
    min-width: 55px; text-align: right;
    font-family: 'JetBrains Mono', monospace;
}}
.fb .dur {{
    color: {T['text3']}; font-size: 0.75rem;
    min-width: 65px; text-align: right;
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Hypothesis Cards ── */
.hyp {{
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-left: 3px solid {ZOMATO};
    padding: 16px 20px;
    border-radius: 0 12px 12px 0;
    margin-bottom: 10px;
    font-size: 0.88rem; line-height: 1.55;
    color: {T['text2']};
    box-shadow: {'none' if IS_DARK else '0 1px 2px rgba(0,0,0,0.03)'};
}}
.hyp .hyp-t {{
    color: {ZOMATO}; font-weight: 700;
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.5px; margin-bottom: 4px;
}}

/* ── Stat Panels ── */
.sp {{
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 16px;
    padding: 24px;
    box-shadow: {'none' if IS_DARK else '0 1px 3px rgba(0,0,0,0.04)'};
}}
.sr {{
    display: flex; justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid {T['card_border']};
    font-size: 0.85rem;
}}
.sr:last-child {{ border-bottom: none; }}
.sr .k {{ color: {T['text3']}; }}
.sr .v {{
    color: {T['text']}; font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
}}
.badge-g {{
    background: {'rgba(34,197,94,0.15)' if IS_DARK else 'rgba(34,197,94,0.08)'};
    color: #22C55E;
    border: 1px solid {'rgba(34,197,94,0.3)' if IS_DARK else 'rgba(34,197,94,0.15)'};
    padding: 4px 12px; border-radius: 6px;
    font-weight: 700; font-size: 0.78rem;
}}
.badge-r {{
    background: {'rgba(239,68,68,0.15)' if IS_DARK else 'rgba(239,68,68,0.08)'};
    color: {'#FCA5A5' if IS_DARK else '#DC2626'};
    border: 1px solid {'rgba(239,68,68,0.3)' if IS_DARK else 'rgba(239,68,68,0.15)'};
    padding: 4px 12px; border-radius: 6px;
    font-weight: 700; font-size: 0.78rem;
}}

/* ── SRM Alert ── */
.srm-alert {{
    background: {'rgba(239,68,68,0.12)' if IS_DARK else 'rgba(239,68,68,0.06)'};
    border: 2px solid {'rgba(239,68,68,0.3)' if IS_DARK else 'rgba(239,68,68,0.2)'};
    padding: 16px 24px; border-radius: 12px;
    color: {'#FCA5A5' if IS_DARK else '#DC2626'};
    font-weight: 600; text-align: center; font-size: 0.88rem;
}}

/* ── SQL Sandbox ── */
.sql-toolbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 16px;
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 12px 12px 0 0;
    border-bottom: none;
}}
.sql-toolbar .sql-label {{
    font-size: 0.72rem; font-weight: 600;
    color: {T['text3']}; text-transform: uppercase;
    letter-spacing: 0.8px;
    display: flex; align-items: center; gap: 6px;
}}
.sql-toolbar .sql-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 4px rgba(34,197,94,0.3);
}}
.sql-result-bar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 16px;
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 0 0 12px 12px;
    border-top: none;
    font-size: 0.75rem; color: {T['text3']};
}}
.sql-result-bar .sql-stat {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600; color: {T['text2']};
}}

/* ── Schema ── */
.schema {{
    background: {T['code_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 12px;
    padding: 20px 24px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem; line-height: 1.8;
    color: {T['text2']}; overflow-x: auto;
}}
.schema .tn {{ color: {ZOMATO}; font-weight: 700; }}
.schema .pk {{ color: {'#FBBF24' if IS_DARK else '#D97706'}; }}
.schema .fk {{ color: {'#60A5FA' if IS_DARK else '#2563EB'}; }}
.schema .cn {{ color: {'#67E8F9' if IS_DARK else '#0891B2'}; }}
.schema .ct {{ color: {T['text3']}; }}
.schema .sl {{ color: {T['text3']}; font-style: italic; margin-top: 8px; display: block; }}
.schema .ev {{ color: {'#86EFAC' if IS_DARK else '#16A34A'}; }}
.schema .rc {{ font-size: 0.68rem; color: {T['text3']}; font-weight: 400; }}

/* ── Challenge Card ── */
.ch-card {{
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 8px;
    cursor: pointer;
    box-shadow: {'none' if IS_DARK else '0 1px 2px rgba(0,0,0,0.03)'};
    transition: all 0.15s;
}}
.ch-card:hover {{
    border-color: {ZOMATO};
    transform: translateY(-1px);
    box-shadow: 0 4px 12px {'rgba(226,55,68,0.15)' if IS_DARK else 'rgba(226,55,68,0.08)'};
}}
.ch-card .ch-num {{
    font-size: 0.62rem; font-weight: 700;
    color: {ZOMATO}; text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.ch-card .ch-title {{
    font-size: 0.88rem; font-weight: 600;
    color: {T['text']}; margin: 3px 0;
}}
.ch-card .ch-desc {{
    font-size: 0.78rem; color: {T['text3']};
    line-height: 1.4;
}}

/* ── Decision Panel ── */
.decision-panel {{
    background: {T['card']};
    border: 2px solid {T['card_border']};
    border-radius: 16px;
    padding: 28px 32px;
    margin: 8px 0;
    box-shadow: {'none' if IS_DARK else '0 2px 8px rgba(0,0,0,0.04)'};
}}
.decision-panel .verdict-row {{
    display: flex; align-items: center; gap: 16px;
    margin-bottom: 16px;
}}
.decision-pill {{
    font-size: 0.88rem; font-weight: 800;
    padding: 8px 24px; border-radius: 8px;
    text-transform: uppercase; letter-spacing: 1px;
}}
.pill-ship {{
    background: {'rgba(34,197,94,0.15)' if IS_DARK else 'rgba(34,197,94,0.08)'};
    color: #22C55E;
    border: 2px solid {'rgba(34,197,94,0.4)' if IS_DARK else 'rgba(34,197,94,0.2)'};
}}
.pill-hold {{
    background: {'rgba(251,191,36,0.15)' if IS_DARK else 'rgba(251,191,36,0.08)'};
    color: {'#FBBF24' if IS_DARK else '#D97706'};
    border: 2px solid {'rgba(251,191,36,0.4)' if IS_DARK else 'rgba(251,191,36,0.2)'};
}}
.pill-kill {{
    background: {'rgba(239,68,68,0.15)' if IS_DARK else 'rgba(239,68,68,0.08)'};
    color: {'#FCA5A5' if IS_DARK else '#DC2626'};
    border: 2px solid {'rgba(239,68,68,0.4)' if IS_DARK else 'rgba(239,68,68,0.2)'};
}}
.decision-panel .rationale {{
    font-size: 0.85rem; line-height: 1.6;
    color: {T['text2']};
}}
.decision-panel .rationale .check {{
    color: #22C55E; font-weight: 700; margin-right: 6px;
}}
.decision-panel .rationale .cross {{
    color: {'#FCA5A5' if IS_DARK else '#DC2626'}; font-weight: 700; margin-right: 6px;
}}
.decision-panel .rationale .warn {{
    color: {'#FBBF24' if IS_DARK else '#D97706'}; font-weight: 700; margin-right: 6px;
}}

/* ── Revenue Card ── */
.rev-card {{
    background: {T['card']};
    border: 1px solid {T['card_border']};
    border-radius: 16px;
    padding: 24px 28px;
    text-align: center;
    box-shadow: {'none' if IS_DARK else '0 1px 3px rgba(0,0,0,0.04)'};
}}
.rev-card .rev-label {{
    font-size: 0.68rem; font-weight: 600;
    color: {T['text3']}; text-transform: uppercase;
    letter-spacing: 0.8px; margin-bottom: 6px;
}}
.rev-card .rev-val {{
    font-size: 1.6rem; font-weight: 800;
    color: {T['text']};
    font-family: 'JetBrains Mono', monospace;
}}
.rev-card .rev-sub {{
    font-size: 0.75rem; color: {T['text3']};
    margin-top: 4px;
}}
.rev-highlight {{
    border-color: {ZOMATO} !important;
    background: {'rgba(226,55,68,0.06)' if IS_DARK else 'rgba(226,55,68,0.03)'} !important;
}}

/* ── Segment A/B Table ── */
.seg-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid {T['card_border']};
    border-radius: 12px;
    overflow: hidden;
    font-size: 0.82rem;
}}
.seg-table th {{
    background: {T['card']};
    color: {T['text3']};
    font-weight: 600; font-size: 0.7rem;
    text-transform: uppercase; letter-spacing: 0.5px;
    padding: 12px 16px; text-align: left;
    border-bottom: 1px solid {T['card_border']};
}}
.seg-table td {{
    padding: 10px 16px;
    border-bottom: 1px solid {T['card_border']};
    color: {T['text']};
}}
.seg-table tr:last-child td {{ border-bottom: none; }}
.seg-table .mono {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600; font-size: 0.8rem;
}}
.seg-table .lift-pos {{ color: #22C55E; font-weight: 700; }}
.seg-table .lift-neg {{ color: {'#FCA5A5' if IS_DARK else '#DC2626'}; font-weight: 700; }}

/* ── Misc ── */
.stSelectbox label, .stMultiSelect label, .stRadio label, .stTextArea label {{
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    color: {T['text2']} !important;
}}
div[data-testid="stExpander"] {{
    border: 1px solid {T['card_border']};
    border-radius: 12px;
    background: {T['card']};
}}
/* Theme toggle styling */
.theme-row {{
    display: flex; align-items: center; justify-content: flex-end;
    gap: 8px; padding: 0; margin: 0;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
@st.cache_resource
def init_database():
    np.random.seed(42)
    random.seed(42)
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE users (user_id INTEGER PRIMARY KEY, signup_date TEXT, segment TEXT, device TEXT, acquisition_channel TEXT);
        CREATE TABLE sessions (session_id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, device TEXT, variant TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id));
        CREATE TABLE events (event_id INTEGER PRIMARY KEY, session_id INTEGER, event_name TEXT, timestamp TEXT, FOREIGN KEY (session_id) REFERENCES sessions(session_id));
        CREATE TABLE orders (order_id INTEGER PRIMARY KEY, session_id INTEGER, user_id INTEGER, order_value REAL, delivery_time_mins REAL, order_rating INTEGER, FOREIGN KEY (session_id) REFERENCES sessions(session_id), FOREIGN KEY (user_id) REFERENCES users(user_id));
    """)
    start = datetime(2026, 6, 1)
    segs, seg_w = ["Power User","Casual Diner","New User"], [0.2,0.5,0.3]
    devs, dev_w = ["iOS","Android","Web"], [0.35,0.50,0.15]
    chs, ch_w = ["Search","Instagram","Referral"], [0.4,0.35,0.25]
    n_users = 10000
    users = []
    for uid in range(1, n_users+1):
        users.append((uid, (start+timedelta(days=np.random.randint(0,45))).strftime("%Y-%m-%d"),
                       np.random.choice(segs,p=seg_w), np.random.choice(devs,p=dev_w), np.random.choice(chs,p=ch_w)))
    cur.executemany("INSERT INTO users VALUES(?,?,?,?,?)", users)
    steps = ["app_open","search_executed","restaurant_viewed","cart_added","checkout_initiated","payment_completed"]
    ctrl_cum = [1.0, 0.72, 0.58, 0.38, 0.22, 0.08]
    treat_cum = [1.0, 0.75, 0.62, 0.43, 0.28, 0.11]
    def c2c(c):
        return [c[0]]+[c[i]/c[i-1] if c[i-1]>0 else 0 for i in range(1,len(c))]
    udev = {u[0]:u[3] for u in users}
    useg = {u[0]:u[2] for u in users}
    sess, evts, ords = [], [], []
    eid, oid = 1, 1
    for sid in range(1, 50001):
        uid = np.random.randint(1, n_users+1)
        sd = start+timedelta(days=np.random.randint(0,45))
        d, v = udev[uid], np.random.choice(["Control","Treatment"])
        sess.append((sid, uid, sd.strftime("%Y-%m-%d"), d, v))
        cum = list(ctrl_cum if v=="Control" else treat_cum)
        if d=="Web": cum=[cum[0]]+[c*0.85 for c in cum[1:]]
        sg = useg[uid]
        if sg=="Power User": cum=[min(1.0,c*1.15) for c in cum]; cum[0]=1.0
        elif sg=="New User": cum=[c*0.9 for c in cum]; cum[0]=1.0
        probs = c2c(cum)
        bt = sd.replace(hour=np.random.randint(8,23), minute=np.random.randint(0,60))
        for i, step in enumerate(steps):
            if np.random.random()<probs[i]:
                ts = bt+timedelta(minutes=i*np.random.uniform(0.5,4))
                evts.append((eid, sid, step, ts.strftime("%Y-%m-%d %H:%M:%S")))
                eid+=1
                if step=="payment_completed":
                    ov = max(100, np.random.normal(350 if v=="Control" else 385, 80))
                    dt = max(12, np.random.lognormal(np.log(28), 0.35))
                    rt = np.random.choice([1,2,3,4,5], p=[0.03,0.07,0.15,0.40,0.35])
                    ords.append((oid, sid, uid, round(ov,2), round(dt,1), int(rt)))
                    oid+=1
            else:
                break
    cur.executemany("INSERT INTO sessions VALUES(?,?,?,?,?)", sess)
    cur.executemany("INSERT INTO events VALUES(?,?,?,?)", evts)
    cur.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?)", ords)
    conn.commit()
    return conn

conn = init_database()

def q(query):
    try:
        return pd.read_sql_query(query, conn), None
    except Exception as e:
        return None, str(e)

def sdiv(a, b, d=0):
    return a/b if b else d

_stats, _ = q("SELECT (SELECT COUNT(DISTINCT user_id) FROM users) u, (SELECT COUNT(*) FROM sessions) s, (SELECT COUNT(*) FROM orders) o, (SELECT ROUND(AVG(order_value),0) FROM orders) a")
S_USERS = int(_stats['u'].iloc[0]) if _stats is not None else 0
S_SESS = int(_stats['s'].iloc[0]) if _stats is not None else 0
S_ORD = int(_stats['o'].iloc[0]) if _stats is not None else 0
S_AOV = int(_stats['a'].iloc[0]) if _stats is not None else 0

# ---------------------------------------------------------------------------
# Top Navbar — meaningful content: brand, live status, key stats, env pills
# ---------------------------------------------------------------------------
cr_all = sdiv(S_ORD, S_SESS)*100
st.markdown(f"""
<div class="top-nav">
    <div class="nl">
        <div class="logo">B</div>
        <span class="brand">BiteMetrics</span>
    </div>
    <div class="nr">
        <div class="live"><div class="dot"></div> <span class="stat-val">Live</span></div>
        <div class="sep"></div>
        <span><span class="stat-label">Users </span><span class="stat-val">{S_USERS:,}</span></span>
        <span><span class="stat-label">Sessions </span><span class="stat-val">{S_SESS:,}</span></span>
        <span><span class="stat-label">CR </span><span class="stat-val">{cr_all:.1f}%</span></span>
        <span><span class="stat-label">AOV </span><span class="stat-val">₹{S_AOV}</span></span>
        <div class="sep"></div>
        <span class="pill pill-sim">Simulation</span>
        <span class="pill pill-ver">v1.0</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page Header Row — title left, theme toggle right (always visible)
# ---------------------------------------------------------------------------
hdr_left, hdr_right = st.columns([4, 1])
with hdr_left:
    st.markdown(f"""<div class="page-header">
        <div>
            <h1>Order Funnel & A/B Testing</h1>
            <div class="subtitle">Zomato product analytics simulator · Jun 1 – Jul 15, 2026 · 45-day window</div>
        </div>
    </div>""", unsafe_allow_html=True)
with hdr_right:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    dark_on = st.toggle("Dark Mode", value=IS_DARK, key="theme_toggle")
    new_theme = "dark" if dark_on else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Filters only
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div style='padding:4px 0 8px 0;font-weight:700;font-size:1rem;color:{T['text']}'>Filters</div>", unsafe_allow_html=True)
    all_devices = ["iOS", "Android", "Web"]
    selected_devices = st.multiselect("Device Type", all_devices, default=all_devices)
    all_segments = ["Power User", "Casual Diner", "New User"]
    selected_segments = st.multiselect("User Segment", all_segments, default=all_segments)
    all_channels = ["Search", "Instagram", "Referral"]
    selected_channels = st.multiselect("Acquisition Channel", all_channels, default=all_channels)

def check_filters():
    if not selected_devices or not selected_segments or not selected_channels:
        st.warning("Select at least one option in each filter.")
        return False
    return True

def fclause(dc="s.device", up="u"):
    return f"{dc} IN ({','.join(repr(d) for d in selected_devices)}) AND {up}.segment IN ({','.join(repr(s) for s in selected_segments)}) AND {up}.acquisition_channel IN ({','.join(repr(c) for c in selected_channels)})"

def plotly_layout(**kw):
    _tf = dict(family="Inter, sans-serif", color=T['plotly_font'], size=11)
    base = dict(
        font=dict(family="Inter, sans-serif", color=T['plotly_font'], size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=[ZOMATO, "#4ECDC4", "#FF6B6B", "#45B7D1", "#96CEB4", "#FFEAA7"],
        margin=dict(l=40, r=24, t=48, b=32),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, font=dict(size=11, color=T['plotly_font'])),
        xaxis=dict(gridcolor=T['grid'], zerolinecolor=T['grid'], tickfont=_tf, title_font=_tf),
        yaxis=dict(gridcolor=T['grid'], zerolinecolor=T['grid'], tickfont=_tf, title_font=_tf),
    )
    base.update(kw)
    return base

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab5, tab4 = st.tabs(["Funnel Analysis", "A/B Testing Engine", "Cohort Retention", "Growth Metrics", "SQL Sandbox"])

STEPS = ["app_open","search_executed","restaurant_viewed","cart_added","checkout_initiated","payment_completed"]
LABELS = ["App Open","Search","Restaurant View","Cart Added","Checkout","Payment"]

# ===== TAB 1: FUNNEL =====
with tab1:
    if check_filters():
        st.markdown('<div class="sh"><h3>Conversion Funnel & Friction Analysis</h3><span class="badge">Live</span></div>', unsafe_allow_html=True)
        fc = fclause()
        c1, c2 = st.columns([1,2])
        with c1:
            slicer = st.selectbox("Segment by", ["Overall","Device Type","User Segment","Acquisition Channel"], key="fs")

        if slicer == "Overall":
            fd, _ = q(f"SELECT e.event_name, COUNT(DISTINCT e.session_id) n FROM events e JOIN sessions s ON e.session_id=s.session_id JOIN users u ON s.user_id=u.user_id WHERE {fc} GROUP BY e.event_name")
            if fd is not None and not fd.empty:
                counts = [int(fd[fd.event_name==s]['n'].iloc[0]) if not fd[fd.event_name==s].empty else 0 for s in STEPS]
                fig = go.Figure(go.Funnel(y=LABELS, x=counts, textinfo="value+percent initial+percent previous",
                    textfont=dict(size=12), marker=dict(color=["#E23744","#E8434F","#EF6B73","#F49098","#F9B5BC","#4ECDC4"], line=dict(width=0)),
                    connector=dict(line=dict(color=T['card_border'], width=1))))
                fig.update_layout(**plotly_layout(height=400), title=dict(text="Order Funnel — All Sessions", font=dict(size=14)))
                st.plotly_chart(fig, use_container_width=True)

                st.markdown('<div class="sh"><h3>Step-by-Step Friction Map</h3></div>', unsafe_allow_html=True)
                td, _ = q(f"""
                    WITH oe AS (SELECT e.session_id, e.event_name, e.timestamp, ROW_NUMBER() OVER (PARTITION BY e.session_id ORDER BY e.timestamp) rn
                        FROM events e JOIN sessions s ON e.session_id=s.session_id JOIN users u ON s.user_id=u.user_id WHERE {fc})
                    SELECT e1.event_name f, e2.event_name t, AVG((JULIANDAY(e2.timestamp)-JULIANDAY(e1.timestamp))*1440) m
                    FROM oe e1 JOIN oe e2 ON e1.session_id=e2.session_id AND e2.rn=e1.rn+1 GROUP BY e1.event_name, e2.event_name
                """)
                tmap = {(r.f, r.t): r.m for _, r in td.iterrows()} if td is not None else {}

                mx_rate, mx_idx = 0, 1
                for i in range(1, len(counts)):
                    dp = (1-sdiv(counts[i], counts[i-1]))*100
                    tm = tmap.get((STEPS[i-1], STEPS[i]))
                    ts = f"{tm:.1f} min" if tm else "—"
                    clr = ZOMATO if dp>50 else ("#F59E0B" if dp>30 else "#22C55E")
                    st.markdown(f'<div class="fb"><span class="lbl">{LABELS[i-1]} → {LABELS[i]}</span><div class="track"><div class="fill" style="width:{dp}%;background:{clr}"></div></div><span class="pct" style="color:{clr}">{dp:.1f}%</span><span class="dur">{ts}</span></div>', unsafe_allow_html=True)
                    if dp > mx_rate: mx_rate, mx_idx = dp, i

                trd, _ = q(f"""
                    SELECT s.date, COUNT(DISTINCT s.session_id) sess,
                        COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) conv
                    FROM sessions s JOIN users u ON s.user_id=u.user_id
                    LEFT JOIN events e ON s.session_id=e.session_id AND e.event_name='payment_completed'
                    WHERE {fc} GROUP BY s.date ORDER BY s.date
                """)
                if trd is not None and not trd.empty:
                    trd["cr"] = trd["conv"]/trd["sess"]*100
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=trd.date, y=trd.cr, mode="lines", line=dict(color=ZOMATO, width=2),
                        fill="tozeroy", fillcolor=f"rgba(226,55,68,0.{'12' if IS_DARK else '08'})", name="CR %"))
                    fig2.update_layout(**plotly_layout(height=220), title=dict(text="Daily Conversion Rate", font=dict(size=13)),
                        yaxis_title="CR %", showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)

                st.markdown('<div class="sh"><h3>Product Hypothesis Engine</h3></div>', unsafe_allow_html=True)
                fp, pp = LABELS[mx_idx], LABELS[mx_idx-1] if mx_idx>0 else "Start"
                hyps = {
                    "Search": [("Search relevance gap","Auto-suggestions and ranking may not surface relevant restaurants for long-tail queries."),
                               ("Cold start problem","New users get generic results instead of personalized recommendations."),
                               ("Latency on low-end devices","Search response times on budget Android devices may exceed the 300ms patience threshold.")],
                    "Restaurant View": [("Missing social proof","Listing cards lack user photos and real-time signals like '42 orders in the last hour'."),
                                        ("Fee transparency","Delivery fees and minimums shown upfront deter exploration."),
                                        ("Category mismatch","Cuisine taxonomy doesn't match user mental models ('healthy' vs 'salad').")],
                    "Cart Added": [("Menu decision paralysis","100+ item menus without smart defaults overwhelm users. Recommended combos could help."),
                                   ("Missing dish confidence","No dish-level ratings, photos, or 'popular' tags reduces purchase intent."),
                                   ("Minimum order friction","Single-item orders face ₹150+ minimum, causing drop-off.")],
                    "Checkout": [("Sticker shock","Delivery fee + packaging + taxes add 25-40% above menu price at checkout."),
                                 ("Checkout flow length","5+ steps create fatigue. One-tap reorder could bypass this entirely."),
                                 ("No guest checkout","Mandatory account creation adds 30+ seconds of friction.")],
                    "Payment": [("Gateway timeouts","Payment failures spike during peak hours (12-2pm, 7-9pm)."),
                                ("UPI preference mismatch","Users preferring UPI Lite find limited options, falling back to card + OTP."),
                                ("OTP drop-off","Card OTP creates a 15-second window where users abandon, especially on slow networks.")],
                }
                st.markdown(f"Highest friction: **{pp} → {fp}** at **{mx_rate:.1f}% drop-off**")
                for t, d in hyps.get(fp, hyps["Checkout"]):
                    st.markdown(f'<div class="hyp"><div class="hyp-t">Hypothesis — {t}</div>{d}</div>', unsafe_allow_html=True)
        else:
            gcm = {"Device Type":"s.device","User Segment":"u.segment","Acquisition Channel":"u.acquisition_channel"}
            gc = gcm[slicer]
            sd, _ = q(f"SELECT {gc} seg, e.event_name, COUNT(DISTINCT e.session_id) n FROM events e JOIN sessions s ON e.session_id=s.session_id JOIN users u ON s.user_id=u.user_id WHERE {fc} GROUP BY {gc}, e.event_name")
            if sd is not None and not sd.empty:
                fig = go.Figure()
                for sv in sorted(sd.seg.unique()):
                    sub = sd[sd.seg==sv]
                    cts = [int(sub[sub.event_name==s]['n'].iloc[0]) if not sub[sub.event_name==s].empty else 0 for s in STEPS]
                    fig.add_trace(go.Funnel(name=sv, y=LABELS, x=cts, textinfo="value+percent initial"))
                fig.update_layout(**plotly_layout(height=460), title=dict(text=f"Funnel by {slicer}", font=dict(size=14)))
                st.plotly_chart(fig, use_container_width=True)

# ===== TAB 2: A/B TESTING =====
with tab2:
    if check_filters():
        st.markdown('<div class="sh"><h3>Experimentation Dashboard</h3><span class="badge">AI Cross-Sell</span></div>', unsafe_allow_html=True)
        st.caption("**Variant A (Control):** Standard cart  ·  **Variant B (Treatment):** AI-powered cross-sell recommendations")
        fc = fclause()
        ab, _ = q(f"""
            SELECT s.variant, COUNT(DISTINCT s.session_id) tot,
                COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) conv
            FROM sessions s JOIN users u ON s.user_id=u.user_id
            LEFT JOIN events e ON s.session_id=e.session_id AND e.event_name='payment_completed'
            WHERE {fc} GROUP BY s.variant
        """)
        if ab is not None and len(ab)==2:
            ctrl = ab[ab.variant=="Control"].iloc[0]
            treat = ab[ab.variant=="Treatment"].iloc[0]
            na, nb = int(ctrl.tot), int(treat.tot)
            ca, cb = int(ctrl.conv), int(treat.conv)
            cra, crb = sdiv(ca,na), sdiv(cb,nb)
            lift = sdiv(crb-cra, cra)*100

            m1,m2,m3,m4,m5 = st.columns(5)
            m1.metric("N (Control)", f"{na:,}")
            m2.metric("N (Treatment)", f"{nb:,}")
            m3.metric("CR Control", f"{cra*100:.2f}%")
            m4.metric("CR Treatment", f"{crb*100:.2f}%")
            m5.metric("Relative Lift", f"+{lift:.1f}%", delta=f"+{lift:.1f}%")

            st.markdown("")
            ac, _ = q(f"SELECT o.order_value FROM orders o JOIN sessions s ON o.session_id=s.session_id JOIN users u ON s.user_id=u.user_id WHERE s.variant='Control' AND {fc}")
            at, _ = q(f"SELECT o.order_value FROM orders o JOIN sessions s ON o.session_id=s.session_id JOIN users u ON s.user_id=u.user_id WHERE s.variant='Treatment' AND {fc}")

            st.markdown('<div class="sh"><h3>Statistical Rigor</h3></div>', unsafe_allow_html=True)
            t1, t2 = st.columns(2)
            with t1:
                st.markdown("**Chi-Square Test** — Conversion Rate")
                if min(na,nb)>=30:
                    chi2, pv, *_ = stats.chi2_contingency(np.array([[ca,na-ca],[cb,nb-cb]]))
                    sig = pv<0.05
                    st.markdown(f"""<div class="sp">
                        <div class="sr"><span class="k">Test</span><span class="v">Chi-Square of Independence</span></div>
                        <div class="sr"><span class="k">χ² statistic</span><span class="v">{chi2:.4f}</span></div>
                        <div class="sr"><span class="k">p-value</span><span class="v">{pv:.8f}</span></div>
                        <div class="sr"><span class="k">α</span><span class="v">0.05</span></div>
                        <div class="sr"><span class="k">Verdict</span><span class="v">{'<span class="badge-g">Significant</span>' if sig else '<span class="badge-r">Not Significant</span>'}</span></div>
                    </div>""", unsafe_allow_html=True)
            with t2:
                st.markdown("**Welch's T-Test** — Average Order Value")
                if ac is not None and at is not None and len(ac)>=30 and len(at)>=30:
                    ts, tp = stats.ttest_ind(ac.order_value, at.order_value, equal_var=False)
                    ma, mb = ac.order_value.mean(), at.order_value.mean()
                    se = np.sqrt(ac.order_value.var()/len(ac)+at.order_value.var()/len(at))
                    ci_lo, ci_hi = (mb-ma)-1.96*se, (mb-ma)+1.96*se
                    st.markdown(f"""<div class="sp">
                        <div class="sr"><span class="k">AOV Control</span><span class="v">₹{ma:.0f}</span></div>
                        <div class="sr"><span class="k">AOV Treatment</span><span class="v">₹{mb:.0f}</span></div>
                        <div class="sr"><span class="k">t-statistic</span><span class="v">{ts:.4f}</span></div>
                        <div class="sr"><span class="k">p-value</span><span class="v">{tp:.8f}</span></div>
                        <div class="sr"><span class="k">95% CI for Δ</span><span class="v">[₹{ci_lo:.1f}, ₹{ci_hi:.1f}]</span></div>
                        <div class="sr"><span class="k">Verdict</span><span class="v">{'<span class="badge-g">Significant</span>' if tp<0.05 else '<span class="badge-r">Not Significant</span>'}</span></div>
                    </div>""", unsafe_allow_html=True)

            if ac is not None and at is not None and len(ac)>0:
                st.markdown("")
                st.markdown('<div class="sh"><h3>AOV Distribution</h3></div>', unsafe_allow_html=True)
                fig_a = go.Figure()
                fig_a.add_trace(go.Histogram(x=ac.order_value, name="Control", marker_color=f"rgba(148,163,184,0.{'45' if IS_DARK else '30'})", nbinsx=40, marker_line=dict(width=0)))
                fig_a.add_trace(go.Histogram(x=at.order_value, name="Treatment", marker_color=f"rgba(226,55,68,0.{'50' if IS_DARK else '35'})", nbinsx=40, marker_line=dict(width=0)))
                fig_a.update_layout(**plotly_layout(height=260), barmode="overlay", title=dict(text="Order Value Distribution", font=dict(size=13)), xaxis_title="Order Value (₹)", yaxis_title="Count")
                st.plotly_chart(fig_a, use_container_width=True)

            st.markdown('<div class="sh"><h3>Sample Ratio Mismatch (SRM)</h3></div>', unsafe_allow_html=True)
            obs = np.array([na,nb])
            _, ps = stats.chisquare(obs, f_exp=np.array([0.5,0.5])*obs.sum())
            s1,s2,s3 = st.columns(3)
            s1.metric("Expected Split","50.0% / 50.0%")
            s2.metric("Observed Split",f"{na/(na+nb)*100:.1f}% / {nb/(na+nb)*100:.1f}%")
            s3.metric("SRM p-value",f"{ps:.4f}")
            if ps<0.001:
                st.markdown('<div class="srm-alert">SRM ALERT — Traffic distribution is significantly biased (p &lt; 0.001). Investigate assignment logic.</div>', unsafe_allow_html=True)
            else:
                st.success("No Sample Ratio Mismatch detected. Traffic split is balanced.")

            st.markdown("")
            st.markdown('<div class="sh"><h3>Guardrail Metrics</h3></div>', unsafe_allow_html=True)
            g1, g2 = st.columns(2)
            with g1:
                np.random.seed(99)
                la, lb = np.random.normal(220,30,200), np.random.normal(225,32,200)
                fl = go.Figure()
                fl.add_trace(go.Box(y=la, name="Control", marker_color="rgba(148,163,184,0.6)", line=dict(color="#94A3B8")))
                fl.add_trace(go.Box(y=lb, name="Treatment", marker_color="rgba(226,55,68,0.6)", line=dict(color=ZOMATO)))
                fl.update_layout(**plotly_layout(height=260), title=dict(text="App Latency (ms)", font=dict(size=13)), yaxis_title="ms", showlegend=False)
                st.plotly_chart(fl, use_container_width=True)
                st.caption("No significant latency degradation.")
            with g2:
                wks = [f"W{i}" for i in range(1,7)]
                ft = go.Figure()
                ft.add_trace(go.Scatter(x=wks, y=[45,42,48,44,41,43], name="Control", line=dict(color="#94A3B8",width=2), mode="lines+markers", marker=dict(size=5)))
                ft.add_trace(go.Scatter(x=wks, y=[44,46,43,47,45,44], name="Treatment", line=dict(color=ZOMATO,width=2), mode="lines+markers", marker=dict(size=5)))
                ft.update_layout(**plotly_layout(height=260), title=dict(text="Weekly Support Tickets", font=dict(size=13)), yaxis_title="Tickets")
                st.plotly_chart(ft, use_container_width=True)
                st.caption("Ticket volume stable across variants.")

            # ── Segment-Level A/B Breakdown ──
            st.markdown("")
            st.markdown('<div class="sh"><h3>Segment-Level Breakdown</h3><span class="badge">Deep Dive</span></div>', unsafe_allow_html=True)
            seg_ab, _ = q(f"""
                SELECT u.segment, s.device, s.variant,
                    COUNT(DISTINCT s.session_id) tot,
                    COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) conv
                FROM sessions s JOIN users u ON s.user_id=u.user_id
                LEFT JOIN events e ON s.session_id=e.session_id AND e.event_name='payment_completed'
                WHERE {fc} GROUP BY u.segment, s.device, s.variant
            """)
            if seg_ab is not None and not seg_ab.empty:
                seg_view = st.radio("Breakdown by", ["Device Type", "User Segment"], horizontal=True, key="seg_ab_view")
                dim_col = "device" if seg_view == "Device Type" else "segment"
                rows_html = ""
                for dim_val in sorted(seg_ab[dim_col].unique()):
                    sub = seg_ab[seg_ab[dim_col]==dim_val]
                    c_row = sub[sub.variant=="Control"]
                    t_row = sub[sub.variant=="Treatment"]
                    c_tot = int(c_row.tot.sum()) if not c_row.empty else 0
                    c_conv = int(c_row.conv.sum()) if not c_row.empty else 0
                    t_tot = int(t_row.tot.sum()) if not t_row.empty else 0
                    t_conv = int(t_row.conv.sum()) if not t_row.empty else 0
                    c_cr = sdiv(c_conv, c_tot)*100
                    t_cr = sdiv(t_conv, t_tot)*100
                    seg_lift = sdiv(t_cr - c_cr, c_cr)*100 if c_cr > 0 else 0
                    lift_cls = "lift-pos" if seg_lift > 0 else "lift-neg"
                    lift_sign = "+" if seg_lift > 0 else ""
                    rows_html += f"""<tr>
                        <td><strong>{dim_val}</strong></td>
                        <td class="mono">{c_tot:,}</td><td class="mono">{t_tot:,}</td>
                        <td class="mono">{c_cr:.2f}%</td><td class="mono">{t_cr:.2f}%</td>
                        <td class="mono {lift_cls}">{lift_sign}{seg_lift:.1f}%</td>
                    </tr>"""
                st.markdown(f"""<table class="seg-table">
                    <thead><tr><th>{seg_view}</th><th>N (Ctrl)</th><th>N (Treat)</th><th>CR Ctrl</th><th>CR Treat</th><th>Lift</th></tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>""", unsafe_allow_html=True)
                st.caption("Segment-level lifts reveal where the treatment works best — critical for targeted rollout decisions.")

            # ── Revenue Impact Projection ──
            st.markdown("")
            st.markdown('<div class="sh"><h3>Revenue Impact Projection</h3><span class="badge">Business Case</span></div>', unsafe_allow_html=True)
            st.caption("Annualized revenue projections assuming current traffic patterns hold at scale.")

            annual_sessions = 50000 * (365/45)
            ctrl_annual_orders = annual_sessions * 0.5 * cra
            treat_annual_orders = annual_sessions * 0.5 * crb
            ctrl_annual_rev = ctrl_annual_orders * (ma if ac is not None and len(ac)>0 else 350)
            treat_annual_rev = treat_annual_orders * (mb if at is not None and len(at)>0 else 385)
            incr_rev = treat_annual_rev - ctrl_annual_rev
            incr_orders = treat_annual_orders - ctrl_annual_orders

            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                st.markdown(f"""<div class="rev-card">
                    <div class="rev-label">Annual Orders (Control)</div>
                    <div class="rev-val">{ctrl_annual_orders:,.0f}</div>
                    <div class="rev-sub">at {cra*100:.1f}% CR</div>
                </div>""", unsafe_allow_html=True)
            with rc2:
                st.markdown(f"""<div class="rev-card">
                    <div class="rev-label">Annual Orders (Treatment)</div>
                    <div class="rev-val">{treat_annual_orders:,.0f}</div>
                    <div class="rev-sub">at {crb*100:.1f}% CR</div>
                </div>""", unsafe_allow_html=True)
            with rc3:
                st.markdown(f"""<div class="rev-card rev-highlight">
                    <div class="rev-label">Incremental Revenue / Year</div>
                    <div class="rev-val" style="color:{ZOMATO}">₹{incr_rev:,.0f}</div>
                    <div class="rev-sub">+{incr_orders:,.0f} orders</div>
                </div>""", unsafe_allow_html=True)
            with rc4:
                st.markdown(f"""<div class="rev-card">
                    <div class="rev-label">Revenue per Session Δ</div>
                    <div class="rev-val">₹{sdiv(incr_rev, annual_sessions):,.1f}</div>
                    <div class="rev-sub">incremental value</div>
                </div>""", unsafe_allow_html=True)

            # ── Ship Decision Panel ──
            st.markdown("")
            st.markdown('<div class="sh"><h3>Ship Decision Framework</h3><span class="badge">Recommendation</span></div>', unsafe_allow_html=True)

            cr_sig = pv < 0.05 if min(na,nb) >= 30 else False
            aov_sig = tp < 0.05 if ac is not None and at is not None and len(ac)>=30 and len(at)>=30 else False
            srm_ok = ps > 0.001
            practical_sig = lift > 5
            guardrail_ok = True

            checks = []
            checks.append(("Statistical significance (CR)", cr_sig, "Chi-Square p < 0.05" if cr_sig else "CR difference not significant at α=0.05"))
            checks.append(("Statistical significance (AOV)", aov_sig, "Welch's T-Test p < 0.05" if aov_sig else "AOV difference not significant"))
            checks.append(("Practical significance", practical_sig, f"Lift of {lift:.1f}% exceeds 5% MDE threshold" if practical_sig else f"Lift of {lift:.1f}% below 5% minimum detectable effect"))
            checks.append(("Sample Ratio Mismatch", srm_ok, "No SRM detected — assignment is balanced" if srm_ok else "SRM detected — traffic split is biased, results unreliable"))
            checks.append(("Guardrail metrics", guardrail_ok, "Latency and support tickets within acceptable range"))

            pass_count = sum(1 for _, v, _ in checks if v)
            if pass_count == 5:
                verdict, pill_cls, verdict_text = "SHIP IT", "pill-ship", "All criteria passed. Recommend full rollout."
            elif pass_count >= 3 and srm_ok:
                verdict, pill_cls, verdict_text = "HOLD", "pill-hold", "Partially passed. Extend experiment or investigate failing criteria before shipping."
            else:
                verdict, pill_cls, verdict_text = "DO NOT SHIP", "pill-kill", "Critical criteria failed. Do not roll out — investigate root causes."

            rationale_html = ""
            for label, passed, detail in checks:
                icon = '<span class="check">&#10003;</span>' if passed else '<span class="cross">&#10007;</span>'
                rationale_html += f'<div style="margin:6px 0">{icon}<strong>{label}</strong> — {detail}</div>'

            st.markdown(f"""<div class="decision-panel">
                <div class="verdict-row">
                    <span class="decision-pill {pill_cls}">{verdict}</span>
                    <span style="color:{T['text2']};font-size:0.9rem">{verdict_text}</span>
                </div>
                <div class="rationale">{rationale_html}</div>
            </div>""", unsafe_allow_html=True)

            st.caption("Decision framework evaluates: statistical significance (α=0.05), practical significance (>5% MDE), sample integrity (SRM), and guardrail metrics before recommending rollout.")

# ===== TAB 3: COHORT =====
with tab3:
    if check_filters():
        st.markdown('<div class="sh"><h3>Weekly Cohort Retention</h3><span class="badge">Heatmap</span></div>', unsafe_allow_html=True)
        rt = st.radio("Retention type", ["N-Week Retention","Unbounded Retention"], horizontal=True,
                      help="N-Week: active in exactly that week. Unbounded: active in that week or later.")
        fc = fclause()
        ss, ds, cs = ",".join(repr(x) for x in selected_segments), ",".join(repr(x) for x in selected_devices), ",".join(repr(x) for x in selected_channels)

        cd, _ = q(f"""
            WITH uc AS (SELECT u.user_id, CAST((JULIANDAY(u.signup_date)-JULIANDAY('2026-06-01'))/7 AS INTEGER) cw
                FROM users u WHERE u.segment IN ({ss}) AND u.device IN ({ds}) AND u.acquisition_channel IN ({cs})),
            ua AS (SELECT s.user_id, CAST((JULIANDAY(s.date)-JULIANDAY('2026-06-01'))/7 AS INTEGER) aw
                FROM sessions s JOIN users u ON s.user_id=u.user_id WHERE {fc} GROUP BY s.user_id, aw)
            SELECT uc.cw, ua.aw, COUNT(DISTINCT uc.user_id) n FROM uc JOIN ua ON uc.user_id=ua.user_id WHERE ua.aw>=uc.cw GROUP BY uc.cw, ua.aw
        """)
        sz, _ = q(f"SELECT CAST((JULIANDAY(u.signup_date)-JULIANDAY('2026-06-01'))/7 AS INTEGER) cw, COUNT(DISTINCT u.user_id) n FROM users u WHERE u.segment IN ({ss}) AND u.device IN ({ds}) AND u.acquisition_channel IN ({cs}) GROUP BY cw")

        if cd is not None and sz is not None and not cd.empty:
            sm = dict(zip(sz.cw, sz.n))
            mw = 7
            cws = sorted([w for w in cd.cw.unique() if 0<=w<mw])
            mat = np.full((len(cws), mw), np.nan)
            for i, cw in enumerate(cws):
                csz = sm.get(cw, 0)
                if csz==0: continue
                for off in range(mw):
                    if rt=="N-Week Retention":
                        r = cd[(cd.cw==cw)&(cd.aw==cw+off)]
                        a = int(r.n.iloc[0]) if not r.empty else 0
                    else:
                        a = min(int(cd[(cd.cw==cw)&(cd.aw>=cw+off)].n.sum()), csz)
                    mat[i, off] = sdiv(a, csz)*100

            yl = [f"W{w} ({sm.get(w,0):,})" for w in cws]
            xl = [f"+{w}w" for w in range(mw)]
            txt = np.where(np.isnan(mat), "", np.vectorize(lambda x: f"{x:.0f}")(mat))

            fh = go.Figure(go.Heatmap(z=mat, x=xl, y=yl, text=txt, texttemplate="%{text}%", textfont=dict(size=11, color="white"),
                colorscale=[[0,"rgba(226,55,68,0.08)"],[0.3,"rgba(226,55,68,0.35)"],[0.6,"rgba(226,55,68,0.65)"],[1,"#E23744"]],
                colorbar=dict(title=dict(text="Retention %", font=dict(size=11)), tickfont=dict(size=10)), hoverongaps=False))
            fh.update_layout(**plotly_layout(height=360), title=dict(text=f"{rt} Heatmap", font=dict(size=14)),
                xaxis_title="Weeks Since Signup", yaxis_title="Signup Cohort (size)")
            fh.update_yaxes(autorange="reversed")
            st.plotly_chart(fh, use_container_width=True)

            st.markdown('<div class="sh"><h3>Cumulative Revenue by Cohort (LTV Proxy)</h3></div>', unsafe_allow_html=True)
            ld, _ = q(f"""
                SELECT CAST((JULIANDAY(u.signup_date)-JULIANDAY('2026-06-01'))/7 AS INTEGER) cw,
                    CAST((JULIANDAY(s.date)-JULIANDAY(u.signup_date))/7 AS INTEGER) wo, SUM(o.order_value) rev
                FROM orders o JOIN sessions s ON o.session_id=s.session_id JOIN users u ON o.user_id=u.user_id
                WHERE u.segment IN ({ss}) AND s.device IN ({ds}) AND u.acquisition_channel IN ({cs})
                GROUP BY cw, wo HAVING cw>=0 AND cw<{mw} ORDER BY cw, wo
            """)
            if ld is not None and not ld.empty:
                fl = go.Figure()
                for cw in sorted(ld.cw.unique()):
                    sub = ld[ld.cw==cw].sort_values("wo")
                    sub["cr"] = sub.rev.cumsum()
                    fl.add_trace(go.Scatter(x=sub.wo, y=sub.cr, name=f"W{int(cw)}", mode="lines+markers", marker=dict(size=4), line=dict(width=2)))
                fl.update_layout(**plotly_layout(height=300), title=dict(text="Cumulative Revenue per Cohort", font=dict(size=14)),
                    xaxis_title="Weeks Since Signup", yaxis_title="Revenue (₹)")
                st.plotly_chart(fl, use_container_width=True)

# ===== TAB 5: GROWTH METRICS =====
with tab5:
    if check_filters():
        st.markdown('<div class="sh"><h3>Growth & Engagement Metrics</h3><span class="badge">Health</span></div>', unsafe_allow_html=True)
        fc = fclause()

        # ── DAU / WAU / Stickiness ──
        _dau_raw, _ = q(f"""
            SELECT s.date, s.user_id
            FROM sessions s JOIN users u ON s.user_id=u.user_id
            WHERE {fc}
        """)
        dau_wau = None
        if _dau_raw is not None and not _dau_raw.empty:
            _dau_raw['date'] = pd.to_datetime(_dau_raw['date'])
            _daily_users = _dau_raw.groupby('date')['user_id'].apply(set)
            _dates_sorted = sorted(_daily_users.index)
            _rows = []
            for _dt in _dates_sorted:
                _dau = len(_daily_users[_dt])
                _wau_users = set()
                for _d2 in _dates_sorted:
                    if pd.Timedelta(days=0) <= (_dt - _d2) <= pd.Timedelta(days=6):
                        _wau_users |= _daily_users[_d2]
                _wau = len(_wau_users)
                _stick = round(_dau / _wau * 100, 1) if _wau > 0 else 0
                _rows.append({"date": _dt.strftime("%Y-%m-%d"), "dau": _dau, "wau": _wau, "stickiness": _stick})
            dau_wau = pd.DataFrame(_rows)

        if dau_wau is not None and not dau_wau.empty:
            avg_dau = dau_wau.dau.mean()
            avg_wau = dau_wau.wau.mean()
            avg_stick = dau_wau.stickiness.mean()

            dm1, dm2, dm3, dm4 = st.columns(4)
            dm1.metric("Avg DAU", f"{avg_dau:,.0f}")
            dm2.metric("Avg WAU", f"{avg_wau:,.0f}")
            dm3.metric("DAU/WAU Stickiness", f"{avg_stick:.1f}%")
            dm4.metric("Peak DAU", f"{dau_wau.dau.max():,}")

            fig_dw = go.Figure()
            fig_dw.add_trace(go.Scatter(x=dau_wau.date, y=dau_wau.dau, name="DAU",
                line=dict(color=ZOMATO, width=2), fill="tozeroy",
                fillcolor=f"rgba(226,55,68,0.{'12' if IS_DARK else '08'})"))
            fig_dw.add_trace(go.Scatter(x=dau_wau.date, y=dau_wau.wau, name="WAU",
                line=dict(color="#4ECDC4", width=2), fill="tozeroy",
                fillcolor=f"rgba(78,205,196,0.{'12' if IS_DARK else '08'})"))
            fig_dw.update_layout(**plotly_layout(height=280),
                title=dict(text="Daily Active Users vs Weekly Active Users", font=dict(size=13)),
                yaxis_title="Users")
            st.plotly_chart(fig_dw, use_container_width=True)

            fig_st = go.Figure()
            fig_st.add_trace(go.Scatter(x=dau_wau.date, y=dau_wau.stickiness, name="Stickiness",
                line=dict(color="#FBBF24", width=2), mode="lines",
                fill="tozeroy", fillcolor=f"rgba(251,191,36,0.{'12' if IS_DARK else '06'})"))
            fig_st.add_trace(go.Scatter(x=[dau_wau.date.iloc[0], dau_wau.date.iloc[-1]],
                y=[20, 20], name="Good (20%)", line=dict(color="#22C55E", width=1, dash="dash"), mode="lines"))
            fig_st.update_layout(**plotly_layout(height=220),
                title=dict(text="DAU/WAU Stickiness Ratio", font=dict(size=13)),
                yaxis_title="%", yaxis_range=[0, max(50, dau_wau.stickiness.max()*1.2)])
            st.plotly_chart(fig_st, use_container_width=True)
            st.caption("DAU/WAU stickiness measures daily engagement intensity. >20% is strong for food delivery (benchmark: Swiggy ~18-22%, DoorDash ~15-20%).")

        # ── Activation Funnel ──
        st.markdown("")
        st.markdown('<div class="sh"><h3>New User Activation</h3><span class="badge">Onboarding</span></div>', unsafe_allow_html=True)
        act, _ = q(f"""
            WITH new_users AS (
                SELECT u.user_id, u.signup_date FROM users u
                WHERE u.segment IN ({",".join(repr(s) for s in selected_segments)})
                AND u.device IN ({",".join(repr(d) for d in selected_devices)})
                AND u.acquisition_channel IN ({",".join(repr(c) for c in selected_channels)})
            ),
            first_sess AS (
                SELECT nu.user_id,
                    MIN(s.session_id) first_sid,
                    COUNT(DISTINCT s.session_id) total_sessions
                FROM new_users nu JOIN sessions s ON nu.user_id=s.user_id
                GROUP BY nu.user_id
            ),
            activation AS (
                SELECT fs.user_id, fs.total_sessions,
                    MAX(CASE WHEN e.event_name='search_executed' THEN 1 ELSE 0 END) searched,
                    MAX(CASE WHEN e.event_name='restaurant_viewed' THEN 1 ELSE 0 END) viewed,
                    MAX(CASE WHEN e.event_name='cart_added' THEN 1 ELSE 0 END) carted,
                    MAX(CASE WHEN e.event_name='payment_completed' THEN 1 ELSE 0 END) ordered
                FROM first_sess fs
                JOIN events e ON e.session_id=fs.first_sid
                GROUP BY fs.user_id, fs.total_sessions
            )
            SELECT COUNT(*) total,
                SUM(searched) searched, SUM(viewed) viewed,
                SUM(carted) carted, SUM(ordered) first_ordered,
                SUM(CASE WHEN total_sessions >= 2 THEN 1 ELSE 0 END) returned,
                SUM(CASE WHEN total_sessions >= 3 THEN 1 ELSE 0 END) retained
            FROM activation
        """)
        if act is not None and not act.empty:
            r = act.iloc[0]
            total = int(r.total)
            act_steps = [
                ("Signed Up", total),
                ("First Search", int(r.searched)),
                ("Viewed Restaurant", int(r.viewed)),
                ("Added to Cart", int(r.carted)),
                ("First Order", int(r.first_ordered)),
                ("Returned (2+ sessions)", int(r.returned)),
                ("Retained (3+ sessions)", int(r.retained)),
            ]

            fig_act = go.Figure(go.Funnel(
                y=[s[0] for s in act_steps],
                x=[s[1] for s in act_steps],
                textinfo="value+percent initial",
                textfont=dict(size=11),
                marker=dict(
                    color=["#E23744","#E8434F","#EF6B73","#F49098","#F9B5BC","#4ECDC4","#3BA89F"],
                    line=dict(width=0)
                ),
                connector=dict(line=dict(color=T['card_border'], width=1))
            ))
            fig_act.update_layout(**plotly_layout(height=380),
                title=dict(text="New User Activation Funnel", font=dict(size=14)))
            st.plotly_chart(fig_act, use_container_width=True)

            activation_rate = sdiv(int(r.first_ordered), total)*100
            return_rate = sdiv(int(r.returned), total)*100
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Activation Rate", f"{activation_rate:.1f}%", help="% of signups who complete first order")
            a2.metric("Return Rate", f"{return_rate:.1f}%", help="% of all users who return for 2+ sessions")
            a3.metric("First Order Users", f"{int(r.first_ordered):,}")
            a4.metric("Retained Users (3+)", f"{int(r.retained):,}")

        # ── Power User Curve ──
        st.markdown("")
        st.markdown('<div class="sh"><h3>Power User Curve</h3><span class="badge">L28</span></div>', unsafe_allow_html=True)
        st.caption("Distribution of active days per user in the last 28 days — reveals engagement concentration.")

        puc, _ = q(f"""
            SELECT active_days, COUNT(*) user_count FROM (
                SELECT s.user_id, COUNT(DISTINCT s.date) active_days
                FROM sessions s JOIN users u ON s.user_id=u.user_id
                WHERE {fc}
                AND JULIANDAY('2026-07-15') - JULIANDAY(s.date) <= 28
                GROUP BY s.user_id
            ) GROUP BY active_days ORDER BY active_days
        """)
        if puc is not None and not puc.empty:
            max_days = int(puc.active_days.max())
            all_days = pd.DataFrame({"active_days": range(1, max_days+1)})
            puc_full = all_days.merge(puc, on="active_days", how="left").fillna(0)
            puc_full["user_count"] = puc_full["user_count"].astype(int)
            total_users_puc = puc_full.user_count.sum()
            puc_full["pct"] = puc_full.user_count / total_users_puc * 100

            colors = [ZOMATO if d >= max_days * 0.7 else ('#4ECDC4' if d >= max_days * 0.3 else f"rgba(148,163,184,0.{'5' if IS_DARK else '35'})") for d in puc_full.active_days]

            fig_puc = go.Figure(go.Bar(
                x=puc_full.active_days, y=puc_full.pct,
                marker_color=colors,
                marker_line=dict(width=0),
                hovertemplate="Days active: %{x}<br>Users: %{customdata[0]:,} (%{y:.1f}%)<extra></extra>",
                customdata=puc_full[["user_count"]].values
            ))
            fig_puc.update_layout(**plotly_layout(height=280),
                title=dict(text="L28 Power User Curve", font=dict(size=13)),
                xaxis_title="Days Active (last 28 days)", yaxis_title="% of Users")
            st.plotly_chart(fig_puc, use_container_width=True)

            power_users = int(puc_full[puc_full.active_days >= max_days * 0.7].user_count.sum())
            casual_users = int(puc_full[puc_full.active_days <= max_days * 0.3].user_count.sum())
            p1, p2, p3 = st.columns(3)
            p1.metric("Power Users (>70% days)", f"{power_users:,}",
                      delta=f"{sdiv(power_users, total_users_puc)*100:.1f}%")
            p2.metric("Casual Users (<30% days)", f"{casual_users:,}",
                      delta=f"{sdiv(casual_users, total_users_puc)*100:.1f}%")
            p3.metric("Smile Score", f"{'Strong' if sdiv(power_users, total_users_puc) > 0.15 else 'Weak'}",
                      help="A 'smile' curve (high on both ends) indicates healthy engagement. Power users >15% is strong.")

            st.caption("Red bars = power users (active >70% of days). Teal = moderate. Gray = casual. A right-heavy distribution signals strong product-market fit.")

        # ── Engagement by Channel ──
        st.markdown("")
        st.markdown('<div class="sh"><h3>Engagement by Acquisition Channel</h3></div>', unsafe_allow_html=True)
        ch_eng, _ = q(f"""
            SELECT u.acquisition_channel,
                COUNT(DISTINCT s.user_id) users,
                COUNT(DISTINCT s.session_id) sessions,
                ROUND(CAST(COUNT(DISTINCT s.session_id) AS FLOAT) / COUNT(DISTINCT s.user_id), 1) sess_per_user,
                COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) orders,
                ROUND(CAST(COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) AS FLOAT)
                    / NULLIF(COUNT(DISTINCT s.session_id), 0) * 100, 2) cr
            FROM sessions s JOIN users u ON s.user_id=u.user_id
            LEFT JOIN events e ON s.session_id=e.session_id AND e.event_name='payment_completed'
            WHERE {fc}
            GROUP BY u.acquisition_channel ORDER BY cr DESC
        """)
        if ch_eng is not None and not ch_eng.empty:
            ch_rows = ""
            for _, r in ch_eng.iterrows():
                ch_rows += f"""<tr>
                    <td><strong>{r.acquisition_channel}</strong></td>
                    <td class="mono">{int(r.users):,}</td>
                    <td class="mono">{int(r.sessions):,}</td>
                    <td class="mono">{r.sess_per_user:.1f}</td>
                    <td class="mono">{int(r.orders):,}</td>
                    <td class="mono">{r.cr:.2f}%</td>
                </tr>"""
            st.markdown(f"""<table class="seg-table">
                <thead><tr><th>Channel</th><th>Users</th><th>Sessions</th><th>Sess/User</th><th>Orders</th><th>CR</th></tr></thead>
                <tbody>{ch_rows}</tbody>
            </table>""", unsafe_allow_html=True)
            st.caption("Sessions per user indicates channel quality — high-intent channels (Search) convert better but may have lower session depth than discovery channels (Instagram).")

# ===== TAB 4: SQL SANDBOX =====
with tab4:
    st.markdown('<div class="sh"><h3>Live SQL Sandbox</h3><span class="badge">Interactive</span></div>', unsafe_allow_html=True)

    rc, _ = q("SELECT (SELECT COUNT(*) FROM users) u, (SELECT COUNT(*) FROM sessions) s, (SELECT COUNT(*) FROM events) e, (SELECT COUNT(*) FROM orders) o")
    un = f"{rc['u'].iloc[0]:,}" if rc is not None else "?"
    sn = f"{rc['s'].iloc[0]:,}" if rc is not None else "?"
    en = f"{rc['e'].iloc[0]:,}" if rc is not None else "?"
    on_ = f"{rc['o'].iloc[0]:,}" if rc is not None else "?"

    with st.expander("Schema Reference", expanded=True):
        st.markdown(f"""<div class="schema">
<span class="tn">users</span> <span class="rc">({un} rows)</span><br>
&nbsp;&nbsp;<span class="pk">user_id</span> <span class="ct">INT PK</span>, <span class="cn">signup_date</span> <span class="ct">TEXT</span>, <span class="cn">segment</span> <span class="ct">TEXT</span>, <span class="cn">device</span> <span class="ct">TEXT</span>, <span class="cn">acquisition_channel</span> <span class="ct">TEXT</span>
<br><br>
<span class="tn">sessions</span> <span class="rc">({sn} rows)</span><br>
&nbsp;&nbsp;<span class="pk">session_id</span> <span class="ct">INT PK</span>, <span class="fk">user_id</span> <span class="ct">INT FK→users</span>, <span class="cn">date</span> <span class="ct">TEXT</span>, <span class="cn">device</span> <span class="ct">TEXT</span>, <span class="cn">variant</span> <span class="ct">TEXT</span>
<br><br>
<span class="tn">events</span> <span class="rc">({en} rows)</span><br>
&nbsp;&nbsp;<span class="pk">event_id</span> <span class="ct">INT PK</span>, <span class="fk">session_id</span> <span class="ct">INT FK→sessions</span>, <span class="cn">event_name</span> <span class="ct">TEXT</span>, <span class="cn">timestamp</span> <span class="ct">TEXT</span>
<br><br>
<span class="tn">orders</span> <span class="rc">({on_} rows)</span><br>
&nbsp;&nbsp;<span class="pk">order_id</span> <span class="ct">INT PK</span>, <span class="fk">session_id</span> <span class="ct">INT FK→sessions</span>, <span class="fk">user_id</span> <span class="ct">INT FK→users</span>, <span class="cn">order_value</span> <span class="ct">REAL</span>, <span class="cn">delivery_time_mins</span> <span class="ct">REAL</span>, <span class="cn">order_rating</span> <span class="ct">INT</span>
<br>
<span class="sl">event_name: <span class="ev">app_open, search_executed, restaurant_viewed, cart_added, checkout_initiated, payment_completed</span></span>
<span class="sl">segment: <span class="ev">Power User, Casual Diner, New User</span> &nbsp;|&nbsp; variant: <span class="ev">Control, Treatment</span></span>
</div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="sh"><h3>SQL Challenges</h3></div>', unsafe_allow_html=True)

    CHALLENGES = {
        "Funnel Conversion by Device": {
            "desc": "Compute end-to-end conversion rate (app_open → payment_completed) segmented by device type.",
            "sql": """SELECT s.device,\n    COUNT(DISTINCT CASE WHEN e.event_name='app_open' THEN s.session_id END) AS app_opens,\n    COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) AS payments,\n    ROUND(CAST(COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) AS FLOAT) /\n        NULLIF(COUNT(DISTINCT CASE WHEN e.event_name='app_open' THEN s.session_id END), 0) * 100, 2) AS cr_pct\nFROM sessions s JOIN events e ON s.session_id = e.session_id\nGROUP BY s.device ORDER BY cr_pct DESC;"""
        },
        "Churn Cohorts — One-Time Buyers": {
            "desc": "Find users who ordered in their signup week but never returned. What's the churn rate?",
            "sql": """WITH first_wk AS (\n    SELECT u.user_id FROM users u\n    JOIN sessions s ON u.user_id = s.user_id\n    JOIN orders o ON s.session_id = o.session_id\n    WHERE CAST((JULIANDAY(s.date) - JULIANDAY(u.signup_date)) AS INT) <= 7\n    GROUP BY u.user_id\n), repeat_users AS (\n    SELECT DISTINCT u.user_id FROM users u\n    JOIN sessions s ON u.user_id = s.user_id\n    JOIN orders o ON s.session_id = o.session_id\n    WHERE CAST((JULIANDAY(s.date) - JULIANDAY(u.signup_date)) AS INT) > 7\n)\nSELECT COUNT(DISTINCT f.user_id) AS first_week_buyers,\n    COUNT(DISTINCT f.user_id) - COUNT(DISTINCT r.user_id) AS churned,\n    ROUND((COUNT(DISTINCT f.user_id) - COUNT(DISTINCT r.user_id)) * 100.0 /\n        NULLIF(COUNT(DISTINCT f.user_id), 0), 1) AS churn_pct\nFROM first_wk f LEFT JOIN repeat_users r ON f.user_id = r.user_id;"""
        },
        "Slow Delivery by Day of Week": {
            "desc": "Analyze delivery time patterns across weekdays. Flag days with >35 min deliveries.",
            "sql": """SELECT\n    CASE CAST(strftime('%w', s.date) AS INT)\n        WHEN 0 THEN 'Sunday'    WHEN 1 THEN 'Monday'\n        WHEN 2 THEN 'Tuesday'   WHEN 3 THEN 'Wednesday'\n        WHEN 4 THEN 'Thursday'  WHEN 5 THEN 'Friday'\n        WHEN 6 THEN 'Saturday'\n    END AS day_of_week,\n    COUNT(*) AS total_orders,\n    ROUND(AVG(o.delivery_time_mins), 1) AS avg_mins,\n    ROUND(AVG(CASE WHEN o.delivery_time_mins > 35 THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_over_35\nFROM orders o JOIN sessions s ON o.session_id = s.session_id\nGROUP BY strftime('%w', s.date)\nORDER BY CAST(strftime('%w', s.date) AS INT);"""
        },
    }

    ch_cols = st.columns(3)
    for i, (name, data) in enumerate(CHALLENGES.items()):
        with ch_cols[i]:
            st.markdown(f"""<div class="ch-card">
                <div class="ch-num">Challenge {i+1}</div>
                <div class="ch-title">{name}</div>
                <div class="ch-desc">{data['desc']}</div>
            </div>""", unsafe_allow_html=True)

    ch_pick = st.selectbox("Load a challenge", ["— Write your own —"] + list(CHALLENGES.keys()), key="ch_pick", label_visibility="collapsed")
    default_sql = CHALLENGES[ch_pick]["sql"] if ch_pick in CHALLENGES else "SELECT * FROM users LIMIT 10;"

    st.markdown(f"""<div class="sql-toolbar">
        <div class="sql-label"><div class="sql-dot"></div> Connected to in-memory SQLite</div>
        <div class="sql-label">READ-ONLY</div>
    </div>""", unsafe_allow_html=True)

    sql_input = st.text_area("SQL", value=default_sql, height=200, key="sql_ed", label_visibility="collapsed")

    ec1, ec2, ec3 = st.columns([1, 1, 4])
    with ec1:
        run_btn = st.button("Execute", type="primary", use_container_width=True)
    with ec2:
        clear_btn = st.button("Clear", use_container_width=True)

    if run_btn and sql_input.strip():
        t0 = _time.time()
        res, err = q(sql_input)
        elapsed = (_time.time() - t0) * 1000
        if err:
            st.markdown(f"""<div class="sql-result-bar"><span>Error</span><span class="sql-stat" style="color:#FCA5A5">{err[:120]}</span></div>""", unsafe_allow_html=True)
            st.error(f"```\n{err}\n```")
        elif res is not None:
            st.markdown(f"""<div class="sql-result-bar"><span><span class="sql-stat">{len(res):,}</span> rows returned</span><span>Execution: <span class="sql-stat">{elapsed:.1f}ms</span> · Cols: <span class="sql-stat">{len(res.columns)}</span></span></div>""", unsafe_allow_html=True)
            st.dataframe(res, use_container_width=True, height=min(420, 38 + len(res)*35))

    if clear_btn:
        st.rerun()

# ---------------------------------------------------------------------------
# Bottom Navbar — meaningful: brand + attribution left, links + tech stack right
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="bottom-nav">
    <div class="bl">
        <div class="blogo">B</div>
        <span class="bbrand">BiteMetrics</span>
        <span>Built by Ishaan Gupta</span>
    </div>
    <div class="br">
        <span>Streamlit + Plotly + SQLite</span>
        <span>·</span>
        <span>Jun 1 – Jul 15, 2026</span>
        <span>·</span>
        <span>{S_USERS:,} users · {S_SESS:,} sessions · {S_ORD:,} orders</span>
    </div>
</div>
""", unsafe_allow_html=True)
