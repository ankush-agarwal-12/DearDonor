
# modules/config.py

BASE_ID = "apps0FRGb4mqoTEEt"
API_KEY = "patJjld5FmlN2i7eZ.3af4b311ce9c5837498c0aaa9cac20065e528916783feb4c5603fe272cb9cbc3"

AIRTABLE_URL_DONATIONS = f"https://api.airtable.com/v0/{BASE_ID}/Donations"
AIRTABLE_URL_DONORS = f"https://api.airtable.com/v0/{BASE_ID}/Donors"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
