import streamlit as st
import re
from modules.supabase_utils import add_donor, fetch_donors

def validate_phone_number(phone):
    """
    Validate Indian phone number format
    Accepts formats like: +91-9876543210, 9876543210, 09876543210, +919876543210
    """
    # Remove all non-digit characters except +
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Check if it starts with +91 (India country code)
    if cleaned_phone.startswith('+91'):
        cleaned_phone = cleaned_phone[3:]  # Remove +91
    
    # Check if it starts with 91 (without +)
    elif cleaned_phone.startswith('91'):
        cleaned_phone = cleaned_phone[2:]  # Remove 91
    
    # Check if it starts with 0
    elif cleaned_phone.startswith('0'):
        cleaned_phone = cleaned_phone[1:]  # Remove leading 0
    
    # Validate the remaining digits
    if len(cleaned_phone) == 10 and cleaned_phone.isdigit():
        # Check if it starts with valid Indian mobile prefixes
        valid_prefixes = ['6', '7', '8', '9']  # Valid starting digits for Indian mobile numbers
        if cleaned_phone[0] in valid_prefixes:
            return True, cleaned_phone
    
    return False, None

def format_phone_number(phone):
    """Format phone number to standard Indian format (+91-XXXXXXXXXX)"""
    is_valid, cleaned_phone = validate_phone_number(phone)
    if is_valid:
        return f"+91-{cleaned_phone}"
    return phone

def add_donor_view():
    st.title("➕ Add New Donor")
    
    with st.form("add_donor_form"):
        full_name = st.text_input("Full Name*")
        phone = st.text_input("Phone Number*", placeholder="e.g., 9876543210 or +91-9876543210")
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
                st.error("Please fill in the required fields marked with *")
                return
            
            # Validate phone number
            is_valid_phone, cleaned_phone = validate_phone_number(phone)
            if not is_valid_phone:
                st.error("❌ Invalid phone number format. Please enter a valid 10-digit Indian mobile number.")
                st.info("💡 **Valid formats:** 9876543210, +91-9876543210, 09876543210, +919876543210")
                return
                
            try:
                # Format phone number to standard format
                formatted_phone = format_phone_number(phone)
                
                result = add_donor(
                    full_name=full_name,
                    phone=formatted_phone,
                    email=email,
                    address=address,
                    pan=pan,
                    donor_type=donor_type
                )
                
                if result:
                    st.success("✅ Donor added successfully!")
                    # Check for duplicate phone number
                    if formatted_phone:
                        donors = fetch_donors()
                        for donor in donors:
                            if donor["Phone"] == formatted_phone and donor["Full Name"] != full_name:
                                st.warning(f"This number is also registered to: {donor['Full Name']}.")
                                break
                    # Clear form
                    st.empty()
                else:
                    st.error("❌ Failed to add donor. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")