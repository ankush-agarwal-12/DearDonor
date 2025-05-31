import streamlit as st
from modules import add_donor, dashboard, donor_info, record_donation,view_receipts

# st.set_page_config(page_title="DearDonor - Nonprofit Management", layout="wide")

# Sidebar Navigation
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", ["Home", "Add Donor", "Record Donation", "Dashboard", "Donor Info","View Receipts"])

# Page Routing
if choice == "Home":
    st.title("Welcome to DearDonor")
    st.write("Your nonprofit management tool. Use the sidebar to navigate.")

elif choice == "Add Donor":
    add_donor.new_donor_view()

elif choice == "Record Donation":
    record_donation.record_donation_view()

elif choice == "Dashboard":
    dashboard.show_dashboard()

elif choice == "Donor Info":
    donor_info.view_donor_profile()

elif choice == "View Receipts":
    view_receipts.st_main()