import os
import requests
from dotenv import load_dotenv
import json
import pandas as pd

load_dotenv()

# Get environment variables with fallbacks
API_KEY = os.getenv("AIRTABLE_API_KEY") or os.getenv("AIRTABLE_API_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
DONORS_TABLE = os.getenv("AIRTABLE_DONORS_TABLE", "Donors")
DONATIONS_TABLE = os.getenv("AIRTABLE_DONATIONS_TABLE", "Donations")

if not API_KEY:
    raise ValueError("Missing Airtable API key. Set AIRTABLE_API_KEY in .env file")
if not BASE_ID:
    raise ValueError("Missing Airtable Base ID. Set AIRTABLE_BASE_ID in .env file")

AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{DONORS_TABLE}"
AIRTABLE_URL_DONATIONS = f"https://api.airtable.com/v0/{BASE_ID}/{DONATIONS_TABLE}"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def add_donor(name, email, phone, address, pan, company):
    """Add a new donor to Airtable"""
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

    try:
        response = requests.post(AIRTABLE_URL, headers=HEADERS, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        return True, response.json().get("records", [{}])[0].get("id")
    except requests.exceptions.RequestException as e:
        print(f"Error adding donor: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False, None

def fetch_donors():
    """Fetch all donors from Airtable"""
    try:
        response = requests.get(AIRTABLE_URL, headers=HEADERS)
        response.raise_for_status()
        
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
    except requests.exceptions.RequestException as e:
        print(f"Error fetching donors: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return []

def add_donation(donor_id=None, amount=None, date=None, purpose=None, mode=None, email_flag=None, whatsapp_flag=None, receipt_path=None, donation_data=None):
    """Add a new donation record to Airtable"""
    try:
        # If donation_data is provided, use it directly
        if donation_data:
            data = {"records": [{"fields": donation_data}]}
        else:
            # Convert date to string if it's a datetime object
            if hasattr(date, 'strftime'):
                date = date.strftime('%Y-%m-%d')
                
            # Create data in the new Airtable format
            data = {
                "records": [{
                    "fields": {
                        "Donor": [donor_id],
                        "Donation Amount": float(amount),
                        "Donation Date": date,
                        "Donation Purpose": purpose,
                        "Donation Mode": mode,
                        "Send Email Receipt": email_flag,
                        "Send WhatsApp Confirmation": whatsapp_flag,
                        "Receipt URL": receipt_path if receipt_path else None
                    }
                }]
            }

        print("Sending donation data:", json.dumps(data, indent=2))
        response = requests.post(
            AIRTABLE_URL_DONATIONS,
            headers=HEADERS,
            json=data
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error adding donation: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

def fetch_all_donations():
    """Fetch all donations from Airtable"""
    try:
        print("Fetching all donations...")
        response = requests.get(AIRTABLE_URL_DONATIONS, headers=HEADERS)
        response.raise_for_status()
        
        print("Response status:", response.status_code)
        data = response.json()
        print("Raw Airtable response:", json.dumps(data, indent=2))

        donations = []
        for r in data.get("records", []):
            fields = r.get("fields", {})
            donor_ids = fields.get("Donor", [])
            if not donor_ids:
                continue
                
            donation = {
                "id": r.get("id"),
                "Donor": donor_ids[0] if donor_ids else "",
                "amount": fields.get("Donation Amount", 0),
                "date": fields.get("Donation Date", ""),
                "payment_method": fields.get("Donation Mode", ""),
                "purpose": fields.get("Donation Purpose", ""),
                "receipt_no": fields.get("Receipt URL", "")
            }
            donations.append(donation)
            
        print(f"Processed {len(donations)} donations")
        print("Sample donation:", json.dumps(donations[0] if donations else {}, indent=2))
        return donations
    except requests.exceptions.RequestException as e:
        print(f"Error fetching donations: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return []

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
    url = f"https://api.airtable.com/v0/{BASE_ID}/{DONORS_TABLE}/{record_id}"
    response = requests.patch(url, headers=HEADERS, json=data)
    
    if response.status_code != 200:
        return False
    
    return True

def get_donor_donations(donor_id):
    """Get donation history for a specific donor"""
    print(f"\nFetching donations for donor: {donor_id}")
    
    try:
        # Fetch all donations first
        response = requests.get(AIRTABLE_URL_DONATIONS, headers=HEADERS)
        response.raise_for_status()
        print(f"Response status: {response.status_code}")
        print(f"Raw response data: {json.dumps(response.json(), indent=2)}")
        
        all_records = response.json().get('records', [])
        print(f"Total donations found: {len(all_records)}")
        
        # Filter for this donor's donations
        donor_records = [
            record for record in all_records 
            if record.get('fields', {}).get('Donor', []) and donor_id in record['fields']['Donor']
        ]
        print(f"Donations for this donor: {len(donor_records)}")
        print("Donor records:", json.dumps(donor_records, indent=2))
        
        if not donor_records:
            print("No donations found for this donor")
            return pd.DataFrame()
            
        donations = []
        for record in donor_records:
            fields = record.get('fields', {})
            donation = {
                'id': record.get('id'),
                'amount': fields.get('Donation Amount', 0),
                'date': fields.get('Donation Date', ''),
                'payment_method': fields.get('Donation Mode', ''),
                'purpose': fields.get('Donation Purpose', ''),
                'receipt_no': fields.get('Receipt URL', '')
            }
            donations.append(donation)
            
        donations_df = pd.DataFrame(donations)
        if not donations_df.empty:
            print("Donation records found:", json.dumps(donations, indent=2))
            donations_df['date'] = pd.to_datetime(donations_df['date'])
            donations_df = donations_df.sort_values('date', ascending=False)
        
        return donations_df
        
    except Exception as e:
        print(f"Error fetching donations: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        return pd.DataFrame()  # Return empty DataFrame on error