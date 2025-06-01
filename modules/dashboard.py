import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from modules.airtable_utils import fetch_all_donations, fetch_donors
from datetime import datetime, timedelta

def get_financial_year_dates():
    today = datetime.now()
    if today.month >= 4:  # If current month is April or later
        start_year = today.year
    else:
        start_year = today.year - 1
    fy_start = datetime(start_year, 4, 1)
    fy_end = datetime(start_year + 1, 3, 31)
    return fy_start, fy_end

def show_dashboard():
    st.title("🔖 Donation Dashboard")

    # Fetch all data
    donations = fetch_all_donations()
    donors = fetch_donors()
    
    if not donations:
        st.warning("No donation data found.")
        return

    # Create donor ID to name mapping
    donor_map = {d["id"]: d["Full Name"] for d in donors}

    # Create DataFrame
    df = pd.DataFrame(donations)
    
    # Replace donor IDs with names
    df['Donor Name'] = df['Donor'].map(donor_map)

    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        print(f"Error processing dates: {e}")
        print("DataFrame columns:", df.columns.tolist())
        print("Sample data:", df.head().to_dict())
        st.error(f"Error processing dates: {e}")
        return

    # Calculate date ranges
    today = datetime.now()
    this_month_start = datetime(today.year, today.month, 1)
    three_months_ago = today - timedelta(days=90)
    fy_start, fy_end = get_financial_year_dates()

    # Calculate metrics
    total_donations = df['amount'].sum()
    this_month_donations = df[df['date'] >= this_month_start]['amount'].sum()
    last_3_months_donations = df[df['date'] >= three_months_ago]['amount'].sum()
    this_fy_donations = df[(df['date'] >= fy_start) & (df['date'] <= fy_end)]['amount'].sum()
    
    # Display metrics in columns
    st.subheader("📊 Donation Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("This Month", f"₹{this_month_donations:,.0f}")
        st.metric("Last 3 Months", f"₹{last_3_months_donations:,.0f}")
    with col2:
        st.metric(f"FY {fy_start.year}-{fy_end.year}", f"₹{this_fy_donations:,.0f}")
        st.metric("Overall Total", f"₹{total_donations:,.0f}")

    # Additional Statistics
    st.subheader("📈 Additional Statistics")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Total Donors", len(donors))
        avg_donation = total_donations / len(df) if len(df) > 0 else 0
        st.metric("Average Donation", f"₹{avg_donation:,.0f}")
    with col4:
        st.metric("Total Donations", len(df))
        if len(df) > 0:
            last_donation_date = df['date'].max().strftime('%Y-%m-%d')
            st.metric("Last Donation", last_donation_date)

    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Top Donors - Horizontal Bar Chart
        st.subheader("🏆 Top Donors")
        top_donors = df.groupby('Donor Name')['amount'].sum().sort_values(ascending=True).tail(5)
        
        fig_donors, ax_donors = plt.subplots(figsize=(6, 3))
        fig_donors.patch.set_facecolor('#0E1117')  # Dark background
        ax_donors.set_facecolor('#1B1E23')  # Slightly lighter dark background
        
        bars = ax_donors.barh(top_donors.index, top_donors.values, color='#00A6FB')  # Blue bars
        ax_donors.set_xlabel('Amount (₹)', color='white')
        ax_donors.tick_params(axis='both', colors='white')
        ax_donors.spines['top'].set_visible(False)
        ax_donors.spines['right'].set_visible(False)
        ax_donors.spines['bottom'].set_color('white')
        ax_donors.spines['left'].set_color('white')
        
        # Add value labels on the bars
        for bar in bars:
            width = bar.get_width()
            ax_donors.text(width, bar.get_y() + bar.get_height()/2, 
                         f'₹{int(width):,}',
                         va='center', color='white', fontsize=8)
        
        plt.tight_layout()
        st.pyplot(fig_donors)
        plt.close()

    with chart_col2:
        # Monthly Donations for Current FY - Horizontal Bar Chart
        st.subheader("📅 Monthly Donations (Current FY)")
        
        # Create a date range for all months in the FY
        months = pd.date_range(start=fy_start, end=fy_end, freq='ME')  # Using 'ME' for month end
        month_labels = months.strftime('%B %Y')
        
        # Group donations by month
        fy_data = df[(df['date'] >= fy_start) & (df['date'] <= fy_end)].copy()
        monthly_donations = fy_data.groupby(fy_data['date'].dt.strftime('%B %Y'))['amount'].sum()
        
        # Ensure all months are present and reverse the order
        monthly_donations = monthly_donations.reindex(month_labels, fill_value=0)
        monthly_donations = monthly_donations.iloc[::-1]  # Reverse the order
        
        fig_monthly, ax_monthly = plt.subplots(figsize=(6, 4))
        fig_monthly.patch.set_facecolor('#0E1117')  # Dark background
        ax_monthly.set_facecolor('#1B1E23')  # Slightly lighter dark background
        
        bars = ax_monthly.barh(monthly_donations.index, monthly_donations.values, color='#00A6FB')  # Blue bars
        ax_monthly.set_xlabel('Amount (₹)', color='white')
        ax_monthly.tick_params(axis='both', colors='white')
        ax_monthly.spines['top'].set_visible(False)
        ax_monthly.spines['right'].set_visible(False)
        ax_monthly.spines['bottom'].set_color('white')
        ax_monthly.spines['left'].set_color('white')
        
        # Add value labels on the bars
        for bar in bars:
            width = bar.get_width()
            if width > 0:  # Only add label if there's a donation
                ax_monthly.text(width, bar.get_y() + bar.get_height()/2, 
                              f'₹{int(width):,}',
                              va='center', color='white', fontsize=8)
        
        plt.tight_layout()
        st.pyplot(fig_monthly)
        plt.close()