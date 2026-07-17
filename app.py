import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from scipy import stats
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="BiteMetrics | Zomato Order Funnel & A/B Testing Simulator",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design System
# ---------------------------------------------------------------------------
ZOMATO_RED = "#E23744"
ZOMATO_RED_LIGHT = "#FF6B6B"
CHARCOAL = "#1C1C1C"
LIGHT_BG = "#F8F9FA"
CARD_BG = "#FFFFFF"
MUTED = "#6C757D"
SUCCESS = "#28A745"
WARNING_CLR = "#FFC107"

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, sans-serif", color="#E0E0E0", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=[ZOMATO_RED, "#4ECDC4", "#FF6B6B", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"],
    margin=dict(l=40, r=24, t=48, b=32),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
        font=dict(size=11),
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --red: #E23744;
    --red-glow: rgba(226,55,68,0.15);
    --card: rgba(255,255,255,0.04);
    --card-border: rgba(255,255,255,0.08);
    --card-hover: rgba(255,255,255,0.07);
    --text-primary: #F0F0F0;
    --text-secondary: #9CA3AF;
    --text-muted: #6B7280;
    --surface: #0E1117;
    --green: #10B981;
    --amber: #F59E0B;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Layout */
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1280px;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0a 0%, #111318 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--card);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid var(--card-border);
}
.stTabs [data-baseweb="tab"] {
    height: 44px;
    border-radius: 10px;
    padding: 0 20px;
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-secondary);
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: var(--red) !important;
    color: white !important;
    box-shadow: 0 2px 12px rgba(226,55,68,0.35);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.25s cubic-bezier(.4,0,.2,1);
}
div[data-testid="stMetric"]:hover {
    background: var(--card-hover);
    border-color: rgba(226,55,68,0.3);
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(226,55,68,0.08);
}
div[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-weight: 600;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700;
    font-size: 1.6rem !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #E23744 0%, #B91C28 60%, #8B1520 100%);
    color: white;
    padding: 36px 44px;
    border-radius: 16px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -0.5px;
    position: relative;
}
.hero .subtitle {
    margin: 6px 0 0 0;
    opacity: 0.85;
    font-size: 0.95rem;
    font-weight: 400;
    position: relative;
}
.hero .hero-stats {
    display: flex;
    gap: 32px;
    margin-top: 20px;
    position: relative;
}
.hero .hero-stat {
    display: flex;
    flex-direction: column;
}
.hero .hero-stat-val {
    font-size: 1.3rem;
    font-weight: 800;
}
.hero .hero-stat-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.7;
    margin-top: 2px;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 8px 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--card-border);
}
.section-header h3 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
}
.section-header .badge {
    background: var(--red);
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Hypothesis cards */
.hyp-card {
    background: rgba(226,55,68,0.06);
    border: 1px solid rgba(226,55,68,0.15);
    border-left: 3px solid var(--red);
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin-bottom: 10px;
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--text-primary);
}
.hyp-card .hyp-label {
    color: var(--red);
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* Stat badges */
.badge-sig {
    background: rgba(16,185,129,0.12);
    color: #34D399;
    border: 1px solid rgba(16,185,129,0.25);
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.82rem;
    display: inline-block;
}
.badge-notsig {
    background: rgba(239,68,68,0.12);
    color: #F87171;
    border: 1px solid rgba(239,68,68,0.25);
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.82rem;
    display: inline-block;
}

/* SRM Alert */
.srm-alert {
    background: rgba(239,68,68,0.1);
    border: 2px solid rgba(239,68,68,0.4);
    padding: 18px 24px;
    border-radius: 12px;
    color: #FCA5A5;
    font-weight: 600;
    text-align: center;
    font-size: 0.9rem;
}

/* Stat card panel */
.stat-panel {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px 24px;
}
.stat-panel h4 {
    margin: 0 0 16px 0;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.88rem;
}
.stat-row:last-child {
    border-bottom: none;
}
.stat-row .label {
    color: var(--text-secondary);
}
.stat-row .value {
    color: var(--text-primary);
    font-weight: 600;
    font-family: 'JetBrains Mono', 'SF Mono', monospace;
}

/* Schema box */
.schema-container {
    background: rgba(0,0,0,0.3);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 20px 24px;
    font-family: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace;
    font-size: 0.78rem;
    line-height: 1.8;
}
.schema-container .tbl-name {
    color: var(--red);
    font-weight: 700;
}
.schema-container .col-pk {
    color: #FBBF24;
}
.schema-container .col-fk {
    color: #60A5FA;
}
.schema-container .col-name {
    color: #A5F3FC;
}
.schema-container .col-type {
    color: var(--text-muted);
}
.schema-container .section-label {
    color: var(--text-muted);
    font-style: italic;
    margin-top: 8px;
    display: block;
}
.schema-container .enum-val {
    color: #86EFAC;
}

/* Friction bar */
.friction-bar {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
}
.friction-bar .step-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 600;
    min-width: 170px;
}
.friction-bar .bar-track {
    flex: 1;
    height: 8px;
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    overflow: hidden;
}
.friction-bar .bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}
.friction-bar .pct {
    color: var(--text-primary);
    font-weight: 700;
    font-size: 0.88rem;
    min-width: 60px;
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
}
.friction-bar .time {
    color: var(--text-muted);
    font-size: 0.78rem;
    min-width: 70px;
    text-align: right;
}

/* Sidebar extras */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.sidebar-brand .logo-text {
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--red);
    letter-spacing: -0.3px;
}
.sidebar-about {
    font-size: 0.75rem;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 16px;
}

/* Footer */
.footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.78rem;
    padding: 24px 0 0 0;
    border-top: 1px solid var(--card-border);
    margin-top: 40px;
}
.footer a {
    color: var(--red);
    text-decoration: none;
}

/* Misc */
.stSelectbox label, .stMultiSelect label, .stRadio label, .stTextArea label {
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: var(--text-secondary) !important;
}
div[data-testid="stExpander"] {
    border: 1px solid var(--card-border);
    border-radius: 12px;
    background: var(--card);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data Generation & Database Setup
# ---------------------------------------------------------------------------
@st.cache_resource
def init_database():
    np.random.seed(42)
    random.seed(42)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            signup_date TEXT,
            segment TEXT,
            device TEXT,
            acquisition_channel TEXT
        );
        CREATE TABLE sessions (
            session_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date TEXT,
            device TEXT,
            variant TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        CREATE TABLE events (
            event_id INTEGER PRIMARY KEY,
            session_id INTEGER,
            event_name TEXT,
            timestamp TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            session_id INTEGER,
            user_id INTEGER,
            order_value REAL,
            delivery_time_mins REAL,
            order_rating INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    start_date = datetime(2026, 6, 1)
    segments = ["Power User", "Casual Diner", "New User"]
    segment_weights = [0.2, 0.5, 0.3]
    devices = ["iOS", "Android", "Web"]
    device_weights = [0.35, 0.50, 0.15]
    channels = ["Search", "Instagram", "Referral"]
    channel_weights = [0.4, 0.35, 0.25]

    n_users = 10000
    users_data = []
    for uid in range(1, n_users + 1):
        signup = start_date + timedelta(days=np.random.randint(0, 45))
        seg = np.random.choice(segments, p=segment_weights)
        dev = np.random.choice(devices, p=device_weights)
        ch = np.random.choice(channels, p=channel_weights)
        users_data.append((uid, signup.strftime("%Y-%m-%d"), seg, dev, ch))

    cursor.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users_data)

    funnel_steps = [
        "app_open", "search_executed", "restaurant_viewed",
        "cart_added", "checkout_initiated", "payment_completed"
    ]

    control_cum = [1.0, 0.72, 0.58, 0.38, 0.22, 0.08]
    treatment_cum = [1.0, 0.75, 0.62, 0.43, 0.28, 0.11]

    def cum_to_conditional(cum):
        return [cum[0]] + [cum[i] / cum[i-1] if cum[i-1] > 0 else 0 for i in range(1, len(cum))]

    n_sessions = 50000
    sessions_data = []
    events_data = []
    orders_data = []
    event_id = 1
    order_id = 1

    user_devices = {u[0]: u[3] for u in users_data}
    user_segments = {u[0]: u[2] for u in users_data}

    for sid in range(1, n_sessions + 1):
        uid = np.random.randint(1, n_users + 1)
        sess_date = start_date + timedelta(days=np.random.randint(0, 45))
        dev = user_devices[uid]
        variant = np.random.choice(["Control", "Treatment"])

        sessions_data.append((sid, uid, sess_date.strftime("%Y-%m-%d"), dev, variant))

        cum = list(control_cum if variant == "Control" else treatment_cum)

        if dev == "Web":
            cum = [cum[0]] + [c * 0.85 for c in cum[1:]]

        seg = user_segments[uid]
        if seg == "Power User":
            cum = [min(1.0, c * 1.15) for c in cum]
            cum[0] = 1.0
        elif seg == "New User":
            cum = [c * 0.9 for c in cum]
            cum[0] = 1.0

        probs = cum_to_conditional(cum)

        base_time = sess_date.replace(
            hour=np.random.randint(8, 23),
            minute=np.random.randint(0, 60)
        )

        for i, step in enumerate(funnel_steps):
            if np.random.random() < probs[i]:
                ts = base_time + timedelta(minutes=i * np.random.uniform(0.5, 4))
                events_data.append((event_id, sid, step, ts.strftime("%Y-%m-%d %H:%M:%S")))
                event_id += 1

                if step == "payment_completed":
                    aov_mean = 350 if variant == "Control" else 385
                    ov = max(100, np.random.normal(aov_mean, 80))
                    dt = max(12, np.random.lognormal(np.log(28), 0.35))
                    rating = np.random.choice([1,2,3,4,5], p=[0.03, 0.07, 0.15, 0.40, 0.35])
                    orders_data.append((order_id, sid, uid, round(ov, 2), round(dt, 1), int(rating)))
                    order_id += 1
            else:
                break

    cursor.executemany("INSERT INTO sessions VALUES (?,?,?,?,?)", sessions_data)
    cursor.executemany("INSERT INTO events VALUES (?,?,?,?)", events_data)
    cursor.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders_data)
    conn.commit()

    return conn


conn = init_database()


def run_query(query):
    try:
        return pd.read_sql_query(query, conn), None
    except Exception as e:
        return None, str(e)


def safe_div(a, b, default=0):
    return a / b if b else default


# ---------------------------------------------------------------------------
# Hero Header
# ---------------------------------------------------------------------------
hero_stats, _ = run_query("""
    SELECT
        (SELECT COUNT(DISTINCT user_id) FROM users) as users,
        (SELECT COUNT(*) FROM sessions) as sessions,
        (SELECT COUNT(*) FROM orders) as orders,
        (SELECT ROUND(AVG(order_value),0) FROM orders) as aov
""")
u_count = f"{hero_stats['users'].iloc[0]:,}" if hero_stats is not None else "—"
s_count = f"{hero_stats['sessions'].iloc[0]:,}" if hero_stats is not None else "—"
o_count = f"{hero_stats['orders'].iloc[0]:,}" if hero_stats is not None else "—"
aov_val = f"₹{hero_stats['aov'].iloc[0]:.0f}" if hero_stats is not None else "—"

st.markdown(f"""
<div class="hero">
    <h1>BiteMetrics</h1>
    <p class="subtitle">Zomato Order Funnel & A/B Testing Simulator — Interactive Product Analytics Dashboard</p>
    <div class="hero-stats">
        <div class="hero-stat"><span class="hero-stat-val">{u_count}</span><span class="hero-stat-label">Users</span></div>
        <div class="hero-stat"><span class="hero-stat-val">{s_count}</span><span class="hero-stat-label">Sessions</span></div>
        <div class="hero-stat"><span class="hero-stat-val">{o_count}</span><span class="hero-stat-label">Orders</span></div>
        <div class="hero-stat"><span class="hero-stat-val">{aov_val}</span><span class="hero-stat-label">Avg Order Value</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand"><span class="logo-text">BiteMetrics</span></div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <p class="sidebar-about">
        A production-grade product analytics simulator modelling Zomato's order funnel,
        A/B experimentation, cohort retention, and a live SQL sandbox.
        Built with Streamlit, Plotly, and SQLite.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("#### Filters")

    all_devices = ["iOS", "Android", "Web"]
    selected_devices = st.multiselect("Device Type", all_devices, default=all_devices)

    all_segments = ["Power User", "Casual Diner", "New User"]
    selected_segments = st.multiselect("User Segment", all_segments, default=all_segments)

    all_channels = ["Search", "Instagram", "Referral"]
    selected_channels = st.multiselect("Acquisition Channel", all_channels, default=all_channels)

    st.markdown("---")
    st.caption("45-day simulation window  \nJun 1 – Jul 15, 2026")


def check_filters():
    if not selected_devices or not selected_segments or not selected_channels:
        st.warning("Please select at least one option in each filter to visualize data.")
        return False
    return True


def get_filter_clause(device_col="s.device", user_prefix="u"):
    devs = ",".join([f"'{d}'" for d in selected_devices])
    segs = ",".join([f"'{s}'" for s in selected_segments])
    chs = ",".join([f"'{c}'" for c in selected_channels])
    return f"{device_col} IN ({devs}) AND {user_prefix}.segment IN ({segs}) AND {user_prefix}.acquisition_channel IN ({chs})"


def make_plotly_layout(**overrides):
    base = dict(PLOTLY_LAYOUT)
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Funnel Analysis",
    "A/B Testing Engine",
    "Cohort Retention",
    "SQL Sandbox"
])

FUNNEL_STEPS = ["app_open", "search_executed", "restaurant_viewed",
                "cart_added", "checkout_initiated", "payment_completed"]
STEP_LABELS = ["App Open", "Search", "Restaurant View",
               "Cart Added", "Checkout", "Payment"]

# ---------------------------------------------------------------------------
# Tab 1: Funnel
# ---------------------------------------------------------------------------
with tab1:
    if check_filters():
        st.markdown('<div class="section-header"><h3>Conversion Funnel & Friction Analysis</h3><span class="badge">Live</span></div>', unsafe_allow_html=True)

        filter_clause = get_filter_clause()

        col_slicer, col_spacer = st.columns([1, 2])
        with col_slicer:
            slice_by = st.selectbox(
                "Segment by",
                ["Overall", "Device Type", "User Segment", "Acquisition Channel"],
                key="funnel_slicer"
            )

        if slice_by == "Overall":
            funnel_df, _ = run_query(f"""
                SELECT e.event_name, COUNT(DISTINCT e.session_id) as sessions
                FROM events e
                JOIN sessions s ON e.session_id = s.session_id
                JOIN users u ON s.user_id = u.user_id
                WHERE {filter_clause}
                GROUP BY e.event_name
            """)
            if funnel_df is not None and not funnel_df.empty:
                counts = []
                for step in FUNNEL_STEPS:
                    row = funnel_df[funnel_df["event_name"] == step]
                    counts.append(int(row["sessions"].iloc[0]) if not row.empty else 0)

                fig = go.Figure(go.Funnel(
                    y=STEP_LABELS,
                    x=counts,
                    textinfo="value+percent initial+percent previous",
                    textfont=dict(size=12),
                    marker=dict(
                        color=["#E23744", "#E8434F", "#EF6B73", "#F49098", "#F9B5BC", "#4ECDC4"],
                        line=dict(width=0),
                    ),
                    connector=dict(line=dict(color="rgba(255,255,255,0.08)", width=1))
                ))
                fig.update_layout(
                    **make_plotly_layout(height=420),
                    title=dict(text="Order Funnel — All Sessions", font=dict(size=14, color="#E0E0E0")),
                    funnelmode="stack",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Drop-off friction bars with time between stages
                st.markdown('<div class="section-header"><h3>Step-by-Step Friction Map</h3></div>', unsafe_allow_html=True)

                time_df, _ = run_query(f"""
                    WITH ordered_events AS (
                        SELECT e.session_id, e.event_name, e.timestamp,
                            ROW_NUMBER() OVER (PARTITION BY e.session_id ORDER BY e.timestamp) as rn
                        FROM events e
                        JOIN sessions s ON e.session_id = s.session_id
                        JOIN users u ON s.user_id = u.user_id
                        WHERE {filter_clause}
                    )
                    SELECT e1.event_name as from_step, e2.event_name as to_step,
                        AVG((JULIANDAY(e2.timestamp) - JULIANDAY(e1.timestamp)) * 1440) as avg_mins
                    FROM ordered_events e1
                    JOIN ordered_events e2 ON e1.session_id = e2.session_id AND e2.rn = e1.rn + 1
                    GROUP BY e1.event_name, e2.event_name
                """)
                time_map = {}
                if time_df is not None:
                    for _, r in time_df.iterrows():
                        time_map[(r["from_step"], r["to_step"])] = r["avg_mins"]

                max_dropoff_rate = 0
                max_dropoff_idx = 1
                for i in range(1, len(counts)):
                    dropoff_pct = (1 - safe_div(counts[i], counts[i-1])) * 100
                    from_step = FUNNEL_STEPS[i-1]
                    to_step = FUNNEL_STEPS[i]
                    avg_time = time_map.get((from_step, to_step), None)
                    time_str = f"{avg_time:.1f} min" if avg_time is not None else "—"

                    bar_color = ZOMATO_RED if dropoff_pct > 50 else ("#F59E0B" if dropoff_pct > 30 else "#10B981")

                    st.markdown(f"""
                    <div class="friction-bar">
                        <span class="step-label">{STEP_LABELS[i-1]} → {STEP_LABELS[i]}</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: {dropoff_pct}%; background: {bar_color};"></div>
                        </div>
                        <span class="pct" style="color: {bar_color};">{dropoff_pct:.1f}%</span>
                        <span class="time">{time_str}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if dropoff_pct > max_dropoff_rate:
                        max_dropoff_rate = dropoff_pct
                        max_dropoff_idx = i

                # Daily conversion trend
                st.markdown("")
                trend_df, _ = run_query(f"""
                    SELECT s.date,
                        COUNT(DISTINCT s.session_id) as sessions,
                        COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) as conversions
                    FROM sessions s
                    JOIN users u ON s.user_id = u.user_id
                    LEFT JOIN events e ON s.session_id = e.session_id AND e.event_name = 'payment_completed'
                    WHERE {filter_clause}
                    GROUP BY s.date ORDER BY s.date
                """)
                if trend_df is not None and not trend_df.empty:
                    trend_df["cr"] = trend_df["conversions"] / trend_df["sessions"] * 100
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=trend_df["date"], y=trend_df["cr"],
                        mode="lines",
                        line=dict(color=ZOMATO_RED, width=2),
                        fill="tozeroy",
                        fillcolor="rgba(226,55,68,0.08)",
                        name="CR %"
                    ))
                    fig_trend.update_layout(
                        **make_plotly_layout(height=250),
                        title=dict(text="Daily Conversion Rate Trend", font=dict(size=14, color="#E0E0E0")),
                        yaxis_title="Conversion Rate %",
                        xaxis_title="",
                        showlegend=False,
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

                # Hypothesis Engine
                st.markdown('<div class="section-header"><h3>Product Hypothesis Engine</h3></div>', unsafe_allow_html=True)

                friction_point = STEP_LABELS[max_dropoff_idx]
                prev_point = STEP_LABELS[max_dropoff_idx - 1] if max_dropoff_idx > 0 else "Start"

                hypotheses = {
                    "Search": [
                        ("Search relevance gap", "Auto-suggestions and search ranking may not surface the most relevant restaurants, especially for long-tail cuisine queries."),
                        ("Cold start problem", "New users without order history get generic results instead of personalized recommendations."),
                        ("Latency on low-end devices", "Search response times on Android budget devices may exceed the 300ms patience threshold."),
                    ],
                    "Restaurant View": [
                        ("Missing social proof", "Listing cards lack user-generated photos and real-time popularity signals (e.g., '42 orders in the last hour')."),
                        ("Fee transparency", "Delivery fees and minimum order values shown on listing cards may deter exploration."),
                        ("Category mismatch", "Cuisine taxonomy may not align with how users think about food (e.g., 'healthy' vs. 'salad')."),
                    ],
                    "Cart Added": [
                        ("Menu decision paralysis", "Restaurants with 100+ items and no smart defaults overwhelm users. Recommended combos could reduce cognitive load."),
                        ("Missing dish confidence signals", "Lack of dish-level ratings, photos, and 'popular' tags reduces purchase confidence."),
                        ("Minimum order friction", "Users wanting a single item face a ₹150+ minimum, causing drop-off at the menu stage."),
                    ],
                    "Checkout": [
                        ("Sticker shock", "Delivery fee + packaging + taxes revealed at checkout total 25-40% above menu price, violating price anchoring."),
                        ("Checkout flow length", "5+ steps (address → slot → tip → instructions → payment) creates fatigue. One-tap reorder could bypass this."),
                        ("Guest checkout absence", "Mandatory account creation forces registration, adding 30+ seconds of friction."),
                    ],
                    "Payment": [
                        ("Gateway timeouts", "Payment gateway failure rates spike during peak hours (12–2pm, 7–9pm), causing abandoned carts."),
                        ("UPI preference mismatch", "Users preferring UPI Lite or specific wallets find limited options, falling back to card + OTP flow."),
                        ("OTP drop-off", "Card payments requiring OTP create a 15-second window where users abandon — especially on slow networks."),
                    ],
                }

                hyps = hypotheses.get(friction_point, hypotheses["Checkout"])
                st.markdown(f"Highest friction: **{prev_point} → {friction_point}** at **{max_dropoff_rate:.1f}% drop-off**")
                for title, desc in hyps:
                    st.markdown(f"""
                    <div class="hyp-card">
                        <div class="hyp-label">Hypothesis — {title}</div>
                        {desc}
                    </div>
                    """, unsafe_allow_html=True)

        else:
            group_col_map = {
                "Device Type": "s.device",
                "User Segment": "u.segment",
                "Acquisition Channel": "u.acquisition_channel"
            }
            group_col = group_col_map[slice_by]

            seg_df, _ = run_query(f"""
                SELECT {group_col} as segment_val, e.event_name, COUNT(DISTINCT e.session_id) as sessions
                FROM events e
                JOIN sessions s ON e.session_id = s.session_id
                JOIN users u ON s.user_id = u.user_id
                WHERE {filter_clause}
                GROUP BY {group_col}, e.event_name
            """)
            if seg_df is not None and not seg_df.empty:
                fig = go.Figure()
                for seg_val in sorted(seg_df["segment_val"].unique()):
                    sub = seg_df[seg_df["segment_val"] == seg_val]
                    counts = []
                    for step in FUNNEL_STEPS:
                        row = sub[sub["event_name"] == step]
                        counts.append(int(row["sessions"].iloc[0]) if not row.empty else 0)
                    fig.add_trace(go.Funnel(
                        name=seg_val,
                        y=STEP_LABELS,
                        x=counts,
                        textinfo="value+percent initial"
                    ))
                fig.update_layout(
                    **make_plotly_layout(height=480),
                    title=dict(text=f"Funnel by {slice_by}", font=dict(size=14, color="#E0E0E0")),
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 2: A/B Testing Engine
# ---------------------------------------------------------------------------
with tab2:
    if check_filters():
        st.markdown('<div class="section-header"><h3>Experimentation Dashboard</h3><span class="badge">AI Cross-Sell</span></div>', unsafe_allow_html=True)
        st.caption("**Variant A (Control):** Standard cart  ·  **Variant B (Treatment):** AI-powered cross-sell recommendations")

        filter_clause = get_filter_clause()

        ab_df, _ = run_query(f"""
            SELECT s.variant,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(DISTINCT CASE WHEN e.event_name='payment_completed' THEN s.session_id END) as conversions
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            LEFT JOIN events e ON s.session_id = e.session_id AND e.event_name='payment_completed'
            WHERE {filter_clause}
            GROUP BY s.variant
        """)

        if ab_df is not None and len(ab_df) == 2:
            control = ab_df[ab_df["variant"] == "Control"].iloc[0]
            treatment = ab_df[ab_df["variant"] == "Treatment"].iloc[0]

            n_a, n_b = int(control["total_sessions"]), int(treatment["total_sessions"])
            conv_a, conv_b = int(control["conversions"]), int(treatment["conversions"])
            cr_a = safe_div(conv_a, n_a)
            cr_b = safe_div(conv_b, n_b)
            relative_lift = safe_div(cr_b - cr_a, cr_a) * 100

            # Core metrics row
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("N (Control)", f"{n_a:,}")
            m2.metric("N (Treatment)", f"{n_b:,}")
            m3.metric("CR Control", f"{cr_a*100:.2f}%")
            m4.metric("CR Treatment", f"{cr_b*100:.2f}%")
            m5.metric("Relative Lift", f"+{relative_lift:.1f}%", delta=f"+{relative_lift:.1f}%")

            st.markdown("")

            # AOV data
            aov_c_df, _ = run_query(f"""
                SELECT o.order_value FROM orders o
                JOIN sessions s ON o.session_id = s.session_id
                JOIN users u ON s.user_id = u.user_id
                WHERE s.variant='Control' AND {filter_clause}
            """)
            aov_t_df, _ = run_query(f"""
                SELECT o.order_value FROM orders o
                JOIN sessions s ON o.session_id = s.session_id
                JOIN users u ON s.user_id = u.user_id
                WHERE s.variant='Treatment' AND {filter_clause}
            """)

            # Statistical Tests — side by side panels
            st.markdown('<div class="section-header"><h3>Statistical Rigor</h3></div>', unsafe_allow_html=True)

            tc1, tc2 = st.columns(2)

            with tc1:
                st.markdown("**Chi-Square Test** — Conversion Rate")
                if min(n_a, n_b) >= 30:
                    contingency = np.array([[conv_a, n_a - conv_a], [conv_b, n_b - conv_b]])
                    chi2, p_val, dof, _ = stats.chi2_contingency(contingency)
                    sig = p_val < 0.05

                    st.markdown(f"""
                    <div class="stat-panel">
                        <div class="stat-row"><span class="label">Test</span><span class="value">Chi-Square of Independence</span></div>
                        <div class="stat-row"><span class="label">χ² statistic</span><span class="value">{chi2:.4f}</span></div>
                        <div class="stat-row"><span class="label">p-value</span><span class="value">{p_val:.8f}</span></div>
                        <div class="stat-row"><span class="label">α</span><span class="value">0.05</span></div>
                        <div class="stat-row"><span class="label">Verdict</span><span class="value">{'<span class="badge-sig">Significant</span>' if sig else '<span class="badge-notsig">Not Significant</span>'}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Sample size < 30 — insufficient for reliable Chi-Square testing.")

            with tc2:
                st.markdown("**Welch's T-Test** — Average Order Value")
                if aov_c_df is not None and aov_t_df is not None and len(aov_c_df) >= 30 and len(aov_t_df) >= 30:
                    t_stat, t_pval = stats.ttest_ind(aov_c_df["order_value"], aov_t_df["order_value"], equal_var=False)
                    aov_a = aov_c_df["order_value"].mean()
                    aov_b = aov_t_df["order_value"].mean()
                    se = np.sqrt(aov_c_df["order_value"].var()/len(aov_c_df) + aov_t_df["order_value"].var()/len(aov_t_df))
                    ci_lo = (aov_b - aov_a) - 1.96 * se
                    ci_hi = (aov_b - aov_a) + 1.96 * se
                    t_sig = t_pval < 0.05

                    st.markdown(f"""
                    <div class="stat-panel">
                        <div class="stat-row"><span class="label">AOV Control</span><span class="value">₹{aov_a:.0f}</span></div>
                        <div class="stat-row"><span class="label">AOV Treatment</span><span class="value">₹{aov_b:.0f}</span></div>
                        <div class="stat-row"><span class="label">t-statistic</span><span class="value">{t_stat:.4f}</span></div>
                        <div class="stat-row"><span class="label">p-value</span><span class="value">{t_pval:.8f}</span></div>
                        <div class="stat-row"><span class="label">95% CI for Δ</span><span class="value">[₹{ci_lo:.1f}, ₹{ci_hi:.1f}]</span></div>
                        <div class="stat-row"><span class="label">Verdict</span><span class="value">{'<span class="badge-sig">Significant</span>' if t_sig else '<span class="badge-notsig">Not Significant</span>'}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Insufficient order data for T-Test.")

            st.markdown("")

            # AOV Distribution
            if aov_c_df is not None and aov_t_df is not None and len(aov_c_df) > 0:
                st.markdown('<div class="section-header"><h3>AOV Distribution</h3></div>', unsafe_allow_html=True)
                fig_aov = go.Figure()
                fig_aov.add_trace(go.Histogram(
                    x=aov_c_df["order_value"], name="Control",
                    marker_color="rgba(108,117,125,0.5)", nbinsx=40,
                    marker_line=dict(width=0),
                ))
                fig_aov.add_trace(go.Histogram(
                    x=aov_t_df["order_value"], name="Treatment",
                    marker_color="rgba(226,55,68,0.5)", nbinsx=40,
                    marker_line=dict(width=0),
                ))
                fig_aov.update_layout(
                    **make_plotly_layout(height=280),
                    barmode="overlay",
                    title=dict(text="Order Value Distribution by Variant", font=dict(size=14, color="#E0E0E0")),
                    xaxis_title="Order Value (₹)",
                    yaxis_title="Count",
                )
                st.plotly_chart(fig_aov, use_container_width=True)

            # SRM Check
            st.markdown('<div class="section-header"><h3>Sample Ratio Mismatch (SRM)</h3></div>', unsafe_allow_html=True)
            observed = np.array([n_a, n_b])
            _, p_srm = stats.chisquare(observed, f_exp=np.array([0.5, 0.5]) * observed.sum())

            srm1, srm2, srm3 = st.columns(3)
            srm1.metric("Expected Split", "50.0% / 50.0%")
            srm2.metric("Observed Split", f"{n_a/(n_a+n_b)*100:.1f}% / {n_b/(n_a+n_b)*100:.1f}%")
            srm3.metric("SRM p-value", f"{p_srm:.4f}")

            if p_srm < 0.001:
                st.markdown('<div class="srm-alert">SRM ALERT — Traffic distribution is significantly biased (p &lt; 0.001). Experiment results may be invalid. Investigate the assignment logic.</div>', unsafe_allow_html=True)
            else:
                st.success("No Sample Ratio Mismatch detected. Traffic split is balanced.")

            # Guardrail Metrics
            st.markdown("")
            st.markdown('<div class="section-header"><h3>Guardrail Metrics</h3></div>', unsafe_allow_html=True)

            g1, g2 = st.columns(2)
            with g1:
                np.random.seed(99)
                lat_a = np.random.normal(220, 30, 200)
                lat_b = np.random.normal(225, 32, 200)
                fig_lat = go.Figure()
                fig_lat.add_trace(go.Box(y=lat_a, name="Control", marker_color="rgba(108,117,125,0.7)", line=dict(color="#6C757D")))
                fig_lat.add_trace(go.Box(y=lat_b, name="Treatment", marker_color="rgba(226,55,68,0.7)", line=dict(color=ZOMATO_RED)))
                fig_lat.update_layout(
                    **make_plotly_layout(height=280),
                    title=dict(text="App Latency (ms) — P50", font=dict(size=13, color="#E0E0E0")),
                    yaxis_title="Latency (ms)",
                    showlegend=False,
                )
                st.plotly_chart(fig_lat, use_container_width=True)
                st.caption("No significant latency degradation in Treatment arm.")

            with g2:
                weeks = [f"W{i}" for i in range(1, 7)]
                tix_a = [45, 42, 48, 44, 41, 43]
                tix_b = [44, 46, 43, 47, 45, 44]
                fig_tix = go.Figure()
                fig_tix.add_trace(go.Scatter(x=weeks, y=tix_a, name="Control", line=dict(color="#6C757D", width=2), mode="lines+markers", marker=dict(size=5)))
                fig_tix.add_trace(go.Scatter(x=weeks, y=tix_b, name="Treatment", line=dict(color=ZOMATO_RED, width=2), mode="lines+markers", marker=dict(size=5)))
                fig_tix.update_layout(
                    **make_plotly_layout(height=280),
                    title=dict(text="Weekly Support Tickets", font=dict(size=13, color="#E0E0E0")),
                    yaxis_title="Tickets",
                )
                st.plotly_chart(fig_tix, use_container_width=True)
                st.caption("Support ticket volume stable across variants.")

# ---------------------------------------------------------------------------
# Tab 3: Cohort Retention
# ---------------------------------------------------------------------------
with tab3:
    if check_filters():
        st.markdown('<div class="section-header"><h3>Weekly Cohort Retention</h3><span class="badge">Heatmap</span></div>', unsafe_allow_html=True)

        retention_type = st.radio(
            "Retention type",
            ["N-Week Retention", "Unbounded Retention"],
            horizontal=True,
            help="N-Week: active in exactly that week. Unbounded: active in that week or any later week."
        )

        filter_clause = get_filter_clause()
        segs_sql = ",".join([f"'{s}'" for s in selected_segments])
        devs_sql = ",".join([f"'{d}'" for d in selected_devices])
        chs_sql = ",".join([f"'{c}'" for c in selected_channels])

        cohort_df, _ = run_query(f"""
            WITH user_cohorts AS (
                SELECT u.user_id,
                    CAST((JULIANDAY(u.signup_date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as cohort_week
                FROM users u
                WHERE u.segment IN ({segs_sql}) AND u.device IN ({devs_sql}) AND u.acquisition_channel IN ({chs_sql})
            ),
            user_activity AS (
                SELECT s.user_id,
                    CAST((JULIANDAY(s.date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as activity_week
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE {filter_clause}
                GROUP BY s.user_id, activity_week
            )
            SELECT uc.cohort_week, ua.activity_week, COUNT(DISTINCT uc.user_id) as active_users
            FROM user_cohorts uc
            JOIN user_activity ua ON uc.user_id = ua.user_id
            WHERE ua.activity_week >= uc.cohort_week
            GROUP BY uc.cohort_week, ua.activity_week
        """)

        sizes_df, _ = run_query(f"""
            SELECT CAST((JULIANDAY(u.signup_date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as cohort_week,
                   COUNT(DISTINCT u.user_id) as cohort_size
            FROM users u
            WHERE u.segment IN ({segs_sql}) AND u.device IN ({devs_sql}) AND u.acquisition_channel IN ({chs_sql})
            GROUP BY cohort_week
        """)

        if cohort_df is not None and sizes_df is not None and not cohort_df.empty:
            sizes_map = dict(zip(sizes_df["cohort_week"], sizes_df["cohort_size"]))

            max_weeks = 7
            cohort_weeks = sorted([w for w in cohort_df["cohort_week"].unique() if 0 <= w < max_weeks])

            retention_matrix = np.full((len(cohort_weeks), max_weeks), np.nan)

            for i, cw in enumerate(cohort_weeks):
                cohort_size = sizes_map.get(cw, 0)
                if cohort_size == 0:
                    continue
                for offset in range(max_weeks):
                    if retention_type == "N-Week Retention":
                        target = cw + offset
                        row = cohort_df[(cohort_df["cohort_week"] == cw) & (cohort_df["activity_week"] == target)]
                        active = int(row["active_users"].iloc[0]) if not row.empty else 0
                    else:
                        targets = range(cw + offset, cw + max_weeks + 5)
                        active = int(cohort_df[
                            (cohort_df["cohort_week"] == cw) & (cohort_df["activity_week"].isin(targets))
                        ]["active_users"].sum())
                        active = min(active, cohort_size)
                    retention_matrix[i, offset] = safe_div(active, cohort_size) * 100

            cohort_labels = [f"W{w} ({sizes_map.get(w,0):,})" for w in cohort_weeks]
            period_labels = [f"+{w}w" for w in range(max_weeks)]

            # Mask NaN cells
            text_matrix = np.where(np.isnan(retention_matrix), "", np.vectorize(lambda x: f"{x:.0f}")(retention_matrix))

            fig_hm = go.Figure(go.Heatmap(
                z=retention_matrix,
                x=period_labels,
                y=cohort_labels,
                text=text_matrix,
                texttemplate="%{text}%",
                textfont=dict(size=11, color="white"),
                colorscale=[
                    [0, "rgba(226,55,68,0.08)"],
                    [0.3, "rgba(226,55,68,0.35)"],
                    [0.6, "rgba(226,55,68,0.65)"],
                    [1, "#E23744"],
                ],
                colorbar=dict(title=dict(text="Retention %", font=dict(size=11)), tickfont=dict(size=10)),
                hoverongaps=False,
            ))
            fig_hm.update_layout(
                **make_plotly_layout(height=380),
                title=dict(text=f"{retention_type} Heatmap", font=dict(size=14, color="#E0E0E0")),
                xaxis_title="Weeks Since Signup",
                yaxis_title="Signup Cohort (size)",
            )
            fig_hm.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_hm, use_container_width=True)

            # LTV
            st.markdown('<div class="section-header"><h3>Cumulative Revenue by Cohort (LTV Proxy)</h3></div>', unsafe_allow_html=True)
            ltv_df, _ = run_query(f"""
                SELECT
                    CAST((JULIANDAY(u.signup_date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as cohort_week,
                    CAST((JULIANDAY(s.date) - JULIANDAY(u.signup_date)) / 7 AS INTEGER) as week_offset,
                    SUM(o.order_value) as revenue
                FROM orders o
                JOIN sessions s ON o.session_id = s.session_id
                JOIN users u ON o.user_id = u.user_id
                WHERE u.segment IN ({segs_sql}) AND s.device IN ({devs_sql}) AND u.acquisition_channel IN ({chs_sql})
                GROUP BY cohort_week, week_offset
                HAVING cohort_week >= 0 AND cohort_week < {max_weeks}
                ORDER BY cohort_week, week_offset
            """)
            if ltv_df is not None and not ltv_df.empty:
                fig_ltv = go.Figure()
                for cw in sorted(ltv_df["cohort_week"].unique()):
                    sub = ltv_df[ltv_df["cohort_week"] == cw].sort_values("week_offset")
                    sub["cum_rev"] = sub["revenue"].cumsum()
                    fig_ltv.add_trace(go.Scatter(
                        x=sub["week_offset"], y=sub["cum_rev"],
                        name=f"W{int(cw)}",
                        mode="lines+markers",
                        marker=dict(size=4),
                        line=dict(width=2),
                    ))
                fig_ltv.update_layout(
                    **make_plotly_layout(height=320),
                    title=dict(text="Cumulative Revenue per Cohort", font=dict(size=14, color="#E0E0E0")),
                    xaxis_title="Weeks Since Signup",
                    yaxis_title="Cumulative Revenue (₹)",
                )
                st.plotly_chart(fig_ltv, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 4: SQL Sandbox
# ---------------------------------------------------------------------------
with tab4:
    st.markdown('<div class="section-header"><h3>Live SQL Sandbox</h3><span class="badge">Interactive</span></div>', unsafe_allow_html=True)
    st.caption("Query the underlying in-memory database directly. Explore the schema, try the challenges, or write your own queries.")

    with st.expander("Database Schema & Row Counts", expanded=True):
        row_counts, _ = run_query("""
            SELECT
                (SELECT COUNT(*) FROM users) as users_n,
                (SELECT COUNT(*) FROM sessions) as sessions_n,
                (SELECT COUNT(*) FROM events) as events_n,
                (SELECT COUNT(*) FROM orders) as orders_n
        """)
        un = f"{row_counts['users_n'].iloc[0]:,}" if row_counts is not None else "?"
        sn = f"{row_counts['sessions_n'].iloc[0]:,}" if row_counts is not None else "?"
        en = f"{row_counts['events_n'].iloc[0]:,}" if row_counts is not None else "?"
        on = f"{row_counts['orders_n'].iloc[0]:,}" if row_counts is not None else "?"

        st.markdown(f"""
<div class="schema-container">
<span class="tbl-name">users</span> <span class="col-type">({un} rows)</span><br>
&nbsp;&nbsp;<span class="col-pk">user_id</span> <span class="col-type">INT PK</span>,
<span class="col-name">signup_date</span> <span class="col-type">TEXT</span>,
<span class="col-name">segment</span> <span class="col-type">TEXT</span>,
<span class="col-name">device</span> <span class="col-type">TEXT</span>,
<span class="col-name">acquisition_channel</span> <span class="col-type">TEXT</span>
<br><br>
<span class="tbl-name">sessions</span> <span class="col-type">({sn} rows)</span><br>
&nbsp;&nbsp;<span class="col-pk">session_id</span> <span class="col-type">INT PK</span>,
<span class="col-fk">user_id</span> <span class="col-type">INT FK→users</span>,
<span class="col-name">date</span> <span class="col-type">TEXT</span>,
<span class="col-name">device</span> <span class="col-type">TEXT</span>,
<span class="col-name">variant</span> <span class="col-type">TEXT</span>
<br><br>
<span class="tbl-name">events</span> <span class="col-type">({en} rows)</span><br>
&nbsp;&nbsp;<span class="col-pk">event_id</span> <span class="col-type">INT PK</span>,
<span class="col-fk">session_id</span> <span class="col-type">INT FK→sessions</span>,
<span class="col-name">event_name</span> <span class="col-type">TEXT</span>,
<span class="col-name">timestamp</span> <span class="col-type">TEXT</span>
<br><br>
<span class="tbl-name">orders</span> <span class="col-type">({on} rows)</span><br>
&nbsp;&nbsp;<span class="col-pk">order_id</span> <span class="col-type">INT PK</span>,
<span class="col-fk">session_id</span> <span class="col-type">INT FK→sessions</span>,
<span class="col-fk">user_id</span> <span class="col-type">INT FK→users</span>,
<span class="col-name">order_value</span> <span class="col-type">REAL</span>,
<span class="col-name">delivery_time_mins</span> <span class="col-type">REAL</span>,
<span class="col-name">order_rating</span> <span class="col-type">INT</span>
<br>
<span class="section-label">event_name: <span class="enum-val">app_open, search_executed, restaurant_viewed, cart_added, checkout_initiated, payment_completed</span></span>
<span class="section-label">segment: <span class="enum-val">Power User, Casual Diner, New User</span> &nbsp;|&nbsp; variant: <span class="enum-val">Control, Treatment</span></span>
</div>
""", unsafe_allow_html=True)

    challenge = st.selectbox(
        "Pre-built SQL challenges",
        [
            "— Write your own —",
            "Challenge 1: Funnel Conversion by Device",
            "Challenge 2: Churn Cohorts — One-Time Buyers",
            "Challenge 3: Slow Delivery Analysis by Day of Week"
        ]
    )

    challenges_sql = {
        "Challenge 1: Funnel Conversion by Device": """-- Conversion rate from app_open to payment_completed by device type
SELECT
    s.device,
    COUNT(DISTINCT CASE WHEN e.event_name = 'app_open' THEN s.session_id END) AS app_opens,
    COUNT(DISTINCT CASE WHEN e.event_name = 'payment_completed' THEN s.session_id END) AS payments,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN e.event_name = 'payment_completed' THEN s.session_id END) AS FLOAT) /
        NULLIF(COUNT(DISTINCT CASE WHEN e.event_name = 'app_open' THEN s.session_id END), 0) * 100, 2
    ) AS conversion_rate_pct
FROM sessions s
JOIN events e ON s.session_id = e.session_id
GROUP BY s.device
ORDER BY conversion_rate_pct DESC;""",
        "Challenge 2: Churn Cohorts — One-Time Buyers": """-- Users who ordered in signup week but never ordered again
WITH first_week_buyers AS (
    SELECT u.user_id, u.signup_date
    FROM users u
    JOIN sessions s ON u.user_id = s.user_id
    JOIN orders o ON s.session_id = o.session_id
    WHERE CAST((JULIANDAY(s.date) - JULIANDAY(u.signup_date)) AS INTEGER) <= 7
    GROUP BY u.user_id
),
repeat_buyers AS (
    SELECT DISTINCT u.user_id
    FROM users u
    JOIN sessions s ON u.user_id = s.user_id
    JOIN orders o ON s.session_id = o.session_id
    WHERE CAST((JULIANDAY(s.date) - JULIANDAY(u.signup_date)) AS INTEGER) > 7
)
SELECT
    COUNT(DISTINCT fwb.user_id) AS first_week_buyers,
    COUNT(DISTINCT fwb.user_id) - COUNT(DISTINCT rb.user_id) AS churned_after_first_week,
    ROUND(
        (COUNT(DISTINCT fwb.user_id) - COUNT(DISTINCT rb.user_id)) * 100.0 /
        NULLIF(COUNT(DISTINCT fwb.user_id), 0), 1
    ) AS churn_rate_pct
FROM first_week_buyers fwb
LEFT JOIN repeat_buyers rb ON fwb.user_id = rb.user_id;""",
        "Challenge 3: Slow Delivery Analysis by Day of Week": """-- Average delivery time by day of week, flagging weekend inefficiency
SELECT
    CASE CAST(strftime('%w', s.date) AS INTEGER)
        WHEN 0 THEN 'Sunday'    WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'   WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'  WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_of_week,
    COUNT(*) AS total_orders,
    ROUND(AVG(o.delivery_time_mins), 1) AS avg_delivery_mins,
    ROUND(AVG(CASE WHEN o.delivery_time_mins > 35 THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_over_35min
FROM orders o
JOIN sessions s ON o.session_id = s.session_id
GROUP BY strftime('%w', s.date)
ORDER BY CAST(strftime('%w', s.date) AS INTEGER);"""
    }

    default_sql = challenges_sql.get(challenge, "SELECT * FROM users LIMIT 10;")
    if challenge == "— Write your own —":
        default_sql = "SELECT * FROM users LIMIT 10;"

    sql_input = st.text_area("SQL Query", value=default_sql, height=200, key="sql_editor")

    if st.button("Execute Query", type="primary", use_container_width=False):
        if sql_input.strip():
            result_df, error = run_query(sql_input)
            if error:
                st.error(f"```\n{error}\n```")
            elif result_df is not None:
                st.success(f"Returned {len(result_df):,} rows")
                st.dataframe(result_df, use_container_width=True, height=420)
        else:
            st.warning("Enter a SQL query to execute.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="footer">
    Built by <strong>Ishaan Gupta</strong> · BiteMetrics v1.0<br>
    Streamlit + Plotly + SQLite · Simulated data for demonstration
</div>
""", unsafe_allow_html=True)
