import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import difflib

# Page Configuration for Executive Business Reporting
st.set_page_config(
    page_title="DOW Logistics Performance Dashboard",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Global Background */
    .stApp {
        background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
    }

    /* Executive Top Banner */
    .banner-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0284C7 100%);
        border-radius: 16px;
        padding: 1.8rem 2.2rem;
        color: white;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
        position: relative;
        overflow: hidden;
    }

    .banner-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0;
        line-height: 1.2;
        background: linear-gradient(180deg, #FFFFFF 0%, #E2E8F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .banner-subtitle {
        font-size: 0.98rem;
        color: #94A3B8;
        margin-top: 0.4rem;
        font-weight: 400;
    }

    .banner-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #E2E8F0;
        margin-right: 0.5rem;
        margin-top: 0.8rem;
    }

    /* Premium KPI Summary Cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.4rem 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        height: 100%;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }

    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }

    .kpi-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
    }

    .kpi-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }

    .icon-award { background: #EFF6FF; color: #2563EB; }
    .icon-actual { background: #ECFDF5; color: #059669; }
    .icon-spot { background: #FFFBEB; color: #D97706; }
    .icon-rate { background: #F3E8FF; color: #7C3AED; }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    .kpi-subtext {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 0.5rem;
        font-weight: 500;
    }

    /* Streamlit Components Customization */
    div[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        padding: 0 20px;
        font-weight: 600;
        font-size: 0.9rem;
        color: #64748B;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# Helper function to format numbers cleanly as whole integers (no decimals)
def fmt_num(val):
    if pd.isna(val):
        return "0"
    try:
        f_val = float(val)
        return f"{int(round(f_val)):,}"
    except (ValueError, TypeError):
        return str(val)

# Helper function for fuzzy column matching
def find_column(df_columns, target_name, fallback_idx=None):
    clean_target = target_name.lower().replace(' ', '').replace('-', '').replace('_', '')
    for col in df_columns:
        clean_col = str(col).lower().replace(' ', '').replace('-', '').replace('_', '')
        if clean_target in clean_col or clean_col in clean_target:
            return col
    
    matches = difflib.get_close_matches(target_name, [str(c) for c in df_columns], n=1, cutoff=0.6)
    if matches:
        return matches[0]
        
    if fallback_idx is not None and fallback_idx < len(df_columns):
        return df_columns[fallback_idx]
    return target_name

# Helper function to safely convert and sum column values (handles single Series & multi-column DataFrames)
def safe_sum_column(df, col_name):
    if df is None or df.empty or col_name not in df.columns:
        return 0.0
    sub = df[col_name]
    if isinstance(sub, pd.DataFrame):
        return float(sub.apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum())
    else:
        return float(pd.to_numeric(sub, errors='coerce').fillna(0).sum())

# Helper function to guarantee unique column names for PyArrow / Streamlit compatibility
def make_unique_headers(headers):
    seen = {}
    unique = []
    for h in headers:
        h_str = str(h).strip()
        if h_str in seen:
            seen[h_str] += 1
            unique.append(f"{h_str}_{seen[h_str]}")
        else:
            seen[h_str] = 0
            unique.append(h_str)
    return unique

# Cached Data Loader
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"Source file not found at: {file_path}")
        return None, None
        
    excel = pd.ExcelFile(file_path)
    
    # 1. Parse 'Awarded ' Sheet
    awarded_sheet = [s for s in excel.sheet_names if 'award' in s.lower()]
    sheet_a_name = awarded_sheet[0] if awarded_sheet else excel.sheet_names[0]
    df_a_raw = pd.read_excel(excel, sheet_a_name, header=None)
    
    header_row_a = 5
    for r in range(min(15, df_a_raw.shape[0])):
        row_str = ' '.join([str(x) for x in df_a_raw.iloc[r].dropna()])
        if 'Item Name' in row_str or 'Plant Location' in row_str:
            header_row_a = r
            break
            
    headers_a_raw = df_a_raw.iloc[header_row_a].tolist()
    
    clean_headers_a = []
    month_cols_a = []
    
    for i, h in enumerate(headers_a_raw):
        if pd.isna(h):
            clean_headers_a.append(f'col_{i}')
        elif isinstance(h, pd.Timestamp) or hasattr(h, 'strftime'):
            m_str = pd.to_datetime(h).strftime('%b %y')
            clean_headers_a.append(m_str)
            month_cols_a.append(m_str)
        else:
            h_str = str(h).strip()
            clean_headers_a.append(h_str)
            if any(m in h_str for m in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']) and ('24' in h_str or '25' in h_str or '26' in h_str):
                month_cols_a.append(h_str)
                
    clean_headers_a = make_unique_headers(clean_headers_a)
    df_a = df_a_raw.iloc[header_row_a + 2:].copy()
    df_a.columns = clean_headers_a
    df_a = df_a[df_a.iloc[:, 0].notna()].copy()
    
    # 2. Parse 'Spot' Sheet
    spot_sheet = [s for s in excel.sheet_names if 'spot' in s.lower()]
    sheet_s_name = spot_sheet[0] if spot_sheet else (excel.sheet_names[1] if len(excel.sheet_names) > 1 else excel.sheet_names[0])
    df_s_raw = pd.read_excel(excel, sheet_s_name, header=None)
    
    header_row_s = 11
    for r in range(min(20, df_s_raw.shape[0])):
        row_str = ' '.join([str(x) for x in df_s_raw.iloc[r].dropna()])
        if 'Item Name' in row_str and 'Plant Location' in row_str:
            header_row_s = r
            
    headers_s_raw = df_s_raw.iloc[header_row_s].tolist()
    
    clean_headers_s = []
    month_cols_s = []
    
    for i, h in enumerate(headers_s_raw):
        if pd.isna(h):
            clean_headers_s.append(f'col_{i}')
        elif isinstance(h, pd.Timestamp) or hasattr(h, 'strftime'):
            dt = pd.to_datetime(h)
            if i < 36 and dt.month == 9 and dt.year == 2025:
                m_str = 'Sep 24'
            else:
                m_str = dt.strftime('%b %y')
            clean_headers_s.append(m_str)
            month_cols_s.append(m_str)
        else:
            h_str = str(h).strip()
            clean_headers_s.append(h_str)
            if any(m in h_str for m in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']) and ('24' in h_str or '25' in h_str or '26' in h_str):
                month_cols_s.append(h_str)
                
    clean_headers_s = make_unique_headers(clean_headers_s)
    df_s = df_s_raw.iloc[header_row_s + 2:].copy()
    df_s.columns = clean_headers_s
    df_s = df_s[df_s.iloc[:, 1].notna() | df_s.iloc[:, 7].notna()].copy()
    
    df_a['Client'] = 'DOW'
    df_s['Client'] = 'DOW'
    
    return df_a, df_s

# Main Dashboard Function
def main():
    updated_file = 'DOW LOADS REPORTING 2025 TO 2026 (R1) 8 (UPDATED).xlsx'
    default_file = 'DOW LOADS REPORTING 2025 TO 2026 (R1) 8.xlsx'
    file_path = updated_file if os.path.exists(updated_file) else default_file
    
    df_a, df_s = load_data(file_path)
    
    if df_a is None or df_s is None:
        st.stop()
        
    # Standardize Column Names via Fuzzy Matching
    col_region_a = find_column(df_a.columns, 'Supplying Region', 1)
    col_country_a = find_column(df_a.columns, 'Shipping Country', 3)
    col_dest_a = find_column(df_a.columns, 'Destination Country', 6)
    col_dest_port_a = find_column(df_a.columns, 'Destination Port Name', 7)
    col_plant_a = find_column(df_a.columns, 'Plant Location', 2)
    col_perf_a = find_column(df_a.columns, 'Perf Center', 9)
    col_forecast_a = find_column(df_a.columns, '12-Months volume forecast - Number of Isotanks', 14)
    col_eway_teu_a = find_column(df_a.columns, 'Eway Actual TEUs', 22)
    
    col_region_s = find_column(df_s.columns, 'Supplying Region', 1)
    col_country_s = find_column(df_s.columns, 'Shipping Country', 4)
    col_dest_s = find_column(df_s.columns, 'Destination Country', 7)
    col_dest_port_s = find_column(df_s.columns, 'Destination Port Name', 8)
    col_plant_s = find_column(df_s.columns, 'Plant Location', 2)
    col_perf_s = find_column(df_s.columns, 'Perf Center', 12)
    col_port_s = find_column(df_s.columns, 'Shipping Port Name', 5)
    col_prep_s = find_column(df_s.columns, 'Prep Cost Region', 18)

    # Monthly Definitions (July to June Contract Cycle)
    months_2024_2025 = ['Jul 24', 'Aug 24', 'Sep 24', 'Oct 24', 'Nov 24', 'Dec 24', 'Jan 25', 'Feb 25', 'Mar 25', 'Apr 25', 'May 25', 'Jun 25']
    months_2025_2026 = ['Jul 25', 'Aug 25', 'Sep 25', 'Oct 25', 'Nov 25', 'Dec 25', 'Jan 26', 'Feb 26', 'Mar 26', 'Apr 26', 'May 26', 'Jun 26']
    months_2025 = ['Jul 25', 'Aug 25', 'Sep 25', 'Oct 25', 'Nov 25', 'Dec 25']
    months_2026 = ['Jan 26', 'Feb 26', 'Mar 26', 'Apr 26', 'May 26', 'Jun 26']
    all_historical_months = months_2024_2025 + months_2025_2026

    # Sidebar Filter Controls
    st.sidebar.markdown("### ⚙️ Scope & Origin Filters")
    
    # Origin Scope Filter (Defaulting to Thailand as requested)
    origin_options = ['Thailand Only (Laem Chabang / Rayong)', 'All Origins (Thailand, S.Korea, Saudi)']
    selected_origin = st.sidebar.selectbox("Origin Location", options=origin_options, index=0)
    
    selected_client = st.sidebar.selectbox("Client Scope", options=['DOW', 'All Clients'], index=0)
    
    selected_horizon = st.sidebar.selectbox(
        "Time Horizon Scope",
        options=[
            '2026 YTD (Jan 26 - Jun 26)', 
            '2025 H2 (Jul 25 - Dec 25)', 
            '2025-2026 Contract Year (Jul 25 - Jun 26)',
            '2024-2025 Contract Year (Jul 24 - Jun 25)',
            'Full 24-Month Horizon (Jul 24 - Jun 26)'
        ],
        index=0
    )
    
    if selected_horizon == '2026 YTD (Jan 26 - Jun 26)':
        active_months = months_2026
        target_year_label = "2026 YTD"
    elif selected_horizon == '2025 H2 (Jul 25 - Dec 25)':
        active_months = months_2025
        target_year_label = "2025 H2"
    elif selected_horizon == '2025-2026 Contract Year (Jul 25 - Jun 26)':
        active_months = months_2025_2026
        target_year_label = "2025-2026 Contract Year"
    elif selected_horizon == '2024-2025 Contract Year (Jul 24 - Jun 25)':
        active_months = months_2024_2025
        target_year_label = "2024-2025 Contract Year"
    else:
        active_months = all_historical_months
        target_year_label = "Full 24-Month Horizon"

    # Dynamically compute month factor based on actual data columns present
    valid_data_m = [m for m in active_months if m in df_a.columns]
    month_factor = (len(valid_data_m) / 12.0) if valid_data_m else 1.0

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Trade Lane Filters")
    
    # Apply Origin Filter First
    df_a_filtered = df_a.copy()
    df_s_filtered = df_s.copy()
    
    if selected_origin.startswith('Thailand'):
        df_a_filtered = df_a_filtered[
            (df_a_filtered[col_country_a].astype(str).str.upper() == 'THAILAND') |
            (df_a_filtered[col_plant_a].astype(str).str.upper() == 'LAEM CHABANG')
        ]
        df_s_filtered = df_s_filtered[
            (df_s_filtered[col_country_s].astype(str).str.upper() == 'THAILAND') |
            (df_s_filtered[col_plant_s].astype(str).str.upper() == 'RAYONG') |
            (df_s_filtered[col_port_s].astype(str).str.upper() == 'LAEM CHABANG') |
            (df_s_filtered[col_prep_s].astype(str).str.upper() == 'THAILAND')
        ]
        origin_label = "Thailand (Laem Chabang / Rayong)"
    else:
        origin_label = "All Global Origins"

    dest_countries_a = sorted([str(x) for x in df_a_filtered[col_dest_a].dropna().unique() if str(x).strip() != 'nan'])
    selected_destinations = st.sidebar.multiselect("Destination Country", options=dest_countries_a, default=[])
    
    perf_centers_a = sorted([str(x) for x in df_a_filtered[col_perf_a].dropna().unique() if str(x).strip() != 'nan'])
    selected_perfs = st.sidebar.multiselect("Performance Center", options=perf_centers_a, default=[])

    if selected_destinations:
        df_a_filtered = df_a_filtered[df_a_filtered[col_dest_a].astype(str).isin(selected_destinations)]
        df_s_filtered = df_s_filtered[df_s_filtered[col_dest_s].astype(str).isin(selected_destinations)]
        
    if selected_perfs:
        df_a_filtered = df_a_filtered[df_a_filtered[col_perf_a].astype(str).isin(selected_perfs)]
        df_s_filtered = df_s_filtered[df_s_filtered[col_perf_s].astype(str).isin(selected_perfs)]

    # Executive Banner Header
    st.markdown(f"""
    <div class="banner-container">
        <h1 class="banner-title">DOW Chemical Logistics Performance Dashboard</h1>
        <div class="banner-subtitle">Executive Volume Analytics & Trade Lane Fulfillment Intelligence</div>
        <div>
            <span class="banner-badge">📍 Origin: <b>{origin_label}</b></span>
            <span class="banner-badge">🏢 Client: <b>{selected_client}</b></span>
            <span class="banner-badge">📅 Scope: <b>{target_year_label}</b></span>
            <span class="banner-badge">🛣️ Active Lanes: <b>{len(df_a_filtered)} Contract Lanes</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Calculate Key Performance Indicators
    total_annual_eway_award = pd.to_numeric(df_a_filtered[col_eway_teu_a], errors='coerce').fillna(0).sum()
    award_target_volume = total_annual_eway_award * month_factor
    
    valid_active_m_a = [m for m in active_months if m in df_a_filtered.columns]
    actual_volume = df_a_filtered[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum()
    
    valid_active_m_s = [m for m in active_months if m in df_s_filtered.columns]
    spot_volume = df_s_filtered[valid_active_m_s].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum()
    
    fulfillment_rate = (actual_volume / award_target_volume * 100) if award_target_volume > 0 else 0.0
    total_shipped = actual_volume + spot_volume

    # Top KPI Summary Cards Row
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    
    with kcol1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Award Target</span>
                <div class="kpi-icon icon-award">🏆</div>
            </div>
            <div class="kpi-value">{fmt_num(award_target_volume)}</div>
            <div class="kpi-subtext">Allocated TEUs ({target_year_label})</div>
        </div>
        """, unsafe_allow_html=True)

    with kcol2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Actual Shipped</span>
                <div class="kpi-icon icon-actual">🚚</div>
            </div>
            <div class="kpi-value">{fmt_num(actual_volume)}</div>
            <div class="kpi-subtext">Awarded Lanes Volume ({target_year_label})</div>
        </div>
        """, unsafe_allow_html=True)

    with kcol3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Spot Volume</span>
                <div class="kpi-icon icon-spot">⚡</div>
            </div>
            <div class="kpi-value">{fmt_num(spot_volume)}</div>
            <div class="kpi-subtext">Ad-hoc Orders ({target_year_label})</div>
        </div>
        """, unsafe_allow_html=True)

    with kcol4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Target Fulfillment</span>
                <div class="kpi-icon icon-rate">🎯</div>
            </div>
            <div class="kpi-value">{int(round(fulfillment_rate))}%</div>
            <div class="kpi-subtext">Actual vs Awarded Target</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Content Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Comparative Performance", 
        "⚡ Spot & Hierarchy Analysis", 
        "📜 Multi-Year Contract Analysis (Jul - Jun)",
        "📋 Trade Lane Matrix & Data"
    ])

    # ----------------------------------------------------
    # TAB 1: Comparative Performance
    # ----------------------------------------------------
    with tab1:
        # 1. Full-Width Row: Monthly Volume Progression
        st.markdown("#### 📊 Monthly Volume Progression & Forecast Target (Awarded vs Actual vs Spot)")
        
        monthly_data = []
        monthly_award_target_overall = award_target_volume / len(valid_active_m_a) if valid_active_m_a else 0
        
        for m in valid_active_m_a:
            act_m = safe_sum_column(df_a_filtered, m)
            spot_m = safe_sum_column(df_s_filtered, m)
            
            monthly_data.append({
                'Month': m,
                'Award Target': monthly_award_target_overall,
                'Actual Volume': act_m,
                'Spot Volume': spot_m
            })
            
        df_monthly_comp = pd.DataFrame(monthly_data)
        
        # Calculate Y-axis headroom to prevent top label overlap
        max_m_val = max(
            df_monthly_comp['Award Target'].max() if not df_monthly_comp.empty else 100,
            df_monthly_comp['Actual Volume'].max() if not df_monthly_comp.empty else 100,
            df_monthly_comp['Spot Volume'].max() if not df_monthly_comp.empty else 100
        )
        y_max_m = max(180, float(max_m_val) * 1.25)
        
        fig_monthly = go.Figure()
        
        fig_monthly.add_trace(go.Bar(
            x=df_monthly_comp['Month'],
            y=df_monthly_comp['Award Target'],
            name='Award Target (Allocated)',
            marker=dict(color='#3B82F6', cornerradius=5),
            text=[fmt_num(v) for v in df_monthly_comp['Award Target']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#1E40AF'),
            hovertemplate="<b>%{x}</b><br>Target: %{y:.0f} TEUs<extra></extra>"
        ))
        
        fig_monthly.add_trace(go.Bar(
            x=df_monthly_comp['Month'],
            y=df_monthly_comp['Actual Volume'],
            name='Actual Volume Shipped',
            marker=dict(color='#10B981', cornerradius=5),
            text=[fmt_num(v) for v in df_monthly_comp['Actual Volume']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#065F46'),
            hovertemplate="<b>%{x}</b><br>Actual: %{y:.0f} TEUs<extra></extra>"
        ))
        
        fig_monthly.add_trace(go.Bar(
            x=df_monthly_comp['Month'],
            y=df_monthly_comp['Spot Volume'],
            name='Spot Volume',
            marker=dict(color='#F59E0B', cornerradius=5),
            text=[fmt_num(v) for v in df_monthly_comp['Spot Volume']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#92400E'),
            hovertemplate="<b>%{x}</b><br>Spot: %{y:.0f} TEUs<extra></extra>"
        ))
        
        fig_monthly.update_layout(
            barmode='group',
            bargap=0.2,
            bargroupgap=0.08,
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title=None, tickfont=dict(size=13, weight='bold')),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='Volume (TEUs)', range=[0, y_max_m]),
            legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="right", x=1, font=dict(size=12)),
            height=430,
            margin=dict(l=20, r=20, t=55, b=20)
        )
        st.plotly_chart(fig_monthly, width='stretch', config={'displayModeBar': False})

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # 2. Row 2: Target Gauge + Top Trade Lanes Bar Chart
        r2_col1, r2_col2 = st.columns([4, 8])
        
        with r2_col1:
            st.markdown("#### 🎯 Target Fulfillment Rate Gauge")
            st.markdown(f'<div style="font-size: 0.85rem; color: #64748B; margin-top: -6px; margin-bottom: 8px;">Scope: <b>{origin_label}</b></div>', unsafe_allow_html=True)
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=round(fulfillment_rate),
                number={'suffix': "%", 'valueformat': '.0f', 'font': {'size': 36, 'family': 'Plus Jakarta Sans', 'weight': 'bold'}},
                delta={'reference': 100, 'relative': False, 'valueformat': '.0f'},
                gauge={
                    'axis': {'range': [None, max(150, round(fulfillment_rate * 1.15))], 'tickwidth': 1},
                    'bar': {'color': "#0F172A"},
                    'bgcolor': "white",
                    'borderwidth': 1,
                    'bordercolor': "#E2E8F0",
                    'steps': [
                        {'range': [0, 80], 'color': '#FEE2E2'},
                        {'range': [80, 100], 'color': '#FEF3C7'},
                        {'range': [100, max(150, round(fulfillment_rate * 1.15))], 'color': '#D1FAE5'}
                    ]
                }
            ))
            
            fig_gauge.update_layout(
                height=260,
                margin=dict(l=20, r=20, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            st.plotly_chart(fig_gauge, width='stretch', config={'displayModeBar': False})

        with r2_col2:
            st.markdown("#### 🛣️ Top Destination Trade Lanes Performance (Award Target vs Actual)")
            
            df_trade_a = df_a_filtered.copy()
            df_trade_a['Actual_Vol'] = df_trade_a[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
            df_trade_a['Award_Allocated'] = pd.to_numeric(df_trade_a[col_eway_teu_a], errors='coerce').fillna(0) * month_factor
            
            trade_grouped = df_trade_a.groupby(col_dest_a)[['Award_Allocated', 'Actual_Vol']].sum().reset_index()
            trade_grouped = trade_grouped.sort_values(by='Award_Allocated', ascending=False).head(7)
            
            # Calculate X-axis headroom to prevent right label cutoff
            max_t_val = max(
                trade_grouped['Award_Allocated'].max() if not trade_grouped.empty else 100,
                trade_grouped['Actual_Vol'].max() if not trade_grouped.empty else 100
            )
            x_max_t = max(200, float(max_t_val) * 1.25)
            
            fig_trade = go.Figure()
            
            fig_trade.add_trace(go.Bar(
                y=trade_grouped[col_dest_a],
                x=trade_grouped['Award_Allocated'],
                name='Award Target',
                orientation='h',
                marker=dict(color='#93C5FD', cornerradius=4),
                text=[fmt_num(v) for v in trade_grouped['Award_Allocated']],
                textposition='outside',
                textfont=dict(size=12, weight='bold', color='#1E40AF')
            ))
            
            fig_trade.add_trace(go.Bar(
                y=trade_grouped[col_dest_a],
                x=trade_grouped['Actual_Vol'],
                name='Actual Volume Shipped',
                orientation='h',
                marker=dict(color='#059669', cornerradius=4),
                text=[fmt_num(v) for v in trade_grouped['Actual_Vol']],
                textposition='outside',
                textfont=dict(size=12, weight='bold', color='#065F46')
            ))
            
            fig_trade.update_layout(
                barmode='group',
                bargap=0.2,
                bargroupgap=0.1,
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif"),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='Volume (TEUs)', range=[0, x_max_t]),
                yaxis=dict(autorange="reversed", tickfont=dict(size=12, weight='bold')),
                legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="right", x=1, font=dict(size=12)),
                margin=dict(l=10, r=50, t=45, b=10)
            )
            st.plotly_chart(fig_trade, width='stretch', config={'displayModeBar': False})

    # ----------------------------------------------------
    # TAB 2: Spot & Hierarchy Analysis
    # ----------------------------------------------------
    with tab2:
        # Full-Width Spot Trend Row
        st.markdown(f"#### ⚡ Monthly Spot Orders Volume Trend ({origin_label})")
        
        spot_trend = []
        for m in valid_active_m_s:
            v = safe_sum_column(df_s_filtered, m)
            spot_trend.append({'Month': m, 'Spot Volume': v, 'Label': fmt_num(v)})
            
        df_spot_trend = pd.DataFrame(spot_trend)
        
        if df_spot_trend.empty or 'Month' not in df_spot_trend.columns:
            st.info("ℹ️ No Spot order volume recorded for the selected time horizon scope (Spot tracking started in Jul 2025).")
        else:
            max_s_val = df_spot_trend['Spot Volume'].max() if not df_spot_trend.empty else 100
            y_max_s = max(120, float(max_s_val) * 1.3)
            
            fig_spot_area = px.area(
                df_spot_trend,
                x='Month',
                y='Spot Volume',
                markers=True,
                color_discrete_sequence=['#F59E0B'],
                text='Label'
            )
            fig_spot_area.update_traces(
                line=dict(width=4, shape='spline'),
                fillcolor='rgba(245, 158, 11, 0.15)',
                marker=dict(size=10, color='#D97706'),
                textposition='top center',
                textfont=dict(size=13, weight='bold', color='#92400E')
            )
            fig_spot_area.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif"),
                xaxis=dict(showgrid=False, tickfont=dict(size=13, weight='bold')),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='Spot Volume (TEUs)', range=[0, y_max_s]),
                height=380,
                margin=dict(l=20, r=20, t=45, b=20)
            )
            st.plotly_chart(fig_spot_area, width='stretch', config={'displayModeBar': False})

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # Full-Width Hierarchy Row
        st.markdown("#### 🌳 Trade Lane Volume Hierarchy & Breakdown (Sunburst)")
        
        df_sun = df_a_filtered.copy()
        df_sun['Volume'] = df_sun[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
        df_sun = df_sun[df_sun['Volume'] > 0]
        
        if not df_sun.empty:
            fig_sun = px.sunburst(
                df_sun,
                path=[col_plant_a, col_dest_a, col_dest_port_a],
                values='Volume',
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_sun.update_traces(
                textinfo="label+value+percent entry",
                insidetextorientation='horizontal'
            )
            fig_sun.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif"),
                height=450,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_sun, width='stretch', config={'displayModeBar': False})
        else:
            st.info("No active volume recorded for selected filters to build hierarchy.")

    # ----------------------------------------------------
    # TAB 3: Multi-Year Contract Analysis (Jul - Jun)
    # ----------------------------------------------------
    with tab3:
        st.markdown(f"#### 📜 Contract Year Performance Comparison: Jul-Jun Cycle ({origin_label})")
        st.markdown("<div style='color: #64748B; font-size: 0.9rem; margin-top: -8px; margin-bottom: 20px;'>Comparative volume performance across 12-Month Contract Cycles (July to June): <b>Contract Year 2024-2025</b> vs <b>Contract Year 2025-2026</b> (Awarded + Spot Orders).</div>", unsafe_allow_html=True)

        # Calculate Contract Cycle Volumes (July to June 12-Month Cycle, Awarded + Spot)
        valid_m_2425_a = [m for m in months_2024_2025 if m in df_a_filtered.columns]
        valid_m_2526_a = [m for m in months_2025_2026 if m in df_a_filtered.columns]
        valid_m_2425_s = [m for m in months_2024_2025 if m in df_s_filtered.columns]
        valid_m_2526_s = [m for m in months_2025_2026 if m in df_s_filtered.columns]

        award_2425 = df_a_filtered[valid_m_2425_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum() if valid_m_2425_a else 0
        award_2526 = df_a_filtered[valid_m_2526_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum() if valid_m_2526_a else 0
        
        spot_2425 = df_s_filtered[valid_m_2425_s].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum() if valid_m_2425_s else 0
        spot_2526 = df_s_filtered[valid_m_2526_s].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum() if valid_m_2526_s else 0

        vol_2425_tot = award_2425 + spot_2425
        vol_2526_tot = award_2526 + spot_2526
        
        growth_vol = vol_2526_tot - vol_2425_tot
        growth_pct = (growth_vol / vol_2425_tot * 100) if vol_2425_tot > 0 else 0

        # Multi-Year Summary Cards
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-header"><span class="kpi-title">Contract Year 24-25</span><div class="kpi-icon icon-award">📜</div></div>
                <div class="kpi-value">{fmt_num(vol_2425_tot)}</div>
                <div class="kpi-subtext">{fmt_num(award_2425)} Awarded + {fmt_num(spot_2425)} Spot</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mcol2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-header"><span class="kpi-title">Contract Year 25-26</span><div class="kpi-icon icon-actual">🚚</div></div>
                <div class="kpi-value">{fmt_num(vol_2526_tot)}</div>
                <div class="kpi-subtext">{fmt_num(award_2526)} Awarded + {fmt_num(spot_2526)} Spot</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mcol3:
            growth_color = "#059669" if growth_vol >= 0 else "#DC2626"
            growth_sign = "+" if growth_vol >= 0 else ""
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-header"><span class="kpi-title">Volume Growth</span><div class="kpi-icon icon-spot">📈</div></div>
                <div class="kpi-value" style="color: {growth_color};">{growth_sign}{fmt_num(growth_vol)}</div>
                <div class="kpi-subtext">Total Expansion ({growth_sign}{int(round(growth_pct))}%)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mcol4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-header"><span class="kpi-title">Contract YoY Growth</span><div class="kpi-icon icon-rate">🚀</div></div>
                <div class="kpi-value">{int(round(growth_pct))}%</div>
                <div class="kpi-subtext">Year-over-Year Total Growth</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # 1. Month-by-Month Contract Year Progression (Jul to Jun)
        st.markdown("#### 📅 Month-by-Month Contract Progression Comparison (Jul to Jun)")
        
        m_labels = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        month_comp_rows = []
        
        for idx, label in enumerate(m_labels):
            m24 = months_2024_2025[idx]
            m25 = months_2025_2026[idx]
            
            a24 = safe_sum_column(df_a_filtered, m24)
            s24 = safe_sum_column(df_s_filtered, m24)
            
            a25 = safe_sum_column(df_a_filtered, m25)
            s25 = safe_sum_column(df_s_filtered, m25)
            
            tot24 = a24 + s24
            tot25 = a25 + s25
            
            month_comp_rows.append({
                'Month': f"M{idx+1:02d} ({label})",
                'Contract 2024-2025': tot24,
                'Contract 2025-2026': tot25,
                'Diff': tot25 - tot24
            })
            
        df_m_comp = pd.DataFrame(month_comp_rows)
        
        max_m_comp_y = max(
            df_m_comp['Contract 2024-2025'].max() if not df_m_comp.empty else 100,
            df_m_comp['Contract 2025-2026'].max() if not df_m_comp.empty else 100
        )
        y_max_m_comp = max(180, float(max_m_comp_y) * 1.25)

        fig_m_comp = go.Figure()
        fig_m_comp.add_trace(go.Bar(
            x=df_m_comp['Month'],
            y=df_m_comp['Contract 2024-2025'],
            name='Contract Year 2024-2025 (Awarded + Spot)',
            marker=dict(color='#94A3B8', cornerradius=4),
            text=[fmt_num(v) for v in df_m_comp['Contract 2024-2025']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#475569')
        ))
        fig_m_comp.add_trace(go.Bar(
            x=df_m_comp['Month'],
            y=df_m_comp['Contract 2025-2026'],
            name='Contract Year 2025-2026 (Awarded + Spot)',
            marker=dict(color='#0284C7', cornerradius=4),
            text=[fmt_num(v) for v in df_m_comp['Contract 2025-2026']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#0369A1')
        ))

        fig_m_comp.update_layout(
            barmode='group',
            bargap=0.2,
            bargroupgap=0.08,
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            xaxis=dict(showgrid=False, tickfont=dict(size=12, weight='bold')),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='Total Shipped Volume (TEUs)', range=[0, y_max_m_comp]),
            legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="right", x=1, font=dict(size=12)),
            margin=dict(l=20, r=20, t=55, b=20)
        )
        st.plotly_chart(fig_m_comp, width='stretch', config={'displayModeBar': False})

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # 2. Trade Lane Performance Comparison (Jul-Jun Contract Year)
        st.markdown("#### 🛣️ Destination Trade Lane Growth (Jul-Jun Contract Cycle)")
        df_my_dest_a = df_a_filtered.copy()
        df_my_dest_a['Vol_2425_A'] = df_my_dest_a[valid_m_2425_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1) if valid_m_2425_a else 0
        df_my_dest_a['Vol_2526_A'] = df_my_dest_a[valid_m_2526_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1) if valid_m_2526_a else 0
        
        dest_my_grouped = df_my_dest_a.groupby(col_dest_a)[['Vol_2425_A', 'Vol_2526_A']].sum().reset_index()
        dest_my_grouped = dest_my_grouped.sort_values(by='Vol_2526_A', ascending=False)

        max_my_x = max(
            dest_my_grouped['Vol_2425_A'].max() if not dest_my_grouped.empty else 100,
            dest_my_grouped['Vol_2526_A'].max() if not dest_my_grouped.empty else 100
        )
        x_max_my = max(200, float(max_my_x) * 1.25)

        fig_my_bar = go.Figure()
        fig_my_bar.add_trace(go.Bar(
            y=dest_my_grouped[col_dest_a],
            x=dest_my_grouped['Vol_2425_A'],
            name='2024-2025 Contract Volume',
            orientation='h',
            marker=dict(color='#94A3B8', cornerradius=4),
            text=[fmt_num(v) for v in dest_my_grouped['Vol_2425_A']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#475569')
        ))
        fig_my_bar.add_trace(go.Bar(
            y=dest_my_grouped[col_dest_a],
            x=dest_my_grouped['Vol_2526_A'],
            name='2025-2026 Contract Volume',
            orientation='h',
            marker=dict(color='#0284C7', cornerradius=4),
            text=[fmt_num(v) for v in dest_my_grouped['Vol_2526_A']],
            textposition='outside',
            textfont=dict(size=12, weight='bold', color='#0369A1')
        ))

        fig_my_bar.update_layout(
            barmode='group',
            bargap=0.2,
            bargroupgap=0.1,
            height=380,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Plus Jakarta Sans, sans-serif"),
            xaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='Actual Shipped Volume (TEUs)', range=[0, x_max_my]),
            yaxis=dict(autorange="reversed", tickfont=dict(size=12, weight='bold')),
            legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="right", x=1, font=dict(size=12)),
            margin=dict(l=10, r=50, t=45, b=10)
        )
        st.plotly_chart(fig_my_bar, width='stretch', config={'displayModeBar': False})

    # ----------------------------------------------------
    # TAB 4: Detailed Matrix & Data Tables
    # ----------------------------------------------------
    with tab4:
        st.markdown(f"#### 📋 Awarded Lanes Detailed Contract Matrix ({origin_label})")
        display_cols_a = [col_plant_a, col_country_a, col_dest_a, col_dest_port_a, col_perf_a, col_forecast_a, col_eway_teu_a] + valid_active_m_a
        df_a_display = df_a_filtered[display_cols_a].copy()
        
        st.dataframe(
            df_a_display,
            width='stretch',
            hide_index=True
        )
        
        st.download_button(
            label="📥 Export Awarded Lanes Data (CSV)",
            data=df_a_display.to_csv(index=False).encode('utf-8'),
            file_name=f"DOW_Awarded_Lanes_Thailand_{target_year_label}.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        st.markdown(f"#### ⚡ Spot Orders Detailed Matrix ({origin_label})")
        display_cols_s = [col_plant_s, col_country_s, col_dest_s, col_dest_port_s, col_perf_s] + valid_active_m_s
        df_s_display = df_s_filtered[display_cols_s].copy()
        
        st.dataframe(
            df_s_display,
            width='stretch',
            hide_index=True
        )
        
        st.download_button(
            label="📥 Export Spot Orders Data (CSV)",
            data=df_s_display.to_csv(index=False).encode('utf-8'),
            file_name=f"DOW_Spot_Orders_Thailand_{target_year_label}.csv",
            mime="text/csv"
        )

if __name__ == '__main__':
    main()
