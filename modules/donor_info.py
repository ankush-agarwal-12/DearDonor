import streamlit as st
from modules.airtable_utils import fetch_donors, get_donor_donations

def view_donor_profile():
    st.title("🔍 Donor Information")

    donors = fetch_donors()
    donor_map = {f"{d['Full Name']} ({d['Email']})": d for d in donors}

    selected = st.selectbox("Select Donor", list(donor_map.keys()))
    donor = donor_map[selected]

    st.markdown(f"**Name:** {donor.get('Full Name', '-')}")
    st.markdown(f"**Email:** {donor.get('Email', '-')}")
    st.markdown(f"**Phone:** {donor.get('Phone Number', '-')}")
    st.markdown(f"**Address:** {donor.get('Address', '-')}")
    st.markdown(f"**PAN:** {donor.get('PAN', '-')}")
    st.markdown(f"**Organization:** {donor.get('Organization', '-')}")

    st.subheader("💸 Donation History")
    donations = get_donor_donations(donor["id"])
    st.write("Debug ID:", donor.get("id"))
    if donations:
        for d in donations:
            st.markdown(f"- ₹{d['Amount']} on {d['Date']} for {d['Purpose']}")
    else:
        st.info("No donations recorded yet.")