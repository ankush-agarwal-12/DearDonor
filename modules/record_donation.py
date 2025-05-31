import streamlit as st
from modules.airtable_utils import fetch_donors, add_donation
from modules.generate_receipt import generate_receipt
from modules.email_utils import send_email_receipt
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def record_donation_view():
    st.title("📝 Record New Donation")

    print("🔍 Fetching donors")
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
        st.warning("Please select a donor to proceed.")
        return

    donor = donor_map[selected]
    donor_id = donor.get("id")
    print(f"📋 Selected donor: {donor['Full Name']}, ID={donor_id}")

    with st.form("record_donation"):
        amount = st.number_input("Donation Amount (₹)", min_value=1.0, step=1.0)
        date = st.date_input("Donation Date", datetime.today())
        purpose = st.text_input("Purpose of Donation")
        mode = st.selectbox("Donation Mode", ["UPI", "Bank Transfer", "Cash", "Online", "Cheque"])
        send_email = st.toggle("Send Email Receipt")
        send_whatsapp = st.toggle("Send WhatsApp Confirmation")
        submitted = st.form_submit_button("➕ Record Donation")

        if submitted:
            if not amount or not purpose:
                st.warning("Please fill all required fields.")
                return

            receipt_filename = f"{donor['Full Name'].replace(' ', '_')}_{date.strftime('%Y%m%d')}.pdf"
            receipt_path = f"receipts/{receipt_filename}"
            os.makedirs("receipts", exist_ok=True)
            print(f"📄 Generating receipt at: {receipt_path}")
            generate_receipt(donor['Full Name'], amount, date.strftime('%Y-%m-%d'), purpose, mode, receipt_path)

            print(f"📝 Adding donation for Donor ID: {donor_id}, Purpose: {purpose}")
            success = add_donation(donor_id, amount, date, purpose, mode, send_email, send_whatsapp, receipt_path)

            if success:
                st.success("✅ Donation recorded successfully!")
                st.markdown(f"**Donor:** {donor['Full Name']}  \n**Amount:** ₹{amount}  \n**Date:** {date.strftime('%Y-%m-%d')}  \n**Purpose:** {purpose}")
                st.info(f"📝 Receipt generated: `{receipt_filename}`")

                if send_email:
                    if os.path.exists(receipt_path):
                        try:
                            print(f"📧 Sending email to: {donor['Email']}")
                            send_email_receipt(donor['Email'], donor['Full Name'], receipt_path)
                            st.success("📧 Email sent with receipt!")
                        except Exception as e:
                            st.error(f"❌ Email sending failed: {e}")
                    else:
                        st.error("❌ Receipt file not found.")
            else:
                st.error("Failed to record donation.")