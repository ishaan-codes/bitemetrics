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
CHARCOAL = "#1C1C1C"
LIGHT_BG = "#F8F9FA"
CARD_BG = "#FFFFFF"
MUTED_TEXT = "#6C757D"

PLOTLY_TEMPLATE = dict(
    layout=go.Layout(
        font=dict(family="Inter, sans-serif", color=CHARCOAL),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[ZOMATO_RED, "#2D2D2D", "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
    )
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main .block-container {
    padding-top: 2rem;
    max-width: 1200px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    height: 48px;
    border-radius: 8px 8px 0 0;
    padding: 0 24px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #E23744 !important;
    color: white !important;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(226,55,68,0.12);
}
div[data-testid="stMetric"] label {
    color: #6C757D !important;
    font-weight: 500;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1C1C1C;
    font-weight: 700;
}
.hero-header {
    background: linear-gradient(135deg, #E23744 0%, #C62828 100%);
    color: white;
    padding: 32px 40px;
    border-radius: 16px;
    margin-bottom: 24px;
}
.hero-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 800;
}
.hero-header p {
    margin: 8px 0 0 0;
    opacity: 0.9;
    font-size: 1rem;
}
.hypothesis-card {
    background: #FFF5F5;
    border-left: 4px solid #E23744;
    padding: 16px 20px;
    border-radius: 0 12px 12px 0;
    margin-bottom: 12px;
}
.hypothesis-card strong {
    color: #E23744;
}
.stat-badge-sig {
    background: #D4EDDA;
    color: #155724;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}
.stat-badge-notsig {
    background: #F8D7DA;
    color: #721C24;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}
.srm-alert {
    background: #F8D7DA;
    border: 2px solid #E23744;
    padding: 16px;
    border-radius: 12px;
    color: #721C24;
    font-weight: 600;
    text-align: center;
}
.schema-box {
    background: #1C1C1C;
    color: #00FF88;
    padding: 16px;
    border-radius: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.6;
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

    # Cumulative funnel rates (fraction of all sessions reaching each step)
    # Control: ~8% end-to-end, Treatment: ~11%
    control_cum = [1.0, 0.72, 0.58, 0.38, 0.22, 0.08]
    treatment_cum = [1.0, 0.75, 0.62, 0.43, 0.28, 0.11]

    def cum_to_conditional(cum):
        return [cum[0]] + [cum[i] / cum[i-1] if cum[i-1] > 0 else 0 for i in range(1, len(cum))]

    control_probs = cum_to_conditional(control_cum)
    treatment_probs = cum_to_conditional(treatment_cum)

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

        # Device modifier (applied to cumulative rates before converting)
        if dev == "Web":
            cum = [cum[0]] + [c * 0.85 for c in cum[1:]]

        # Segment modifier
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
        df = pd.read_sql_query(query, conn)
        return df, None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <h1>🍽️ BiteMetrics</h1>
    <p>Zomato Order Funnel & A/B Testing Simulator — Interactive Product Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ Global Filters")
    st.markdown("---")

    all_devices = ["iOS", "Android", "Web"]
    selected_devices = st.multiselect("Device Type", all_devices, default=all_devices)

    all_segments = ["Power User", "Casual Diner", "New User"]
    selected_segments = st.multiselect("User Segment", all_segments, default=all_segments)

    all_channels = ["Search", "Instagram", "Referral"]
    selected_channels = st.multiselect("Acquisition Channel", all_channels, default=all_channels)

    st.markdown("---")
    st.markdown("##### 📊 Data Summary")
    summary, _ = run_query("SELECT COUNT(DISTINCT user_id) as users, COUNT(DISTINCT session_id) as sessions FROM sessions")
    if summary is not None:
        st.metric("Total Users", f"{summary['users'].iloc[0]:,}")
        st.metric("Total Sessions", f"{summary['sessions'].iloc[0]:,}")

    order_count, _ = run_query("SELECT COUNT(*) as cnt FROM orders")
    if order_count is not None:
        st.metric("Total Orders", f"{order_count['cnt'].iloc[0]:,}")


def check_filters():
    if not selected_devices or not selected_segments or not selected_channels:
        st.warning("⚠️ Please select at least one option in each filter to visualize data.")
        return False
    return True


def get_filter_clause(device_col="s.device", user_table_prefix="u"):
    devs = ",".join([f"'{d}'" for d in selected_devices])
    segs = ",".join([f"'{s}'" for s in selected_segments])
    chs = ",".join([f"'{c}'" for c in selected_channels])
    return f"""
        {device_col} IN ({devs})
        AND {user_table_prefix}.segment IN ({segs})
        AND {user_table_prefix}.acquisition_channel IN ({chs})
    """


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Funnel Analysis",
    "🧪 A/B Testing Engine",
    "📈 Cohort Retention",
    "💻 SQL Sandbox"
])

# ---------------------------------------------------------------------------
# Tab 1: Funnel Drop-off & Friction Analysis
# ---------------------------------------------------------------------------
with tab1:
    if check_filters():
        st.markdown("### Conversion Funnel Drop-off Analysis")

        slice_by = st.selectbox(
            "Segment funnel by:",
            ["Overall", "Device Type", "User Segment", "Acquisition Channel"],
            key="funnel_slicer"
        )

        filter_clause = get_filter_clause()

        funnel_steps = ["app_open", "search_executed", "restaurant_viewed",
                        "cart_added", "checkout_initiated", "payment_completed"]
        step_labels = ["App Open", "Search", "Restaurant View",
                       "Cart Added", "Checkout", "Payment"]

        if slice_by == "Overall":
            funnel_query = f"""
                SELECT e.event_name, COUNT(DISTINCT e.session_id) as sessions
                FROM events e
                JOIN sessions s ON e.session_id = s.session_id
                JOIN users u ON s.user_id = u.user_id
                WHERE {filter_clause}
                GROUP BY e.event_name
            """
            funnel_df, err = run_query(funnel_query)
            if funnel_df is not None and not funnel_df.empty:
                counts = []
                for step in funnel_steps:
                    row = funnel_df[funnel_df["event_name"] == step]
                    counts.append(row["sessions"].iloc[0] if not row.empty else 0)

                fig = go.Figure(go.Funnel(
                    y=step_labels,
                    x=counts,
                    textinfo="value+percent initial+percent previous",
                    marker=dict(color=[ZOMATO_RED, "#FF6B6B", "#FF8A80", "#FFAB91", "#FFCC80", "#4ECDC4"]),
                    connector=dict(line=dict(color="#E8E8E8", width=2))
                ))
                fig.update_layout(
                    template=PLOTLY_TEMPLATE,
                    height=500,
                    margin=dict(l=20, r=20, t=40, b=20),
                    title=dict(text="Order Funnel — All Sessions", font=dict(size=16))
                )
                st.plotly_chart(fig, use_container_width=True)

                # Drop-off metrics
                st.markdown("#### 📉 Step-by-Step Drop-off Rates")
                cols = st.columns(5)
                for i in range(1, len(counts)):
                    if counts[i-1] > 0:
                        dropoff = (1 - counts[i] / counts[i-1]) * 100
                    else:
                        dropoff = 0
                    cols[i-1].metric(
                        f"{step_labels[i-1]} → {step_labels[i]}",
                        f"{dropoff:.1f}% drop",
                        delta=f"-{counts[i-1] - counts[i]:,} sessions",
                        delta_color="inverse"
                    )

                # Time between stages
                st.markdown("#### ⏱️ Average Time Between Stages (minutes)")
                time_query = f"""
                    SELECT e1.event_name as from_step, e2.event_name as to_step,
                        AVG((JULIANDAY(e2.timestamp) - JULIANDAY(e1.timestamp)) * 1440) as avg_mins
                    FROM events e1
                    JOIN events e2 ON e1.session_id = e2.session_id
                    JOIN sessions s ON e1.session_id = s.session_id
                    JOIN users u ON s.user_id = u.user_id
                    WHERE {filter_clause}
                    AND e1.event_name = 'checkout_initiated'
                    AND e2.event_name = 'payment_completed'
                    GROUP BY e1.event_name, e2.event_name
                """
                time_df, _ = run_query(time_query)
                if time_df is not None and not time_df.empty:
                    avg_payment_time = time_df["avg_mins"].iloc[0]
                    st.info(f"🕐 **Checkout → Payment avg time: {avg_payment_time:.1f} min** — "
                            f"{'⚠️ High friction detected!' if avg_payment_time > 3 else '✅ Acceptable latency.'}")

                # Hypothesis Engine
                st.markdown("#### 💡 Product Hypothesis Engine")
                max_dropoff_idx = 0
                max_dropoff_rate = 0
                for i in range(1, len(counts)):
                    if counts[i-1] > 0:
                        rate = 1 - counts[i] / counts[i-1]
                        if rate > max_dropoff_rate:
                            max_dropoff_rate = rate
                            max_dropoff_idx = i

                friction_point = step_labels[max_dropoff_idx]
                prev_point = step_labels[max_dropoff_idx - 1] if max_dropoff_idx > 0 else "Start"

                hypotheses = {
                    "Search": [
                        "Search ranking relevance may be poor — users aren't finding restaurants they want.",
                        "Auto-suggestions may be missing for popular cuisines, causing user drop-off.",
                        "Search latency on older devices could exceed user patience thresholds."
                    ],
                    "Restaurant View": [
                        "Restaurant listing cards may lack social proof (ratings, photos) to drive clicks.",
                        "High delivery fees shown upfront on listing cards may deter exploration.",
                        "Cuisine categorization may not match user mental models."
                    ],
                    "Cart Added": [
                        "Menu UI complexity may overwhelm users — too many options without smart defaults.",
                        "Missing dish-level ratings or photos reduces purchase confidence.",
                        "Minimum order value requirements may create friction for single-item orders."
                    ],
                    "Checkout": [
                        "Unexpected delivery fees or taxes revealed at checkout cause 'sticker shock'.",
                        "Checkout flow has too many steps — address, payment, tip, instructions.",
                        "Lack of a guest checkout option forces registration, increasing abandonment."
                    ],
                    "Payment": [
                        "Payment gateway timeouts are causing transaction failures.",
                        "Limited payment options (no UPI/wallet) for the user's preferred method.",
                        "OTP/2FA friction on card payments creates a point of no return."
                    ],
                }

                hyps = hypotheses.get(friction_point, hypotheses["Checkout"])
                st.markdown(f"**Biggest friction: {prev_point} → {friction_point} ({max_dropoff_rate*100:.1f}% drop-off)**")
                for h in hyps:
                    st.markdown(f'<div class="hypothesis-card">💡 <strong>Hypothesis:</strong> {h}</div>', unsafe_allow_html=True)

        else:
            group_col_map = {
                "Device Type": "s.device",
                "User Segment": "u.segment",
                "Acquisition Channel": "u.acquisition_channel"
            }
            group_col = group_col_map[slice_by]

            seg_query = f"""
                SELECT {group_col} as segment_val, e.event_name, COUNT(DISTINCT e.session_id) as sessions
                FROM events e
                JOIN sessions s ON e.session_id = s.session_id
                JOIN users u ON s.user_id = u.user_id
                WHERE {filter_clause}
                GROUP BY {group_col}, e.event_name
            """
            seg_df, _ = run_query(seg_query)
            if seg_df is not None and not seg_df.empty:
                fig = go.Figure()
                for seg_val in seg_df["segment_val"].unique():
                    sub = seg_df[seg_df["segment_val"] == seg_val]
                    counts = []
                    for step in funnel_steps:
                        row = sub[sub["event_name"] == step]
                        counts.append(row["sessions"].iloc[0] if not row.empty else 0)
                    fig.add_trace(go.Funnel(
                        name=seg_val,
                        y=step_labels,
                        x=counts,
                        textinfo="value+percent initial"
                    ))
                fig.update_layout(
                    template=PLOTLY_TEMPLATE,
                    height=500,
                    margin=dict(l=20, r=20, t=40, b=20),
                    title=dict(text=f"Funnel by {slice_by}", font=dict(size=16))
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 2: A/B Testing Engine
# ---------------------------------------------------------------------------
with tab2:
    if check_filters():
        st.markdown("### 🧪 Experimentation Dashboard — AI Cross-Sell Recommendations")
        st.caption("**Control (A):** Standard cart  |  **Treatment (B):** AI-powered cross-sell recommendations")

        filter_clause = get_filter_clause()

        # Core metrics
        ab_query = f"""
            SELECT
                s.variant,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COUNT(DISTINCT CASE WHEN e.event_name = 'payment_completed' THEN s.session_id END) as conversions
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            LEFT JOIN events e ON s.session_id = e.session_id AND e.event_name = 'payment_completed'
            WHERE {filter_clause}
            GROUP BY s.variant
        """
        ab_df, _ = run_query(ab_query)

        aov_query = f"""
            SELECT s.variant, AVG(o.order_value) as avg_aov, COUNT(*) as order_count,
                   GROUP_CONCAT(o.order_value) as all_values
            FROM orders o
            JOIN sessions s ON o.session_id = s.session_id
            JOIN users u ON s.user_id = u.user_id
            WHERE {filter_clause}
            GROUP BY s.variant
        """
        aov_df, _ = run_query(aov_query)

        if ab_df is not None and len(ab_df) == 2:
            control = ab_df[ab_df["variant"] == "Control"].iloc[0]
            treatment = ab_df[ab_df["variant"] == "Treatment"].iloc[0]

            n_a, n_b = int(control["total_sessions"]), int(treatment["total_sessions"])
            conv_a, conv_b = int(control["conversions"]), int(treatment["conversions"])
            cr_a = conv_a / n_a if n_a > 0 else 0
            cr_b = conv_b / n_b if n_b > 0 else 0
            relative_lift = ((cr_b - cr_a) / cr_a * 100) if cr_a > 0 else 0

            st.markdown("#### 📊 Core Experiment Metrics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Control CR", f"{cr_a*100:.2f}%", help="Conversion rate for Variant A")
            col2.metric("Treatment CR", f"{cr_b*100:.2f}%", help="Conversion rate for Variant B")
            col3.metric("Relative Lift", f"+{relative_lift:.1f}%", delta=f"+{relative_lift:.1f}%")
            col4.metric("Sample Sizes", f"{n_a:,} / {n_b:,}", help="N_A / N_B")

            st.markdown("---")

            # Statistical Tests
            st.markdown("#### 🔬 Statistical Rigor")
            test_col1, test_col2 = st.columns(2)

            with test_col1:
                st.markdown("##### Chi-Square Test (Conversion Rate)")
                if min(n_a, n_b) >= 30:
                    contingency = np.array([
                        [conv_a, n_a - conv_a],
                        [conv_b, n_b - conv_b]
                    ])
                    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
                    significant = p_value < 0.05

                    st.markdown(f"**χ² statistic:** {chi2:.4f}")
                    st.markdown(f"**p-value:** {p_value:.6f}")
                    if significant:
                        st.markdown('<span class="stat-badge-sig">✅ Statistically Significant (p < 0.05)</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="stat-badge-notsig">❌ Not Significant (p ≥ 0.05)</span>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Sample size < 30. Results may be unreliable.")

            with test_col2:
                st.markdown("##### Welch's T-Test (Average Order Value)")
                if aov_df is not None and len(aov_df) == 2:
                    aov_control_vals_q = f"""
                        SELECT o.order_value FROM orders o
                        JOIN sessions s ON o.session_id = s.session_id
                        JOIN users u ON s.user_id = u.user_id
                        WHERE s.variant = 'Control' AND {filter_clause}
                    """
                    aov_treat_vals_q = f"""
                        SELECT o.order_value FROM orders o
                        JOIN sessions s ON o.session_id = s.session_id
                        JOIN users u ON s.user_id = u.user_id
                        WHERE s.variant = 'Treatment' AND {filter_clause}
                    """
                    aov_c, _ = run_query(aov_control_vals_q)
                    aov_t, _ = run_query(aov_treat_vals_q)

                    if aov_c is not None and aov_t is not None and len(aov_c) >= 30 and len(aov_t) >= 30:
                        t_stat, t_pval = stats.ttest_ind(aov_c["order_value"], aov_t["order_value"], equal_var=False)
                        aov_a_mean = aov_c["order_value"].mean()
                        aov_b_mean = aov_t["order_value"].mean()

                        ci_diff = aov_b_mean - aov_a_mean
                        se = np.sqrt(aov_c["order_value"].var()/len(aov_c) + aov_t["order_value"].var()/len(aov_t))
                        ci_lower = ci_diff - 1.96 * se
                        ci_upper = ci_diff + 1.96 * se

                        st.markdown(f"**AOV Control:** ₹{aov_a_mean:.0f}  |  **AOV Treatment:** ₹{aov_b_mean:.0f}")
                        st.markdown(f"**t-statistic:** {t_stat:.4f}")
                        st.markdown(f"**p-value:** {t_pval:.6f}")
                        st.markdown(f"**95% CI for Δ AOV:** [₹{ci_lower:.1f}, ₹{ci_upper:.1f}]")

                        if t_pval < 0.05:
                            st.markdown('<span class="stat-badge-sig">✅ AOV Lift Significant</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="stat-badge-notsig">❌ AOV Lift Not Significant</span>', unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Insufficient order data for T-Test.")

            st.markdown("---")

            # SRM Check
            st.markdown("#### 🚨 Sample Ratio Mismatch (SRM) Check")
            expected_ratio = np.array([0.5, 0.5])
            observed = np.array([n_a, n_b])
            chi2_srm, p_srm = stats.chisquare(observed, f_exp=expected_ratio * observed.sum())

            srm_col1, srm_col2, srm_col3 = st.columns(3)
            srm_col1.metric("Expected Split", "50% / 50%")
            srm_col2.metric("Observed Split", f"{n_a/(n_a+n_b)*100:.1f}% / {n_b/(n_a+n_b)*100:.1f}%")
            srm_col3.metric("SRM p-value", f"{p_srm:.6f}")

            if p_srm < 0.001:
                st.markdown('<div class="srm-alert">🚨 <strong>SRM ALERT:</strong> Traffic distribution is significantly biased (p < 0.001). Experiment results may be invalid. Investigate assignment logic.</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No Sample Ratio Mismatch detected. Traffic split is balanced.")

            st.markdown("---")

            # Guardrail Metrics
            st.markdown("#### 🛡️ Guardrail Metrics")
            g_col1, g_col2 = st.columns(2)

            with g_col1:
                st.markdown("##### App Latency (simulated)")
                latency_a = np.random.normal(220, 30, 100)
                latency_b = np.random.normal(225, 32, 100)
                fig_lat = go.Figure()
                fig_lat.add_trace(go.Box(y=latency_a, name="Control", marker_color=MUTED_TEXT))
                fig_lat.add_trace(go.Box(y=latency_b, name="Treatment", marker_color=ZOMATO_RED))
                fig_lat.update_layout(
                    template=PLOTLY_TEMPLATE, height=300,
                    title="P50 Latency (ms)", yaxis_title="ms",
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_lat, use_container_width=True)
                st.caption("No significant latency degradation in Treatment.")

            with g_col2:
                st.markdown("##### Support Tickets (simulated)")
                weeks = [f"W{i}" for i in range(1, 7)]
                tickets_a = [45, 42, 48, 44, 41, 43]
                tickets_b = [44, 46, 43, 47, 45, 44]
                fig_tix = go.Figure()
                fig_tix.add_trace(go.Scatter(x=weeks, y=tickets_a, name="Control", line=dict(color=MUTED_TEXT, width=2)))
                fig_tix.add_trace(go.Scatter(x=weeks, y=tickets_b, name="Treatment", line=dict(color=ZOMATO_RED, width=2)))
                fig_tix.update_layout(
                    template=PLOTLY_TEMPLATE, height=300,
                    title="Weekly Support Tickets", yaxis_title="Tickets",
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_tix, use_container_width=True)
                st.caption("Support ticket volume stable across variants.")

# ---------------------------------------------------------------------------
# Tab 3: Cohort Retention
# ---------------------------------------------------------------------------
with tab3:
    if check_filters():
        st.markdown("### 📈 Weekly Cohort Retention Analysis")

        retention_type = st.radio(
            "Retention Type:",
            ["N-Week Retention", "Unbounded Retention"],
            horizontal=True,
            help="N-Week: active in exactly that week. Unbounded: active in that week or any later week."
        )

        filter_clause = get_filter_clause()

        cohort_query = f"""
            WITH user_cohorts AS (
                SELECT u.user_id,
                    CAST((JULIANDAY(u.signup_date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as cohort_week
                FROM users u
                WHERE u.segment IN ({",".join([f"'{s}'" for s in selected_segments])})
                    AND u.device IN ({",".join([f"'{d}'" for d in selected_devices])})
                    AND u.acquisition_channel IN ({",".join([f"'{c}'" for c in selected_channels])})
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
        """

        cohort_sizes_query = f"""
            SELECT CAST((JULIANDAY(u.signup_date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as cohort_week,
                   COUNT(DISTINCT u.user_id) as cohort_size
            FROM users u
            WHERE u.segment IN ({",".join([f"'{s}'" for s in selected_segments])})
                AND u.device IN ({",".join([f"'{d}'" for d in selected_devices])})
                AND u.acquisition_channel IN ({",".join([f"'{c}'" for c in selected_channels])})
            GROUP BY cohort_week
        """

        cohort_df, _ = run_query(cohort_query)
        sizes_df, _ = run_query(cohort_sizes_query)

        if cohort_df is not None and sizes_df is not None and not cohort_df.empty:
            sizes_map = dict(zip(sizes_df["cohort_week"], sizes_df["cohort_size"]))

            max_weeks = 7
            cohort_weeks = sorted(cohort_df["cohort_week"].unique())
            cohort_weeks = [w for w in cohort_weeks if w >= 0 and w < max_weeks]

            retention_matrix = np.zeros((len(cohort_weeks), max_weeks))

            for i, cw in enumerate(cohort_weeks):
                cohort_size = sizes_map.get(cw, 0)
                if cohort_size == 0:
                    continue

                if retention_type == "N-Week Retention":
                    for week_offset in range(max_weeks):
                        target_week = cw + week_offset
                        row = cohort_df[(cohort_df["cohort_week"] == cw) & (cohort_df["activity_week"] == target_week)]
                        active = row["active_users"].iloc[0] if not row.empty else 0
                        retention_matrix[i, week_offset] = active / cohort_size * 100
                else:
                    for week_offset in range(max_weeks):
                        target_weeks = range(cw + week_offset, cw + max_weeks + 5)
                        active = cohort_df[
                            (cohort_df["cohort_week"] == cw) &
                            (cohort_df["activity_week"].isin(target_weeks))
                        ]["active_users"].sum()
                        active = min(active, cohort_size)
                        retention_matrix[i, week_offset] = active / cohort_size * 100

            cohort_labels = [f"Week {w}" for w in cohort_weeks]
            period_labels = [f"+{w}w" for w in range(max_weeks)]

            fig_heatmap = px.imshow(
                retention_matrix,
                x=period_labels,
                y=cohort_labels,
                color_continuous_scale=[[0, "#FFF5F5"], [0.5, "#FF6B6B"], [1, "#E23744"]],
                aspect="auto",
                text_auto=".1f",
                labels=dict(x="Weeks Since Signup", y="Cohort", color="Retention %")
            )
            fig_heatmap.update_layout(
                template=PLOTLY_TEMPLATE,
                height=400,
                title=dict(text=f"{retention_type} Heatmap", font=dict(size=16)),
                margin=dict(l=20, r=20, t=60, b=20)
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

            # LTV Projection
            st.markdown("#### 💰 Cumulative Revenue by Cohort (LTV Proxy)")
            ltv_query = f"""
                SELECT
                    CAST((JULIANDAY(u.signup_date) - JULIANDAY('2026-06-01')) / 7 AS INTEGER) as cohort_week,
                    CAST((JULIANDAY(s.date) - JULIANDAY(u.signup_date)) / 7 AS INTEGER) as week_offset,
                    SUM(o.order_value) as revenue
                FROM orders o
                JOIN sessions s ON o.session_id = s.session_id
                JOIN users u ON o.user_id = u.user_id
                WHERE u.segment IN ({",".join([f"'{s}'" for s in selected_segments])})
                    AND s.device IN ({",".join([f"'{d}'" for d in selected_devices])})
                    AND u.acquisition_channel IN ({",".join([f"'{c}'" for c in selected_channels])})
                GROUP BY cohort_week, week_offset
                HAVING cohort_week >= 0 AND cohort_week < {max_weeks}
                ORDER BY cohort_week, week_offset
            """
            ltv_df, _ = run_query(ltv_query)
            if ltv_df is not None and not ltv_df.empty:
                fig_ltv = go.Figure()
                for cw in sorted(ltv_df["cohort_week"].unique()):
                    sub = ltv_df[ltv_df["cohort_week"] == cw].sort_values("week_offset")
                    sub["cum_revenue"] = sub["revenue"].cumsum()
                    fig_ltv.add_trace(go.Scatter(
                        x=sub["week_offset"],
                        y=sub["cum_revenue"],
                        name=f"Cohort W{int(cw)}",
                        mode="lines+markers"
                    ))
                fig_ltv.update_layout(
                    template=PLOTLY_TEMPLATE,
                    height=350,
                    title="Cumulative Revenue per Cohort",
                    xaxis_title="Weeks Since Signup",
                    yaxis_title="Cumulative Revenue (₹)",
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                st.plotly_chart(fig_ltv, use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 4: SQL Sandbox
# ---------------------------------------------------------------------------
with tab4:
    st.markdown("### 💻 Live SQL Sandbox")
    st.caption("Query the underlying database directly. Explore the schema, try the challenges, or write your own.")

    with st.expander("📋 Database Schema", expanded=False):
        st.markdown("""
<div class="schema-box">
<strong>users</strong> (user_id INT PK, signup_date TEXT, segment TEXT, device TEXT, acquisition_channel TEXT)<br>
<strong>sessions</strong> (session_id INT PK, user_id INT FK, date TEXT, device TEXT, variant TEXT)<br>
<strong>events</strong> (event_id INT PK, session_id INT FK, event_name TEXT, timestamp TEXT)<br>
<strong>orders</strong> (order_id INT PK, session_id INT FK, user_id INT FK, order_value REAL, delivery_time_mins REAL, order_rating INT)<br>
<br>
<em>event_name values:</em> app_open, search_executed, restaurant_viewed, cart_added, checkout_initiated, payment_completed<br>
<em>segment values:</em> Power User, Casual Diner, New User<br>
<em>variant values:</em> Control, Treatment
</div>
""", unsafe_allow_html=True)

    challenge = st.selectbox(
        "🏆 Pre-Built SQL Challenges:",
        [
            "-- Select a challenge --",
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
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
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
    if challenge == "-- Select a challenge --":
        default_sql = "SELECT * FROM users LIMIT 10;"

    sql_input = st.text_area(
        "Write your SQL query:",
        value=default_sql,
        height=180,
        key="sql_editor"
    )

    if st.button("▶️ Execute Query", type="primary"):
        if sql_input.strip():
            result_df, error = run_query(sql_input)
            if error:
                st.error(f"```\nSQL Error: {error}\n```")
            elif result_df is not None:
                st.success(f"✅ Query returned {len(result_df)} rows.")
                st.dataframe(result_df, use_container_width=True, height=400)
        else:
            st.warning("Please enter a SQL query.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#6C757D; font-size:0.85rem;'>"
    "Built by <strong>Ishaan Gupta</strong> — BiteMetrics v1.0 | "
    "Streamlit + Plotly + SQLite | "
    "Simulated data for demonstration purposes"
    "</div>",
    unsafe_allow_html=True
)
