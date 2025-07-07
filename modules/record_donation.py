import streamlit as st
from modules.supabase_utils import (
    fetch_donors, 
    record_donation,
    get_last_receipt_number,
    get_organization_receipt_number,
    get_organization_receipt_path
)
from modules.pdf_template import generate_receipt, DEFAULT_RECEIPT_SETTINGS
from modules.email_utils import send_email_receipt
from modules.settings import load_settings, save_settings, load_org_settings
import os
from datetime import datetime
from dotenv import load_dotenv

import pandas as pd
import uuid
import re
from dateutil.relativedelta import relativedelta
import urllib.parse

load_dotenv()

def generate_receipt_number(organization_id: str = None):
    """Generate a sequential receipt number based on organization settings"""
    if not organization_id:
        raise ValueError("Organization ID is required")
        
    # Use the new organization-specific function
    return get_organization_receipt_number(organization_id)

def record_donation_view():
    # Custom CSS for styling
    st.markdown("""
        <style>
        .donor-card {
            background-color: #f1f8e9;
            border: 2px solid #2e7d32;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
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

        .form-section {
            background-color: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .form-section-title {
            color: #1976d2;
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .receipt-preview {
            background-color: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .stButton>button {
            width: 100%;
        }

        /* Add custom styling for quick amount buttons */
        .quick-amount-btn {
            background-color: transparent !important;
            border: 1px solid #d3d3d3 !important;
            border-radius: 999px !important;
            padding: 4px 12px !important;
            font-size: 0.9em !important;
            color: #333 !important;
            transition: background-color 0.2s ease !important;
            margin: 0 4px !important;
            min-width: 80px !important;
            text-align: center !important;
        }
        .quick-amount-btn:hover {
            background-color: #f5f5f5 !important;
            border-color: #bdbdbd !important;
        }
        .quick-amount-btn:active {
            background-color: #f0f0f0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_donor' not in st.session_state:
        st.session_state.selected_donor = None
    if 'amount' not in st.session_state:
        st.session_state.amount = 0.0
    if 'selected_purpose' not in st.session_state:
        st.session_state.selected_purpose = "General Fund"
    if 'show_add_donor' not in st.session_state:
        st.session_state.show_add_donor = False
    
    # Header
    st.markdown("# 💰 Record Donation")
    
    # Get organization_id from session state
    if 'organization' not in st.session_state:
        st.error("❌ Organization not found. Please login again.")
        return
    
    organization_id = st.session_state.organization['id']
    
    # Load settings (moved after organization_id is defined)
    settings = load_org_settings(organization_id)
    predefined_purposes = settings.get("donation_purposes", ["General Fund"])
    
    # Fetch donors
    donors = fetch_donors(organization_id=organization_id)
    if not donors:
        st.warning("No donors found. Please add a donor first.")
        if st.button("➕ Add New Donor"):
            st.session_state.show_add_donor = True
            st.rerun()
        return
    
    # Create donor options with search
    donor_options = {
        f"{d['Full Name']} ({d.get('Email', 'No email')})": d 
        for d in donors
    }
    
    # Add empty option at the beginning
    donor_options = {"Select a donor...": None} | donor_options
    
    # Donor selection with search
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_donor = st.selectbox(
            "Search and select donor*",
            options=list(donor_options.keys()),
            index=0,  # Set default to first option (empty)
            help="Type to search by name or email"
        )
    with col2:
        if st.button("➕ Add New Donor", use_container_width=True):
            st.session_state.show_add_donor = True
            st.rerun()
    
            # Display donor info
    if st.session_state.get('show_add_donor'):
        from modules.add_donor import add_donor_view
        add_donor_view()
        if st.button("← Back to Record Donation"):
            st.session_state.show_add_donor = False
            st.rerun()
        return
    
    if selected_donor and selected_donor != "Select a donor...":
        donor_info = donor_options[selected_donor]
        donor_id = donor_options[selected_donor]["id"]
        
        # Display donor information
        st.markdown(f"""
            <div class="donor-card">
                <div class="donor-name">👤 {donor_info["Full Name"]}</div>
                <div class="donor-field"><strong>📧 Email</strong>{donor_info.get("Email", "Not provided")}</div>
                <div class="donor-field"><strong>📱 Phone</strong>{donor_info.get("Phone", "Not provided")}</div>
                <div class="donor-field"><strong>🏢 Address</strong>{donor_info.get("Address", "Not provided")}</div>
                <div class="donor-field"><strong>🆔 PAN</strong>{donor_info.get("PAN", "Not provided")}</div>
            </div>
        """, unsafe_allow_html=True)


        # 3. Donation Entry Section (fields outside form for instant reactivity)
        st.markdown("### 💳 Donation Details")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Amount (₹)*",
                min_value=0.0,
                step=100.0,
                value=st.session_state.amount,
                help="Enter the donation amount",
                key="amount"
            )
        with col2:
            st.date_input(
                "Date*",
                value=st.session_state.get("date", datetime.now()),
                help="When was the donation made?",
                key="date"
            )
        col1, col2 = st.columns(2)
        with col1:
            purpose_options = ["General Fund"] + predefined_purposes
            if "Other" not in purpose_options:
                purpose_options.append("Other")
            selected_purpose = st.selectbox(
                "Purpose*",
                options=purpose_options,
                index=purpose_options.index(st.session_state.selected_purpose) if st.session_state.selected_purpose in purpose_options else 0,
                help="Select the purpose of the donation",
                key="selected_purpose"
            )
            if selected_purpose == "Other":
                st.text_input("Specify Purpose*", key="other_purpose")
        with col2:
            st.selectbox(
                "Payment Method*",
                ["Cash", "UPI", "Cheque", "Card / Net Banking"],
                help="How was the payment made?",
                key="payment_method"
            )
        # Additional payment fields
        if st.session_state.payment_method in ["Card / Net Banking", "Cheque"]:
            st.text_input(
                f"{st.session_state.payment_method} Number",
                help=f"Enter the {st.session_state.payment_method.lower()} number (optional)",
                key="reference_no"
            )
        elif st.session_state.payment_method == "UPI":
            st.text_input(
                "Transaction Reference",
                help="Enter the transaction reference number (optional)",
                key="reference_no"
            )
        # 4. Form for receipt options and submit
        with st.form("donation_form", clear_on_submit=False):
            st.markdown("### 📄 Receipt Options")
            if donor_options[selected_donor].get("Email"):
                send_receipt = st.checkbox(
                    "📧 Send receipt via email",
                    value=True,
                    help=f"Send receipt to: {donor_options[selected_donor].get('Email')}"
                )
            else:
                st.warning("⚠️ No email address available for this donor")
                send_receipt = False
            # Submit button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button(
                    "💰 Record Payment",
                    use_container_width=True
                )
            if submitted:
                amount = st.session_state.amount
                date = st.session_state.date
                if st.session_state.selected_purpose == "Other":
                    purpose = st.session_state.other_purpose
                else:
                    purpose = st.session_state.selected_purpose
                payment_method = st.session_state.payment_method
                reference_no = st.session_state.get("reference_no", None)
                if not amount or not date:
                    st.error("Please fill in all required fields marked with *")
                    return
                try:
                    # Show progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Update progress for each step
                    status_text.text("Preparing payment details...")
                    progress_bar.progress(20)
                    
                    # Prepare payment details
                    payment_details = {
                        "method": payment_method,
                        "date": date.isoformat()
                    }
                    if payment_method in ["Card / Net Banking", "Cheque"]:
                        if reference_no:  # Only add reference if provided
                            payment_details.update({
                                "reference_no": reference_no
                            })
                    elif payment_method == "UPI":
                        if reference_no:  # Only add reference if provided
                            payment_details["reference_no"] = reference_no

                    # Generate receipt number
                    status_text.text("Generating receipt number...")
                    progress_bar.progress(40)
                    receipt_number = generate_receipt_number(organization_id=organization_id)
                    
                    # Add receipt info to payment details (no longer storing permanent path)
                    payment_details["receipt_number"] = receipt_number
                    
                    status_text.text("Recording payment...")
                    progress_bar.progress(60)
                    
                    # Record donation
                    result = record_donation(
                        donor_id=donor_options[selected_donor]["id"],
                        amount=amount,
                        date=date.isoformat(),
                        purpose=purpose if selected_purpose == "Other" else selected_purpose,
                        payment_method=payment_method,
                        payment_details=payment_details,
                        organization_id=organization_id
                    )

                    if result:
                        success_message = "✅ Donation recorded successfully!"
                    
                    if result:
                        status_text.text("Generating receipt...")
                        progress_bar.progress(80)
                        
                        donor_data = {
                            "name": donor_options[selected_donor]["Full Name"],
                            "amount": amount,
                            "date": date.strftime("%Y-%m-%d"),
                            "receipt_number": receipt_number,
                            "purpose": purpose if selected_purpose == "Other" else selected_purpose,
                            "payment_mode": payment_method,
                            "pan": donor_options[selected_donor].get("PAN", "")
                        }
                        
                        try:
                            temp_receipt_path = None
                            
                            # Send email if requested (generate temporary receipt)
                            if send_receipt and donor_options[selected_donor].get("Email"):
                                status_text.text("Generating temporary receipt for email...")
                                progress_bar.progress(80)
                                
                                # Create temporary receipt for email
                                import tempfile
                                temp_dir = tempfile.gettempdir()
                                temp_receipt_path = os.path.join(temp_dir, f"temp_receipt_{receipt_number.replace('/', '_')}.pdf")
                                
                                generate_receipt(donor_data, temp_receipt_path, organization_id=organization_id)
                                
                                status_text.text("Sending email receipt...")
                                progress_bar.progress(90)
                                email_sent = send_email_receipt(
                                    to_email=donor_options[selected_donor]["Email"],
                                    donor_name=donor_options[selected_donor]["Full Name"],
                                    receipt_path=temp_receipt_path,
                                    amount=donor_data["amount"],
                                    receipt_number=receipt_number,
                                    purpose=donor_data["purpose"],
                                    payment_mode=payment_method
                                )
                                if email_sent:
                                    success_message += "\n📧 Receipt sent via email!"
                                else:
                                    success_message += "\n⚠️ Failed to send receipt via email."
                                
                                # Clean up temporary file immediately
                                try:
                                    os.remove(temp_receipt_path)
                                except:
                                    pass
                            
                            # Complete progress
                            status_text.text("Payment recorded successfully!")
                            progress_bar.progress(100)
                            
                            # Store info in session state (no permanent receipt path)
                            st.session_state.last_receipt_number = receipt_number
                            st.session_state.last_success_message = success_message
                            st.session_state.last_donation_data = donor_data
                            
                            # Rerun to show success message
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Failed to process receipt: {str(e)}")
                    else:
                        st.error("❌ Failed to record donation. Please try again.")

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    # Show success message if donation was recorded
    if 'last_success_message' in st.session_state:
        st.success(st.session_state.last_success_message)
        
        # Note: Receipts are now generated on-demand. Users can access them from Donor Info section.
        st.info("📄 **Receipt Access:** You can download receipts anytime from the 'View Donor Info' section.")
        
        # Clear session state after showing message
        if st.button("Record Another Donation"):
            for key in ['last_receipt_number', 'last_success_message', 'last_donation_data']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

            # Add WhatsApp notification button
            if donor_options[selected_donor] and donor_options[selected_donor].get("Phone"):
                # Get organization name from settings
                settings = load_org_settings(organization_id)
                org_name = settings.get('organization', {}).get('name', 'Our Organization')
                
                # Get donation data from session state
                donation_data = st.session_state.last_donation_data
                
                # Prepare WhatsApp message
                message = f"""Thank you for your generous donation to *{org_name}*.\n
*Amount:* ₹{donation_data['amount']}
*Date:* {donation_data['date']}
*Receipt No:* {st.session_state.last_receipt_number}\n
The donation receipt has been sent to your email: {donor_options[selected_donor].get('Email', '')}.
_Thank you for supporting us!_ :) """
                # Sanitize phone number and create WhatsApp URL
                phone = donor_options[selected_donor]["Phone"].replace("+", "").replace(" ", "")
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
                
                st.link_button(
                    label="Notify Donor on WhatsApp",
                    url=whatsapp_url,
                    use_container_width=True
                )

def custom_button(label, is_primary=True):
    """Create a custom styled button"""
    button_style = f"""
        <style>
            div.stButton > button:first-child {{
                background-color: {'#FF4B4B' if is_primary else '#FFFFFF'};
                color: {'white' if is_primary else '#000000'};
                border: {'none' if is_primary else '1px solid #CCCCCC'};
                padding: 0.5rem 1rem;
                font-weight: {'bold' if is_primary else 'normal'};
                width: 100%;
                margin: 0;
            }}
            div.stButton > button:hover {{
                background-color: {'#FF6B6B' if is_primary else '#F0F0F0'};
                border: {'none' if is_primary else '1px solid #CCCCCC'};
            }}
        </style>
    """
    st.markdown(button_style, unsafe_allow_html=True)
    return st.button(label, use_container_width=True)

