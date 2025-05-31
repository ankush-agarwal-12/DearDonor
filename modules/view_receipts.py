import streamlit as st
from modules.airtable_utils import fetch_all_donations
from datetime import datetime
import os

def st_main():
    st.title("📄 All Donation Receipts")

    donations = fetch_all_donations()
    if not donations:
        st.warning("No donation records found.")
        return

    st.sidebar.header("Filter Donations")
    donor_filter = st.sidebar.text_input("Search Donor ID")
    mode_filter = st.sidebar.selectbox("Donation Mode", ["All", "UPI", "Cash", "Bank Transfer", "Online", "Cheque"])
    start_date = st.sidebar.date_input("Start Date", value=datetime(2024, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

    filtered = []
    for d in donations:
        try:
            donor_id = d.get("Donor", "")
            amount = float(d.get("Amount", 0))
            date_str = d.get("Date", "")
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            mode = d.get("Mode", "")
            purpose = d.get("Purpose", "")
            receipt_path = d.get("Receipt", "")

            if donor_filter and donor_id and donor_filter.lower() not in donor_id.lower():
                continue
            if mode_filter != "All" and mode != mode_filter:
                continue
            if date < start_date or date > end_date:
                continue

            filtered.append({
                "Donor": donor_id,
                "Amount": amount,
                "Date": date_str,
                "Mode": mode,
                "Purpose": purpose,
                "Receipt Path": receipt_path
            })
        except Exception as e:
            print(f"Error processing donation record: {e}")
            continue

    st.write(f"Showing {len(filtered)} donation(s)")
    for record in filtered:
        with st.expander(f"₹{record['Amount']}: {record['Purpose']} on {record['Date']}"):
            st.write(f"**Donor ID:** {record['Donor']}")
            st.write(f"**Purpose:** {record['Purpose']}")
            st.write(f"**Mode:** {record['Mode']}")
            if record["Receipt Path"] and os.path.exists(record["Receipt Path"]):
                with open(record["Receipt Path"], "rb") as f:
                    st.download_button(
                        label="📄 Download Receipt",
                        data=f,
                        file_name=os.path.basename(record["Receipt Path"]),
                        mime="application/pdf",
                        key=f"download_{record['Donor']}_{record['Date']}_{record['Purpose']}"
                    )
            else:
                st.warning(f"No valid receipt found for {record['Purpose']}.")