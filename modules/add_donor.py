import streamlit as st
from modules.supabase_utils import add_donor

def add_donor_view():
    st.title("➕ Add New Donor")
    
    with st.form("add_donor_form"):
        full_name = st.text_input("Full Name*")
        email = st.text_input("Email*")
        phone = st.text_input("Phone Number")
        address = st.text_area("Address")
        pan = st.text_input("PAN Number")
        donor_type = st.selectbox(
            "Donor Type",
            ["Individual", "Company"],
            index=0
        )
        
        submitted = st.form_submit_button("Add Donor")
        
        if submitted:
            if not full_name or not email:
                st.error("Please fill in all required fields marked with *")
                return
                
            try:
                result = add_donor(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    pan=pan,
                    donor_type=donor_type
                )
                
                if result:
                    st.success("✅ Donor added successfully!")
                    # Clear form
                    st.empty()
                else:
                    st.error("❌ Failed to add donor. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")