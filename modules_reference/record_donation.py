import streamlit as st
from modules.supabase_utils import (
    fetch_donors, 
    record_donation,
    get_active_recurring_donations,
    update_recurring_donation_status, 
    get_last_receipt_number,
    record_recurring_payment,
    get_organization_receipt_number,
    get_organization_receipt_path
)
from modules.pdf_template import generate_receipt, DEFAULT_RECEIPT_SETTINGS
from modules.email_utils import send_email_receipt
from modules.settings import load_settings, save_settings, load_org_settings
import os
from datetime import datetime
from dotenv import load_dotenv
from modules.recurring_donations import calculate_next_due_date
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
        .recurring-alert {
            background-color: #e3f2fd;
            border: 2px solid #1976d2;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .recurring-alert-title {
            color: #1976d2;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .recurring-info {
            background-color: #fff;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .recurring-field {
            margin: 8px 0;
            color: #333;
        }
        .recurring-field strong {
            color: #1976d2;
            margin-right: 10px;
            min-width: 120px;
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
        .recurring-payment-section {
            background-color: #e8f5e9;
            border: 2px solid #43a047;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .recurring-payment-title {
            color: #2e7d32;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
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
    if 'active_recurring_plans' not in st.session_state:
        st.session_state.active_recurring_plans = None
    if 'amount' not in st.session_state:
        st.session_state.amount = 0.0
    if 'selected_purpose' not in st.session_state:
        st.session_state.selected_purpose = "General Fund"
    if 'is_recurring_payment' not in st.session_state:
        st.session_state.is_recurring_payment = False
    if 'selected_recurring_plan' not in st.session_state:
        st.session_state.selected_recurring_plan = None
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
    
    # Display donor info and handle recurring donation check
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
        
        # Check for active recurring plans
        recurring_plans = get_active_recurring_donations(donor_id, organization_id=organization_id)
        st.session_state.active_recurring_plans = recurring_plans
        
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
        
        # Handle recurring donation section
        if recurring_plans:
            with st.expander("🔄 Active Recurring Plans Found", expanded=True):
                st.markdown("""
                    <div class="recurring-alert">
                        <div class="recurring-alert-title">🔄 Active Recurring Plans</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Create radio options for selecting a recurring plan or one-time donation
                plan_options = ["One-time donation"] + [
                    f"₹{plan['Amount']:,.2f} {plan['Frequency']} - {plan['Purpose']}"
                    for plan in recurring_plans
                ]
                selected_plan_idx = st.radio(
                    "Is this donation a payment for an existing recurring plan?",
                    options=range(len(plan_options)),
                    format_func=lambda x: plan_options[x],
                    help="Select a recurring plan to link this payment to, or choose 'One-time donation' for a regular donation",
                    key="recurring_plan_selector"
                )
                
                if selected_plan_idx == 0:  # One-time donation is selected
                    st.session_state.selected_recurring_plan = None
                    st.session_state.is_recurring_payment = False
                else:  # A recurring plan is selected
                    selected_plan = recurring_plans[selected_plan_idx - 1]
                    st.session_state.is_recurring_payment = True
                    st.session_state.selected_recurring_plan = selected_plan
                    st.session_state.show_recurring_fields = False
                    
                    # Display selected plan details
                    st.markdown(f"""
                        <div class="recurring-info">
                            <div class="recurring-field">
                                <strong>Amount</strong>₹{selected_plan['Amount']:,.2f}
                            </div>
                            <div class="recurring-field">
                                <strong>Frequency</strong>{selected_plan['Frequency']}
                            </div>
                            <div class="recurring-field">
                                <strong>Next Due Date</strong>{pd.to_datetime(selected_plan['next_due_date']).strftime('%Y-%m-%d') if selected_plan.get('next_due_date') else 'Not set'}
                            </div>
                            <div class="recurring-field">
                                <strong>Start Date</strong>{pd.to_datetime(selected_plan['start_date']).strftime('%Y-%m-%d') if selected_plan.get('start_date') else 'Not available'}
                            </div>
                            <div class="recurring-field">
                                <strong>Last Paid</strong>{pd.to_datetime(selected_plan['last_paid_date']).strftime('%Y-%m-%d') if selected_plan.get('last_paid_date') else 'No payments yet'}
                            </div>
                            <div class="recurring-field">
                                <strong>Purpose</strong>{selected_plan['Purpose']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("ℹ️ This payment will be linked to the selected recurring plan and update the next due date automatically.")
        else:
            st.session_state.is_recurring_payment = False
            st.session_state.selected_recurring_plan = None

        # Show option to set up new recurring donation outside the expander
        if not st.session_state.is_recurring_payment:
            setup_recurring = st.checkbox("Set up recurring donation?", key="setup_new_recurring")
            st.session_state.show_recurring_fields = setup_recurring
            
            if st.session_state.show_recurring_fields:
                with st.container():
                    st.markdown("""
                        <div class="recurring-alert">
                            <div class="recurring-alert-title">🔄 Configure Recurring Donation</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        recurring_frequency = st.selectbox(
                            "Frequency*",
                            ["Monthly", "Quarterly", "Half-Yearly", "Yearly"],
                            help="How often should this donation repeat?"
                        )
                    with col2:
                        start_date = st.date_input(
                            "Start Date*",
                            value=datetime.now(),
                            help="When should the recurring donation start?"
                        )
                    
                    if start_date and recurring_frequency:
                        if recurring_frequency == "Monthly":
                            next_due = start_date + relativedelta(months=1)
                        elif recurring_frequency == "Quarterly":
                            next_due = start_date + relativedelta(months=3)
                        elif recurring_frequency == "Half-Yearly":
                            next_due = start_date + relativedelta(months=6)
                        else:  # Yearly
                            next_due = start_date + relativedelta(years=1)
                        
                        st.info(f"📅 First payment will be due on: {next_due.strftime('%Y-%m-%d')}")
        
        # Update form fields based on selected recurring plan
        if st.session_state.get('selected_recurring_plan'):
            plan = st.session_state.selected_recurring_plan
            amount = plan['Amount']
            purpose = plan['Purpose']
        else:
            amount = st.session_state.amount
            purpose = st.session_state.selected_purpose

        # 3. Donation Entry Section (fields outside form for instant reactivity)
        st.markdown("### 💳 Donation Details")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.is_recurring_payment:
                st.number_input(
                    "Amount (₹)*",
                    value=float(st.session_state.selected_recurring_plan['Amount']),
                    disabled=True,
                    help="Amount is fixed for recurring payments",
                    key="amount"
                )
            else:
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
            if st.session_state.is_recurring_payment:
                st.text_input(
                    "Purpose*",
                    value=st.session_state.selected_recurring_plan['Purpose'],
                    disabled=True,
                    help="Purpose is fixed for recurring payments",
                    key="selected_purpose"
                )
            else:
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

                    # Generate receipt number and path
                    status_text.text("Generating receipt number...")
                    progress_bar.progress(40)
                    receipt_number = generate_receipt_number(organization_id=organization_id)
                    receipt_path = get_organization_receipt_path(organization_id, receipt_number)
                    
                    # Add receipt info to payment details
                    payment_details["receipt_number"] = receipt_number
                    payment_details["receipt_path"] = receipt_path
                    
                    status_text.text("Recording payment...")
                    progress_bar.progress(60)
                    
                    if st.session_state.get('selected_recurring_plan'):
                        # Record recurring payment
                        plan = st.session_state.selected_recurring_plan
                        result = record_recurring_payment(
                            donor_id=donor_options[selected_donor]["id"],
                            recurring_id=plan['id'],
                            amount=plan['Amount'],
                            payment_date=date,
                            payment_details=payment_details,
                            organization_id=organization_id
                        )

                        if result:
                            success_message = "✅ Recurring payment recorded successfully!"
                    else:
                        # Record regular donation
                        result = record_donation(
                            donor_id=donor_options[selected_donor]["id"],
                            amount=amount,
                            date=date.isoformat(),
                            purpose=purpose if selected_purpose == "Other" else selected_purpose,
                            payment_method=payment_method,
                            payment_details=payment_details,
                            is_recurring=st.session_state.show_recurring_fields,
                            recurring_frequency=recurring_frequency if st.session_state.show_recurring_fields else None,
                            start_date=start_date.isoformat() if st.session_state.show_recurring_fields else None,
                            next_due_date=next_due.isoformat() if st.session_state.show_recurring_fields else None,
                            recurring_status="Active" if st.session_state.show_recurring_fields else None,
                            linked_to_recurring=False,
                            is_scheduled_payment=False,
                            organization_id=organization_id
                        )

                        if result:
                            success_message = "✅ Donation recorded successfully!"
                            if st.session_state.show_recurring_fields:
                                success_message += "\n🔄 Recurring donation has been set up!"
                    
                    if result:
                        status_text.text("Generating receipt...")
                        progress_bar.progress(80)
                        
                        donor_data = {
                            "name": donor_options[selected_donor]["Full Name"],
                            "amount": plan['Amount'] if st.session_state.get('selected_recurring_plan') else amount,
                            "date": date.strftime("%Y-%m-%d"),
                            "receipt_number": receipt_number,
                            "purpose": plan.get('Purpose', 'General Fund') if st.session_state.get('selected_recurring_plan') else (purpose if selected_purpose == "Other" else selected_purpose),
                            "payment_mode": payment_method,
                            "pan": donor_options[selected_donor].get("PAN", "")
                        }
                        
                        try:
                            # Generate receipt
                            generate_receipt(donor_data, receipt_path, organization_id=organization_id)
                            
                            # Send email if requested
                            if send_receipt and donor_options[selected_donor].get("Email"):
                                status_text.text("Sending email receipt...")
                                progress_bar.progress(90)
                                email_sent = send_email_receipt(
                                    to_email=donor_options[selected_donor]["Email"],
                                    donor_name=donor_options[selected_donor]["Full Name"],
                                    receipt_path=receipt_path,
                                    amount=donor_data["amount"],
                                    receipt_number=receipt_number,
                                    purpose=donor_data["purpose"],
                                    payment_mode=payment_method
                                )
                                if email_sent:
                                    success_message += "\n📧 Receipt sent via email!"
                                else:
                                    success_message += "\n⚠️ Failed to send receipt via email."
                            
                            # Complete progress
                            status_text.text("Payment recorded successfully!")
                            progress_bar.progress(100)
                            
                            # Store receipt info in session state for access outside form
                            st.session_state.last_receipt_path = receipt_path
                            st.session_state.last_receipt_number = receipt_number
                            st.session_state.last_success_message = success_message
                            st.session_state.last_donation_data = donor_data
                            
                            # Rerun to show the download button outside form
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Failed to generate receipt: {str(e)}")
                            receipt_path = None
                    else:
                        st.error("❌ Failed to record donation. Please try again.")

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

    # Show receipt download options outside the form if a receipt was generated
    if 'last_receipt_path' in st.session_state and st.session_state.last_receipt_path:
        st.success(st.session_state.last_success_message)
        
        with open(st.session_state.last_receipt_path, "rb") as file:
            st.download_button(
                label="📄 Download Receipt",
                data=file,
                file_name=f"{st.session_state.last_receipt_number.replace('/', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

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

def show_donation_form():
    try:
        # Get donor options
        donor_options = get_donor_options()
        if not donor_options:
            st.error("No donors found. Please add a donor first.")
            return

        # Create donor selection
        donor_names = [f"{donor['Full Name']} ({donor['Email']})" for donor in donor_options]
        selected_donor = st.selectbox("Select Donor", range(len(donor_names)), format_func=lambda x: donor_names[x])

        # Get active recurring plans for selected donor
        recurring_plans = get_active_recurring_donations(donor_options[selected_donor]["id"], organization_id=organization_id)
        
        # Initialize session state for recurring fields if not exists
        if 'show_recurring_fields' not in st.session_state:
            st.session_state.show_recurring_fields = False
        if 'selected_recurring_plan' not in st.session_state:
            st.session_state.selected_recurring_plan = None

        # Show recurring plans if they exist
        if recurring_plans:
            st.info("This donor has active recurring donation plans:")
            
            # Create radio options for recurring plans
            plan_options = ["One Time Payment"]  # Add one-time payment option
            for plan in recurring_plans:
                plan_text = f"{format_amount(plan['Amount'])} {plan['Frequency']} ({plan['Purpose']})"
                plan_options.append(plan_text)
            
            selected_option = st.radio(
                "Select Payment Type",
                plan_options,
                key="payment_type"
            )
            
            # Handle selection
            if selected_option == "One Time Payment":
                st.session_state.selected_recurring_plan = None
                # Show option to set up new recurring
                setup_recurring = st.checkbox("Set up recurring donation?", key="setup_new_recurring")
                st.session_state.show_recurring_fields = setup_recurring
            else:
                # Find the selected plan
                selected_plan_idx = plan_options.index(selected_option) - 1  # Subtract 1 for "One Time Payment"
                st.session_state.selected_recurring_plan = recurring_plans[selected_plan_idx]
                st.session_state.show_recurring_fields = False
        else:
            # No recurring plans exist, show option to set up recurring
            st.session_state.selected_recurring_plan = None
            setup_recurring = st.checkbox("Set up recurring donation?", key="setup_new_recurring")
            st.session_state.show_recurring_fields = setup_recurring

        # Rest of the form
        with st.form("donation_form", clear_on_submit=False):
            # Only show amount field for non-recurring payments
            if not st.session_state.selected_recurring_plan:
                amount = st.number_input("Amount (₹)", min_value=0.0, format="%f")
            else:
                amount = st.session_state.selected_recurring_plan['Amount']
                st.info(f"Amount: {format_amount(amount)} (as per recurring plan)")

            # Date picker
            date = st.date_input("Date", datetime.now())

            # Purpose selection
            if not st.session_state.selected_recurring_plan:
                purpose_options = ["General Fund", "Corpus Fund", "Other"]
                selected_purpose = st.selectbox("Purpose", purpose_options)
                purpose = st.text_input("Specify Purpose") if selected_purpose == "Other" else selected_purpose
            else:
                purpose = st.session_state.selected_recurring_plan['Purpose']
                st.info(f"Purpose: {purpose} (as per recurring plan)")

            # Payment method
            payment_method = st.selectbox("Payment Method", ["Cash", "Cheque", "Card / Net Banking", "UPI"])
            
            # Additional fields based on payment method
            reference_no = None
            bank_name = None
            
            if payment_method in ["Cheque", "Card / Net Banking"]:
                col1, col2 = st.columns(2)
                with col1:
                    reference_no = st.text_input(f"{payment_method} Number")
                with col2:
                    bank_name = st.text_input("Bank Name")
            elif payment_method == "UPI":
                reference_no = st.text_input("Transaction Reference Number")

            # Show recurring donation fields if setting up new recurring
            if st.session_state.show_recurring_fields:
                st.markdown("### Recurring Donation Setup")
                recurring_frequency = st.selectbox("Frequency", ["Monthly", "Quarterly", "Yearly"])
                start_date = st.date_input("Start Date", date)
                next_due = calculate_next_due_date(start_date, recurring_frequency)
                st.info(f"Next due date will be: {next_due}")

            # Single submit button with clear styling
            submitted = st.form_submit_button(
                "💰 Record Payment",
                type="primary",
                use_container_width=True
            )

            if submitted:
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

                    if payment_method in ["Cheque", "Card / Net Banking"]:
                        if not reference_no or not bank_name:
                            st.error(f"Please enter both {payment_method} number and bank name")
                            return
                        payment_details.update({
                            "reference_no": reference_no,
                            "bank_name": bank_name
                        })
                    elif payment_method == "UPI":
                        if not reference_no:
                            st.error("Please enter the transaction reference number")
                            return
                        payment_details["reference_no"] = reference_no

                    # Generate receipt number and path
                    status_text.text("Generating receipt number...")
                    progress_bar.progress(40)
                    receipt_number = generate_receipt_number(organization_id=organization_id)
                    receipt_path = get_organization_receipt_path(organization_id, receipt_number)
                    
                    # Add receipt info to payment details
                    payment_details["receipt_number"] = receipt_number
                    payment_details["receipt_path"] = receipt_path
                    
                    status_text.text("Recording payment...")
                    progress_bar.progress(60)
                    
                    if st.session_state.get('selected_recurring_plan'):
                        # Record recurring payment
                        plan = st.session_state.selected_recurring_plan
                        result = record_recurring_payment(
                            donor_id=donor_options[selected_donor]["id"],
                            recurring_id=plan['id'],
                            amount=plan['Amount'],
                            payment_date=date,
                            payment_details=payment_details,
                            organization_id=organization_id
                        )

                        if result:
                            success_message = "✅ Recurring payment recorded successfully!"
                    else:
                        # Record regular donation
                        result = record_donation(
                            donor_id=donor_options[selected_donor]["id"],
                            amount=amount,
                            date=date.isoformat(),
                            purpose=purpose if selected_purpose == "Other" else selected_purpose,
                            payment_method=payment_method,
                            payment_details=payment_details,
                            is_recurring=st.session_state.show_recurring_fields,
                            recurring_frequency=recurring_frequency if st.session_state.show_recurring_fields else None,
                            start_date=start_date.isoformat() if st.session_state.show_recurring_fields else None,
                            next_due_date=next_due.isoformat() if st.session_state.show_recurring_fields else None,
                            recurring_status="Active" if st.session_state.show_recurring_fields else None,
                            linked_to_recurring=False,
                            is_scheduled_payment=False,
                            organization_id=organization_id
                        )

                        if result:
                            success_message = "✅ Donation recorded successfully!"
                            if st.session_state.show_recurring_fields:
                                success_message += "\n🔄 Recurring donation has been set up!"
                    
                    if result:
                        status_text.text("Generating receipt...")
                        progress_bar.progress(80)
                        
                        donor_data = {
                            "name": donor_options[selected_donor]["Full Name"],
                            "amount": plan['Amount'] if st.session_state.get('selected_recurring_plan') else amount,
                            "date": date.strftime("%Y-%m-%d"),
                            "receipt_number": receipt_number,
                            "purpose": plan.get('Purpose', 'General Fund') if st.session_state.get('selected_recurring_plan') else (purpose if selected_purpose == "Other" else selected_purpose),
                            "payment_mode": payment_method,
                            "pan": donor_options[selected_donor].get("PAN", "")
                        }
                        
                        try:
                            # Generate receipt
                            generate_receipt(donor_data, receipt_path, organization_id=organization_id)
                            
                            # Send email if requested
                            if send_receipt and donor_options[selected_donor].get("Email"):
                                status_text.text("Sending email receipt...")
                                progress_bar.progress(90)
                                email_sent = send_email_receipt(
                                    to_email=donor_options[selected_donor]["Email"],
                                    donor_name=donor_options[selected_donor]["Full Name"],
                                    receipt_path=receipt_path,
                                    amount=donor_data["amount"],
                                    receipt_number=receipt_number,
                                    purpose=donor_data["purpose"],
                                    payment_mode=payment_method
                                )
                                if email_sent:
                                    success_message += "\n📧 Receipt sent via email!"
                                else:
                                    success_message += "\n⚠️ Failed to send receipt via email."
                            
                            # Complete progress
                            status_text.text("Payment recorded successfully!")
                            progress_bar.progress(100)
                            
                            # Store receipt info in session state for access outside form
                            st.session_state.last_receipt_path = receipt_path
                            st.session_state.last_receipt_number = receipt_number
                            st.session_state.last_success_message = success_message
                            st.session_state.last_donation_data = donor_data
                            
                            # Rerun to show the download button outside form
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Failed to generate receipt: {str(e)}")
                            receipt_path = None
                    else:
                        st.error("❌ Failed to record donation. Please try again.")

                except Exception as e:
                    st.error(f"An error occurred while recording the donation: {str(e)}")
    except Exception as e:
        st.error(f"An error occurred while loading the form: {str(e)}")

# ... rest of the existing code ...