import streamlit as st
from modules.supabase_utils import fetch_all_donations, fetch_donors, delete_donation
from datetime import datetime, timedelta
import os
import pandas as pd
import zipfile
from io import BytesIO
import calendar
from dateutil.relativedelta import relativedelta

def format_amount(amount):
    return f"₹{amount:,.0f}"

def view_receipts_view():
    # Header with icon and title
    st.markdown("# 📜 View Receipts")
    
    # Initialize session state for deletion confirmation
    if 'show_delete_confirm' not in st.session_state:
        st.session_state.show_delete_confirm = False
    if 'donation_to_delete' not in st.session_state:
        st.session_state.donation_to_delete = None
    
    # Fetch all donations and donors
    donations = fetch_all_donations()
    donors = fetch_donors()
    
    if not donations:
        st.warning("No donation records found.")
        return
    
    # Create donor map for quick lookups
    donor_map = {d["id"]: d["Full Name"] for d in donors}
    
    # Convert to DataFrame
    df = pd.DataFrame(donations)
    df['donor_name'] = df['Donor'].map(donor_map)
    df['date'] = pd.to_datetime(df['date'])
    
    # Add sorting options
    st.markdown("### 🔄 Sort Options")
    sort_order = st.radio(
        "Sort donations by date:",
        ["Latest to Oldest", "Oldest to Latest"],
        horizontal=True
    )
    
    # Sort the dataframe based on user selection
    df = df.sort_values('date', ascending=(sort_order == "Oldest to Latest"))
    
    # Filters section
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        date_filter = st.selectbox(
            "Date Range",
            ["All Time", "This Month", "Last Month", "Last 3 Months", "Last 6 Months", "This Year", "Custom"]
        )
        
        if date_filter == "Custom":
            start_date = st.date_input("Start Date", value=df['date'].min())
            end_date = st.date_input("End Date", value=df['date'].max())
            filtered_df = df[
                (df['date'].dt.date >= start_date) & 
                (df['date'].dt.date <= end_date)
            ]
        else:
            today = pd.Timestamp.now()
            if date_filter == "This Month":
                start_date = today.replace(day=1)
                end_date = (start_date + pd.offsets.MonthEnd(0))
            elif date_filter == "Last Month":
                start_date = (today - pd.offsets.MonthBegin(1)).replace(day=1)
                end_date = (start_date + pd.offsets.MonthEnd(0))
            elif date_filter == "Last 3 Months":
                start_date = (today - pd.DateOffset(months=3))
                end_date = today
            elif date_filter == "Last 6 Months":
                start_date = (today - pd.DateOffset(months=6))
                end_date = today
            elif date_filter == "This Year":
                start_date = today.replace(month=1, day=1)
                end_date = today
            else:  # All Time
                filtered_df = df
                start_date = None
                end_date = None
            
            if start_date and end_date:
                filtered_df = df[
                    (df['date'].dt.date >= start_date.date()) & 
                    (df['date'].dt.date <= end_date.date())
                ]
    
    with col2:
        # Donor filter
        donor_filter = st.multiselect(
            "Select Donors",
            options=sorted(df['donor_name'].unique()),
            default=[]
        )
        if donor_filter:
            filtered_df = filtered_df[filtered_df['donor_name'].isin(donor_filter)]
    
    with col3:
        # Amount range filter
        min_amount = st.number_input("Minimum Amount", value=0.0, step=100.0)
        max_amount = st.number_input(
            "Maximum Amount",
            value=float(filtered_df['Amount'].max()),
            step=100.0
        )
        filtered_df = filtered_df[
            (filtered_df['Amount'] >= min_amount) & 
            (filtered_df['Amount'] <= max_amount)
        ]
    
    # Summary section
    st.markdown("### 📊 Summary")
    
    if not filtered_df.empty:
        # Display metrics in one row
        col1, col2, col3 = st.columns(3)
        
        total_amount = filtered_df['Amount'].sum()
        total_donations = len(filtered_df)
        avg_amount = total_amount / total_donations if total_donations > 0 else 0
        
        with col1:
            st.metric("Total Donations", f"₹{total_amount:,.2f}")
        with col2:
            st.metric("Number of Donations", total_donations)
        with col3:
            st.metric("Average Donation", f"₹{avg_amount:,.2f}")
        
        # Export buttons in a row
        st.markdown("### 📥 Export Options")
        button_col1, button_col2, button_col3 = st.columns(3)
        
        with button_col1:
            # Export to CSV
            if st.button("📊 Export to CSV"):
                # Prepare data for export
                export_df = filtered_df[[
                    'date', 'donor_name', 'Amount', 'Purpose', 
                    'payment_method', 'receipt_no'
                ]].copy()
                export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                export_df.columns = [
                    'Date', 'Donor', 'Amount', 'Purpose', 
                    'Payment Mode', 'Receipt Path'
                ]
                
                # Convert to CSV
                csv = export_df.to_csv(index=False)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"donations_{timestamp}.csv",
                    "text/csv",
                    key='download-csv'
                )
        
        with button_col2:
            # Export to Excel
            if st.button("📊 Export to Excel"):
                # Prepare data for export
                export_df = filtered_df[[
                    'date', 'donor_name', 'Amount', 'Purpose', 
                    'payment_method', 'receipt_no'
                ]].copy()
                export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                export_df.columns = [
                    'Date', 'Donor', 'Amount', 'Purpose', 
                    'Payment Mode', 'Receipt Path'
                ]
                
                # Create Excel buffer
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Donations', index=False)
                    
                    # Add summary sheet
                    summary_data = {
                        'Metric': ['Total Donations', 'Number of Donations', 'Average Donation'],
                        'Value': [
                            f"₹{total_amount:,.2f}",
                            total_donations,
                            f"₹{avg_amount:,.2f}"
                        ]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                excel_buffer.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    "📥 Download Excel",
                    excel_buffer,
                    f"donations_{timestamp}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key='download-excel'
                )
        
        with button_col3:
            # Export receipts as ZIP
            receipts_available = filtered_df['receipt_no'].notna().any()
            if receipts_available:
                # Add debug information about filtered data
                st.write("Debug Information:")
                st.write(f"Total donations in filter: {len(filtered_df)}")
                st.write(f"Donations with receipts: {filtered_df['receipt_no'].notna().sum()}")
                
                # Create a list of valid receipt paths
                valid_receipts = []
                for receipt_path in filtered_df['receipt_no'].dropna():
                    # Check if file exists and is a PDF
                    if os.path.exists(receipt_path) and receipt_path.lower().endswith('.pdf'):
                        valid_receipts.append({
                            'path': receipt_path,
                            'donor_name': filtered_df[filtered_df['receipt_no'] == receipt_path]['donor_name'].iloc[0]
                        })
                
                st.write(f"Valid receipts found: {len(valid_receipts)}")
                
                if valid_receipts:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for receipt in valid_receipts:
                            try:
                                receipt_path = receipt['path']
                                # Check if file exists and is readable
                                if os.path.exists(receipt_path) and os.access(receipt_path, os.R_OK):
                                    # Clean donor name - remove special characters and spaces
                                    donor_name = ''.join(e for e in receipt['donor_name'] if e.isalnum() or e == ' ').strip()
                                    # Get original filename
                                    filename = os.path.basename(receipt_path)
                                    # Create new filename with donor name
                                    new_filename = f"{donor_name}_{filename}"
                                    # Add file to ZIP
                                    zip_file.write(receipt_path, new_filename)
                                    st.write(f"Added receipt: {new_filename}")  # Debug line
                            except Exception as e:
                                st.warning(f"Could not add receipt {receipt_path} to ZIP: {str(e)}")
                                continue
                    
                    # Only offer download if we successfully added files
                    if zip_file.filelist:
                        st.write(f"Total receipts in ZIP: {len(zip_file.filelist)}")  # Debug line
                        zip_buffer.seek(0)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            "📑 Download All Receipts",
                            data=zip_buffer.getvalue(),
                            file_name=f"all_receipts_{timestamp}.zip",
                            mime="application/zip",
                            help=f"Download all {len(zip_file.filelist)} available donation receipts as a ZIP file"
                        )
                    else:
                        st.error("Failed to create ZIP file - no valid receipts could be added.")
                else:
                    st.warning("No valid PDF receipt files found in the selected date range.")
            else:
                st.warning("No receipts available for the selected donations.")

        # Display donations table
        st.markdown("### 📋 Detailed Donations")
        
        # Create display DataFrame
        display_df = pd.DataFrame({
            'Date': filtered_df['date'].dt.strftime('%Y-%m-%d'),
            'Donor': filtered_df['donor_name'],
            'Amount': filtered_df['Amount'].apply(format_amount),
            'Purpose': filtered_df['Purpose'],
            'Payment Mode': filtered_df['payment_method'],
            'Receipt': filtered_df['receipt_no'].apply(
                lambda x: "Available" if pd.notna(x) and os.path.exists(x) else "Not Available"
            )
        })

        # Add download links for individual receipts
        def create_download_link(row):
            if pd.notna(row['receipt_no']) and os.path.exists(row['receipt_no']):
                return f"[📄 Download]({row['receipt_no']})"
            return "Not Available"
            
        display_df['Download'] = filtered_df.apply(
            lambda row: create_download_link(row), axis=1
        )

        # Display the table with formatting
        st.dataframe(
            display_df,
            column_config={
                "Date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD",
                ),
                "Amount": st.column_config.TextColumn(
                    "Amount",
                    help="Donation amount in INR",
                    width="medium",
                ),
                "Purpose": st.column_config.TextColumn(
                    "Purpose",
                    width="large",
                ),
                "Payment Mode": st.column_config.TextColumn(
                    "Payment Mode",
                    width="medium",
                ),
                "Download": st.column_config.LinkColumn(
                    "Receipt",
                    width="small",
                )
            },
            hide_index=True
        )

        # Add delete buttons for each donation
        st.markdown("### ❌ Delete Donations")
        st.markdown("Select a donation to delete. Note: Active recurring donations cannot be deleted.")
        
        # Create a selection box for donations
        deletable_donations = filtered_df[
            ~(filtered_df['is_recurring'] & (filtered_df['recurring_status'] != 'Cancelled'))
        ]
        
        if not deletable_donations.empty:
            donation_options = [
                f"{row['date'].strftime('%Y-%m-%d')} - {row['donor_name']} - {format_amount(row['Amount'])} - {row['Purpose']}"
                for _, row in deletable_donations.iterrows()
            ]
            donation_indices = deletable_donations.index.tolist()
            
            selected_donation_idx = st.selectbox(
                "Select donation to delete:",
                range(len(donation_options)),
                format_func=lambda x: donation_options[x]
            )
            
            if st.button("🗑️ Delete Selected Donation", type="primary"):
                selected_donation = deletable_donations.iloc[selected_donation_idx]
                st.session_state.show_delete_confirm = True
                st.session_state.donation_to_delete = selected_donation['id']

            # Handle deletion confirmation
            if st.session_state.show_delete_confirm and st.session_state.donation_to_delete:
                with st.container():
                    st.warning("⚠️ Are you sure you want to delete this donation? This action cannot be undone.")
                    
                    donation_info = filtered_df[filtered_df['id'] == st.session_state.donation_to_delete].iloc[0]
                    st.info(f"""
                    Donation Details:
                    - Date: {donation_info['date'].strftime('%Y-%m-%d')}
                    - Donor: {donation_info['donor_name']}
                    - Amount: {format_amount(donation_info['Amount'])}
                    - Purpose: {donation_info['Purpose']}
                    """)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
                            if delete_donation(st.session_state.donation_to_delete):
                                st.success("Donation deleted successfully!")
                                # Reset confirmation state
                                st.session_state.show_delete_confirm = False
                                st.session_state.donation_to_delete = None
                                st.rerun()
                            else:
                                st.error("Failed to delete donation. Please try again.")
                    
                    with col2:
                        if st.button("❌ No, Keep", use_container_width=True):
                            st.session_state.show_delete_confirm = False
                            st.session_state.donation_to_delete = None
                            st.rerun()
        else:
            st.info("No deletable donations found in the current filter.")
    else:
        st.warning("No donations match the selected filters.")