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

# Custom Premium CSS Styling (Executive Dark-Slate & Glassmorphism Aesthetics)
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
        padding: 2rem 2.2rem;
        color: white;
        margin-bottom: 2rem;
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
        font-size: 1rem;
        color: #94A3B8;
        margin-top: 0.5rem;
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
        margin-top: 1rem;
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

# Helper function for fuzzy column matching with error handling
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

# Cached Data Loader Function
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
            if any(m in h_str for m in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']) and ('25' in h_str or '26' in h_str):
                month_cols_a.append(h_str)
                
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
            m_str = pd.to_datetime(h).strftime('%b %y')
            clean_headers_s.append(m_str)
            month_cols_s.append(m_str)
        else:
            h_str = str(h).strip()
            clean_headers_s.append(h_str)
            if any(m in h_str for m in ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']) and ('25' in h_str or '26' in h_str):
                month_cols_s.append(h_str)
                
    df_s = df_s_raw.iloc[header_row_s + 2:].copy()
    df_s.columns = clean_headers_s
    df_s = df_s[df_s.iloc[:, 1].notna() | df_s.iloc[:, 7].notna()].copy()
    
    df_a['Client'] = 'DOW'
    df_s['Client'] = 'DOW'
    
    return df_a, df_s

# Main Dashboard Function
def main():
    file_path = 'DOW LOADS REPORTING 2025 TO 2026 (R1) 8.xlsx'
    
    df_a, df_s = load_data(file_path)
    
    if df_a is None or df_s is None:
        st.stop()
        
    # Standardize Column Names via Fuzzy Matching
    col_region_a = find_column(df_a.columns, 'Supplying Region', 1)
    col_dest_a = find_column(df_a.columns, 'Destination Country', 6)
    col_dest_port_a = find_column(df_a.columns, 'Destination Port Name', 7)
    col_plant_a = find_column(df_a.columns, 'Plant Location', 2)
    col_perf_a = find_column(df_a.columns, 'Perf Center', 9)
    col_forecast_a = find_column(df_a.columns, '12-Months volume forecast - Number of Isotanks', 14)
    col_eway_teu_a = find_column(df_a.columns, 'Eway Actual TEUs', 22)
    
    col_region_s = find_column(df_s.columns, 'Supplying Region', 1)
    col_dest_s = find_column(df_s.columns, 'Destination Country', 7)
    col_dest_port_s = find_column(df_s.columns, 'Destination Port Name', 8)
    col_plant_s = find_column(df_s.columns, 'Plant Location', 2)
    col_perf_s = find_column(df_s.columns, 'Perf Center', 12)

    # Monthly Definitions
    months_2025 = ['Jul 25', 'Aug 25', 'Sep 25', 'Oct 25', 'Nov 25', 'Dec 25']
    months_2026 = ['Jan 26', 'Feb 26', 'Mar 26', 'Apr 26', 'May 26', 'Jun 26']
    all_months = months_2025 + months_2026

    # Sidebar Filter Controls
    st.sidebar.markdown("### ⚙️ Dashboard Controls")
    
    selected_client = st.sidebar.selectbox("Client Scope", options=['DOW', 'All Clients'], index=0)
    
    selected_horizon = st.sidebar.selectbox(
        "Time Horizon Scope",
        options=['2026 YTD (Current Year)', '2025 (Jul - Dec)', 'Full Contract (2025-2026)'],
        index=0
    )
    
    if selected_horizon == '2026 YTD (Current Year)':
        active_months = months_2026
        target_year_label = "2026 YTD"
        month_factor = 6.0 / 12.0
    elif selected_horizon == '2025 (Jul - Dec)':
        active_months = months_2025
        target_year_label = "2025"
        month_factor = 6.0 / 12.0
    else:
        active_months = all_months
        target_year_label = "2025-2026"
        month_factor = 1.0

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Trade Lane Filters")
    
    dest_countries_a = sorted([str(x) for x in df_a[col_dest_a].dropna().unique() if str(x).strip() != 'nan'])
    selected_destinations = st.sidebar.multiselect("Destination Country", options=dest_countries_a, default=[])
    
    perf_centers_a = sorted([str(x) for x in df_a[col_perf_a].dropna().unique() if str(x).strip() != 'nan'])
    selected_perfs = st.sidebar.multiselect("Performance Center", options=perf_centers_a, default=[])

    # Apply Filters
    df_a_filtered = df_a.copy()
    df_s_filtered = df_s.copy()
    
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
            <span class="banner-badge">🏢 Client: <b>{selected_client}</b></span>
            <span class="banner-badge">📅 Scope: <b>{target_year_label}</b></span>
            <span class="banner-badge">📍 Active Lanes: <b>{len(df_a_filtered)} Contract Lanes</b></span>
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
            <div class="kpi-value">{award_target_volume:,.1f}</div>
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
            <div class="kpi-value">{actual_volume:,.1f}</div>
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
            <div class="kpi-value">{spot_volume:,.1f}</div>
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
            <div class="kpi-value">{fulfillment_rate:.1f}%</div>
            <div class="kpi-subtext">Actual vs Awarded Target</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Content Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Comparative Performance", 
        "⚡ Spot & Hierarchy Analysis", 
        "📋 Trade Lane Matrix & Data"
    ])

    # ----------------------------------------------------
    # TAB 1: Comparative Performance
    # ----------------------------------------------------
    with tab1:
        c1, c2 = st.columns([7, 5])
        
        with c1:
            st.markdown("#### Monthly Volume Progression & Forecast Target")
            
            monthly_data = []
            monthly_award_target_overall = award_target_volume / len(valid_active_m_a) if valid_active_m_a else 0
            
            for m in valid_active_m_a:
                act_m = pd.to_numeric(df_a_filtered[m], errors='coerce').fillna(0).sum()
                spot_m = pd.to_numeric(df_s_filtered[m], errors='coerce').fillna(0).sum() if m in df_s_filtered.columns else 0
                
                monthly_data.append({
                    'Month': m,
                    'Award Target': monthly_award_target_overall,
                    'Actual Volume': act_m,
                    'Spot Volume': spot_m
                })
                
            df_monthly_comp = pd.DataFrame(monthly_data)
            
            fig_monthly = go.Figure()
            
            fig_monthly.add_trace(go.Bar(
                x=df_monthly_comp['Month'],
                y=df_monthly_comp['Award Target'],
                name='Award Target (Allocated)',
                marker=dict(color='#3B82F6', cornerradius=4),
                text=df_monthly_comp['Award Target'].round(1),
                textposition='outside',
                hovertemplate="<b>%{x}</b><br>Target: %{y:.1f} TEUs<extra></extra>"
            ))
            
            fig_monthly.add_trace(go.Bar(
                x=df_monthly_comp['Month'],
                y=df_monthly_comp['Actual Volume'],
                name='Actual Volume Shipped',
                marker=dict(color='#10B981', cornerradius=4),
                text=df_monthly_comp['Actual Volume'].round(1),
                textposition='outside',
                hovertemplate="<b>%{x}</b><br>Actual: %{y:.1f} TEUs<extra></extra>"
            ))
            
            fig_monthly.add_trace(go.Bar(
                x=df_monthly_comp['Month'],
                y=df_monthly_comp['Spot Volume'],
                name='Spot Volume',
                marker=dict(color='#F59E0B', cornerradius=4),
                text=df_monthly_comp['Spot Volume'].round(1),
                textposition='outside',
                hovertemplate="<b>%{x}</b><br>Spot: %{y:.1f} TEUs<extra></extra>"
            ))
            
            fig_monthly.update_layout(
                barmode='group',
                bargap=0.25,
                bargroupgap=0.1,
                font=dict(family="Plus Jakarta Sans, sans-serif"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, title=None),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='Volume (TEUs)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                height=420,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_monthly, width='stretch')

        with c2:
            st.markdown("#### Fulfillment Gauge & Top Trade Lanes")
            
            # Gauge Chart for Fulfillment Rate
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=fulfillment_rate,
                number={'suffix': "%", 'font': {'size': 32, 'family': 'Plus Jakarta Sans'}},
                title={'text': "Target Fulfillment Rate %", 'font': {'size': 14, 'color': '#64748B'}},
                delta={'reference': 100, 'relative': False, 'valueformat': '.1f'},
                gauge={
                    'axis': {'range': [None, max(150, fulfillment_rate * 1.1)], 'tickwidth': 1},
                    'bar': {'color': "#0F172A"},
                    'bgcolor': "white",
                    'borderwidth': 1,
                    'bordercolor': "#E2E8F0",
                    'steps': [
                        {'range': [0, 80], 'color': '#FEE2E2'},
                        {'range': [80, 100], 'color': '#FEF3C7'},
                        {'range': [100, max(150, fulfillment_rate * 1.1)], 'color': '#D1FAE5'}
                    ]
                }
            ))
            
            fig_gauge.update_layout(
                height=220,
                margin=dict(l=20, r=20, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            st.plotly_chart(fig_gauge, width='stretch')

            # Top Trade Lanes Bar Chart
            df_trade_a = df_a_filtered.copy()
            df_trade_a['Actual_Vol'] = df_trade_a[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
            df_trade_a['Award_Allocated'] = pd.to_numeric(df_trade_a[col_eway_teu_a], errors='coerce').fillna(0) * month_factor
            
            trade_grouped = df_trade_a.groupby(col_dest_a)[['Award_Allocated', 'Actual_Vol']].sum().reset_index()
            trade_grouped = trade_grouped.sort_values(by='Award_Allocated', ascending=False).head(5)
            
            fig_trade = go.Figure()
            fig_trade.add_trace(go.Bar(
                y=trade_grouped[col_dest_a],
                x=trade_grouped['Award_Allocated'],
                name='Award Target',
                orientation='h',
                marker=dict(color='#93C5FD', cornerradius=3)
            ))
            fig_trade.add_trace(go.Bar(
                y=trade_grouped[col_dest_a],
                x=trade_grouped['Actual_Vol'],
                name='Actual Volume',
                orientation='h',
                marker=dict(color='#059669', cornerradius=3)
            ))
            
            fig_trade.update_layout(
                barmode='group',
                height=220,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif"),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0', title=None),
                yaxis=dict(autorange="reversed"),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig_trade, width='stretch')

    # ----------------------------------------------------
    # TAB 2: Spot & Hierarchy Analysis
    # ----------------------------------------------------
    with tab2:
        s_col1, s_col2 = st.columns([6, 6])
        
        with s_col1:
            st.markdown("#### Monthly Spot Orders Trend Curve")
            
            spot_trend = []
            for m in valid_active_m_s:
                v = pd.to_numeric(df_s_filtered[m], errors='coerce').fillna(0).sum()
                spot_trend.append({'Month': m, 'Spot Volume': v})
                
            df_spot_trend = pd.DataFrame(spot_trend)
            
            fig_spot_area = px.area(
                df_spot_trend,
                x='Month',
                y='Spot Volume',
                markers=True,
                color_discrete_sequence=['#F59E0B']
            )
            fig_spot_area.update_traces(
                line=dict(width=3, shape='spline'),
                fillcolor='rgba(245, 158, 11, 0.15)',
                marker=dict(size=8, color='#D97706')
            )
            fig_spot_area.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans, sans-serif"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0', title='TEUs'),
                height=380,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_spot_area, width='stretch')

        with s_col2:
            st.markdown("#### Trade Lane Volume Hierarchy (Sunburst)")
            
            df_sun = df_a_filtered.copy()
            df_sun['Volume'] = df_sun[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
            df_sun = df_sun[df_sun['Volume'] > 0]
            
            if not df_sun.empty:
                fig_sun = px.sunburst(
                    df_sun,
                    path=[col_region_a, col_dest_a, col_dest_port_a],
                    values='Volume',
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_sun.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans, sans-serif"),
                    height=380,
                    margin=dict(l=10, r=10, t=20, b=10)
                )
                st.plotly_chart(fig_sun, width='stretch')
            else:
                st.info("No active volume recorded for selected filters to build hierarchy.")

    # ----------------------------------------------------
    # TAB 3: Detailed Matrix & Data Tables
    # ----------------------------------------------------
    with tab3:
        st.markdown("#### 📋 Awarded Lanes Detailed Contract Matrix")
        display_cols_a = [col_plant_a, col_dest_a, col_dest_port_a, col_perf_a, col_forecast_a, col_eway_teu_a] + valid_active_m_a
        df_a_display = df_a_filtered[display_cols_a].copy()
        
        st.dataframe(
            df_a_display,
            width='stretch',
            hide_index=True
        )
        
        st.download_button(
            label="📥 Export Awarded Lanes Data (CSV)",
            data=df_a_display.to_csv(index=False).encode('utf-8'),
            file_name=f"DOW_Awarded_Lanes_{target_year_label}.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        st.markdown("#### ⚡ Spot Orders Detailed Matrix")
        display_cols_s = [col_plant_s, col_dest_s, col_dest_port_s, col_perf_s] + valid_active_m_s
        df_s_display = df_s_filtered[display_cols_s].copy()
        
        st.dataframe(
            df_s_display,
            width='stretch',
            hide_index=True
        )
        
        st.download_button(
            label="📥 Export Spot Orders Data (CSV)",
            data=df_s_display.to_csv(index=False).encode('utf-8'),
            file_name=f"DOW_Spot_Orders_{target_year_label}.csv",
            mime="text/csv"
        )

if __name__ == '__main__':
    main()
