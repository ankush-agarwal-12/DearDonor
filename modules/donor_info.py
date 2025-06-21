import streamlit as st
import pandas as pd
from modules.supabase_utils import fetch_donors, get_donor_donations, update_donor, delete_donation, delete_donor
import zipfile
from io import BytesIO
import os
from datetime import datetime, timedelta
import plotly.express as px

def format_amount(amount):
    return f"₹{amount:,.2f}"

def get_financial_year_dates():
    """Get current financial year start and end dates (April 1 to March 31)"""
    current_date = datetime.now()
    if current_date.month >= 4:
        # Current financial year started in April of current year
        fy_start = datetime(current_date.year, 4, 1)
        fy_end = datetime(current_date.year + 1, 3, 31)
    else:
        # Current financial year started in April of previous year
        fy_start = datetime(current_date.year - 1, 4, 1)
        fy_end = datetime(current_date.year, 3, 31)
    return fy_start, fy_end

def filter_donations_by_date_range(donations_df, date_filter, custom_start=None, custom_end=None):
    """Filter donations based on selected date range"""
    if date_filter == "All Time":
        return donations_df
    
    # Convert date column to datetime if not already
    donations_df['date'] = pd.to_datetime(donations_df['date'])
    
    if date_filter == "This Month":
        current_date = datetime.now()
        start_date = datetime(current_date.year, current_date.month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    elif date_filter == "Last Month":
        current_date = datetime.now()
        if current_date.month == 1:
            start_date = datetime(current_date.year - 1, 12, 1)
        else:
            start_date = datetime(current_date.year, current_date.month - 1, 1)
        end_date = datetime(current_date.year, current_date.month, 1) - timedelta(days=1)
    
    elif date_filter == "This Financial Year":
        start_date, end_date = get_financial_year_dates()
    
    elif date_filter == "Last Financial Year":
        current_date = datetime.now()
        if current_date.month >= 4:
            start_date = datetime(current_date.year - 1, 4, 1)
            end_date = datetime(current_date.year, 3, 31)
        else:
            start_date = datetime(current_date.year - 2, 4, 1)
            end_date = datetime(current_date.year - 1, 3, 31)
    
    elif date_filter == "Custom Range":
        if custom_start and custom_end:
            start_date = pd.to_datetime(custom_start)
            end_date = pd.to_datetime(custom_end)
        else:
            return donations_df
    
    else:
        return donations_df
    
    # Filter donations within the date range
    filtered_df = donations_df[
        (donations_df['date'] >= start_date) & 
        (donations_df['date'] <= end_date)
    ]
    
    return filtered_df

def donor_info_view():
    # Header with icon and title
    st.markdown("# 👥 Donor Information")

    # Fetch all donors
    donors = fetch_donors()
    
    if not donors:
        st.warning("No donors found in the database.")
        st.markdown("""
        ### 🚀 Get Started
        1. Click on "Add New Donor" in the sidebar to add your first donor
        2. Fill in the donor details
        3. Return here to view and manage donor information
        """)
        return

    # Convert to DataFrame for easier handling
    donors_df = pd.DataFrame(donors)
    
    # Ensure donor_type exists with a default value
    if 'donor_type' not in donors_df.columns:
        donors_df['donor_type'] = 'Individual'
    
    
    
    # Create donor options with formatted display names
    donor_options = {}
    for d in donors:
        display_name = f"{d['Full Name']} ({d.get('Email', 'No email')})"
        donor_options[display_name] = d
    
    # Add empty option at the beginning
    donor_options = {"Select a donor...": None} | donor_options
    
    # Initialize selected donor in session state if not exists
    if 'selected_donor_display' not in st.session_state:
        st.session_state.selected_donor_display = "Select a donor..."
    
    # Find the index of the currently selected donor
    donor_options_list = list(donor_options.keys())
    try:
        current_index = donor_options_list.index(st.session_state.selected_donor_display)
    except ValueError:
        # If the selected donor is not found (e.g., after editing), default to first option
        current_index = 0
        st.session_state.selected_donor_display = "Select a donor..."
    
    selected_donor = st.selectbox(
        "Search and select donor",
        options=donor_options_list,
        index=current_index,
        key="donor_search"
    )
    
    # Update session state with the selected donor
    st.session_state.selected_donor_display = selected_donor

    # Filter donors based on search
    if selected_donor and selected_donor != "Select a donor...":
        selected_donor_info = donor_options[selected_donor]
        filtered_donors = donors_df[donors_df['Full Name'] == selected_donor_info['Full Name']]
    else:
        filtered_donors = pd.DataFrame([])  # Empty DataFrame if no donor selected

    for _, donor in filtered_donors.iterrows():
        
            col1, col2 = st.columns([3, 2])
            
            with col1:
                col3, col4 = st.columns([7, 1])
                with col3:
                # Contact Information
                    st.markdown("#### 🗂️ Donor Information")
                with col4:
                    # Edit Donor Information
                    if st.button(f"Edit", key=f"edit_{donor['id']}"):
                        st.session_state.editing_donor = donor['id']
                        st.session_state.edit_name = donor['Full Name']
                        st.session_state.edit_email = donor['Email']
                        st.session_state.edit_phone = donor['Phone']
                        st.session_state.edit_address = donor['Address']
                        st.session_state.edit_pan = donor.get('PAN', '')
                        st.session_state.edit_type = donor.get('donor_type', 'Individual')

                # Apply similar card style as Record Donation
                st.markdown("""
                    <style>
                    .donor-card {
                        background-color: #f1f8e9;
                        border: 2px solid #2e7d32;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 0 0 20px 0;
                    }
                    .donor-name {
                        font-size: 1.3em;
                        font-weight: bold;
                        color: #1b5e20;
                        margin-bottom: 15px;
                    }
                    .donor-field {
                        margin: 8px 0;
                        color: #333;
                    }
                    .donor-field strong {
                        color: #2e7d32;
                        margin-right: 10px;
                        min-width: 80px;
                        display: inline-block;
                    }
                    </style>
                """, unsafe_allow_html=True)



                st.markdown(f"""
    <div class="donor-card">
        <div class="donor-name">👤 {donor['Full Name']}</div>
        <div class="donor-field"><strong>📧 Email</strong>{donor['Email']}</div>
        <div class="donor-field"><strong>📱 Phone</strong>{donor['Phone']}</div>
        <div class="donor-field"><strong>🏢 Address</strong>{donor['Address']}</div>
        <div class="donor-field"><strong>🆔 PAN</strong>{donor['PAN'] if pd.notna(donor.get('PAN')) else 'Not Provided'}</div>
    </div>
""", unsafe_allow_html=True)

                # Fetch donor's donations once
                donations = get_donor_donations(donor['id'])
                
                # Delete Donor Section - Only show if no donations exist
                if not donations:
                    st.markdown("#### 🗑️ Delete Donor")
                    st.warning("⚠️ **Warning**: Deleting a donor is permanent and cannot be undone.")
                    
                    # Confirmation checkbox
                    confirm_delete = st.checkbox(
                        "I understand that this action cannot be undone and I want to delete this donor",
                        key=f"confirm_delete_{donor['id']}"
                    )
                    
                    if confirm_delete:
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("🗑️ Delete Donor", type="secondary", key=f"delete_donor_{donor['id']}"):
                                # Attempt to delete the donor
                                if delete_donor(donor['id']):
                                    st.success("Donor deleted successfully!")
                                    # Reset the selected donor to default
                                    st.session_state.selected_donor_display = "Select a donor..."
                                    st.rerun()
                                else:
                                    st.error("Failed to delete donor. They may have donation history that prevents deletion.")
                        with col2:
                            st.info("Click the button to permanently delete this donor.")

            with col2:
                # Use the already fetched donations for statistics
                if donations:
                    donations_df = pd.DataFrame(donations)
                    
                    # Donation Statistics
                    st.markdown("#### 📊 Donation Statistics")
                    total_donated = donations_df['Amount'].sum()
                    avg_donation = donations_df['Amount'].mean()
                    num_donations = len(donations_df)
                    last_donation = donations_df['date'].max()
                    
                    st.markdown(f"**Total Donated:** {format_amount(total_donated)}")
                    st.markdown(f"**Average Donation:** {format_amount(avg_donation)}")
                    st.markdown(f"**Number of Donations:** {num_donations}")
                    st.markdown(f"**Last Donation:** {pd.to_datetime(last_donation).strftime('%d-%m-%Y')}")
                else:
                    st.info("No donations recorded yet")

            # Show donation history if available
            if donations:
                st.markdown("#### 📜 Donation History")
                
                # Date Range Filter
                st.markdown("**Filter by Date Range:**")
                col1, col2 = st.columns([2, 2])
                
                with col1:
                    date_filter = st.selectbox(
                        "Select Date Range",
                        ["All Time", "This Month", "Last Month", "This Financial Year", "Last Financial Year", "Custom Range"],
                        key="date_filter"
                    )
                
                with col2:
                    if date_filter == "Custom Range":
                        custom_start = st.date_input("Start Date", key="custom_start")
                        custom_end = st.date_input("End Date", key="custom_end")
                    else:
                        custom_start = None
                        custom_end = None
                
                # Create donation history table
                history_df = pd.DataFrame(donations)
                history_df['date'] = pd.to_datetime(history_df['date'])
                
                # Apply date filter
                filtered_history_df = filter_donations_by_date_range(
                    history_df, date_filter, custom_start, custom_end
                )
                
                # Sort by date (most recent first)
                filtered_history_df = filtered_history_df.sort_values('date', ascending=False)
                
                # Show filter summary
                if date_filter != "All Time":
                    st.info(f"📅 Showing donations for: **{date_filter}**")
                    if len(filtered_history_df) != len(history_df):
                        st.info(f"Displaying {len(filtered_history_df)} of {len(history_df)} total donations")
                
                # Display as a clean table
                if not filtered_history_df.empty:
                    st.dataframe(
                        filtered_history_df[['date', 'Amount', 'payment_method', 'Purpose']].assign(
                            date=filtered_history_df['date'].dt.strftime('%d-%m-%Y'),
                            Amount=filtered_history_df['Amount'].apply(format_amount)
                        ),
                        column_config={
                            "date": "Date",
                            "Amount": "Amount",
                            "payment_method": "Payment Method",
                            "Purpose": "Purpose"
                        },
                        hide_index=True
                    )
                    
                    # Show filtered statistics
                    if date_filter != "All Time":
                        filtered_total = filtered_history_df['Amount'].sum()
                        filtered_avg = filtered_history_df['Amount'].mean()
                        st.markdown(f"**Filtered Total:** {format_amount(filtered_total)}")
                        st.markdown(f"**Filtered Average:** {format_amount(filtered_avg)}")
                else:
                    st.info(f"No donations found for the selected date range: {date_filter}")
                
                # Delete Donation Section
                st.markdown("#### 🗑️ Delete Donation")
                st.warning("⚠️ **Warning**: Deleting a donation is permanent and cannot be undone.")
                
                # Create options for donation deletion (use filtered donations for selection)
                if not filtered_history_df.empty:
                    donation_options = {}
                    for _, donation in filtered_history_df.iterrows():
                        donation_date = donation['date'].strftime('%d-%m-%Y')
                        display_name = f"₹{donation['Amount']:,.2f} on {donation_date} - {donation['Purpose']}"
                        donation_options[display_name] = donation['id']
                    
                    selected_donation_to_delete = st.selectbox(
                        "Select donation to delete:",
                        options=["Select a donation..."] + list(donation_options.keys()),
                        key="delete_donation_select"
                    )
                    
                    if selected_donation_to_delete and selected_donation_to_delete != "Select a donation...":
                        donation_id_to_delete = donation_options[selected_donation_to_delete]
                        
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("🗑️ Delete Donation", type="secondary"):
                                # Attempt to delete the donation
                                if delete_donation(donation_id_to_delete):
                                    st.success("Donation deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete donation. It may be linked to a recurring plan or already deleted.")
                        with col2:
                            st.info("Click the button to permanently delete this donation.")
                else:
                    st.info("No donations available for deletion with the current filter.")

    # Edit Donor Form
    if hasattr(st.session_state, 'editing_donor'):
        st.markdown("### ✏️ Edit Donor Information")
        
        edit_col1, edit_col2 = st.columns(2)
        
        with edit_col1:
            new_name = st.text_input("Full Name", st.session_state.edit_name)
            new_email = st.text_input("Email", st.session_state.edit_email)
            new_phone = st.text_input("Phone", st.session_state.edit_phone)
        
        with edit_col2:
            new_address = st.text_area("Address", st.session_state.edit_address)
            new_pan = st.text_input("PAN", st.session_state.edit_pan)
            new_type = st.selectbox(
                "Donor Type",
                options=['Individual', 'Company'],
                index=['Individual', 'Company'].index(st.session_state.edit_type) if st.session_state.edit_type in ['Individual', 'Company'] else 0
            )

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("💾 Save Changes"):
                # Update donor information
                update_donor(
                    st.session_state.editing_donor,
                    {
                        "full_name": new_name,
                        "email": new_email,
                        "phone": new_phone,
                        "address": new_address,
                        "pan": new_pan,
                        "donor_type": new_type
                    }
                )
                # Update the selected donor display name in session state
                new_display_name = f"{new_name} ({new_email})"
                st.session_state.selected_donor_display = new_display_name
                del st.session_state.editing_donor
                st.success("Donor information updated successfully!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                del st.session_state.editing_donor
                st.rerun()