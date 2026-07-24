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
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive CSS Styling
st.markdown("""
<style>
    /* Global Styling */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Header Styling */
    .header-title {
        color: #0F172A;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        color: #475569;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    
    /* Executive Metric Cards */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    
    .metric-subtext {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 0.4rem;
    }
    
    /* Specific Accent Card Borders */
    .metric-award { border-left: 5px solid #3B82F6; }
    .metric-actual { border-left: 5px solid #10B981; }
    .metric-spot { border-left: 5px solid #F59E0B; }
    .metric-fulfill { border-left: 5px solid #8B5CF6; }

    /* Section Cards */
    .content-container {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #E2E8F0;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    /* Streamlit Metric Overrides */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
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
    
    # Try fuzzy match
    matches = difflib.get_close_matches(target_name, [str(c) for c in df_columns], n=1, cutoff=0.6)
    if matches:
        return matches[0]
        
    if fallback_idx is not None and fallback_idx < len(df_columns):
        return df_columns[fallback_idx]
    return target_name

# Data Loader Function
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"Source file not found at: {file_path}")
        return None, None
        
    excel = pd.ExcelFile(file_path)
    
    # ----------------------------------------------------
    # 1. Parse 'Awarded ' Sheet
    # ----------------------------------------------------
    awarded_sheet = [s for s in excel.sheet_names if 'award' in s.lower()]
    sheet_a_name = awarded_sheet[0] if awarded_sheet else excel.sheet_names[0]
    
    df_a_raw = pd.read_excel(excel, sheet_a_name, header=None)
    
    # Locate header row dynamically (look for 'Item Name' or 'Plant Location')
    header_row_a = 5
    for r in range(min(15, df_a_raw.shape[0])):
        row_str = ' '.join([str(x) for x in df_a_raw.iloc[r].dropna()])
        if 'Item Name' in row_str or 'Plant Location' in row_str:
            header_row_a = r
            break
            
    headers_a_raw = df_a_raw.iloc[header_row_a].tolist()
    
    # Clean headers & standardise month names
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
    # Filter out empty rows or total rows
    df_a = df_a[df_a.iloc[:, 0].notna()].copy()
    
    # ----------------------------------------------------
    # 2. Parse 'Spot' Sheet
    # ----------------------------------------------------
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
    # Filter out empty rows or sample headers
    df_s = df_s[df_s.iloc[:, 1].notna() | df_s.iloc[:, 7].notna()].copy()
    
    # Default Client column addition if not explicit
    df_a['Client'] = 'DOW'
    df_s['Client'] = 'DOW'
    
    return df_a, df_s

# Main Dashboard Function
def main():
    file_path = 'DOW LOADS REPORTING 2025 TO 2026 (R1) 8.xlsx'
    
    df_a, df_s = load_data(file_path)
    
    if df_a is None or df_s is None:
        st.stop()
        
    # Standardize column mappings using fuzzy lookup
    col_dest_a = find_column(df_a.columns, 'Destination Country', 6)
    col_dest_port_a = find_column(df_a.columns, 'Destination Port Name', 7)
    col_plant_a = find_column(df_a.columns, 'Plant Location', 2)
    col_perf_a = find_column(df_a.columns, 'Perf Center', 9)
    col_forecast_a = find_column(df_a.columns, '12-Months volume forecast - Number of Isotanks', 14)
    col_eway_teu_a = find_column(df_a.columns, 'Eway Actual TEUs', 22)
    
    col_dest_s = find_column(df_s.columns, 'Destination Country', 7)
    col_dest_port_s = find_column(df_s.columns, 'Destination Port Name', 8)
    col_plant_s = find_column(df_s.columns, 'Plant Location', 2)
    col_perf_s = find_column(df_s.columns, 'Perf Center', 12)

    # Define Monthly Sets
    months_2025 = ['Jul 25', 'Aug 25', 'Sep 25', 'Oct 25', 'Nov 25', 'Dec 25']
    months_2026 = ['Jan 26', 'Feb 26', 'Mar 26', 'Apr 26', 'May 26', 'Jun 26']
    all_months = months_2025 + months_2026

    # ----------------------------------------------------
    # Sidebar Filters
    # ----------------------------------------------------
    st.sidebar.image("https://img.icons8.com/color/96/container-truck.png", width=64)
    st.sidebar.title("Filter Options")
    
    # 1. Client Filter
    clients = ['DOW', 'All Clients']
    selected_client = st.sidebar.selectbox("Client Scope", options=clients, index=0)
    
    # 2. Time Horizon Scope
    year_options = ['2026 YTD (Current Year)', '2025 (Jul - Dec)', 'Full Contract (2025-2026)']
    selected_horizon = st.sidebar.selectbox("Time Horizon Scope", options=year_options, index=0)
    
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

    # 3. Trade Lane / Destination Country Filter
    dest_countries_a = sorted([str(x) for x in df_a[col_dest_a].dropna().unique() if str(x).strip() != 'nan'])
    selected_destinations = st.sidebar.multiselect("Destination Country", options=dest_countries_a, default=[])
    
    # 4. Performance Center Filter
    perf_centers_a = sorted([str(x) for x in df_a[col_perf_a].dropna().unique() if str(x).strip() != 'nan'])
    selected_perfs = st.sidebar.multiselect("Performance Center", options=perf_centers_a, default=[])

    # Filter Dataframes
    df_a_filtered = df_a.copy()
    df_s_filtered = df_s.copy()
    
    if selected_destinations:
        df_a_filtered = df_a_filtered[df_a_filtered[col_dest_a].astype(str).isin(selected_destinations)]
        df_s_filtered = df_s_filtered[df_s_filtered[col_dest_s].astype(str).isin(selected_destinations)]
        
    if selected_perfs:
        df_a_filtered = df_a_filtered[df_a_filtered[col_perf_a].astype(str).isin(selected_perfs)]
        df_s_filtered = df_s_filtered[df_s_filtered[col_perf_s].astype(str).isin(selected_perfs)]

    # ----------------------------------------------------
    # Header Section
    # ----------------------------------------------------
    st.markdown('<div class="header-title">DOW Chemical Logistics Performance Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="header-subtitle">Executive Volume Analysis & Trade Lane Tracking • <b>Scope: {selected_client} | Period: {target_year_label}</b></div>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # KPI Calculation
    # ----------------------------------------------------
    # Awarded Annual Forecast Volume
    total_annual_award_forecast = pd.to_numeric(df_a_filtered[col_forecast_a], errors='coerce').fillna(0).sum()
    total_annual_eway_award = pd.to_numeric(df_a_filtered[col_eway_teu_a], errors='coerce').fillna(0).sum()
    
    # Awarded Target for Selected Horizon
    award_target_volume = total_annual_eway_award * month_factor
    
    # Actual Volume on Awarded Lanes
    valid_active_m_a = [m for m in active_months if m in df_a_filtered.columns]
    actual_volume = df_a_filtered[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum()
    
    # Spot Volume
    valid_active_m_s = [m for m in active_months if m in df_s_filtered.columns]
    spot_volume = df_s_filtered[valid_active_m_s].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum()
    
    # Fulfillment Rate
    fulfillment_rate = (actual_volume / award_target_volume * 100) if award_target_volume > 0 else 0.0
    
    total_shipped_volume = actual_volume + spot_volume

    # ----------------------------------------------------
    # KPI Summary Cards (Top Row)
    # ----------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card metric-award">
            <div class="metric-label">Award Volume Target</div>
            <div class="metric-value">{award_target_volume:,.1f} <span style="font-size:1rem;font-weight:400">TEUs</span></div>
            <div class="metric-subtext">Allocated Target for {target_year_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card metric-actual">
            <div class="metric-label">Actual Volume Shipped</div>
            <div class="metric-value">{actual_volume:,.1f} <span style="font-size:1rem;font-weight:400">TEUs</span></div>
            <div class="metric-subtext">Awarded Lanes Shipped ({target_year_label})</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card metric-spot">
            <div class="metric-label">Spot Volume Shipped</div>
            <div class="metric-value">{spot_volume:,.1f} <span style="font-size:1rem;font-weight:400">TEUs</span></div>
            <div class="metric-subtext">Ad-hoc / Spot Orders ({target_year_label})</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card metric-fulfill">
            <div class="metric-label">Target Fulfillment Rate</div>
            <div class="metric-value">{fulfillment_rate:.1f}%</div>
            <div class="metric-subtext">Actual vs Awarded Target</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # Tabbed Dashboard Sections
    # ----------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["📊 Comparative Performance", "⚡ Spot Analysis", "📋 Trade Lane Matrix & Data"])

    # ----------------------------------------------------
    # TAB 1: Comparative Performance Chart
    # ----------------------------------------------------
    with tab1:
        st.subheader("Awarded Target vs. Actual Volume Performance")
        
        col_c1, col_c2 = st.columns([7, 5])
        
        with col_c1:
            # Monthly Comparison Grouped Bar Chart
            monthly_data = []
            
            # Prorated monthly target allocation per row
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
                marker_color='#3B82F6',
                text=df_monthly_comp['Award Target'].round(1),
                textposition='auto'
            ))
            fig_monthly.add_trace(go.Bar(
                x=df_monthly_comp['Month'],
                y=df_monthly_comp['Actual Volume'],
                name='Actual Volume',
                marker_color='#10B981',
                text=df_monthly_comp['Actual Volume'].round(1),
                textposition='auto'
            ))
            fig_monthly.add_trace(go.Bar(
                x=df_monthly_comp['Month'],
                y=df_monthly_comp['Spot Volume'],
                name='Spot Volume',
                marker_color='#F59E0B',
                text=df_monthly_comp['Spot Volume'].round(1),
                textposition='auto'
            ))
            
            fig_monthly.update_layout(
                barmode='group',
                title=f'Monthly Volume Comparison ({target_year_label})',
                xaxis_title='Month',
                yaxis_title='Volume (TEUs)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template='plotly_white',
                height=420,
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig_monthly, use_container_width=True)

        with col_c2:
            # Trade Lane / Destination Country Breakdown
            df_trade_a = df_a_filtered.copy()
            df_trade_a['Actual_Vol'] = df_trade_a[valid_active_m_a].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
            df_trade_a['Award_Allocated'] = pd.to_numeric(df_trade_a[col_eway_teu_a], errors='coerce').fillna(0) * month_factor
            
            trade_grouped = df_trade_a.groupby(col_dest_a)[['Award_Allocated', 'Actual_Vol']].sum().reset_index()
            trade_grouped = trade_grouped.sort_values(by='Award_Allocated', ascending=False).head(8)
            
            fig_trade = go.Figure()
            fig_trade.add_trace(go.Bar(
                y=trade_grouped[col_dest_a],
                x=trade_grouped['Award_Allocated'],
                name='Award Target',
                orientation='h',
                marker_color='#93C5FD'
            ))
            fig_trade.add_trace(go.Bar(
                y=trade_grouped[col_dest_a],
                x=trade_grouped['Actual_Vol'],
                name='Actual Volume',
                orientation='h',
                marker_color='#059669'
            ))
            
            fig_trade.update_layout(
                barmode='group',
                title=f'Top Destination Countries: Award vs Actual',
                xaxis_title='Volume (TEUs)',
                yaxis_title='Destination Country',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template='plotly_white',
                height=420,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig_trade, use_container_width=True)

    # ----------------------------------------------------
    # TAB 2: Spot Volume Analysis
    # ----------------------------------------------------
    with tab2:
        st.subheader("Spot Volume Analysis & Trend Tracking")
        
        col_s1, col_s2 = st.columns([6, 6])
        
        with col_s1:
            # Spot Volume Trend Line Chart
            spot_trend = []
            for m in valid_active_m_s:
                v = pd.to_numeric(df_s_filtered[m], errors='coerce').fillna(0).sum()
                spot_trend.append({'Month': m, 'Spot Volume': v})
                
            df_spot_trend = pd.DataFrame(spot_trend)
            
            fig_spot_trend = px.line(
                df_spot_trend,
                x='Month',
                y='Spot Volume',
                markers=True,
                title=f'Monthly Spot Volume Trend ({target_year_label})',
                labels={'Spot Volume': 'Spot Volume (TEUs)'},
                color_discrete_sequence=['#D97706']
            )
            fig_spot_trend.update_traces(line=dict(width=3), marker=dict(size=8))
            fig_spot_trend.update_layout(
                template='plotly_white',
                height=400,
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig_spot_trend, use_container_width=True)

        with col_s2:
            # Spot Volume by Destination Country / Port
            df_s_filtered['Total_Spot_Period'] = df_s_filtered[valid_active_m_s].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)
            spot_dest = df_s_filtered.groupby([col_dest_s])[ 'Total_Spot_Period'].sum().reset_index()
            spot_dest = spot_dest[spot_dest['Total_Spot_Period'] > 0].sort_values(by='Total_Spot_Period', ascending=False)
            
            fig_spot_pie = px.pie(
                spot_dest,
                names=col_dest_s,
                values='Total_Spot_Period',
                title=f'Spot Volume Distribution by Destination ({target_year_label})',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_spot_pie.update_layout(
                template='plotly_white',
                height=400,
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig_spot_pie, use_container_width=True)

    # ----------------------------------------------------
    # TAB 3: Data Table & Detailed Matrix
    # ----------------------------------------------------
    with tab3:
        st.subheader("Detailed Trade Lane Volumes Data Matrix")
        
        st.markdown("#### Awarded Lanes Detail Table")
        display_cols_a = [col_plant_a, col_dest_a, col_dest_port_a, col_perf_a, col_forecast_a, col_eway_teu_a] + valid_active_m_a
        df_a_display = df_a_filtered[display_cols_a].copy()
        
        st.dataframe(
            df_a_display,
            use_container_width=True,
            hide_index=True
        )
        
        st.download_button(
            label="📥 Download Awarded Lanes Data (CSV)",
            data=df_a_display.to_csv(index=False).encode('utf-8'),
            file_name=f"DOW_Awarded_Lanes_{target_year_label}.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        st.markdown("#### Spot Orders Detail Table")
        display_cols_s = [col_plant_s, col_dest_s, col_dest_port_s, col_perf_s] + valid_active_m_s
        df_s_display = df_s_filtered[display_cols_s].copy()
        
        st.dataframe(
            df_s_display,
            use_container_width=True,
            hide_index=True
        )
        
        st.download_button(
            label="📥 Download Spot Orders Data (CSV)",
            data=df_s_display.to_csv(index=False).encode('utf-8'),
            file_name=f"DOW_Spot_Orders_{target_year_label}.csv",
            mime="text/csv"
        )

if __name__ == '__main__':
    main()
