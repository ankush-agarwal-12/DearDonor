import streamlit as st
from modules.airtable_utils import fetch_all_donations, fetch_donors
from datetime import datetime
import os
import pandas as pd

def format_amount(amount):
    return f"₹{amount:,.0f}"

def st_main():
    st.title("📋 All Donations")

    # Fetch all data
    donations = fetch_all_donations()
    donors = fetch_donors()
    
    if not donations:
        st.warning("No donation records found.")
        return

    # Create donor ID to name mapping
    donor_map = {d["id"]: d["Full Name"] for d in donors}

    # Convert to DataFrame for easier filtering
    df = pd.DataFrame([{
        'date': d['date'],
        'amount': d['amount'],
        'payment_method': d['payment_method'],
        'purpose': d['purpose'],
        'Donor': d['Donor'],
        'receipt_no': d.get('receipt_no', ''),
        'id': d['id']
    } for d in donations])
    
    df['date'] = pd.to_datetime(df['date'])
    df['Donor Name'] = df['Donor'].map(donor_map)
    
    # Sidebar filters
    st.sidebar.header("Filter Donations")
    
    # Donor filter with names
    donor_names = sorted(list(set(df['Donor Name'].dropna())))
    donor_filter = st.sidebar.selectbox("Select Donor", ["All"] + donor_names)
    
    # Mode filter
    modes = sorted(list(set(df['payment_method'].dropna())))
    mode_filter = st.sidebar.selectbox("Payment Mode", ["All"] + modes)
    
    # Date range filter
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=min_date)
    with col2:
        end_date = st.date_input("End Date", value=max_date)
    
    # Amount range filter
    min_amount = int(df['amount'].min())
    max_amount = int(df['amount'].max())
    amount_range = st.sidebar.slider("Amount Range (₹)", 
                                   min_value=min_amount,
                                   max_value=max_amount,
                                   value=(min_amount, max_amount))

    # Apply filters
    mask = pd.Series(True, index=df.index)
    
    if donor_filter != "All":
        mask &= df['Donor Name'] == donor_filter
    
    if mode_filter != "All":
        mask &= df['payment_method'] == mode_filter
    
    mask &= df['date'].dt.date >= start_date
    mask &= df['date'].dt.date <= end_date
    mask &= df['amount'] >= amount_range[0]
    mask &= df['amount'] <= amount_range[1]
    
    filtered_df = df[mask].sort_values('date', ascending=False)
    
    # Display summary statistics
    if not filtered_df.empty:
        total_amount = filtered_df['amount'].sum()
        avg_amount = filtered_df['amount'].mean()
        
        st.markdown("### 📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Amount", format_amount(total_amount))
        with col2:
            st.metric("Average Amount", format_amount(avg_amount))
        with col3:
            st.metric("Number of Donations", f"{len(filtered_df):,}")
        
        # Export functionality
        export_df = pd.DataFrame({
            'Date': filtered_df['date'].dt.strftime('%Y-%m-%d'),
            'Donor Name': filtered_df['Donor Name'],
            'Amount': filtered_df['amount'],
            'Payment Mode': filtered_df['payment_method'],
            'Purpose': filtered_df['purpose']
        })
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"donations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Display receipt download buttons separately if needed
        st.markdown("### 📄 Download Receipts")
        for idx, row in filtered_df.iterrows():
            if pd.notna(row.get('receipt_no')) and os.path.exists(row['receipt_no']):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{row['Donor Name']} - {row['date'].strftime('%Y-%m-%d')} - {format_amount(row['amount'])}")
                with col2:
                    with open(row['receipt_no'], "rb") as f:
                        st.download_button(
                            label="📄 Download",
                            data=f,
                            file_name=os.path.basename(row['receipt_no']),
                            mime="application/pdf",
                            key=f"download_{idx}"
                        )