import streamlit as st
from modules.airtable_utils import add_donor

def new_donor_view():
    st.title("New Donor")

    with st.form("new_donor_form"):
        col1, col2 = st.columns(2)
        with col1:
            donor_name = st.text_input("Donor Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
        with col2:
            address = st.text_input("Address")
            pan_number = st.text_input("PAN Number")
            is_company = st.toggle("Company")

        submitted = st.form_submit_button("Save Donor")

        if submitted:
            if not donor_name or not email:
                st.warning("Please fill all required fields (Donor Name, Email).")
                return

            success, donor_id = add_donor(
                name=donor_name,
                email=email,
                phone=phone,
                address=address,
                pan=pan_number,
                company=is_company
            )

            if success:
                st.success("✅ Donor profile created successfully!")
                st.info("You can now record donations for this donor from the 'Record Donation' page.")
            else:
                st.error("Failed to save donor.")