import streamlit as st
from modules.airtable_utils import fetch_donors, add_donation
from modules.generate_receipt import generate_receipt
from modules.email_utils import send_email_receipt
from modules.settings import load_settings
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def record_donation_view():
    st.title("💰 Record Donation")

    donors = fetch_donors()
    if not donors:
        st.error("No donors found. Please add donors first.")
        return

    donor_map = {f"{d['Full Name']} ({d['Email']})": d for d in donors}
    selected = st.selectbox(
        "Select Donor",
        options=["Select a donor..."] + list(donor_map.keys()),
        index=0
    )

    if selected == "Select a donor...":
        st.warning("Please select a donor.")
        return

    donor = donor_map[selected]

    # Payment method selection outside form
    payment_method = st.selectbox(
        "Payment Method",
        ["Cash", "Cheque", "UPI", "Bank Transfer", "Credit Card", "Other"]
    )
    
    # Additional fields based on payment method outside form
    payment_details = {}
    if payment_method == "Cheque":
        payment_details["cheque_no"] = st.text_input("Cheque Number")
        payment_details["bank_name"] = st.text_input("Bank Name")
    elif payment_method in ["Bank Transfer", "UPI"]:
        payment_details["transaction_id"] = st.text_input("Transaction ID")
        payment_details["bank_name"] = st.text_input("Bank Name")

    # Load predefined purposes from settings
    settings = load_settings()
    predefined_purposes = settings.get("donation_purposes", [])
    
    # Add "Other" option to predefined purposes
    purpose_options = predefined_purposes + ["Other"]
    selected_purpose = st.selectbox("Select Purpose", purpose_options)
    
    # Initialize purpose variable
    purpose = selected_purpose
    
    # Show text input if "Other" is selected
    if selected_purpose == "Other":
        purpose = st.text_input("Enter Custom Purpose", key="custom_purpose")

    # Create form for donation details
    with st.form("donation_form"):
        amount = st.number_input("Amount (₹)", min_value=1.0, step=100.0)
        date = st.date_input("Date")

        # Communication preferences
        st.subheader("Communication Preferences")
        send_email = st.checkbox("Send Email Receipt", value=True)
        send_whatsapp = st.checkbox("Send WhatsApp Confirmation")

        submitted = st.form_submit_button("Record Donation")

    if submitted:
        try:
            # Validate payment details
            if payment_method == "Cheque" and (not payment_details.get("cheque_no") or not payment_details.get("bank_name")):
                st.error("Please fill in all cheque details.")
                return
            elif payment_method in ["Bank Transfer", "UPI"] and (not payment_details.get("transaction_id") or not payment_details.get("bank_name")):
                st.error("Please fill in all transaction details.")
                return
                
            # Validate purpose
            if selected_purpose == "Other" and not purpose.strip():
                st.error("Please enter a custom purpose for the donation.")
                return

            # Create receipts directory if it doesn't exist
            os.makedirs("receipts", exist_ok=True)
            
            # Generate receipt filename with timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            receipt_filename = f"{donor['Full Name'].replace(' ', '_')}_{timestamp}.pdf"
            receipt_path = f"receipts/{receipt_filename}"
            
            # Generate receipt
            generate_receipt(
                donor_name=donor['Full Name'],
                amount=amount,
                date=date.strftime("%Y-%m-%d"),
                purpose=purpose,
                mode=payment_method,
                receipt_path=receipt_path,
                payment_details=payment_details
            )

            # Add donation to Airtable using the old function signature
            success = add_donation(
                donor_id=donor["id"],
                amount=amount,
                date=date,
                purpose=purpose,
                mode=payment_method,
                email_flag=send_email,
                whatsapp_flag=send_whatsapp,
                receipt_path=receipt_path
            )
            
            if success:
                st.success("✅ Donation recorded successfully!")
                
                # Send email if requested
                if send_email and donor.get('Email'):
                    email_sent = send_email_receipt(
                        to_email=donor['Email'],
                        donor_name=donor['Full Name'],
                        receipt_path=receipt_path,
                        amount=amount
                    )
                    if email_sent:
                        st.success("✅ Email sent with receipt")
                    else:
                        st.warning("⚠️ Failed to send email")
                
                # Send WhatsApp if requested
                if send_whatsapp and donor.get('Phone'):
                    st.info("WhatsApp integration coming soon!")
            else:
                st.error("❌ Failed to record donation")
                
        except Exception as e:
            st.error(f"❌ Error recording donation: {str(e)}")
            raise e  # Re-raise the exception for debugging