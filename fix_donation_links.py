from modules.airtable_utils import fetch_all_donations

donations = fetch_all_donations()
for d in donations:
    print(f"Donation ID: {d['id']}, Donor: {d['Donor']}, Purpose: {d['Purpose']}, Date: {d['Date']}")
