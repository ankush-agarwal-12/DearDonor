import streamlit as st
import json
import os

SETTINGS_FILE = "config/settings.json"

def ensure_settings_file():
    """Ensure settings file exists with default values"""
    os.makedirs("config", exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        default_settings = {
            "donation_purposes": [
                "Corpus Fund",
                "General Operational Fund",
                "Construction Fund",
                "Education Fund",
                "Healthcare Fund"
            ]
        }
        save_settings(default_settings)
    return load_settings()

def load_settings():
    """Load settings from file"""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return ensure_settings_file()

def save_settings(settings):
    """Save settings to file"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def settings_page():
    st.title("⚙️ Settings")
    
    settings = load_settings()
    
    st.header("Common Donation Purposes")
    st.markdown("""
    Define common donation purposes to avoid repeated typing in the donation form. 
    These will appear as quick selections when recording donations.
    """)
    
    # Display current purposes
    st.subheader("Current Purposes")
    purposes = settings.get("donation_purposes", [])
    
    # Edit existing purposes
    updated_purposes = []
    for i, purpose in enumerate(purposes):
        col1, col2 = st.columns([3, 1])
        with col1:
            updated_purpose = st.text_input(f"Purpose {i+1}", value=purpose, key=f"purpose_{i}")
            if updated_purpose.strip():  # Only add non-empty purposes
                updated_purposes.append(updated_purpose)
        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                continue  # Skip this purpose in updated_purposes
    
    # Add new purpose
    st.subheader("Add New Purpose")
    new_purpose = st.text_input("New Purpose")
    if st.button("Add Purpose") and new_purpose.strip():
        updated_purposes.append(new_purpose)
    
    # Save changes
    if st.button("Save Changes"):
        settings["donation_purposes"] = updated_purposes
        save_settings(settings)
        st.success("✅ Settings saved successfully!")
        st.rerun()  # Refresh the page to show updated list 