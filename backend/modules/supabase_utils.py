import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import json
import pandas as pd
from dateutil.relativedelta import relativedelta
import re

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL:
    raise ValueError("Missing Supabase URL. Set SUPABASE_URL in .env file")
if not SUPABASE_KEY:
    raise ValueError("Missing Supabase Key. Set SUPABASE_SERVICE_KEY in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_donor(full_name: str, email: str, phone: str = None, address: str = None, pan: str = None, donor_type: str = "Individual", organization_id: str = None) -> dict:
    """Add a new donor to Supabase"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "pan": pan,
            "donor_type": donor_type,
            "organization_id": organization_id,
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

def fetch_donors(organization_id: str = None):
    """Fetch all donors from Supabase for a specific organization"""
    if not organization_id:
        raise ValueError("Organization ID is required")
        
    try:
        result = supabase.table("donors").select("*").eq("organization_id", organization_id).execute()
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
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        print(f"Error fetching donors: {str(e)}")
        return []

def record_donation(donor_id, amount, date, purpose, payment_method, payment_details, is_recurring=False, recurring_frequency=None, start_date=None, next_due_date=None, recurring_status=None, linked_to_recurring=False, recurring_id=None, is_scheduled_payment=False, organization_id=None):
    """Record a donation in the database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
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
            "organization_id": organization_id,
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

def fetch_all_donations(organization_id: str = None):
    """Fetch all donations from Supabase for a specific organization"""
    if not organization_id:
        raise ValueError("Organization ID is required")
        
    try:
        result = supabase.table("donations")\
            .select("*, donors(full_name, email)")\
            .eq("organization_id", organization_id)\
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
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        print(f"Error fetching donations: {str(e)}")
        return []

def get_donor_donations(donor_id: str, organization_id: str = None):
    """Get donation history for a specific donor"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        result = supabase.table("donations")\
            .select("*")\
            .eq("donor_id", donor_id)\
            .eq("organization_id", organization_id)\
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

def update_donor(record_id: str, data: dict, organization_id: str = None) -> bool:
    """Update donor information"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        result = supabase.table("donors")\
            .update(data)\
            .eq("id", record_id)\
            .eq("organization_id", organization_id)\
            .execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error updating donor: {str(e)}")
        return False

def get_active_recurring_donations(donor_id, organization_id: str = None):
    """Get all active recurring donations for a donor from the donations table"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        print(f"\n=== Debugging get_active_recurring_donations ===")
        print(f"Input donor_id: {donor_id}")
        print(f"Input organization_id: {organization_id}")
        
        # Query the donations table for active recurring donations
        # Only get the original recurring plans, not the linked payments
        query = supabase.table("donations") \
            .select("*, donors(full_name, email)") \
            .eq("donor_id", donor_id) \
            .eq("organization_id", organization_id) \
            .eq("is_recurring", True) \
            .eq("recurring_status", "Active") \
            .eq("linked_to_recurring", False) \
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

def get_last_receipt_number(organization_id: str = None):
    """Get the last receipt number from the donations table for a specific organization"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        result = supabase.table("donations") \
            .select("payment_details") \
            .eq("organization_id", organization_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
            
        if result.data and result.data[0].get("payment_details"):
            return result.data[0]["payment_details"].get("receipt_number")
        return None
    except Exception as e:
        print(f"Error getting last receipt number: {str(e)}")
        return None

def record_recurring_payment(donor_id, recurring_id, amount, payment_date, payment_details, organization_id=None):
    """Record a payment for a recurring donation"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        # Get the recurring donation details
        recurring = supabase.table("donations")\
            .select("*")\
            .eq("id", recurring_id)\
            .eq("organization_id", organization_id)\
            .single()\
            .execute()
            
        if not recurring.data:
            print("No recurring plan found")
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
            "organization_id": organization_id,
            "receipt_path": payment_details.get("receipt_path") if payment_details else None
        }
        
        result = supabase.table("donations").insert(data).execute()
        
        if result.data:
            # Calculate next due date based on frequency
            frequency = recurring.data.get("recurring_frequency")
            payment_date_obj = datetime.fromisoformat(payment_date.isoformat()) if hasattr(payment_date, 'isoformat') else datetime.fromisoformat(payment_date)
            
            if frequency == "Monthly":
                next_due = payment_date_obj + relativedelta(months=1)
            elif frequency == "Quarterly":
                next_due = payment_date_obj + relativedelta(months=3)
            elif frequency == "Half-Yearly":
                next_due = payment_date_obj + relativedelta(months=6)
            else:  # Yearly
                next_due = payment_date_obj + relativedelta(years=1)
            
            # Update both last_paid_date and next_due_date
            update_data = {
                "last_paid_date": payment_date.isoformat() if hasattr(payment_date, 'isoformat') else payment_date,
                "next_due_date": next_due.isoformat()
            }
            
            print(f"Updating recurring plan with data: {update_data}")
            
            update_result = supabase.table("donations")\
                .update(update_data)\
                .eq("id", recurring_id)\
                .execute()
            
            print(f"Update result: {update_result.data}")
            
            return update_result.data is not None
            
        return False
    except Exception as e:
        print(f"Error recording recurring payment: {str(e)}")
        return False

def update_recurring_donation_status(recurring_id, last_payment_date, was_overdue, organization_id: str = None):
    """Update the status of a recurring donation after payment"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        result = supabase.table("donations") \
            .select("*") \
            .eq("id", recurring_id) \
            .eq("organization_id", organization_id) \
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

def get_active_recurring_donation(donation_id: str, organization_id: str = None):
    """Fetch a specific active recurring donation by ID"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        result = supabase.table("donations")\
            .select("*, donors(full_name, email)")\
            .eq("id", donation_id)\
            .eq("organization_id", organization_id)\
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

def update_recurring_status(donation_id: str, new_status: str, organization_id: str = None) -> bool:
    """Update the status of a recurring donation (Active/Paused/Cancelled)"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        data = {
            "recurring_status": new_status,
            "next_due_date": None if new_status == "Cancelled" else None
        }
        result = supabase.table("donations")\
            .update(data)\
            .eq("id", donation_id)\
            .eq("organization_id", organization_id)\
            .execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error updating recurring status: {str(e)}")
        return False

def bulk_update_recurring_status(donation_ids: list, new_status: str, organization_id: str = None) -> bool:
    """Update the status of multiple recurring donations"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        success = True
        for donation_id in donation_ids:
            result = update_recurring_status(donation_id, new_status, organization_id)
            if not result:
                success = False
        return success
    except Exception as e:
        print(f"Error in bulk update: {str(e)}")
        return False

def delete_donation(donation_id: str, organization_id: str = None) -> bool:
    """Delete a donation from the database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        # First get the donation to check if it's linked to a recurring plan
        result = supabase.table("donations") \
            .select("*") \
            .eq("id", donation_id) \
            .eq("organization_id", organization_id) \
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
            .eq("organization_id", organization_id) \
            .execute()
            
        return bool(result.data)
    except Exception as e:
        print(f"Error deleting donation: {str(e)}")
        return False

def delete_donor(donor_id: str, organization_id: str = None) -> bool:
    """Delete a donor from the database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        # First check if the donor has any donations
        donations = supabase.table("donations") \
            .select("id") \
            .eq("donor_id", donor_id) \
            .eq("organization_id", organization_id) \
            .execute()
            
        if donations.data:
            print(f"Error: Cannot delete donor with ID {donor_id} - they have donation history")
            return False
        
        # Delete the donor
        result = supabase.table("donors") \
            .delete() \
            .eq("id", donor_id) \
            .eq("organization_id", organization_id) \
            .execute()
            
        return bool(result.data)
    except Exception as e:
        print(f"Error deleting donor: {str(e)}")
        return False

def get_organization_settings(organization_id: str) -> dict:
    """Get organization settings from database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        # Get organization data
        org_result = supabase.table("organizations").select("*").eq("id", organization_id).execute()
        
        if not org_result.data:
            print(f"Warning: No organization found for ID {organization_id}")
            return {}
            
        org_data = org_result.data[0]
        if org_data is None:
            print(f"Warning: Organization data is None for ID {organization_id}")
            return {}
        
        # Get organization settings
        settings_result = supabase.table("organization_settings").select("*").eq("organization_id", organization_id).execute()
        
        # Build settings dictionary
        settings = {}
        for setting in settings_result.data:
            settings[setting['setting_key']] = setting['setting_value']
        
        # Extract social media and signature holder from JSONB columns with safety checks
        social_media = org_data.get('social_media', {}) if org_data else {}
        if isinstance(social_media, str):
            try:
                social_media = json.loads(social_media)
            except Exception as e:
                print(f"Warning: Failed to parse social_media JSON for org {organization_id}: {e}")
                social_media = {}
        
        signature_holder = org_data.get('signature_holder', {}) if org_data else {}
        if isinstance(signature_holder, str):
            try:
                signature_holder = json.loads(signature_holder)
            except Exception as e:
                print(f"Warning: Failed to parse signature_holder JSON for org {organization_id}: {e}")
                signature_holder = {}
        
        # Combine organization data with settings
        org_settings = {
            'organization': {
                'name': org_data.get('name', '') if org_data else '',
                'office_address': org_data.get('office_address', '') if org_data else '',
                'phone': org_data.get('phone', '') if org_data else '',
                'email': org_data.get('email', '') if org_data else '',
                'website': org_data.get('website', '') if org_data else '',
                'registration_number': org_data.get('registration_number', '') if org_data else '',
                'pan_number': org_data.get('pan_number', '') if org_data else '',
                'csr_number': org_data.get('csr_number', '') if org_data else '',
                'tax_exemption_number': org_data.get('tax_exemption_number', '') if org_data else '',
                'social_media': {
                    'facebook': social_media.get('facebook', '') if social_media else '',
                    'instagram': social_media.get('instagram', '') if social_media else '',
                    'youtube': social_media.get('youtube', '') if social_media else ''
                },
                'signature_holder': {
                    'name': signature_holder.get('name', '') if signature_holder else '',
                    'designation': signature_holder.get('designation', '') if signature_holder else ''
                }
            },
            'receipt_format': settings.get('receipt_format', {
                'prefix': 'REC',
                'format': '{prefix}/{YY}/{MM}/{XXX}',
                'next_sequence': 1
            }),
            'donation_purposes': settings.get('donation_purposes', ['General Fund', 'Corpus Fund', 'Emergency Fund']),
            'payment_methods': settings.get('payment_methods', ['Cash', 'UPI', 'Bank Transfer', 'Cheque']),
            'email_config': settings.get('email_config', {
                'email_address': '',
                'email_password': '',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True
            })
        }
        
        print(f"Debug: Successfully loaded settings for organization {organization_id}")
        return org_settings
    except Exception as e:
        print(f"Error getting organization settings for {organization_id}: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {}

def save_organization_settings(organization_id: str, settings: dict) -> bool:
    """Save organization settings to database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
        
        # Update organization data
        org_data = {}
        if 'organization' in settings:
            org = settings['organization']
            org_data = {
                'name': org.get('name', ''),
                'office_address': org.get('office_address', ''),
                'phone': org.get('phone', ''),
                'email': org.get('email', ''),
                'website': org.get('website', ''),
                'registration_number': org.get('registration_number', ''),
                'pan_number': org.get('pan_number', ''),
                'csr_number': org.get('csr_number', ''),
                'tax_exemption_number': org.get('tax_exemption_number', ''),
                'social_media': org.get('social_media', {}),
                'signature_holder': org.get('signature_holder', {}),
                'updated_at': datetime.now().isoformat()
            }
            
            # Update organization record
            supabase.table("organizations").update(org_data).eq("id", organization_id).execute()
        
        # Update organization settings
        for key, value in settings.items():
            if key != 'organization':  # Skip organization data as it's handled above
                # Upsert setting
                setting_data = {
                    'organization_id': organization_id,
                    'setting_key': key,
                    'setting_value': value
                }
                
                # Check if setting exists
                existing = supabase.table("organization_settings")\
                    .select("id")\
                    .eq("organization_id", organization_id)\
                    .eq("setting_key", key)\
                    .execute()
                
                if existing.data:
                    # Update existing setting
                    supabase.table("organization_settings")\
                        .update({'setting_value': value})\
                        .eq("organization_id", organization_id)\
                        .eq("setting_key", key)\
                        .execute()
                else:
                    # Insert new setting
                    supabase.table("organization_settings").insert(setting_data).execute()
        
        return True
    except Exception as e:
        print(f"Error saving organization settings: {str(e)}")
        return False

def get_organization_receipt_number(organization_id: str) -> str:
    """Generate organization-specific receipt number"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        # Get organization settings
        settings = get_organization_settings(organization_id)
        receipt_format = settings.get('receipt_format', {
            'prefix': 'REC',
            'format': '{prefix}/{YY}/{MM}/{XXX}',
            'next_sequence': 1
        })

        current_date = datetime.now()
        year_short = str(current_date.year)[-2:]
        month = str(current_date.month).zfill(2)
        
        # Get last receipt number for this organization
        last_receipt = get_last_receipt_number(organization_id=organization_id)
        
        sequence = receipt_format['next_sequence']
        if last_receipt:
            # Extract sequence from last receipt
            pattern = receipt_format['format'].format(
                prefix=receipt_format['prefix'],
                YY=year_short,
                MM=month,
                XXX=r"(\d+)"
            ).replace("/", "\\/")
            
            match = re.search(pattern, last_receipt)
            if match:
                try:
                    sequence = int(match.group(1)) + 1
                except ValueError:
                    sequence = receipt_format['next_sequence']
        
        # Generate new receipt number
        receipt_number = receipt_format['format'].format(
            prefix=receipt_format['prefix'],
            YY=year_short,
            MM=month,
            XXX=str(sequence).zfill(3)
        )
        
        # Update next sequence in database
        receipt_format['next_sequence'] = sequence + 1
        save_organization_settings(organization_id, {'receipt_format': receipt_format})
        
        return receipt_number
    except Exception as e:
        print(f"Error generating receipt number: {str(e)}")
        return f"REC/{year_short}/{month}/001"

def get_organization_asset_path(organization_id: str, asset_type: str) -> str:
    """Get organization-specific asset path"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        asset_dir = f"uploads/organizations/{organization_id}/assets"
        os.makedirs(asset_dir, exist_ok=True)
        
        if asset_type == 'logo':
            return os.path.join(asset_dir, 'logo.png')
        elif asset_type == 'signature':
            return os.path.join(asset_dir, 'signature.png')
        else:
            return os.path.join(asset_dir, f'{asset_type}.png')
    except Exception as e:
        print(f"Error getting asset path: {str(e)}")
        return f"assets/{asset_type}.png"  # Fallback

def get_organization_receipt_path(organization_id: str, receipt_number: str) -> str:
    """Get organization-specific receipt path"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
        receipt_dir = f"uploads/organizations/{organization_id}/receipts"
        os.makedirs(receipt_dir, exist_ok=True)
        
        return os.path.join(receipt_dir, f"{receipt_number.replace('/', '_')}.pdf")
    except Exception as e:
        print(f"Error getting receipt path: {str(e)}")
        return f"receipts/{receipt_number.replace('/', '_')}.pdf"  # Fallback