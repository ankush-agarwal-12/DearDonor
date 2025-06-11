import streamlit as st
import os
from dotenv import load_dotenv
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

# Define multiple default templates
FORMAL_TEMPLATE = """Dear {{Name}},

Thank you for your generous donation of Rs. {{Amount}} /- (Rupees {{AmountInWords}} Only) to {{orgName}}. Your contribution will help us make a significant impact in the lives of stray animals.

Receipt Details:
Receipt Number: {{receiptNumber}}
Amount: Rs. {{Amount}} /-
Date: {{Date}}
Purpose: {{Purpose}}
Mode of Payment: {{PaymentMode}}

We have attached the official donation receipt to this email for your records.

Thank you for your support in our mission to help stray animals.

Best regards,
{{orgDepartment}}
{{orgName}}

Contact Information:
Email: {{orgEmail}}
Phone: {{orgPhone}}
Website: {{orgSocial}}

This is an automated receipt. For any questions or concerns, please reach out to us at {{orgEmail}}."""

CONCISE_TEMPLATE = """Dear {{Name}},

Thank you for your generous donation of Rs. {{Amount}} /- to {{orgName}}. Your contribution will help us make a difference in the lives of stray animals.

Receipt Details:
- Receipt No: {{receiptNumber}}
- Date: {{Date}}

The official receipt is attached to this email.

Best regards,
{{orgDepartment}}
{{orgName}}
{{orgEmail}} | {{orgPhone}}
{{orgSocial}}

This is an automated receipt. For any questions or concerns, please reach out to us at {{orgEmail}}."""



DETAILED_TEMPLATE = """Dear {{Name}},

On behalf of {{orgName}}, I want to express our deepest gratitude for your generous donation of Rs. {{Amount}} /- received on {{Date}}. Your support is instrumental in our mission.

Your Donation Details:
Receipt Number: {{receiptNumber}}
Amount: Rs. {{Amount}} /-
Date of Donation: {{Date}}
Purpose: {{Purpose}}
Payment Mode: {{PaymentMode}}

Impact of Your Donation:
Your contribution helps us provide:
- Medical care for injured strays
- Food and shelter
- Vaccination programs
- Emergency rescue services

We have attached the official receipt to this email for your records.

With supporters like you, we can continue our work to make a lasting difference in the lives of stray animals. Thank you for being a part of our mission.

With sincere appreciation,

{{orgDepartment}}
{{orgName}}

Contact Information:
{{orgEmail}}
{{orgPhone}}
Follow us: {{orgSocial}}

This is an automated receipt. For any questions or concerns, please reach out to us at {{orgEmail}}."""

# Set the formal template as the default
DEFAULT_TEMPLATE = FORMAL_TEMPLATE
DEFAULT_SUBJECT = "Donation Receipt – Thank You, {{Name}}"

def save_template(template, subject):
    """Save the email template and subject to .env file"""
    env_path = '.env'
    
    # Read existing .env content
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add template and subject
    template_found = subject_found = False
    for i, line in enumerate(lines):
        if line.startswith('EMAIL_TEMPLATE='):
            lines[i] = f'EMAIL_TEMPLATE="""{template}"""\n'
            template_found = True
        elif line.startswith('EMAIL_SUBJECT='):
            lines[i] = f'EMAIL_SUBJECT="""{subject}"""\n'
            subject_found = True
    
    if not template_found:
        lines.append(f'\nEMAIL_TEMPLATE="""{template}"""\n')
    if not subject_found:
        lines.append(f'EMAIL_SUBJECT="""{subject}"""\n')

    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    # Update environment variables
    os.environ['EMAIL_TEMPLATE'] = template
    os.environ['EMAIL_SUBJECT'] = subject

def get_template():
    """Get the current email template"""
    return os.getenv('EMAIL_TEMPLATE', DEFAULT_TEMPLATE)

def get_subject():
    """Get the current email subject"""
    return os.getenv('EMAIL_SUBJECT', DEFAULT_SUBJECT)

def format_preview(text):
    """Convert HTML-style formatting to Streamlit markdown"""
    # Replace HTML tags with markdown
    formatted = text.replace('<b>', '**').replace('</b>', '**')\
                   .replace('<i>', '_').replace('</i>', '_')\
                   .replace('<u>', '__').replace('</u>', '__')\
                   .replace('<small>', '<span style="font-size: 0.8em">')\
                   .replace('</small>', '</span>')\
                   .replace('\n', '<br>')\
                   .replace('  ', '&nbsp;&nbsp;')  # Preserve multiple spaces
    return formatted

def email_settings_page():
    st.title("✉️ Email Template Settings")
    
    # Documentation in a clean, collapsible section
    with st.expander("📝 How to Use Templates", expanded=False):
        st.markdown("""
        ### Available Variables
        Insert these variables in your template - they will be automatically replaced with actual values:
        
        **Donor Details:**
        - `{{Name}}` - Donor's name
        - `{{Amount}}` - Donation amount
        - `{{AmountInWords}}` - Amount in words
        - `{{Date}}` - Donation date
        - `{{receiptNumber}}` - Receipt number
        - `{{Purpose}}` - Purpose of donation
        - `{{PaymentMode}}` - Payment method
        
        **Organization Details:**
        - `{{orgName}}` - Organization name
        - `{{orgDepartment}}` - Department name
        - `{{orgEmail}}` - Contact email
        - `{{orgPhone}}` - Contact phone
        - `{{orgSocial}}` - Social media links
        
        ### Simple Text Formatting
        - Start a line with `#` for a large heading
        - Use `**text**` for bold text
        - Use `*text*` for italic text
        - Start a line with `- ` for bullet points
        """)

    # Template Selection
    st.subheader("1. Choose Your Template")
    template_style = st.radio(
        "Select a template style:",
        options=["Simple", "Detailed", "Custom"],
        horizontal=True,
        help="Choose a pre-made template or create your own"
    )

    # Initialize the template based on selection
    if "current_template" not in st.session_state:
        st.session_state.current_template = get_template()

    if template_style == "Simple":
        current_template = CONCISE_TEMPLATE
    elif template_style == "Detailed":
        current_template = DETAILED_TEMPLATE
    else:  # Custom
        current_template = st.session_state.current_template

    # Template Editor
    st.subheader("2. Edit Template")
    new_template = st.text_area(
        "Edit your email template:",
        value=current_template,
        height=300,
        help="Use the variables listed above in double curly braces"
    )

    # Subject Line Editor
    st.subheader("3. Edit Subject Line")
    current_subject = get_subject()
    new_subject = st.text_input(
        "Email subject line:",
        value=current_subject,
        help="You can use {{Name}} in the subject line"
    )

    # Preview Section
    st.subheader("4. Preview")
    with st.expander("📋 View Template Preview", expanded=True):
        st.markdown("### Subject Line:")
        st.info(new_subject.replace("{{Name}}", "John Doe"))
        
        st.markdown("### Email Body:")
        preview = new_template\
            .replace("{{Name}}", "John Doe")\
            .replace("{{Amount}}", "1,000")\
            .replace("{{AmountInWords}}", "One Thousand")\
            .replace("{{Date}}", "01/01/2024")\
            .replace("{{receiptNumber}}", "REC123")\
            .replace("{{Purpose}}", "General Donation")\
            .replace("{{PaymentMode}}", "Online Transfer")\
            .replace("{{orgName}}", "Animal Welfare Organization")\
            .replace("{{orgDepartment}}", "Accounts Department")\
            .replace("{{orgEmail}}", "contact@example.org")\
            .replace("{{orgPhone}}", "+91 1234567890")\
            .replace("{{orgSocial}}", "Follow us on social media")
        
        st.markdown(format_preview(preview), unsafe_allow_html=True)

    # Save Button
    if st.button("💾 Save Template"):
        save_template(new_template, new_subject)
        st.success("✅ Template and subject line saved successfully!")
        st.session_state.current_template = new_template

def send_email(to_email, subject, body, receipt_path=None):
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = get_sender_email()
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add body text - preserve line breaks by using proper MIME type
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
        # Attach receipt if provided
        if receipt_path and os.path.exists(receipt_path):
            with open(receipt_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{os.path.basename(receipt_path)}"'
                )
                msg.attach(part)

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(get_sender_email(), get_email_password())
            server.send_message(msg)
            
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}" 