import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import from the src folder
from src.load_data import (
    load_and_clean_expenses,
    categorize_transaction,
    detect_anomalies,
    calculate_monthly_stats,
    calculate_category_stats,
    calculate_net_flow,
    CATEGORIES
)

# --- Page Config ---
st.set_page_config(
    page_title="Personal Finance Analyzer",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State & Callbacks ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Default to dark mode as per user preference? Or False.

def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# --- Dynamic Colors ---
if st.session_state.dark_mode:
    text_main_color = "#ffffff"
    text_sub_color = "#e2e8f0"
    card_bg_color = "#1e293b"
    card_border_color = "#334155"
    sidebar_bg_color = "#0f172a"
    sidebar_text_color = "#ffffff"
else:
    text_main_color = "#1a202c"
    text_sub_color = "#4a5568"
    card_bg_color = "#ffffff"
    card_border_color = "#cbd5e0"
    sidebar_bg_color = "#f7fafc"
    sidebar_text_color = "#1a202c"

# --- Custom CSS ---
custom_css = f"""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Variables for dynamic use in CSS if needed, though we use f-strings mainly */
    :root {{
        --text-color: {text_main_color};
        --bg-color: {card_bg_color};
    }}

    /* Global Text Visibility */
    body, .stApp {{
        color: {text_main_color} !important;
        background-color: {'#0f172a' if st.session_state.dark_mode else '#f1f5f9'} !important;
    }}
    
    h1, h2, h3, h4, h5, h6, p, li, span, div, label, td, th, caption, .caption {{
        color: {text_main_color} !important;
    }}
    
    .stMarkdown p {{
        color: {text_main_color} !important;
    }}

    /* Sidebar Specifics */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg_color} !important;
        border-right: 1px solid {card_border_color} !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: {sidebar_text_color} !important;
    }}
    
    [data-testid="stSidebar"] a {{
        color: #3b82f6 !important;
    }}

    /* Sticky Mode Toggle Button */
    /* Target the container of the toggle button specifically */
    div.stButton > button:first-child {{
        border-radius: 9999px;
        font-weight: bold;
    }}
    
    /* We assume the toggle is the first button in the main area or we target it by key in a specific block */
    /* Since we can't easily target by key in CSS, we'll rely on placement */

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent !important;
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: {card_bg_color} !important;
        border: 1px solid {card_border_color} !important;
        color: {text_main_color} !important;
        border-radius: 8px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: #2563eb !important;
        color: white !important;
        border-color: #2563eb !important;
    }}

    /* File Uploader Redesign */
    [data-testid="stFileUploader"] {{
        background-color: {card_bg_color} !important;
        border: 2px dashed {card_border_color} !important;
        border-radius: 12px;
        padding: 1rem;
    }}
    
    [data-testid="stFileUploader"] section {{
        background-color: transparent !important;
    }}
    
    /* Browse Button Styling */
    [data-testid="stFileUploader"] button {{
        background-color: {('#334155' if st.session_state.dark_mode else '#e2e8f0')} !important;
        color: {text_main_color} !important;
        border: none !important;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: none !important; /* Remove hover transition */
    }}
    
    [data-testid="stFileUploader"] button:hover {{
        background-color: {('#475569' if st.session_state.dark_mode else '#cbd5e0')} !important;
        color: {text_main_color} !important;
        box-shadow: none !important;
        transform: none !important;
    }}
    
    /* Cards */
    .spending-card, .feature-card {{
        background-color: {card_bg_color} !important;
        border: 2px solid {card_border_color} !important;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: {text_main_color} !important;
    }}
    
    .spending-card h4, .feature-card h3 {{
        font-weight: 700 !important;
        opacity: 0.9;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select {{
        background-color: {card_bg_color} !important;
        color: {text_main_color} !important;
        border: 1px solid {card_border_color} !important;
        border-radius: 8px;
    }}

    /* Remove Hover Effects / Transforms globally on buttons */
    button {{
        transition: none !important;
        transform: none !important;
    }}
    button:hover {{
        transform: none !important;
        box-shadow: none !important;
    }}
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Layout: Header + Sticky Button ---
# To make a button truly interaction-safe and sticky, we place it in a container
# but standard CSS stickiness is best applied to a specific known container.
# Here we use a 'float' approach for visual stickiness.
st.markdown(f"""
    <style>
    div.element-container:has(button#dark_mode_toggle) {{
        position: fixed;
        top: 25px;
        right: 25px;
        z-index: 999999;
    }}
    </style>
""", unsafe_allow_html=True)

# We use an empty container to inject the button, relying on the 'key' (id) for positioning if possible?
# Streamlit generates ids like 'bui-2'. Reliable styling requires placement.
# We will place it in col2 of the header, and style that column to be fixed.

col_header_1, col_header_2 = st.columns([6, 1])

with col_header_1:
    st.title("💸 Personal Finance Analyzer")
    st.markdown("Smart insights with auto-categorization and anomaly detection.")

with col_header_2:
    # Sticky Toggle Button
    # We apply a wrapper div to target it easier if needed, or just use the layout trick.
    # The 'key' helps preserve state but not CSS target directly in basic Streamlit.
    # We use the previous CSS rule: [data-testid="column"]:nth-child(2) .stButton
    st.markdown(f"""
    <style>
    [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type(2) .stButton {{
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 999999;
        width: auto;
    }}
    [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type(2) .stButton button {{
        background-color: {'#3b82f6' if st.session_state.dark_mode else '#2563eb'} !important;
        color: white !important;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Callback-based toggle (no st.rerun needed, but good practice to allow standard flow)
    st.button(
        "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light", 
        on_click=toggle_dark_mode,
        key="btn_toggle_mode",
        use_container_width=False
    )

# --- Sidebar ---
with st.sidebar:
    st.header("📤 Upload Data")
    uploaded = st.file_uploader(
        "Upload bank statement CSV",
        type=["csv"],
        key="file_uploader_main"
    )
    
    if uploaded:
        st.markdown("---")
        st.header("⚙️ Settings")
        with st.expander("🔧 Format Options", expanded=False):
            manual_header = st.checkbox("Manually set header row", value=True)
            if manual_header:
                header_row = st.number_input("Header row (0-indexed)", 0, 50, 6)
            else:
                header_row = 6
    else:
        manual_header = True
        header_row = 6
    
    st.markdown("---")
    st.header("ℹ️ About")
    # Using specific class to ensure visibility if needed, but the global * selector should handle it
    st.markdown("""
    This app automatically:
    
    - ✅ **Cleans** data
    - 🏷️ **Categorizes** transactions
    - 📊 **Visualizes** patterns
    - 🚨 **Detects** anomalies
    - 💰 **Tracks** cash flow
    """)
    
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit & Python")

# --- Caching Data Processing ---
@st.cache_data(show_spinner=False)
def process_data(file, header_row_idx, manual_mode):
    # We need to read the file. Since file pointers reset, we might need to handle copies.
    # Streamlit passes a BytesIO-like object. 
    # To cache effectively, we shouldn't pass the open file object directly if it changes.
    # But for simplicity in this user fix, standard processing is fine if efficient.
    # We will just call the src functions.
    
    # Heuristic: Read raw first to avoid pointer issues inside cache
    if manual_mode and header_row_idx is not None:
        file.seek(0)
        df_raw = pd.read_csv(file, skiprows=range(0, header_row_idx), header=0)
        if 'unnamed' in str(df_raw.columns[0]).lower():
            df_raw = df_raw.iloc[:, 1:]
    else:
        file.seek(0)
        df_raw = pd.read_csv(file)
        
    df_clean = load_and_clean_expenses(df_override=df_raw, skip_header_detection=manual_mode)
    if not df_clean.empty:
        df_clean['category'] = df_clean['description'].apply(categorize_transaction)
        df_clean['is_anomaly'] = detect_anomalies(df_clean)
        df_clean['month'] = df_clean['date'].dt.to_period('M').astype(str)
        
    return df_clean

# --- Main Content ---
if not uploaded:
    # Landing Page
    st.markdown(f"""
        <div style="text-align: center; margin: 3rem 0;">
            <h2>Welcome to Your Financial Command Center 🚀</h2>
            <p style="font-size: 1.2rem; opacity: 0.8;">Upload your bank statement to begin</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <div class="spending-card">
                <div style='font-size: 0.9rem; font-weight: 700; color: {text_sub_color};'>🏷️ FEATURE</div>
                <div style='font-size: 1.5rem; font-weight: 900; margin: 0.5rem 0;'>Auto Categorization</div>
                <div style='font-size: 1rem; opacity: 0.8;'>Smart AI classification</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="feature-card">
                <div style='font-size: 0.9rem; font-weight: 700; color: {text_sub_color};'>🚨 FEATURE</div>
                <div style='font-size: 1.5rem; font-weight: 900; margin: 0.5rem 0;'>Anomaly Detection</div>
                <div style='font-size: 1rem; opacity: 0.8;'>Spot unusual transactions</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="feature-card">
                <div style='font-size: 0.9rem; font-weight: 700; color: {text_sub_color};'>💰 FEATURE</div>
                <div style='font-size: 1.5rem; font-weight: 900; margin: 0.5rem 0;'>Track Savings</div>
                <div style='font-size: 1rem; opacity: 0.8;'>Monitor financial health</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("📋 Data Format Guide"):
        st.info("Required columns: Date, Description, Amount (or Debit/Credit)")
        
    st.stop()

# --- Process Uploaded Data ---
try:
    # Use the cached function
    df = process_data(uploaded, header_row, manual_header)
    
    if df.empty:
        st.warning("⚠️ No valid transactions found.")
        st.stop()

    # --- Dashboard ---
    # Metrics
    st.header("📈 Financial Overview")
    net_flow = calculate_net_flow(df)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
                <div style='font-size: 0.9rem; margin-bottom: 0.2rem;'>💰 Income</div>
                <div style='font-size: 1.8rem; font-weight: 800;'>₦{net_flow['income']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
                <div style='font-size: 0.9rem; margin-bottom: 0.2rem;'>💸 Expenses</div>
                <div style='font-size: 1.8rem; font-weight: 800;'>₦{net_flow['expenses']:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
                <div style='font-size: 0.9rem; margin-bottom: 0.2rem;'>📊 Net Flow</div>
                <div style='font-size: 1.8rem; font-weight: 800;'>₦{net_flow['net']:,.0f}</div>
                <div style='font-size: 0.8rem;'>{net_flow['savings_rate']:.1f}% Savings</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        acount = df['is_anomaly'].sum()
        acolor = "#ef4444" if acount > 0 else "#10b981"
        st.markdown(f"""
            <div style='background: {acolor}; padding: 1.5rem; border-radius: 12px; color: white; text-align: center;'>
                <div style='font-size: 0.9rem; margin-bottom: 0.2rem;'>🚨 Anomalies</div>
                <div style='font-size: 1.8rem; font-weight: 800;'>{acount}</div>
                <div style='font-size: 0.8rem;'>{'Check details' if acount > 0 else 'All good'}</div>
            </div>
        """, unsafe_allow_html=True)

    # Key Stats Cards
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    
    top_cat = df.groupby('category')['amount'].sum().abs().idxmax()
    top_amt = df.groupby('category')['amount'].sum().abs().max()
    avg_txn = df['amount'].abs().mean()
    daily = df[df['amount'] < 0]['amount'].sum() / ((df['date'].max() - df['date'].min()).days + 1)
    
    with k1:
        st.markdown(f"""
            <div class="spending-card">
                <div style='font-size: 0.9rem; font-weight: 700; color: {text_sub_color};'>💳 Top Expense</div>
                <div style='font-size: 1.6rem; font-weight: 900; margin: 0.5rem 0;'>{top_cat}</div>
                <div style='font-size: 1rem; opacity: 0.8;'>₦{top_amt:,.0f} total</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="spending-card">
                <div style='font-size: 0.9rem; font-weight: 700; color: {text_sub_color};'>📊 Avg Transaction</div>
                <div style='font-size: 1.6rem; font-weight: 900; margin: 0.5rem 0;'>₦{avg_txn:,.0f}</div>
                <div style='font-size: 1rem; opacity: 0.8;'>{len(df)} transactions</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="spending-card">
                <div style='font-size: 0.9rem; font-weight: 700; color: {text_sub_color};'>📅 Daily Burn</div>
                <div style='font-size: 1.6rem; font-weight: 900; margin: 0.5rem 0;'>₦{abs(daily):,.0f}</div>
                <div style='font-size: 1rem; opacity: 0.8;'>Average daily spend</div>
            </div>
        """, unsafe_allow_html=True)

    # Detailed Tabs
    st.markdown("<br>", unsafe_allow_html=True)
    tabs = st.tabs(["📊 Patterns", "📅 Trends", "🥧 breakdown", "💹 Cash Flow", "🎯 Budget"])
    
    with tabs[0]:
        cat_stats = calculate_category_stats(df)
        fig = px.bar(cat_stats.reset_index(), x='category', y='Total', color='Total')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=text_main_color)
        st.plotly_chart(fig, use_container_width=True)
        
    with tabs[1]:
        m_stats = calculate_monthly_stats(df)
        
        # Enhanced Trends Chart
        fig = go.Figure()
        
        # Colors based on mode
        line_color = '#60a5fa' if st.session_state.dark_mode else '#2563eb' # Lighter blue in dark, Strong blue in light
        marker_color = '#ffffff' if st.session_state.dark_mode else '#1e40af'
        
        fig.add_trace(go.Scatter(
            x=m_stats.index.astype(str), 
            y=m_stats['Total'], 
            mode='lines+markers+text',
            name='Spending',
            line=dict(color=line_color, width=4),
            marker=dict(size=8, color=marker_color, line=dict(width=2, color=line_color)),
            text=[f"₦{v:,.0f}" for v in m_stats['Total']],
            textposition="top center",
            textfont=dict(
                size=12, 
                color=text_main_color,
                family="sans-serif",
                weight="bold"
            )
        ))
        
        fig.update_layout(
            title=dict(
                text='Monthly Spending Trend',
                font=dict(size=18, color=text_main_color)
            ),
            xaxis=dict(
                title="Month",
                showgrid=True,
                gridcolor=card_border_color,
                tickfont=dict(color=text_main_color)
            ),
            yaxis=dict(
                title="Amount (₦)",
                showgrid=True,
                gridcolor=card_border_color,
                tickfont=dict(color=text_main_color),
                zeroline=False
            ),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            height=450,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tabs[2]:
        sub_df = df[df['category'] != 'Income']
        fig = px.pie(sub_df, values='amount', names='category', hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color=text_main_color)
        st.plotly_chart(fig, use_container_width=True)
        
    with tabs[3]:
        # Cash flow stub
        nf = calculate_net_flow(df)
        nf_df = pd.DataFrame.from_dict(nf, orient='index', columns=['value'])
        # Format currency rows with commas
        for idx in ['income', 'expenses', 'net']:
            nf_df.loc[idx, 'value'] = f"{nf_df.loc[idx, 'value']:,.2f}"
        st.dataframe(nf_df, use_container_width=True)
        
    with tabs[4]:
        st.subheader("🎯 Budget Tracker", anchor=False)
        
        # Budget Input & Period
        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            budget = st.number_input("Set Budget Target (₦)", value=200000, step=5000)
        with col_b2:
            period = st.selectbox("Period", ["All Time", "This Month", "Last Month"], index=1)
            
        # Calculate Logic based on Period
        if period == "This Month":
            current_month = df['date'].max().to_period('M')
            mask = df['month'] == str(current_month)
            spent = abs(df[mask & (df['amount'] < 0)]['amount'].sum())
        elif period == "Last Month":
            last_month = (df['date'].max() - pd.DateOffset(months=1)).to_period('M')
            mask = df['month'] == str(last_month)
            spent = abs(df[mask & (df['amount'] < 0)]['amount'].sum())
        else:
            spent = abs(df[df['amount'] < 0]['amount'].sum())
        
        if budget > 0:
            percent = (spent / budget) * 100
        else:
            percent = 100 if spent > 0 else 0
            
        remaining = budget - spent
        
        # Determine Color & Status
        if percent >= 100:
            status_color = "#ef4444"  # Red
            status_msg = "⚠️ OVER BUDGET"
        elif percent >= 80:
            status_color = "#f59e0b"  # Yellow/Orange
            status_msg = "⚠️ Approaching Limit"
        else:
            status_color = "#10b981"  # Green
            status_msg = "✅ Within Budget"
            
        # Display Metrics
        b1, b2, b3 = st.columns(3)
        with b1:
            st.metric("Total Budget", f"₦{budget:,.0f}")
        with b2:
            st.metric("Total Spent", f"₦{spent:,.0f}", delta=f"{percent:.1f}% used", delta_color="inverse")
        with b3:
            st.metric("Remaining", f"₦{remaining:,.0f}", delta=f"₦{remaining:,.0f}", delta_color="normal")
            
        # Custom Progress Bar HTML
        st.markdown(f"""
            <div style="margin-top: 20px; background-color: {card_border_color}; border-radius: 999px; height: 24px; width: 100%; overflow: hidden;">
                <div style="background-color: {status_color}; width: {min(percent, 100)}%; height: 100%; border-radius: 999px; transition: width 0.5s ease-in-out;">
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px; font-weight: bold; color: {status_color};">
                <span>{status_msg}</span>
                <span>{percent:.1f}%</span>
            </div>
        """, unsafe_allow_html=True)

    # Anomaly Table
    if df['is_anomaly'].any():
        st.subheader("🚨 Detected Anomalies")
        st.dataframe(
            df[df['is_anomaly']].style.format({'amount': '{:,.2f}'}), 
            use_container_width=True
        )

except Exception as e:
    st.error("Something went wrong processing the data.")
    with st.expander("Error Details"):
        st.code(str(e))
