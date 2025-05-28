print("🔄 LOADING vire_receipts.py")
import streamlit as st
from airtable_utils import fetch_all_donations
from datetime import datetime

st.title("📄 All Donation Receipts")

# Load all donations
donations = fetch_all_donations()

if not donations:
    st.warning("No donation records found.")
    st.stop()

# Sidebar filters (UI retained but logic skipped for now)
st.sidebar.header("Filter Donations")
st.sidebar.text_input("Search Donor Name")  # donor_filter = ...
st.sidebar.selectbox("Payment Mode", ["All", "UPI", "Cash", "Bank Transfer", "Cheque"])  # mode_filter = ...
st.sidebar.date_input("Start Date", value=datetime(2024, 1, 1))  # start_date = ...
st.sidebar.date_input("End Date", value=datetime.now())  # end_date = ...

# Prepare unfiltered list
filtered = []
for d in donations:
    try:
        name = d.get("Donor Name", "")
        amount = d.get("Amount", 0)
        date_str = d.get("Date", "")
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        mode = d.get("Payment Mode", "")
        purpose = d.get("Purpose", "")
        receipt_url = d.get("Receipt", "")  # NOTE: update if your field name is "Receipt URL"
        
        filtered.append({
            "Donor": name,
            "Amount": amount,
            "Date": date_str,
            "Mode": mode,
            "Purpose": purpose,
            "Receipt URL": receipt_url
        })
    except Exception:
        continue

# Display all donations
st.write(f"Showing {len(filtered)} donation(s)")
for record in filtered:
    with st.expander(f"₹{record['Amount']} – {record['Donor']} on {record['Date']}"):
        st.write(f"**Purpose:** {record['Purpose']}")
        st.write(f"**Payment Mode:** {record['Mode']}")
        if record["Receipt URL"]:
            st.markdown(f"📄 [View Receipt PDF]({record['Receipt URL']})", unsafe_allow_html=True)
        else:
            st.warning("No receipt found.")
