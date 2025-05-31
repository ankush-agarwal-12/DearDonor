import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AIRTABLE_API_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("DONOR_TABLE_NAME")

print("DEBUG: AIRTABLE_BASE_ID =", BASE_ID)
print("DEBUG: AIRTABLE_API_TOKEN =", API_KEY)
print("DEBUG: DONOR_TABLE_NAME =", TABLE_NAME)

if not all([API_KEY, BASE_ID, TABLE_NAME]):
    raise ValueError("Missing required environment variables: AIRTABLE_BASE_ID, AIRTABLE_API_TOKEN, or DONOR_TABLE_NAME")

AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
AIRTABLE_URL_DONATIONS = f"https://api.airtable.com/v0/{BASE_ID}/Donations"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def add_donor(name, email, phone, address, pan, company):
    data = {
        "records": [{
            "fields": {
                "Full Name": name,
                "Email": email,
                "Phone Number": phone,
                "Address": address,
                "PAN": pan,
                "Organization": "Company" if company else "Individual",
            }
        }]
    }

    print("📤 Sending to Airtable Donors:", data)
    response = requests.post(AIRTABLE_URL, headers=HEADERS, json=data)
    print("📥 Airtable response:", response.status_code, response.json())
    
    if response.status_code != 200:
        print("ERROR: Failed to add donor:", response.status_code, response.json())
        return False, None
    
    return True, response.json().get("records", [{}])[0].get("id")

def fetch_donors():
    print("🔍 Fetching all donors from Airtable")
    response = requests.get(AIRTABLE_URL, headers=HEADERS)
    if response.status_code != 200:
        print("ERROR: Failed to fetch donors:", response.status_code, response.json())
        return []
    
    donor_list = []
    for r in response.json().get("records", []):
        fields = r.get("fields", {})
        print(f"🐝 Donor record: ID={r.get('id')}, Fields={fields}")
        donor_list.append({
            "id": r.get("id"),
            "Full Name": fields.get("Full Name", ""),
            "Email": fields.get("Email", ""),
            "Phone": fields.get("Phone Number", ""),
            "Address": fields.get("Address", ""),
            "PAN": fields.get("PAN", ""),
            "Organization": fields.get("Organization", "")
        })
    print(f"📊 Fetched {len(donor_list)} donors")
    return donor_list

def add_donation(donor_id, amount, date, purpose, mode, email_flag, whatsapp_flag, receipt_path=""):
    data = {
        "records": [{
            "fields": {
                "Donor": [donor_id],
                "Donation Amount": float(amount),
                "Donation Date": str(date),
                "Donation Purpose": purpose,
                "Donation Mode": mode,
                "Send Email Receipt": email_flag,
                "Send WhatsApp Confirmation": whatsapp_flag,
                "Receipt URL": receipt_path
            }
        }]
    }

    print(f"📤 Sending to Airtable Donations: DonorID={donor_id}, Data={data}")
    response = requests.post(AIRTABLE_URL_DONATIONS, headers=HEADERS, json=data)
    print("📥 Airtable response:", response.status_code, response.json())
    
    if response.status_code != 200:
        print("ERROR: Failed to add donation:", response.status_code, response.json())
        return False
    
    return True

def update_donor_info(record_id, name, email, phone, address, pan, org):
    data = {
        "fields": {
            "Full Name": name,
            "Email": email,
            "Phone Number": phone,
            "Address": address,
            "PAN": pan,
            "Organization": org
        }
    }
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
    print("📤 Sending update to Airtable:", data)
    response = requests.patch(url, headers=HEADERS, json=data)
    print("📥 Airtable response:", response.status_code, response.json())
    
    if response.status_code != 200:
        print("ERROR: Failed to update donor:", response.status_code, response.json())
        return False
    
    return True

def fetch_all_donations():
    print("🔍 Fetching all donations from Airtable")
    response = requests.get(AIRTABLE_URL_DONATIONS, headers=HEADERS)
    if response.status_code != 200:
        print("ERROR: Failed to fetch donations:", response.status_code, response.json())
        return []

    donations = []
    for r in response.json().get("records", []):
        fields = r.get("fields", {})
        print(f"🐝 Donation record: ID={r.get('id')}, Donor={fields.get('Donor')}, Fields={fields}")
        donations.append({
            "id": r.get("id"),
            "Donor": fields.get("Donor", [""])[0] if fields.get("Donor") else "",
            "Amount": fields.get("Donation Amount", 0),
            "Date": fields.get("Donation Date", ""),
            "Purpose": fields.get("Donation Purpose", ""),
            "Mode": fields.get("Donation Mode", ""),
            "Receipt": fields.get("Receipt URL", "")
        })
    print(f"📊 Fetched {len(donations)} donations")
    return donations

def get_donor_donations(donor_id):
    params = {
        "filterByFormula": f"FIND('{donor_id}', ARRAYJOIN({{Donor}}))"
    }
    print("💬 Donor ID used in filter:", donor_id)
    print("💬 Query URL:", f"{AIRTABLE_URL_DONATIONS}?filterByFormula={params['filterByFormula']}")
    response = requests.get(AIRTABLE_URL_DONATIONS, headers=HEADERS, params=params)
    print("🧾 Raw Airtable response:", response.status_code, response.json())
    if response.status_code != 200:
        print("ERROR: Failed to fetch donor donations:", response.status_code, response.json())
        return []

    records = response.json().get("records", [])
    result = []
    for r in records:
        f = r.get("fields", {})
        print(f"🐝 Processing donation: ID={r.get('id')}, Donor={f.get('Donor')}, Fields={f}")
        result.append({
            "Amount": f.get("Donation Amount", 0),
            "Date": f.get("Donation Date", ""),
            "Purpose": f.get("Donation Purpose", ""),
            "Mode": f.get("Donation Mode", ""),
            "Receipt": f.get("Receipt URL", "")
        })
    
    print("🐝 Donation records fetched:", result)
    return result