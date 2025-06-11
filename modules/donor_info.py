import streamlit as st
import pandas as pd
from modules.supabase_utils import fetch_donors, get_donor_donations, update_donor
import zipfile
from io import BytesIO
import os
from datetime import datetime
import plotly.express as px

def format_amount(amount):
    return f"₹{amount:,.2f}"

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
    
    # Search and filter section
    st.markdown('<p class="section-header">🔍 Search & Filter</p>', unsafe_allow_html=True)
    
    # Create donor options with formatted display names
    donor_options = {}
    for d in donors:
        display_name = f"{d['Full Name']} ({d.get('Email', 'No email')})"
        donor_options[display_name] = d
    
    selected_donor = st.selectbox(
        "Search and select donor",
        options=list(donor_options.keys()),
        key="donor_search"
    )
    
    # Filter donors based on search
    if selected_donor:
        selected_donor_info = donor_options[selected_donor]
        filtered_donors = donors_df[donors_df['Full Name'] == selected_donor_info['Full Name']]
    else:
        filtered_donors = donors_df

    for _, donor in filtered_donors.iterrows():
        with st.expander(f"🧑 {donor['Full Name']}"):
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Contact Information
                st.markdown("#### 📞 Contact Information")
                st.markdown(f"**Email:** {donor['Email']}")
                st.markdown(f"**Phone:** {donor['Phone']}")
                st.markdown(f"**Address:** {donor['Address']}")
                if pd.notna(donor.get('PAN')):
                    st.markdown(f"**PAN:** {donor['PAN']}")

                # Edit Donor Information
                if st.button(f"✏️ Edit {donor['Full Name']}'s Information", key=f"edit_{donor['id']}"):
                    st.session_state.editing_donor = donor['id']
                    st.session_state.edit_name = donor['Full Name']
                    st.session_state.edit_email = donor['Email']
                    st.session_state.edit_phone = donor['Phone']
                    st.session_state.edit_address = donor['Address']
                    st.session_state.edit_pan = donor.get('PAN', '')
                    st.session_state.edit_type = donor.get('donor_type', 'Individual')

            with col2:
                # Fetch donor's donations
                donations = get_donor_donations(donor['id'])
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
                    st.markdown(f"**Last Donation:** {pd.to_datetime(last_donation).strftime('%Y-%m-%d')}")
                else:
                    st.info("No donations recorded yet")

            # Show donation history if available
            if donations:
                st.markdown("#### 📜 Donation History")
                
                # Create donation history table
                history_df = pd.DataFrame(donations)
                history_df['date'] = pd.to_datetime(history_df['date'])
                history_df = history_df.sort_values('date', ascending=False)
                
                # Display as a clean table
                st.dataframe(
                    history_df[['date', 'Amount', 'payment_method', 'Purpose']].assign(
                        date=history_df['date'].dt.strftime('%Y-%m-%d'),
                        Amount=history_df['Amount'].apply(format_amount)
                    ),
                    column_config={
                        "date": "Date",
                        "Amount": "Amount",
                        "payment_method": "Payment Method",
                        "Purpose": "Purpose"
                    },
                    hide_index=True
                )

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
                options=['Individual', 'Organization', 'Trust', 'Other'],
                index=['Individual', 'Organization', 'Trust', 'Other'].index(st.session_state.edit_type)
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
                del st.session_state.editing_donor
                st.success("Donor information updated successfully!")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                del st.session_state.editing_donor
                st.rerun()