import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.supabase_utils import fetch_all_donations, fetch_donors
import locale
from dateutil.relativedelta import relativedelta

# Set locale for Indian number formatting
locale.setlocale(locale.LC_MONETARY, 'en_IN')

def format_indian_currency(amount):
    """Format amount in Indian currency style"""
    try:
        amount = float(amount)
        if amount >= 10000000:  # For crores
            return f"₹{amount/10000000:.2f} Cr"
        elif amount >= 100000:  # For lakhs
            return f"₹{amount/100000:.2f} L"
        else:
            return f"₹{amount:,.2f}"
    except:
        return f"₹{amount}"

def get_date_range(period):
    """Get start and end dates based on selected period"""
    today = datetime.now()
    if period == "Last 7 Days":
        return today - timedelta(days=7), today
    elif period == "Last 30 Days":
        return today - timedelta(days=30), today
    elif period == "This Month":
        return today.replace(day=1), today
    elif period == "Last Month":
        last_month = today.replace(day=1) - timedelta(days=1)
        return last_month.replace(day=1), last_month
    elif period == "This FY":
        if today.month >= 4:  # After April
            return today.replace(month=4, day=1), today
        else:  # Before April
            return today.replace(year=today.year-1, month=4, day=1), today
    return None, None

def format_date(date_value):
    """Safely format date value handling NaT"""
    try:
        if pd.isna(date_value):
            return "Not scheduled"
        return date_value.strftime('%d %b %Y')
    except:
        return "Not scheduled"

def dashboard_view():
    # Custom CSS with fixed light theme styling
    st.markdown("""
        <style>
        /* Base theme */
        .main {
            color: black;
        }
        
        /* Dashboard header */
        .stMarkdown h1 {
            margin-bottom: 1rem;
        }
        
        /* Header controls */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            padding-left: 0;
            padding-right: 0;
        }
        
        /* Time range label */
        .time-range-label {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: rgb(49, 51, 63);
        }
        
        /* Last updated section */
        .last-updated-section {
            text-align: right;
            margin-bottom: 0.5rem;
        }
        
        .last-updated-label {
            font-size: 1.2rem;
            font-weight: 600;
            color: rgb(49, 51, 63);
            margin-right: 0.5rem;
        }
        
        .last-updated-time {
            font-size: 1.2rem;
            color: rgb(49, 51, 63);
        }
        
        /* Cards */
        .metric-card {
            background-color: #f8f9fa;
            color: black;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 4px solid #007BFF;
            margin-bottom: 1rem;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: #f0f0f0;
        }
        
        /* Tooltips */
        .tooltip {
            visibility: hidden;
            background-color: #f8f9fa;
            color: black;
            text-align: center;
            padding: 5px 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.8rem;
            white-space: nowrap;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-card:hover .tooltip {
            visibility: visible;
            opacity: 1;
        }
        
        /* Donation Cards */
        .recent-donation-card {
            background-color: #f8f9fa;
            color: black;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
            border-left: 4px solid #4CAF50;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            transition: transform 0.2s ease;
        }
        .recent-donation-card:hover {
            transform: translateX(5px);
            background-color: #f0f0f0;
        }
        
        /* Status Tags */
        .status-tag {
            padding: 0.25rem 0.5rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-block;
        }
        .status-active {
            background-color: #E8F5E9;
            color: #2E7D32;
        }
        .status-paused {
            background-color: #FFF3E0;
            color: #E65100;
        }
        
        /* Quick Actions */
        .floating-actions {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background-color: #f8f9fa;
            color: black;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
            border: 1px solid #e0e0e0;
            transition: transform 0.2s ease;
        }
        .floating-actions:hover {
            transform: translateY(-5px);
        }
        
        /* Section Headers */
        .section-header {
            color: black;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        /* Links */
        a {
            color: #007BFF;
            text-decoration: none;
            transition: color 0.2s ease;
        }
        a:hover {
            color: #007BFF;
            text-decoration: underline;
        }
        
        /* Charts */
        .js-plotly-plot {
            background-color: #f8f9fa !important;
        }
        .js-plotly-plot .main-svg {
            background-color: #f8f9fa !important;
        }
        
        /* Reduce spacing in selectbox */
        .stSelectbox {
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Dashboard Title
    st.markdown("# 🏠 Dashboard")
    
    # Last Updated section (right-aligned)
    st.markdown(
        '<div class="last-updated-section">'
        '<span class="last-updated-label">Last Updated</span>'
        f'<span class="last-updated-time">{datetime.now().strftime("%I:%M %p")}</span>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Time range and refresh controls on same line
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown('<p class="time-range-label">Select Time Range</p>', unsafe_allow_html=True)
        time_range = st.selectbox(
            "",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "This Year", "All Time"],
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<p class="time-range-label">&nbsp;</p>', unsafe_allow_html=True)  # Spacer for alignment
        if st.button("🔄 Refresh", type="primary", use_container_width=True):
            st.rerun()

    # Custom date range if selected
    if time_range == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
            # Convert date to datetime at midnight
            start_date = datetime.combine(start_date, datetime.min.time())
        with col2:
            end_date = st.date_input("End Date")
            # Convert date to datetime at end of day
            end_date = datetime.combine(end_date, datetime.max.time())
    else:
        start_date, end_date = get_date_range(time_range)

    # Fetch and process data
    donations = fetch_all_donations()
    donors = fetch_donors()
    
    if not donations or not donors:
        st.warning("No data available. Start by adding donors and recording donations.")
        return

    # Create donor map
    donor_map = {d["id"]: d["Full Name"] for d in donors}
    
    # Filter donations by date range
    df_donations = pd.DataFrame(donations)
    df_donations['date'] = pd.to_datetime(df_donations['date'])
    if start_date and end_date:
        mask = (df_donations['date'] >= start_date) & (df_donations['date'] <= end_date)
        filtered_df = df_donations[mask]
    else:
        filtered_df = df_donations

    # 2. Quick Statistics Section
    st.markdown("### 📊 Key Metrics")
    
    total_amount = filtered_df['Amount'].sum()
    num_donations = len(filtered_df)
    active_donors = filtered_df['Donor'].nunique()
    
    col1, col2, col3 = st.columns(3)  # Changed from 4 columns to 3
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="tooltip">Total donations received in the selected period</div>
                <h3>💰 Total Donations</h3>
                <h2>{format_indian_currency(total_amount)}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="tooltip">Number of donations received</div>
                <h3>📊 Number of Donations</h3>
                <h2>{num_donations:,}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="tooltip">Unique donors who contributed in this period</div>
                <h3>👥 Active Donors</h3>
                <h2>{active_donors:,}</h2>
            </div>
        """, unsafe_allow_html=True)

    # Split view for Recent Donations and Top Donors
    col1, col2 = st.columns([1.5, 1])
    
    # Recent Donations Section
    with col1:
        st.markdown('<h3 class="section-header">🔄 Recent Donations</h3>', unsafe_allow_html=True)
        recent = filtered_df.sort_values('date', ascending=True).tail(3).iloc[::-1]
        
        for _, donation in recent.iterrows():
            st.markdown(f"""
                <div class="recent-donation-card">
                    <h4>{format_indian_currency(donation['Amount'])} - {donor_map.get(donation['Donor'], 'Unknown')}</h4>
                    <p>📅 {donation['date'].strftime('%d %b %Y')}</p>
                    <p>🎯 {donation.get('Purpose', 'General Donation')}</p>
                </div>
            """, unsafe_allow_html=True)
        
    # Top Donors Section
    with col2:
        st.markdown('<h3 class="section-header">🏆 Top Donors</h3>', unsafe_allow_html=True)
        
        # Calculate top donors
        top_donors_df = filtered_df.groupby('Donor').agg({
            'Amount': 'sum'
        }).sort_values('Amount', ascending=False).head(5)
        
        # Create a DataFrame with donor names
        top_donors_display = pd.DataFrame({
            'Donor': [donor_map.get(d, 'Unknown') for d in top_donors_df.index],
            'Total Amount': [format_indian_currency(amt) for amt in top_donors_df['Amount']]
        })
        
        # Display as a styled table
        st.markdown("""
            <style>
            .top-donors-table {
                font-size: 0.9rem;
                width: 100%;
                margin-bottom: 1rem;
            }
            .top-donors-table th {
                background-color: #f0f2f6;
                padding: 0.5rem;
                text-align: left;
            }
            .top-donors-table td {
                padding: 0.5rem;
                border-bottom: 1px solid #e0e0e0;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown(
            top_donors_display.to_html(
                index=False,
                classes=['top-donors-table'],
                escape=False
            ),
            unsafe_allow_html=True
        )

    # Remove the entire footer section and its styles
    st.markdown("---")