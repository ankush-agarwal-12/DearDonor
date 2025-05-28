
print("🔄 LOADING add_donor.py")

import streamlit as st
from modules.airtable_utils import add_donor
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
            donation_amount = st.number_input("Donation Amount", min_value=0.0, step=10.0)
            donation_date = st.date_input("Donation Date", value=datetime.today())

        send_email = st.toggle("Send Email")
        send_whatsapp = st.toggle("Send WhatsApp")
        is_company = st.toggle("Company")
        pan_number = st.text_input("PAN Number")

        submitted = st.form_submit_button("Save Donor")

        if submitted:
            success = add_donor(
                name=donor_name,
                email=email,
                phone=phone,
                address=address,
                pan=pan_number,
                company=is_company,
                mode=donation_mode,
                amount=donation_amount,
                date=donation_date,
                email_flag=send_email,
                whatsapp_flag=send_whatsapp
            )

            if success:
                st.success("Donor saved successfully!")

                # Generate receipt
                receipt_path = f"receipts/{donor_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                generate_receipt(donor_name, donation_amount, donation_date, "N/A", donation_mode, receipt_path)
                print("📄 Receipt generated at:", receipt_path)

                # Try sending email if requested
                if send_email:
                    if os.path.exists(receipt_path):
                        try:
                            send_email_receipt(email, donor_name, receipt_path)
                            st.success("📧 Email sent with receipt!")
                        except Exception as e:
                            print("❌ Email sending failed:", e)
                            st.error("Email failed to send. Please check email settings.")
                    else:
                        print("❌ Receipt file not found:", receipt_path)
                        st.error("Receipt file missing. Could not send email.")
            else:
                st.error("Something went wrong while saving donor data.")

