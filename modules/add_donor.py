import streamlit as st
from modules.airtable_utils import add_donor, add_donation
from datetime import datetime
from modules.generate_receipt import generate_receipt
from modules.email_utils import send_email_receipt
import os

def new_donor_view():
    st.title("New Donor")

    with st.form("new_donor_form"):
        col1, col2 = st.columns(2)
        with col1:
            donor_name = st.text_input("Donor Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            donation_mode = st.selectbox("Donation Mode", ["Cash", "UPI", "Bank Transfer", "Cheque"])
        with col2:
            address = st.text_input("Address")
            donation_amount = st.number_input("Donation Amount", min_value=1.0, step=10.0)
            donation_date = st.date_input("Donation Date", value=datetime.today())

        send_email = st.toggle("Send Email")
        send_whatsapp = st.toggle("Send WhatsApp")
        is_company = st.toggle("Company")
        pan_number = st.text_input("PAN Number")

        submitted = st.form_submit_button("Save Donor")

        if submitted:
            if not donor_name or not email or not donation_amount:
                st.warning("Please fill all required fields (Donor Name, Email, Donation Amount).")
                return

            print(f"📝 Adding new donor: {donor_name}, {email}")
            success, donor_id = add_donor(
                name=donor_name,
                email=email,
                phone=phone,
                address=address,
                pan=pan_number,
                company=is_company
            )

            if success:
                receipt_filename = f"{donor_name.replace(' ', '_')}_{donation_date.strftime('%Y%m%d')}.pdf"
                receipt_path = f"receipts/{receipt_filename}"
                os.makedirs("receipts", exist_ok=True)
                print(f"📄 Generating receipt at: {receipt_path}")
                generate_receipt(donor_name, donation_amount, donation_date.strftime('%Y-%m-%d'), "Initial Donation", donation_mode, receipt_path)
                
                print(f"📝 Adding donation for Donor ID: {donor_id}")
                donation_success = add_donation(
                    donor_id=donor_id,
                    amount=donation_amount,
                    date=donation_date,
                    purpose="Initial Donation",
                    mode=donation_mode,
                    email_flag=send_email,
                    whatsapp_flag=send_whatsapp,
                    receipt_path=receipt_path
                )

                if donation_success:
                    st.success("Donor and donation saved successfully!")
                    st.info(f"📄 Receipt generated at: {receipt_path}")

                    if send_email:
                        if os.path.exists(receipt_path):
                            try:
                                print(f"📧 Sending email to: {email}")
                                send_email_receipt(email, donor_name, receipt_path)
                                st.success("📧 Email sent with receipt!")
                            except Exception as e:
                                st.error(f"❌ Email sending failed: {e}")
                        else:
                            st.error("❌ Receipt file not found.")
                else:
                    st.error("Donor saved, but failed to save donation.")
            else:
                st.error("Failed to save donor.")