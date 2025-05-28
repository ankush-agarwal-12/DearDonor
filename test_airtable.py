from modules.airtable_utils import fetch_donors

donors = fetch_donors()
print(f"Total donors fetched: {len(donors)}")

for donor in donors:
    print(donor)
