import streamlit as st
from modules.supabase_utils import add_donor, fetch_donors

def add_donor_view():
    st.title("➕ Add New Donor")
    
    with st.form("add_donor_form"):
        full_name = st.text_input("Full Name*")
        phone = st.text_input("Phone Number*")
        email = st.text_input("Email")
        address = st.text_area("Address")
        pan = st.text_input("PAN Number")
        donor_type = st.selectbox(
            "Donor Type",
            ["Individual", "Company"],
            index=0
        )
        
        submitted = st.form_submit_button("Add Donor")
        
        if submitted:
            if not full_name or not phone:
                st.error("Please fill in the required field marked with *")
                return
                
            try:
                result = add_donor(
                    full_name=full_name,
                    phone=phone,
                    email=email,
                    address=address,
                    pan=pan,
                    donor_type=donor_type
                )
                
                if result:
                    st.success("✅ Donor added successfully!")
                    # Check for duplicate phone number
                    if phone:
                        donors = fetch_donors()
                        for donor in donors:
                            if donor["Phone"] == phone and donor["Full Name"] != full_name:
                                st.warning(f"This number is also registered to : {donor['Full Name']}.")
                                break
                    # Clear form
                    st.empty()
                else:
                    st.error("❌ Failed to add donor. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")