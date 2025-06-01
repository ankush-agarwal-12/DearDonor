import streamlit as st
import pandas as pd
from modules.airtable_utils import fetch_donors, AIRTABLE_URL_DONATIONS, HEADERS
import os
import zipfile
from io import BytesIO
from datetime import datetime
import requests
import json

def create_zip_of_receipts(receipts_data):
    """Create a zip file containing donation receipts
    receipts_data should be a list of tuples containing (receipt_path, donation_id)"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for receipt_path in receipts_data:
            if receipt_path and os.path.exists(receipt_path):
                # Get just the filename without the path
                filename = os.path.basename(receipt_path)
                # Add the file to the zip
                zip_file.write(receipt_path, filename)
    return zip_buffer

def get_donor_donations(donor_id):
    """Get donation history for a specific donor from Airtable"""
    try:
        # Fetch donations from Airtable
        response = requests.get(
            f"{AIRTABLE_URL_DONATIONS}",
            headers=HEADERS,
            params={
                "filterByFormula": f"FIND('{donor_id}', ARRAYJOIN(Donor))"
            }
        )
        response.raise_for_status()
        
        # Convert Airtable response to DataFrame
        records = response.json().get('records', [])
        if not records:
            return pd.DataFrame()  # Return empty DataFrame if no donations found
            
        donations = []
        for record in records:
            fields = record['fields']
            donation = {
                'donation_id': record['id'],
                'amount': fields.get('Donation Amount', 0),
                'date': fields.get('Donation Date', ''),
                'payment_method': fields.get('Donation Mode', ''),
                'purpose': fields.get('Donation Purpose', ''),
                'receipt_no': fields.get('Receipt URL', '')
            }
            donations.append(donation)
            
        donations_df = pd.DataFrame(donations)
        if not donations_df.empty:
            donations_df['date'] = pd.to_datetime(donations_df['date'])
            donations_df = donations_df.sort_values('date', ascending=False)
            
        return donations_df
        
    except Exception as e:
        print(f"Error fetching donations: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def export_donor_donations(donor_id, donor_name, donations_df):
    """Export donor's donation history to Excel"""
    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"donor_{donor_id}_donations_{timestamp}.xlsx"
    
    # Create Excel writer object
    with pd.ExcelWriter(f"exports/{filename}") as writer:
        # Write donations data
        donations_df.to_excel(writer, sheet_name="Donations", index=False)
        
        # Create summary sheet
        summary_data = {
            "Total Donations": len(donations_df),
            "Total Amount": donations_df['amount'].sum(),
            "Average Amount": donations_df['amount'].mean(),
            "Minimum Amount": donations_df['amount'].min(),
            "Maximum Amount": donations_df['amount'].max(),
            "First Donation": donations_df['date'].min(),
            "Latest Donation": donations_df['date'].max()
        }
        
        summary_df = pd.DataFrame(list(summary_data.items()), 
                               columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        # Add monthly trends
        if not donations_df.empty:
            donations_df['date'] = pd.to_datetime(donations_df['date'])
            monthly_donations = donations_df.set_index('date').resample('ME')['amount'].sum().reset_index()
            monthly_donations.columns = ['Month', 'Total Amount']
            monthly_donations.to_excel(writer, sheet_name="Monthly Trends", index=False)
    
    return filename

def view_donor_profile():
    st.title("🔍 Donor Information")

    donors = fetch_donors()
    if not donors:
        st.error("No donors found. Please check your Airtable connection or add donors.")
        return

    donor_map = {f"{d['Full Name']} ({d['Email']})": d for d in donors}
    selected = st.selectbox(
        "Select Donor",
        options=["Select a donor..."] + list(donor_map.keys()),
        index=0
    )

    if selected == "Select a donor...":
        st.warning("Please select a donor to view their profile.")
        return

    donor = donor_map[selected]
    print("\nSelected donor:", json.dumps(donor, indent=2))
    
    st.markdown(f"**Name:** {donor.get('Full Name', '-')}")
    st.markdown(f"**Email:** {donor.get('Email', '-')}")
    st.markdown(f"**Phone:** {donor.get('Phone', '-')}")
    st.markdown(f"**Address:** {donor.get('Address', '-')}")
    st.markdown(f"**PAN:** {donor.get('PAN', '-')}")
    st.markdown(f"**Organization:** {donor.get('Organization', '-')}")

    st.subheader("💸 Donation History")
    print(f"\nFetching donations for donor ID: {donor['id']}")
    
    # Use the get_donor_donations function from airtable_utils
    from modules.airtable_utils import get_donor_donations as fetch_donations
    donations = fetch_donations(donor["id"])
    print("\nReceived donations DataFrame:")
    print(donations)
    
    if donations.empty:
        st.info("No donations recorded yet.")
    else:
        print("\nFormatting donation amounts...")
        # Format the Amount column with ₹ symbol and commas
        donations['amount'] = donations['amount'].apply(lambda x: f"₹{x:,.0f}")
        
        # Sort by date in descending order (most recent first)
        donations['date'] = pd.to_datetime(donations['date'])
        donations = donations.sort_values('date', ascending=False)
        
        # Calculate total donations before formatting
        total_amount = sum([float(amt.replace('₹', '').replace(',', '')) for amt in donations['amount']])
        print(f"\nTotal amount calculated: ₹{total_amount:,.2f}")
        
        # Format date for display
        donations['date'] = donations['date'].dt.strftime('%Y-%m-%d')
        
        print("\nFinal DataFrame for display:")
        print(donations[['date', 'amount', 'purpose', 'payment_method']])
        
        # Display the table with custom styling
        st.dataframe(
            donations[['date', 'amount', 'purpose', 'payment_method']],
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "amount": st.column_config.TextColumn("Amount", width="medium"),
                "purpose": st.column_config.TextColumn("Purpose", width="large"),
                "payment_method": st.column_config.TextColumn("Payment Method", width="medium"),
            },
            hide_index=True,
        )
        
        # Show summary statistics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Total Donations:** ₹{total_amount:,.0f}")
        with col2:
            st.markdown(f"**Number of Donations:** {len(donations)}")
        
        # Add download receipts button
        receipts = [r for r in donations['receipt_no'] if isinstance(r, str) and r.startswith('receipts/')]
        if receipts:
            with col3:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, receipt_path in enumerate(receipts):
                        if os.path.exists(receipt_path):
                            # Get original filename and add donation index to make it unique
                            original_filename = os.path.basename(receipt_path)
                            base, ext = os.path.splitext(original_filename)
                            unique_filename = f"{base}_{idx+1}{ext}"
                            zip_file.write(receipt_path, unique_filename)
                
                if zip_buffer.tell() > 0:  # Check if any files were added
                    zip_buffer.seek(0)
                    st.download_button(
                        label="📥 Download All Receipts",
                        data=zip_buffer.getvalue(),
                        file_name=f"{donor.get('Full Name', 'Donor')}_All_Receipts.zip",
                        mime="application/zip"
                    )
                else:
                    st.info("No receipt files found")
        else:
            with col3:
                st.info("No receipts available for download")

        # Display donation statistics
        st.markdown("### Donation Statistics")
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.metric(
                "Total Donations",
                len(donations)
            )
        
        with stats_col2:
            st.metric(
                "Total Amount",
                f"₹{total_amount:,.2f}"
            )
        
        with stats_col3:
            st.metric(
                "Average Amount",
                f"₹{total_amount/len(donations):,.2f}"
            )
        
        with stats_col4:
            st.metric(
                "Latest Donation",
                donations['date'].iloc[0]
            )