print("🔄 LOADING airtable_utils.py")
# modules/airtable_utils.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
API_KEY = os.getenv("AIRTABLE_API_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("DONOR_TABLE_NAME")

AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
AIRTABLE_URL_DONATIONS = f"https://api.airtable.com/v0/{BASE_ID}/Donations"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ✅ Donor creation
def add_donor(name, email, phone, address, pan, company, mode, amount, date, email_flag, whatsapp_flag):
    data = {
    "Full Name": name,
    "Email": email,
    "Phone Number": phone,
    "Address": address,
    "PAN": pan,
    "Organization": "Company" if company else "Individual",
}

    response = requests.post(AIRTABLE_URL, headers=HEADERS, json={"fields": data})
    
    print("📤 Sent to Airtable:", data)
    print("📥 Airtable response:", response.status_code, response.text)

    return response.status_code == 200
# ✅ Optional: used by other views
def fetch_donors():
    response = requests.get(AIRTABLE_URL_DONORS, headers=HEADERS)
    if response.status_code != 200:
        return []
    
    donor_list = []
    for r in response.json().get("records", []):
        fields = r.get("fields", {})
        donor_list.append({
            "id": r.get("id"),
            "Full Name": fields.get("Full Name", ""),
            "Email": fields.get("Email", ""),
            "Phone": fields.get("Phone Number", ""),
            "Address": fields.get("Address", ""),
            "PAN": fields.get("PAN", ""),
            "Organization": fields.get("Organization", "")
        })
    return donor_list

def add_donation(donor_id, amount, date, purpose, mode, email_flag, whatsapp_flag):
    data = {
        "fields": {
            "Donor": [donor_id],  # Linked field in Airtable
            "Donation Amount": float(amount),
            "Donation Date": str(date),
            "Donation Purpose": purpose,
            "Donation Mode": mode,
            "Send Email Receipt": email_flag,
            "Send WhatsApp Confirmation": whatsapp_flag,
        }
    }

    response = requests.post(AIRTABLE_URL_DONATIONS, headers=HEADERS, json={"fields": data})

    print("📤 Sent to Airtable Donations:", data)
    print("📥 Airtable response:", response.status_code, response.text)

    return response.status_code == 200

def update_donor_info(record_id, name, email, phone, address, pan, org):
    data = {
        "Full Name": name,
        "Email": email,
        "Phone Number": phone,
        "Address": address,
        "PAN": pan,
        "Organization": org
    }
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
    response = requests.patch(url, headers=HEADERS, json={"fields": data})
    return response.status_code == 200

def fetch_all_donations():
    response = requests.get(AIRTABLE_URL_DONATIONS, headers=HEADERS)
    if response.status_code != 200:
        return []

    donations = []
    for r in response.json().get("records", []):
        fields = r.get("fields", {})
        donations.append({
            "Donor": fields.get("Donor", [""])[0],
            "Amount": fields.get("Donation Amount", 0),
            "Date": fields.get("Donation Date", ""),
            "Purpose": fields.get("Donation Purpose", ""),
            "Mode": fields.get("Mode of Payment", ""),
            "Receipt": fields.get("Receipt URL", "")
        })
    return donations

import requests
from .config import AIRTABLE_URL_DONATIONS, HEADERS

def get_donor_donations(donor_id):
    params = {
        "filterByFormula": f"RECORD_ID(Donor) = '{donor_id}'"
    }
    print("💬 Donor ID used in filter:", donor_id)
    response = requests.get(AIRTABLE_URL_DONATIONS, headers=HEADERS, params=params)
    print("🧾 Raw Airtable response:", response.json())
    if response.status_code != 200:
        return []

    records = response.json().get("records", [])
    result = []
    for r in records:
        f = r.get("fields", {})
        result.append({
            "Amount": f.get("Donation Amount", 0),
            "Date": f.get("Donation Date", ""),
            "Purpose": f.get("Donation Purpose", ""),
            "Mode": f.get("Mode of Payment", ""),
            "Receipt": f.get("Receipt URL", "")
        })
    
    print("🐝 Donation records fetched:", result)
    return result
