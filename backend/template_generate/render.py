#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import os
import tempfile
import shutil
from datetime import datetime
from num2words import num2words
import base64
import boto3
import sys
from pathlib import Path
import PyPDF2

# Add the backend app path to import settings
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

try:
    from app.core.config import get_settings
    settings = get_settings()
except ImportError:
    settings = None
    print("Warning: Could not import settings, organization assets may not work")

def get_s3_client():
    """Get S3 client for Supabase storage"""
    if not settings:
        return None
    
    try:
        return boto3.client(
            's3',
            endpoint_url=settings.SUPABASE_STORAGE_URL,
            region_name=settings.SUPABASE_STORAGE_REGION,
            aws_access_key_id=settings.SUPABASE_STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SUPABASE_STORAGE_SECRET_ACCESS_KEY
        )
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        return None

def get_s3_asset(org_id, asset_type):
    """Fetch organization asset from Supabase storage"""
    s3_client = get_s3_client()
    if not s3_client:
        return None
        
    asset_key = f"{org_id}/assets/{asset_type}.png"
    try:
        response = s3_client.get_object(
            Bucket=settings.SUPABASE_STORAGE_BUCKET, 
            Key=asset_key
        )
        return response['Body'].read()
    except Exception as e:
        print(f"Error fetching asset {asset_key}: {e}")
        return None

def render_template_with_data(template_path, data):
    """
    Read an HTML template file and replace placeholders with real data.
    Returns the rendered HTML content as a string.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace all placeholders with actual data
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"  # {{ and }} for template variables
        html_content = html_content.replace(placeholder, str(value))
    
    return html_content

def get_asset_base64(asset_path, fallback_path=None):
    """Convert asset to base64 for embedding in HTML"""
    try:
        if os.path.exists(asset_path):
            with open(asset_path, 'rb') as f:
                data = f.read()
                return base64.b64encode(data).decode('utf-8')
        elif fallback_path and os.path.exists(fallback_path):
            with open(fallback_path, 'rb') as f:
                data = f.read()
                return base64.b64encode(data).decode('utf-8')
    except Exception as e:
        print(f"Error reading asset {asset_path}: {e}")
    return None

def prepare_template_directory(organization_id=None):
    """Prepare a temporary directory with CSS files and all required assets"""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    base_dir = os.path.dirname(__file__)
    
    # Copy CSS files to temp directory
    css_files = ['receipt.css', 'cert.css', 'styles.css']
    for css_file in css_files:
        src_css = os.path.join(base_dir, css_file)
        if os.path.exists(src_css):
            shutil.copy2(src_css, temp_dir)
    
    # Create assets directory in temp
    assets_dir = os.path.join(temp_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # Copy ALL assets from the original assets directory (fonts, backgrounds, etc.)
    default_assets_dir = os.path.join(base_dir, 'assets')
    if os.path.exists(default_assets_dir):
        for asset_file in os.listdir(default_assets_dir):
            src_asset = os.path.join(default_assets_dir, asset_file)
            if os.path.isfile(src_asset):
                shutil.copy2(src_asset, assets_dir)
                print(f"Copied asset: {asset_file}")
    
    # Handle organization-specific assets (logo and signature)
    if organization_id:
        print(f"Fetching organization assets for: {organization_id}")
        
        # Fetch and save organization logo
        logo_bytes = get_s3_asset(organization_id, 'logo')
        if logo_bytes:
            logo_dest = os.path.join(assets_dir, 'logo.png')
            with open(logo_dest, 'wb') as f:
                f.write(logo_bytes)
            print(f"✅ Fetched organization logo for {organization_id}")
        else:
            print(f"⚠️ No organization logo found for {organization_id}, using fallback")
        
        # Fetch and save organization signature  
        signature_bytes = get_s3_asset(organization_id, 'signature')
        if signature_bytes:
            signature_dest = os.path.join(assets_dir, 'signature.jpg')
            with open(signature_dest, 'wb') as f:
                f.write(signature_bytes)
            print(f"✅ Fetched organization signature for {organization_id}")
        else:
            print(f"⚠️ No organization signature found for {organization_id}, using fallback")
    
    print(f"Assets directory prepared at: {assets_dir}")
    print(f"Assets available: {os.listdir(assets_dir) if os.path.exists(assets_dir) else 'None'}")
    
    return temp_dir

def generate_receipt_templates(donor_data, org_data, donation_data, organization_id=None):
    """
    Generate HTML files with real data for receipt generation.
    Returns paths to the generated HTML files and temp directory.
    """
    # Prepare template directory with CSS and assets
    temp_dir = prepare_template_directory(organization_id)
    
    # Prepare template data
    template_data = {
        # Organization data
        'org_name': org_data.get('name', 'Organization Name Not Set').upper(),
        'org_name_proper': org_data.get('name', 'Organization Name Not Set'),
        'registration_number': org_data.get('registration_number', 'Registration Number Not Set'),
        'office_address': org_data.get('office_address', 'Address Not Set'),
        'org_pan': org_data.get('pan_number', 'PAN Number Not Set'),
        'csr_number': org_data.get('csr_number', 'CSR Number Not Set'),
        'tax_exemption_12a': org_data.get('tax_exemption_12a', '12A Number Not Set'),  # Use separate 12A field
        'tax_exemption_80g': org_data.get('tax_exemption_80g', '80G Number Not Set'),  # Use separate 80G field
        'org_phone': org_data.get('phone', 'Phone Number Not Set'),
        'org_email': org_data.get('email', 'Email Not Set'),
        'org_website': org_data.get('website', 'Website Not Set'),
        
        # Donation data
        'receipt_number': donation_data.get('receipt_number', 'REC/2024/001'),
        'amount': f"Rs. {float(donation_data.get('amount', 0)):,.0f}",
        'amount_only': f"{float(donation_data.get('amount', 0)):,.0f}",
        'amount_words': convert_amount_to_words(donation_data.get('amount', 0)),
        'donation_date': donation_data.get('date', datetime.now().strftime('%d/%m/%Y')),
        'donation_date_iso': donation_data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'purpose': donation_data.get('purpose', 'General Fund'),
        'payment_mode': donation_data.get('payment_mode', 'Online'),
        'payment_details': donation_data.get('payment_details', 'N/A'),
        'financial_year': get_financial_year(donation_data.get('date', datetime.now().strftime('%Y-%m-%d'))),
        
        # Donor data
        'donor_name': donor_data.get('name', 'Donor Name Not Set'),
        'name': donor_data.get('name', 'Donor Name Not Set'),  # For thank you template
        'donor_address': donor_data.get('address', 'Address Not Provided'),
        'donor_phone': donor_data.get('phone', 'Phone Not Provided'),
        'donor_email': donor_data.get('email', 'Email Not Provided'),
        'donor_pan': donor_data.get('pan', 'N/A'),
        
        # Signature data
        'signatory_name': org_data.get('signature_holder', {}).get('name', 'Authorized Signatory'),
        'signatory_designation': org_data.get('signature_holder', {}).get('designation', 'Authorized Signatory')
    }
    
    # Generate template files
    base_dir = os.path.dirname(__file__)
    generated_files = {}
    
    # Generate receipt.html
    receipt_template = os.path.join(base_dir, 'receipt.html')
    receipt_content = render_template_with_data(receipt_template, template_data)
    receipt_content = replace_hardcoded_values_receipt(receipt_content, template_data)
    
    receipt_output = os.path.join(temp_dir, 'receipt_generated.html')
    with open(receipt_output, 'w', encoding='utf-8') as f:
        f.write(receipt_content)
    generated_files['receipt'] = receipt_output
    
    # Generate cert.html
    cert_template = os.path.join(base_dir, 'cert.html')
    cert_content = render_template_with_data(cert_template, template_data)
    cert_content = replace_hardcoded_values_cert(cert_content, template_data)
    
    cert_output = os.path.join(temp_dir, 'cert_generated.html')
    with open(cert_output, 'w', encoding='utf-8') as f:
        f.write(cert_content)
    generated_files['cert'] = cert_output
    
    # Generate templateThankYou.html
    thankyou_template = os.path.join(base_dir, 'templateThankYou.html')
    thankyou_content = render_template_with_data(thankyou_template, template_data)
    thankyou_content = replace_hardcoded_values_thankyou(thankyou_content, template_data)
    
    thankyou_output = os.path.join(temp_dir, 'thankyou_generated.html')
    with open(thankyou_output, 'w', encoding='utf-8') as f:
        f.write(thankyou_content)
    generated_files['thankyou'] = thankyou_output
    
    return generated_files, temp_dir

def replace_hardcoded_values_receipt(html_content, data):
    """Replace hardcoded values in receipt.html with real data"""
    # Organization name and details
    html_content = html_content.replace('THE STRAY ARMY CHARITABLE TRUST', data['org_name'])
    html_content = html_content.replace('The Stray Army Charitable Trust', data['org_name'])
    html_content = html_content.replace('ABC1234567', data['registration_number'])
    html_content = html_content.replace('DON/2025/041', data['receipt_number'])
    html_content = html_content.replace('123 Gandhi Road, Dimna Road Mango JamshedpurMumbai, Maharashtra – 400001', data['office_address'])
    html_content = html_content.replace('ABCDE1234F', data['org_pan'])
    html_content = html_content.replace('CSR-908765', data['csr_number'])
    html_content = html_content.replace('AAETT3091Q24PT01', data['tax_exemption_12a'])  # 12A number
    html_content = html_content.replace('AAETT3091Q25PT01', data['tax_exemption_80g'])  # 80G number
    
    # Donor details
    html_content = html_content.replace('Mrs. Dewi Sharma', data['donor_name'])
    html_content = html_content.replace('Rs. 10,000', data['amount'])
    html_content = html_content.replace('Rupees Ten Thousand Only', data['amount_words'])
    html_content = html_content.replace('UTIB00012345678', data['payment_details'])
    html_content = html_content.replace('02/08/2025', data['donation_date'])
    html_content = html_content.replace('General Fund', data['purpose'])
    html_content = html_content.replace('5thn Residency, Navi Mumbai5th Floor,, Sion Residency, Navi Mumbai5th Floor, Sion Residency, Navi Mumbai5th Floor,, Sion Residency, Navi Mumbai5th Floor, Sion Residency, Navi Mumbai5th Floor, ai', data['donor_address'])
    html_content = html_content.replace('+91-9876543210', data['donor_phone'])
    html_content = html_content.replace('XYZP1234Q', data['donor_pan'])
    html_content = html_content.replace('dewi@example.com', data['donor_email'])
    
    return html_content

def replace_hardcoded_values_cert(html_content, data):
    """Replace hardcoded values in cert.html with real data"""
    # Organization name and details
    html_content = html_content.replace('THE STRAY ARMY CHARITABLE TRUST', data['org_name'])
    html_content = html_content.replace('The Stray Army Charitable Trust', data['org_name'])
    html_content = html_content.replace('EXAMPLE CHARITABLE TRUST', data['org_name'])
    html_content = html_content.replace('ABC1234567', data['registration_number'])
    html_content = html_content.replace('DON/2025/041', data['receipt_number'])
    html_content = html_content.replace('123 Gandhi Road, Dimna Road Mango Jamshedpur, Maharashtra – 400001', data['office_address'])
    html_content = html_content.replace('ABCDE1234F', data['donor_pan'])
    html_content = html_content.replace('CSR-908765', data['csr_number'])
    html_content = html_content.replace('12A-908765', data['tax_exemption_12a'])
    html_content = html_content.replace('80G-908765', data['tax_exemption_80g'])
    html_content = html_content.replace('+91 9876543210', data['org_phone'])
    html_content = html_content.replace('info@example.com', data['org_email'])
    html_content = html_content.replace('www.example.com', data['org_website'])
    html_content = html_content.replace('2025-04-01', data['donation_date_iso'])
    html_content = html_content.replace('100000', data['amount_only'])
    html_content = html_content.replace('Ten Thousand Only', data['amount_words'])
    html_content = html_content.replace('2025-26', data['financial_year'])
    html_content = html_content.replace('Education', data['purpose'])
    html_content = html_content.replace('John Doe', data['donor_name'])
    html_content = html_content.replace('Signatory Name', data['signatory_name'])
    html_content = html_content.replace('Designation', data['signatory_designation'])
    
    return html_content

def replace_hardcoded_values_thankyou(html_content, data):
    """Replace hardcoded values in templateThankYou.html with real data"""
    html_content = html_content.replace('{{ name }}', data['donor_name'])
    html_content = html_content.replace('EXAMPLE CHARITABLE TRUST', data['org_name_proper'])
    html_content = html_content.replace('Example Charitable Trust Team', f"{data['org_name_proper']} Team")
    
    return html_content

def convert_amount_to_words(amount):
    """Convert amount to words in Indian style"""
    try:
        amount_float = float(amount)
        words = num2words(amount_float, lang='en_IN').title()
        return f"Rupees {words} Only"
    except:
        return "Rupees Zero Only"

def get_financial_year(date_str):
    """Get financial year from date string"""
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = date_str
        
        year = date_obj.year
        if date_obj.month >= 4:  # April or later
            return f"{year}-{str(year + 1)[2:]}"
        else:  # January to March
            return f"{year - 1}-{str(year)[2:]}"
    except:
        current_year = datetime.now().year
        return f"{current_year}-{str(current_year + 1)[2:]}"

def combine_html_to_pdf(html_files, output_pdf, base_path=None):
    """
    Render each HTML in html_files using Playwright, concatenate their pages, 
    and write out a single PDF at output_pdf.
    """
    print(f"🚀 Starting PDF generation with Playwright for {len(html_files)} HTML files")
    
    temp_pdfs = []
    
    try:
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Process each HTML file
            for i, html_file in enumerate(html_files):
                print(f"📄 Processing HTML file {i+1}/{len(html_files)}: {html_file}")
                
                # Convert to absolute path and file:// URL
                if base_path:
                    # If HTML file is relative to base_path, make it absolute
                    if not os.path.isabs(html_file):
                        html_file = os.path.join(base_path, html_file)
                
                html_path = os.path.abspath(html_file)
                file_url = Path(html_path).as_uri()
                
                print(f"📂 Loading: {file_url}")
                
                # Load the HTML file
                page.goto(file_url, wait_until="networkidle")
                
                # Wait a bit for any remaining CSS/fonts to load
                page.wait_for_timeout(1000)  # 1 second
                
                # Generate temporary PDF for this HTML
                temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                temp_pdf_path = temp_pdf.name
                temp_pdf.close()
                
                # Generate PDF with proper dimensions (2000x1414 as per your templates)
                page.pdf(
                    path=temp_pdf_path,
                    width="2000px", 
                    height="1414px",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={
                        "top": "0px",
                        "bottom": "0px", 
                        "left": "0px",
                        "right": "0px"
                    }
                )
                
                temp_pdfs.append(temp_pdf_path)
                print(f"✅ Generated temporary PDF: {temp_pdf_path}")
            
            browser.close()
        
        # Combine all PDFs into one
        if len(temp_pdfs) == 1:
            # Only one PDF, just copy it
            shutil.copy2(temp_pdfs[0], output_pdf)
            print(f"📄 Single PDF copied to: {output_pdf}")
        else:
            # Multiple PDFs, combine them
            print(f"🔗 Combining {len(temp_pdfs)} PDFs into one...")
            combine_pdfs(temp_pdfs, output_pdf)
        
        print(f"📄✅ Successfully generated combined PDF: {output_pdf}")
        
    except Exception as e:
        print(f"❌ Error generating PDF with Playwright: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise
        
    finally:
        # Clean up temporary PDFs
        for temp_pdf in temp_pdfs:
            try:
                if os.path.exists(temp_pdf):
                    os.unlink(temp_pdf)
                    print(f"🗑️ Cleaned up temp PDF: {temp_pdf}")
            except Exception as e:
                print(f"⚠️ Warning: Could not delete temp PDF {temp_pdf}: {e}")

def combine_pdfs(pdf_files, output_path):
    """Combine multiple PDF files into one using PyPDF2"""
    try:
        pdf_merger = PyPDF2.PdfMerger()
        
        for pdf_file in pdf_files:
            print(f"📎 Adding PDF to merger: {pdf_file}")
            with open(pdf_file, 'rb') as f:
                pdf_merger.append(f)
        
        # Write the combined PDF
        with open(output_path, 'wb') as output_file:
            pdf_merger.write(output_file)
        
        pdf_merger.close()
        print(f"🔗✅ Successfully combined {len(pdf_files)} PDFs into: {output_path}")
        
    except Exception as e:
        print(f"❌ Error combining PDFs: {str(e)}")
        raise

def generate_receipt_pdf(donor_data, org_data, donation_data, donor_type="Individual", organization_id=None):
    """
    Generate receipt PDF based on donor type.
    Returns PDF bytes.
    """
    temp_dir = None
    try:
        print(f"Generating receipt for donor type: {donor_type}, org: {organization_id}")
        
        # Generate HTML templates with real data
        generated_files, temp_dir = generate_receipt_templates(donor_data, org_data, donation_data, organization_id)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        # Combine appropriate templates based on donor type
        if donor_type.lower() == "company":
            # Company: cert + receipt
            print("Generating Company receipt (Certificate + Receipt)")
            combine_html_to_pdf(
                [generated_files['cert'], generated_files['receipt']],
                temp_pdf_path,
                base_path=temp_dir
            )
        else:
            # Individual: thankyou + receipt
            print("Generating Individual receipt (Thank You + Receipt)")
            combine_html_to_pdf(
                [generated_files['thankyou'], generated_files['receipt']],
                temp_pdf_path,
                base_path=temp_dir
            )
        
        # Read PDF bytes
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Clean up temporary PDF file
        os.unlink(temp_pdf_path)
        
        print(f"✅ Successfully generated {len(pdf_bytes)} bytes PDF")
        return pdf_bytes
        
    except Exception as e:
        print(f"Error in generate_receipt_pdf: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    # 1) templateThankYou + receipt
    combine_html_to_pdf(
        ["templateThankYou.html", "receipt.html"],
        "thankyou_receipt.pdf"
    )

    # 2) cert + receipt
    combine_html_to_pdf(
        ["cert.html", "receipt.html"],
        "cert_receipt.pdf"
    )
