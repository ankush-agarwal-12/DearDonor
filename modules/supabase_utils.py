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

def extract_receipt_number_from_path(receipt_path: str) -> str:
    """Extract just the receipt number from full file path"""
    if not receipt_path:
        return ""
    
    # Get filename from path and remove extension
    filename = os.path.basename(receipt_path)
    receipt_number = os.path.splitext(filename)[0]
    
    # Convert underscores back to slashes for proper receipt number format
    receipt_number = receipt_number.replace('_', '/')
    
    return receipt_number

def get_receipt_file_path(receipt_path: str) -> str:
    """Get the full file path for downloading receipt"""
    if not receipt_path:
        return ""
    
    # If it's already a full path, return as is
    if receipt_path.startswith('uploads/'):
        return receipt_path
    
    # Otherwise, it might be just the receipt number, reconstruct the path
    return receipt_path

def validate_email_format(email: str) -> bool:
    """Validate email format using regex"""
    if not email or email.strip() == "":
        return True  # Empty email is allowed
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def check_email_exists(email: str, organization_id: str, exclude_donor_id: str = None) -> tuple[bool, dict]:
    """
    Check if email already exists for the organization
    Returns (exists, donor_info)
    """
    if not email or email.strip() == "":
        return False, {}
    
    try:
        query = supabase.table("donors").select("id, full_name, email").eq("organization_id", organization_id).eq("email", email.strip().lower())
        
        # Exclude current donor if updating
        if exclude_donor_id:
            query = query.neq("id", exclude_donor_id)
            
        result = query.execute()
        
        if result.data:
            return True, result.data[0]
        return False, {}
    except Exception as e:
        print(f"Error checking email existence: {str(e)}")
        return False, {}

def add_donor(full_name: str, email: str, phone: str = None, address: str = None, pan: str = None, donor_type: str = "Individual", organization_id: str = None) -> dict:
    """Add a new donor to Supabase with email validation"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
        
        # Validate email format
        if email and not validate_email_format(email):
            raise ValueError("Invalid email format")
        
        # Check for duplicate email within organization
        if email and email.strip():
            email_exists, existing_donor = check_email_exists(email.strip().lower(), organization_id)
            if email_exists:
                raise ValueError(f"Email already exists for donor: {existing_donor['full_name']}")
            
        data = {
            "full_name": full_name,
            "email": email.strip().lower() if email else email,
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
        raise e  # Re-raise to show specific error message

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

def record_donation(donor_id, amount, date, purpose, payment_method, payment_details, organization_id=None):
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
            "organization_id": organization_id,
            "receipt_path": payment_details.get("receipt_path") if payment_details else None
        }

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
            receipt_path = donation.get("receipt_path", "")
            transformed_donations.append({
                "id": donation["id"],
                "Donor": donation["donor_id"],
                "Email": donor["email"],
                "Amount": donation["amount"],
                "date": donation["date"],
                "Purpose": donation.get("purpose", ""),
                "payment_method": donation["payment_mode"],
                "receipt_no": extract_receipt_number_from_path(receipt_path),
                "receipt_path": receipt_path  # Keep full path for downloads
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
            receipt_path = donation.get("receipt_path", "")
            transformed_donations.append({
                "id": donation["id"],
                "Amount": donation["amount"],
                "date": donation["date"],
                "payment_method": donation["payment_mode"],
                "Purpose": donation["purpose"],
                "receipt_no": extract_receipt_number_from_path(receipt_path),
                "receipt_path": receipt_path  # Keep full path for downloads
            })
        
        return transformed_donations
    except Exception as e:
        print(f"Error fetching donor donations: {str(e)}")
        return []

def update_donor(record_id: str, data: dict, organization_id: str = None) -> bool:
    """Update donor information with email validation"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
        
        # If email is being updated, validate it
        if 'email' in data:
            email = data['email']
            
            # Validate email format
            if email and not validate_email_format(email):
                raise ValueError("Invalid email format")
            
            # Check for duplicate email within organization (excluding current donor)
            if email and email.strip():
                email_exists, existing_donor = check_email_exists(email.strip().lower(), organization_id, record_id)
                if email_exists:
                    raise ValueError(f"Email already exists for donor: {existing_donor['full_name']}")
                
                # Normalize email
                data['email'] = email.strip().lower()
            
        result = supabase.table("donors")\
            .update(data)\
            .eq("id", record_id)\
            .eq("organization_id", organization_id)\
            .execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error updating donor: {str(e)}")
        raise e  # Re-raise to show specific error message



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











def delete_donation(donation_id: str, organization_id: str = None) -> bool:
    """Delete a donation from the database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
            
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
            return {}
            
        org_data = org_result.data[0]
        
        # Get organization settings
        settings_result = supabase.table("organization_settings").select("*").eq("organization_id", organization_id).execute()
        
        # Build settings dictionary
        settings = {}
        for setting in settings_result.data:
            settings[setting['setting_key']] = setting['setting_value']
        
        # Extract social media and signature holder from JSONB columns
        social_media = org_data.get('social_media', {})
        if isinstance(social_media, str):
            try:
                social_media = json.loads(social_media)
            except:
                social_media = {}
        
        signature_holder = org_data.get('signature_holder', {})
        if isinstance(signature_holder, str):
            try:
                signature_holder = json.loads(signature_holder)
            except:
                signature_holder = {}
        
        # Combine organization data with settings
        org_settings = {
            'organization': {
                'name': org_data.get('name', ''),
                'office_address': org_data.get('office_address', ''),
                'phone': org_data.get('phone', ''),
                'email': org_data.get('email', ''),
                'website': org_data.get('website', ''),
                'registration_number': org_data.get('registration_number', ''),
                'pan_number': org_data.get('pan_number', ''),
                'csr_number': org_data.get('csr_number', ''),
                'tax_exemption_number': org_data.get('tax_exemption_number', ''),
                'social_media': {
                    'facebook': social_media.get('facebook', ''),
                    'instagram': social_media.get('instagram', ''),
                    'youtube': social_media.get('youtube', '')
                },
                'signature_holder': {
                    'name': signature_holder.get('name', ''),
                    'designation': signature_holder.get('designation', '')
                }
            },
            'receipt_format': settings.get('receipt_format', {
                'prefix': 'REC',
                'format': '{prefix}/{YY}/{MM}/{XXX}',
                'next_sequence': 1
            }),
            'donation_purposes': settings.get('donation_purposes', ['General Fund', 'Corpus Fund', 'Emergency Fund']),
            'payment_methods': settings.get('payment_methods', ['Cash', 'UPI', 'Bank Transfer', 'Cheque'])
        }
        
        return org_settings
    except Exception as e:
        print(f"Error getting organization settings: {str(e)}")
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

def generate_receipt_on_demand(donation_id: str, organization_id: str) -> str:
    """Generate receipt PDF on-demand for download"""
    try:
        # Get donation details
        result = supabase.table("donations").select(
            "*, donors(full_name, email, pan)"
        ).eq("id", donation_id).eq("organization_id", organization_id).execute()
        
        if not result.data:
            raise ValueError("Donation not found")
        
        donation = result.data[0]
        donor = donation["donors"]
        
        # Get payment details
        payment_details = donation.get("payment_details", {})
        receipt_number = payment_details.get("receipt_number", "")
        
        # Prepare donor data for PDF generation
        donor_data = {
            "name": donor["full_name"],
            "email": donor["email"],
            "pan": donor.get("pan", "N/A"),
            "amount": str(donation["amount"]),
            "date": donation["date"],
            "purpose": donation["purpose"],
            "payment_mode": donation["payment_mode"],
            "receipt_number": receipt_number
        }
        
        # Create temporary file path
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"receipt_{donation_id}_{receipt_number.replace('/', '_')}.pdf")
        
        # Generate PDF
        from modules.pdf_template import generate_receipt
        generate_receipt(donor_data, temp_file, organization_id=organization_id)
        
        return temp_file
        
    except Exception as e:
        print(f"Error generating receipt on demand: {str(e)}")
        return None

def cleanup_temp_receipts():
    """Clean up temporary receipt files"""
    try:
        import tempfile
        import glob
        
        temp_dir = tempfile.gettempdir()
        receipt_pattern = os.path.join(temp_dir, "receipt_*.pdf")
        
        # Find and delete temporary receipt files older than 1 hour
        import time
        current_time = time.time()
        deleted_count = 0
        
        for file_path in glob.glob(receipt_pattern):
            try:
                # Check file age (1 hour = 3600 seconds)
                if os.path.exists(file_path) and (current_time - os.path.getmtime(file_path)) > 3600:
                    os.remove(file_path)
                    deleted_count += 1
            except:
                continue  # Skip files that can't be deleted
        
        print(f"Cleaned up {deleted_count} temporary receipt files")
        return deleted_count
        
    except Exception as e:
        print(f"Error cleaning up temporary receipts: {str(e)}")
        return 0

def send_organization_email_receipt(to_email, donor_name, receipt_path, amount, receipt_number="", purpose="", payment_mode="", organization_id=None):
    """Send donation receipt email using organization-specific details from database"""
    try:
        if not organization_id:
            raise ValueError("Organization ID is required")
        
        # Get organization settings from database
        org_settings = get_organization_settings(organization_id)
        org_data = org_settings.get('organization', {})
        
        # Import email modules
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        from num2words import num2words
        from datetime import datetime
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Email settings
        EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-email@gmail.com")
        EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        
        # Subject
        subject = f"Donation Receipt - Thank You, {donor_name}"
        msg['Subject'] = subject
        
        # Convert amount to words
        try:
            amount_in_words = num2words(float(amount), lang='en_IN').title()
        except:
            amount_in_words = str(amount)
        
        # Get social media links
        social_media = org_data.get('social_media', {})
        social_links = []
        if social_media.get('facebook'):
            social_links.append(f"Facebook: {social_media['facebook']}")
        if social_media.get('instagram'):
            social_links.append(f"Instagram: {social_media['instagram']}")
        if social_media.get('youtube'):
            social_links.append(f"YouTube: {social_media['youtube']}")
        social_text = " | ".join(social_links) if social_links else "Follow us on social media"
        
        # Create email body with organization-specific details
        email_body = f"""Dear {donor_name},

Thank you for your generous donation of Rs. {amount} /- ({amount_in_words}) to {org_data.get('name', 'Our Organization')}. Your contribution will help us make a difference.

Receipt Details:
- Receipt Number: {receipt_number}
- Date: {datetime.now().strftime("%d/%m/%Y")}
- Purpose: {purpose or "General Donation"}
- Payment Mode: {payment_mode or "Online"}

The official receipt is attached to this email.

Best regards,
Accounts Department
{org_data.get('name', 'Our Organization')}

Contact us:
{org_data.get('email', '')} | {org_data.get('phone', '')}
{social_text}
Address: {org_data.get('office_address', '')}
"""
        
        # Add plain text version
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Add HTML version with better formatting
        html_body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    color: #2196F3;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .receipt-details {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                }}
                .contact-info {{
                    margin-top: 20px;
                    font-size: 14px;
                    color: #666;
                }}
                a {{
                    color: #2196F3;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <p>Dear {donor_name},</p>
            
            <p>Thank you for your generous donation of <strong>Rs. {amount} /-</strong> (<em>{amount_in_words}</em>) to <strong>{org_data.get('name', 'Our Organization')}</strong>. Your contribution will help us make a difference.</p>
            
            <div class="receipt-details">
                <div class="header">Receipt Details:</div>
                <ul>
                    <li><strong>Receipt Number:</strong> {receipt_number}</li>
                    <li><strong>Date:</strong> {datetime.now().strftime("%d/%m/%Y")}</li>
                    <li><strong>Purpose:</strong> {purpose or "General Donation"}</li>
                    <li><strong>Payment Mode:</strong> {payment_mode or "Online"}</li>
                </ul>
            </div>
            
            <p>The official receipt is attached to this email.</p>
            
            <p>Best regards,<br>
            Accounts Department<br>
            <strong>{org_data.get('name', 'Our Organization')}</strong></p>
            
            <div class="contact-info">
                <strong>Contact us:</strong><br>
                Email: <a href="mailto:{org_data.get('email', '')}">{org_data.get('email', '')}</a><br>
                Phone: <a href="tel:{org_data.get('phone', '')}">{org_data.get('phone', '')}</a><br>
                {social_text}<br>
                Address: {org_data.get('office_address', '')}
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Attach the PDF receipt with proper receipt number filename
        with open(receipt_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            # Use clean receipt number as filename
            clean_filename = f"{receipt_number.replace('/', '_')}.pdf"
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{clean_filename}"'
            )
            msg.attach(part)
        
        # Send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        return True
        
    except Exception as e:
        print(f"Error sending organization email: {str(e)}")
        return False