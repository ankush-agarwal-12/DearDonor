import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import json
import pandas as pd

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL:
    raise ValueError("Missing Supabase URL. Set SUPABASE_URL in .env file")
if not SUPABASE_KEY:
    raise ValueError("Missing Supabase Key. Set SUPABASE_SERVICE_KEY in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_donor(full_name: str, email: str, phone: str = None, address: str = None, pan: str = None, donor_type: str = "Individual") -> dict:
    """Add a new donor to Supabase"""
    try:
        data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "pan": pan,
            "donor_type": donor_type,
            "created_at": datetime.now().isoformat()
        }
        
        print(f"Attempting to add donor with data: {data}")
        result = supabase.table("donors").insert(data).execute()
        print(f"Supabase response: {result}")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error adding donor: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {e.__dict__}")
        return None

def fetch_donors():
    """Fetch all donors from Supabase"""
    try:
        result = supabase.table("donors").select("*").execute()
        donors = result.data
        
        transformed_donors = []
        for donor in donors:
            transformed_donors.append({
                "id": donor["id"],
                "Full Name": donor["full_name"],
                "Email": donor["email"],
                "Phone": donor["phone"],
                "Address": donor["address"],
                "PAN": donor.get("pan", ""),
                "donor_type": donor.get("donor_type", "Individual"),
                "created_at": donor.get("created_at", datetime.now().isoformat())
            })
        
        return transformed_donors
    except Exception as e:
        print(f"Error fetching donors: {str(e)}")
        return []

def record_donation(donor_id, amount, date, purpose, payment_method, payment_details, is_recurring=False, recurring_frequency=None, start_date=None, next_due_date=None, recurring_status=None, linked_to_recurring=False, recurring_id=None, is_scheduled_payment=False):
    """Record a donation in the database"""
    try:
        data = {
            "donor_id": donor_id,
            "amount": amount,
            "date": date,
            "purpose": purpose,
            "payment_mode": payment_method,
            "payment_details": payment_details,
            "is_recurring": is_recurring,
            "recurring_frequency": recurring_frequency,
            "start_date": start_date,
            "next_due_date": next_due_date,
            "recurring_status": recurring_status,
            "linked_to_recurring": linked_to_recurring,
            "recurring_id": recurring_id,
            "is_scheduled_payment": is_scheduled_payment,
            "receipt_path": payment_details.get("receipt_path") if payment_details else None
        }

        # If this is a new recurring donation, set the last_paid_date to start_date
        if is_recurring and not linked_to_recurring:
            data["last_paid_date"] = start_date

        result = supabase.table("donations").insert(data).execute()
        
        return result.data is not None and len(result.data) > 0
    except Exception as e:
        print(f"Error recording donation: {str(e)}")
        return False

def fetch_all_donations():
    """Fetch all donations from Supabase"""
    try:
        result = supabase.table("donations")\
            .select("*, donors(full_name, email)")\
            .execute()
        
        donations = result.data
        transformed_donations = []
        
        for donation in donations:
            donor = donation["donors"]
            transformed_donations.append({
                "id": donation["id"],
                "Donor": donation["donor_id"],
                "Email": donor["email"],
                "Amount": donation["amount"],
                "date": donation["date"],
                "Purpose": donation.get("purpose", ""),
                "payment_method": donation["payment_mode"],
                "receipt_no": donation.get("receipt_path"),
                "is_recurring": donation.get("is_recurring", False),
                "recurring_frequency": donation.get("recurring_frequency"),
                "start_date": donation.get("start_date"),
                "next_due_date": donation.get("next_due_date"),
                "recurring_status": donation.get("recurring_status"),
                "last_paid_date": donation.get("last_paid_date"),
                "linked_to_recurring": donation.get("linked_to_recurring", False),
                "recurring_id": donation.get("recurring_id")
            })
        
        return transformed_donations
    except Exception as e:
        print(f"Error fetching donations: {str(e)}")
        return []

def get_donor_donations(donor_id: str):
    """Get donation history for a specific donor"""
    try:
        result = supabase.table("donations")\
            .select("*")\
            .eq("donor_id", donor_id)\
            .execute()
        
        transformed_donations = []
        for donation in result.data:
            transformed_donations.append({
                "id": donation["id"],
                "Amount": donation["amount"],
                "date": donation["date"],
                "payment_method": donation["payment_mode"],
                "Purpose": donation["purpose"],
                "receipt_no": donation.get("receipt_path", "")
            })
        
        return transformed_donations
    except Exception as e:
        print(f"Error fetching donor donations: {str(e)}")
        return []

def update_donor(record_id: str, data: dict) -> bool:
    """Update donor information"""
    try:
        result = supabase.table("donors")\
            .update(data)\
            .eq("id", record_id)\
            .execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error updating donor: {str(e)}")
        return False

def get_active_recurring_donations(donor_id):
    """Get all active recurring donations for a donor from the donations table"""
    try:
        print(f"\n=== Debugging get_active_recurring_donations ===")
        print(f"Input donor_id: {donor_id}")
        
        # Query the donations table for active recurring donations
        query = supabase.table("donations") \
            .select("*, donors(full_name, email)") \
            .eq("donor_id", donor_id) \
            .eq("is_recurring", True) \
            .eq("recurring_status", "Active") \
            .order("start_date", desc=True)
            
        print(f"Executing query: {query}")
        result = query.execute()
        
        print(f"Query result data: {result.data}")
        print(f"Query result count: {len(result.data) if result.data else 0}")
        
        recurring_plans = []
        if result.data:
            for donation in result.data:
                recurring_info = {
                    "id": donation["id"],
                    "Amount": donation["amount"],
                    "Frequency": donation.get("recurring_frequency", "Monthly"),
                    "start_date": donation.get("start_date"),
                    "next_due_date": donation.get("next_due_date"),
                    "recurring_status": donation.get("recurring_status"),
                    "Purpose": donation.get("purpose", "General Fund"),
                    "last_paid_date": donation.get("last_paid_date")
                }
                recurring_plans.append(recurring_info)
            
            print(f"Found {len(recurring_plans)} recurring plans")
            return recurring_plans
            
        print("No active recurring donations found")
        return None
    except Exception as e:
        print(f"Error in get_active_recurring_donations: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

# Remove the legacy function since it's redundant
# def get_active_recurring_donation(donor_id):
#     """Get active recurring donations for a donor (legacy function)"""
#     return get_active_recurring_donations(donor_id)

def get_last_receipt_number():
    """Get the last receipt number from the donations table"""
    try:
        result = supabase.table("donations") \
            .select("payment_details") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
            
        if result.data and result.data[0].get("payment_details"):
            return result.data[0]["payment_details"].get("receipt_number")
        return None
    except Exception as e:
        print(f"Error getting last receipt number: {str(e)}")
        return None

def record_recurring_payment(donor_id, recurring_id, amount, payment_date, payment_details):
    """Record a payment for a recurring donation"""
    try:
        # Get the recurring donation details
        recurring = supabase.table("donations")\
            .select("*")\
            .eq("id", recurring_id)\
            .single()\
            .execute()
            
        if not recurring.data:
            return False
            
        # Record the payment as a linked donation
        data = {
            "donor_id": donor_id,
            "amount": amount,
            "date": payment_date.isoformat() if hasattr(payment_date, 'isoformat') else payment_date,
            "purpose": recurring.data.get("purpose"),
            "payment_mode": recurring.data.get("payment_mode"),
            "payment_details": payment_details,
            "is_recurring": True,
            "recurring_frequency": recurring.data.get("recurring_frequency"),
            "linked_to_recurring": True,
            "recurring_id": recurring_id,
            "receipt_path": payment_details.get("receipt_path") if payment_details else None
        }
        
        result = supabase.table("donations").insert(data).execute()
        
        if result.data:
            # Update the last_paid_date of the recurring donation
            update_result = supabase.table("donations")\
                .update({"last_paid_date": payment_date})\
                .eq("id", recurring_id)\
                .execute()
            
            return update_result.data is not None
            
        return False
    except Exception as e:
        print(f"Error recording recurring payment: {str(e)}")
        return False

def update_recurring_donation_status(recurring_id, last_payment_date, was_overdue):
    """Update the status of a recurring donation after payment"""
    try:
        result = supabase.table("donations") \
            .select("*") \
            .eq("id", recurring_id) \
            .execute()
            
        if not result.data:
            return False
            
        recurring_info = result.data[0]
        frequency = recurring_info["recurring_frequency"]
        
        from modules.recurring_donations import calculate_next_due_date
        next_due = calculate_next_due_date(last_payment_date, frequency)
            
        update_data = {
            "last_paid_date": last_payment_date.isoformat(),
            "next_due_date": next_due.isoformat(),
            "recurring_status": "Active"
        }
        
        result = supabase.table("donations") \
            .update(update_data) \
            .eq("id", recurring_id) \
            .execute()
            
        return bool(result.data)
    except Exception as e:
        print(f"Error updating recurring donation status: {str(e)}")
        return False

def get_active_recurring_donation(donation_id: str):
    """Fetch a specific active recurring donation by ID"""
    try:
        result = supabase.table("donations")\
            .select("*, donors(full_name, email)")\
            .eq("id", donation_id)\
            .eq("is_recurring", True)\
            .neq("recurring_status", "Cancelled")\
            .execute()
        
        if not result.data:
            return None
        
        donation = result.data[0]
        donor = donation["donors"]
        
        return {
            "id": donation["id"],
            "Donor": donation["donor_id"],
            "Email": donor["email"],
            "Amount": donation["amount"],
            "recurring_frequency": donation.get("recurring_frequency"),
            "start_date": donation.get("start_date"),
            "next_due_date": donation.get("next_due_date"),
            "recurring_status": donation.get("recurring_status"),
            "last_paid_date": donation.get("last_paid_date"),
            "purpose": donation.get("purpose", "Recurring Donation")
        }
    except Exception as e:
        print(f"Error fetching recurring donation: {str(e)}")
        return None

def update_recurring_status(donation_id: str, new_status: str) -> bool:
    """Update the status of a recurring donation (Active/Paused/Cancelled)"""
    try:
        data = {
            "recurring_status": new_status,
            "next_due_date": None if new_status == "Cancelled" else None
        }
        result = supabase.table("donations")\
            .update(data)\
            .eq("id", donation_id)\
            .execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error updating recurring status: {str(e)}")
        return False

def bulk_update_recurring_status(donation_ids: list, new_status: str) -> bool:
    """Update the status of multiple recurring donations"""
    try:
        success = True
        for donation_id in donation_ids:
            result = update_recurring_status(donation_id, new_status)
            if not result:
                success = False
        return success
    except Exception as e:
        print(f"Error in bulk update: {str(e)}")
        return False

def delete_donation(donation_id: str) -> bool:
    """Delete a donation from the database"""
    try:
        # First get the donation to check if it's linked to a recurring plan
        result = supabase.table("donations") \
            .select("*") \
            .eq("id", donation_id) \
            .execute()
            
        if not result.data:
            print(f"Error: Donation with ID {donation_id} not found")
            return False
            
        donation = result.data[0]
        
        # If this is a recurring donation with linked payments, don't allow deletion
        if donation.get("is_recurring") and donation.get("recurring_status") != "Cancelled":
            linked_payments = supabase.table("donations") \
                .select("id") \
                .eq("recurring_id", donation_id) \
                .eq("linked_to_recurring", True) \
                .execute()
                
            if linked_payments.data:
                print(f"Error: Cannot delete active recurring donation with linked payments")
                return False
        
        # Delete the donation
        result = supabase.table("donations") \
            .delete() \
            .eq("id", donation_id) \
            .execute()
            
        return bool(result.data)
    except Exception as e:
        print(f"Error deleting donation: {str(e)}")
        return False