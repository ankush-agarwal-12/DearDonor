import streamlit as st
import os
from dotenv import load_dotenv
import html

load_dotenv()

# Define multiple default templates
FORMAL_TEMPLATE = """Dear {{Name}},

We hope this message finds you well. We want to express our heartfelt gratitude for your generous donation to The Stray Army Charitable Trust. Your support means a lot to us and plays a vital role in helping us care for the injured / sick strays.

As a token of our appreciation and for your records, we are pleased to provide you with the Money Receipt for your donation:

<b>Donor Name:</b> {{Name}}
<b>Donation Amount:</b> Rs. {{Amount}} /-
<b>Donation Date:</b> {{Date}}
<b>Receipt Number:</b> {{receiptNumber}}

Attached to this email, you will find the official donation receipt for your records. 

Once again, thank you for your generosity and support. Together, we can make a positive impact in our community.

Warm regards,


{{orgDepartment}}
<b>{{orgName}}</b>
<u>{{orgEmail}}</u>
{{orgPhone}}
<i>{{orgSocial}}</i>



<small>** This is a system-generated email, so we kindly ask you to review the receipt for any discrepancies. Please feel free to mail our team at ({{orgEmail}}), if you have any questions or require additional documentation. **</small>"""

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

<small>For any queries, please contact us at {{orgEmail}}</small>"""

DETAILED_TEMPLATE = """Dear {{Name}},

On behalf of {{orgName}}, I want to express our deepest gratitude for your generous donation of Rs. {{Amount}} /- received on {{Date}}. Your support is instrumental in our mission to provide care and shelter to stray animals in need.

Your Donation Details:
<b>Receipt Number:</b> {{receiptNumber}}
<b>Amount:</b> Rs. {{Amount}} /-
<b>Date of Donation:</b> {{Date}}

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
<b>{{orgName}}</b>
Contact Information:
<u>{{orgEmail}}</u>
{{orgPhone}}
Follow us: <i>{{orgSocial}}</i>

<small>This is an automated receipt. For any questions or concerns, please reach out to us at {{orgEmail}}.</small>"""

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
    
    # Documentation section in an expander
    with st.expander("📚 Template Documentation", expanded=True):
        # Content Placeholders
        st.markdown("""
        <style>
        .placeholder-box {
            border: 1px solid #444;
            border-radius: 5px;
            padding: 15px;
            margin: 8px 0;
            background-color: #2b2b2b;
        }
        .section-header {
            color: #00cc66;
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: bold;
        }
        .placeholder-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
            padding: 8px;
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 4px;
        }
        .placeholder-code {
            background-color: #333;
            padding: 2px 6px;
            border-radius: 3px;
            color: #00cc66;
            font-family: monospace;
        }
        .placeholder-arrow {
            color: #888;
            margin: 0 8px;
        }
        .placeholder-desc {
            color: #ddd;
        }
        .tips-list {
            margin: 0;
            padding-left: 20px;
            color: #ddd;
        }
        .tips-list li {
            margin: 5px 0;
        }
        .format-example {
            margin-top: 4px;
            color: #888;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<h3 class="section-header">📝 Content Placeholders</h3>', unsafe_allow_html=True)
            st.markdown('<div class="placeholder-box">', unsafe_allow_html=True)
            for placeholder, desc in {
                "{{Name}}": "Donor's full name",
                "{{Amount}}": "Donation amount",
                "{{Date}}": "Donation date",
                "{{receiptNumber}}": "Receipt number"
            }.items():
                st.markdown(f"""
                <div class="placeholder-item">
                    <span class="placeholder-code">{placeholder}</span>
                    <span class="placeholder-arrow">→</span>
                    <span class="placeholder-desc">{desc}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<h3 class="section-header">🏢 Organization Details</h3>', unsafe_allow_html=True)
            st.markdown('<div class="placeholder-box">', unsafe_allow_html=True)
            for placeholder, desc in {
                "{{orgName}}": "Your organization's name",
                "{{orgDepartment}}": "Department name",
                "{{orgEmail}}": "Contact email",
                "{{orgPhone}}": "Contact phone number",
                "{{orgSocial}}": "Social media links"
            }.items():
                st.markdown(f"""
                <div class="placeholder-item">
                    <span class="placeholder-code">{placeholder}</span>
                    <span class="placeholder-arrow">→</span>
                    <span class="placeholder-desc">{desc}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<h3 class="section-header">🎨 Text Formatting</h3>', unsafe_allow_html=True)
            st.markdown('<div class="placeholder-box">', unsafe_allow_html=True)
            
            formatting_examples = {
                "<b>text</b>": ("Bold text", "<b>Example</b>"),
                "<i>text</i>": ("Italic text", "<i>Example</i>"),
                "<u>text</u>": ("Underlined text", "<u>Example</u>"),
                "<small>text</small>": ("Smaller text", "<small>Example</small>")
            }
            
            for tag, (desc, example) in formatting_examples.items():
                st.markdown(f"""
                <div class="placeholder-item">
                    <span class="placeholder-code">{tag}</span>
                    <span class="placeholder-arrow">→</span>
                    <span class="placeholder-desc">{desc}</span>
                    <div class="format-example">Example: {example}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<h3 class="section-header">💡 Tips</h3>', unsafe_allow_html=True)
            st.markdown("""
            <div class="placeholder-box">
            <ul class="tips-list">
                <li>Use placeholders consistently throughout the template</li>
                <li>Preview your template before saving</li>
                <li>Test formatting with different content lengths</li>
                <li>Keep the email professional and concise</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

    # Rest of the existing code
    current_template = get_template()
    current_subject = get_subject()
    
    # Add additional styles for preview settings
    st.markdown("""
        <style>
        .preview-section {
            background-color: #2b2b2b;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
        }
        .preview-header {
            color: #00cc66;
            font-size: 1.1em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .preview-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 10px;
        }
        .preview-item {
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 8px;
        }
        .preview-label {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.form("email_template_form"):
        # Template Selection
        st.subheader("Choose a Template Style")
        template_style = st.radio(
            "Select a pre-defined template style or customize your own:",
            options=["Formal (Default)", "Concise", "Detailed", "Custom"],
            help="Choose a template style as a starting point. You can modify any template after selection."
        )

        # Set template based on selection
        if template_style == "Formal (Default)":
            current_template = FORMAL_TEMPLATE
        elif template_style == "Concise":
            current_template = CONCISE_TEMPLATE
        elif template_style == "Detailed":
            current_template = DETAILED_TEMPLATE
        else:  # Custom
            current_template = get_template()

        # Template Preview Cards
        st.markdown("### Template Previews")
        preview_col1, preview_col2 = st.columns(2)
        
        with preview_col1:
            with st.expander("📝 Formal Template"):
                st.markdown(format_preview(FORMAL_TEMPLATE.replace("{{Name}}", "John Doe")
                    .replace("{{Amount}}", "1000")
                    .replace("{{Date}}", "2024-03-21")
                    .replace("{{receiptNumber}}", "RCPT123")
                    .replace("{{orgName}}", "Organization Name")
                    .replace("{{orgDepartment}}", "Department")
                    .replace("{{orgEmail}}", "email@org.com")
                    .replace("{{orgPhone}}", "123-456-7890")
                    .replace("{{orgSocial}}", "Social Media")), unsafe_allow_html=True)
            
            with st.expander("📋 Detailed Template"):
                st.markdown(format_preview(DETAILED_TEMPLATE.replace("{{Name}}", "John Doe")
                    .replace("{{Amount}}", "1000")
                    .replace("{{Date}}", "2024-03-21")
                    .replace("{{receiptNumber}}", "RCPT123")
                    .replace("{{orgName}}", "Organization Name")
                    .replace("{{orgDepartment}}", "Department")
                    .replace("{{orgEmail}}", "email@org.com")
                    .replace("{{orgPhone}}", "123-456-7890")
                    .replace("{{orgSocial}}", "Social Media")), unsafe_allow_html=True)

        with preview_col2:
            with st.expander("✨ Concise Template"):
                st.markdown(format_preview(CONCISE_TEMPLATE.replace("{{Name}}", "John Doe")
                    .replace("{{Amount}}", "1000")
                    .replace("{{Date}}", "2024-03-21")
                    .replace("{{receiptNumber}}", "RCPT123")
                    .replace("{{orgName}}", "Organization Name")
                    .replace("{{orgDepartment}}", "Department")
                    .replace("{{orgEmail}}", "email@org.com")
                    .replace("{{orgPhone}}", "123-456-7890")
                    .replace("{{orgSocial}}", "Social Media")), unsafe_allow_html=True)

        # Email Subject
        st.subheader("Email Settings")
        subject = st.text_input(
            "Email Subject Line",
            value=current_subject,
            help="You can use {{Name}} in the subject line"
        )
        
        # Email Body
        template = st.text_area(
            "Email Body Template",
            value=current_template,
            height=500,
            help="Use the placeholders and formatting tags mentioned above"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save Template"):
                save_template(template, subject)
                st.success("✅ Email template saved successfully!")
        
        with col2:
            if st.form_submit_button("Reset to Default"):
                save_template(DEFAULT_TEMPLATE, DEFAULT_SUBJECT)
                st.rerun()

    # Show preview
    st.subheader("Preview")
    
    # Preview subject
    st.markdown("##### Subject Line Preview:")
    preview_subject = subject.replace("{{Name}}", "John Doe")
    st.info(preview_subject)
    
    # Preview body
    st.markdown("##### Email Body Preview:")
    st.info("This is how your email will look:")
    st.markdown("---")
    
    # Replace placeholders
    preview = template.replace("{{Name}}", "John Doe") \
                     .replace("{{Amount}}", "1000") \
                     .replace("{{Date}}", "2024-03-21") \
                     .replace("{{receiptNumber}}", "RCPT123") \
                     .replace("{{orgName}}", "Organization Name") \
                     .replace("{{orgDepartment}}", "Department") \
                     .replace("{{orgEmail}}", "email@org.com") \
                     .replace("{{orgPhone}}", "123-456-7890") \
                     .replace("{{orgSocial}}", "Social Media")
    
    # Format and display preview
    st.markdown(format_preview(preview), unsafe_allow_html=True)
    st.markdown("---") 