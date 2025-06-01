from PIL import Image, ImageDraw, ImageFont
import os

def load_organization_logo():
    """Load the organization logo if it exists"""
    logo_path = 'assets/logo.png'
    if os.path.exists(logo_path):
        return Image.open(logo_path)
    return None

def load_signature():
    """Load the digital signature if it exists"""
    sig_path = 'assets/signature.png'
    if os.path.exists(sig_path):
        return Image.open(sig_path)
    return None

def create_receipt_preview(style="classic", settings=None):
    """Create a preview image for receipt template"""
    if settings is None:
        settings = {}
    
    # Create a new image with a white background
    width = 800
    height = 1000
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Load organization logo
    logo = load_organization_logo()
    
    # Common information from settings
    org_name = settings.get('org_name', "THE STRAY ARMY CHARITABLE TRUST")
    reg_info = f"Registered Under Indian Trusts Act, 1882. (Reg No. - {settings.get('reg_no', '2022/JSR/1732/BK4/109')})"
    office_address = settings.get('office_address', "Office - Flat No. 218, 2nd Floor, Block-A, Triveni Bhaskar City")
    pan_no = f"PAN - {settings.get('pan_no', 'AAETT3091Q')}"
    csr_no = f"CSR No. - {settings.get('csr_no', 'CSR00072375')}"
    contact = f"📞 {settings.get('phone', '7609874246')}  |  ✉️ {settings.get('email', 'thestrayarmy@gmail.com')}"
    website = settings.get('website', 'www.thestrayarmy.com')
    
    if style == "classic":
        # Draw border
        if settings.get('show_border', True):
            draw.rectangle([20, 20, width-20, height-20], outline=settings.get('border_color', 'black'), width=2)
        
        # Draw logo if exists
        if logo:
            logo_size = (100, 100)
            logo = logo.resize(logo_size)
            if settings.get('logo_position', 'left') == 'left':
                image.paste(logo, (40, 40))
                text_start = 160
            else:
                image.paste(logo, (width-140, 40))
                text_start = 40
        else:
            text_start = 40
        
        # Draw header text
        y = 50
        draw.text((text_start, y), org_name, fill='black')
        y += 30
        draw.text((text_start, y), reg_info, fill='black')
        y += 30
        draw.text((text_start, y), office_address, fill='black')
        y += 30
        draw.text((text_start, y), f"{pan_no}  |  {csr_no}", fill='black')
        y += 30
        draw.text((text_start, y), contact, fill='black')
        y += 30
        draw.text((text_start, y), website, fill='black')
        
        # Draw utilization certificate title
        y += 50
        draw.text((width//2, y), "UTILISATION CERTIFICATE", fill='black', anchor="mm")
        
        # Draw receipt details
        y += 50
        draw.text((50, y), "TSA/DR/24/025/ACK", fill='black')
        draw.text((width-200, y), "Date: 16/04/2024", fill='black')
        
        # Draw main content
        y += 50
        content = (
            "This is to certify that The Stray Army Charitable Trust has received Rs. 25,000.00 "
            "(Rupees Twenty Five Thousand Only) in FY 2024-25 in support of its efforts in "Animal Recovery Center". "
            "The details are as below:"
        )
        draw.text((50, y), content, fill='black')
        
        # Draw table
        y += 80
        table_data = [
            ["Receiving Date", "Name", "PAN", "Amount (Rs.)"],
            ["16th April, 2024", "Pebco Motors Ltd", "AABCP5073C", "25,000.00"]
        ]
        
        # Draw table headers and content
        col_widths = [150, 250, 150, 150]
        x_positions = [50]
        for width in col_widths[:-1]:
            x_positions.append(x_positions[-1] + width)
        
        for row_idx, row in enumerate(table_data):
            for col_idx, (text, width) in enumerate(zip(row, col_widths)):
                x = x_positions[col_idx]
                draw.text((x, y), text, fill='black')
                if row_idx == 0:  # Draw header underline
                    draw.line([x, y+20, x+width-10, y+20], fill='black')
            y += 40
        
        # Draw PAN information
        y += 20
        draw.text((50, y), f"The Permanent Account Number (PAN) of The Stay Army Charitable Trust - {settings.get('pan_no', 'AAETT3091Q')}.", fill='black')
        
        # Draw thank you message
        y += 40
        draw.text((50, y), "We thank you for your kind consideration.", fill='black')
        
        # Draw signature
        y += 60
        draw.text((50, y), "Sincerely,", fill='black')
        y += 40
        draw.text((50, y), "For The Stray Army Charitable Trust", fill='black')
        
        # Add digital signature if available
        signature = load_signature()
        if signature and settings.get('include_signature', True):
            sig_size = (150, 80)
            signature = signature.resize(sig_size)
            image.paste(signature, (50, y+20), signature)
            
        y += 120
        draw.text((50, y), "Piyush Agarwal", fill='black')
        y += 25
        draw.text((50, y), "Founder", fill='black')
        
    elif style == "modern":
        # Modern header with accent color
        header_color = settings.get('header_color', '#4A90E2')
        draw.rectangle([0, 0, width, 150], fill=header_color)
        
        # Add logo
        if logo:
            logo_size = (80, 80)
            logo = logo.resize(logo_size)
            if settings.get('logo_position', 'left') == 'left':
                image.paste(logo, (30, 35))
                text_start = 130
            else:
                image.paste(logo, (width-110, 35))
                text_start = 30
        else:
            text_start = 30
        
        # Header text in white
        draw.text((text_start, 40), org_name, fill='white')
        draw.text((text_start, 70), reg_info, fill='white')
        draw.text((text_start, 100), pan_no, fill='white')
        
        # Modern content layout
        y = 180
        draw.text((width//2, y), "UTILISATION CERTIFICATE", fill=header_color, anchor="mm")
        
        # Receipt details in modern grid
        y += 50
        draw.rectangle([40, y, width-40, y+400], outline='#ddd')
        
        # Table with modern styling
        table_data = [
            ["RECEIVING DATE", "16th April, 2024"],
            ["DONOR", "Pebco Motors Ltd"],
            ["AMOUNT", "Rs. 25,000.00"],
            ["PAN", "AABCP5073C"],
            ["PURPOSE", "Animal Recovery Center"]
        ]
        
        for i, (label, value) in enumerate(table_data):
            box_y = y + (i * 45)
            draw.rectangle([50, box_y, width-50, box_y+35], fill='#f8f9fa')
            draw.text((60, box_y+10), label, fill='#666666')
            draw.text((250, box_y+10), value, fill=header_color)
        
    elif style == "minimal":
        # Simple top border
        draw.line([0, 40, width, 40], fill='#000', width=2)
        
        # Add logo
        if logo:
            logo_size = (60, 60)
            logo = logo.resize(logo_size)
            if settings.get('logo_position', 'left') == 'left':
                image.paste(logo, (50, 60))
                text_start = 130
            else:
                image.paste(logo, (width-110, 60))
                text_start = 50
        else:
            text_start = 50
        
        # Minimal header
        y = 60
        draw.text((text_start, y), org_name, fill='black')
        y += 30
        draw.text((text_start, y), reg_info, fill='black')
        y += 30
        draw.text((text_start, y), pan_no, fill='black')
        
        # Clean, minimal content layout
        y += 50
        draw.text((width//2, y), "UTILISATION CERTIFICATE", fill='black', anchor="mm")
        
        # Receipt information in minimal style
        y += 50
        fields = [
            ("Receipt No.", "TSA/DR/24/025/ACK"),
            ("Date", "16/04/2024"),
            ("Amount", "Rs. 25,000.00"),
            ("Donor", "Pebco Motors Ltd"),
            ("PAN", "AABCP5073C"),
            ("Purpose", "Animal Recovery Center")
        ]
        
        for label, value in fields:
            draw.line([50, y-5, width-50, y-5], fill='#eee')
            draw.text((50, y), label, fill='#666666')
            draw.text((200, y), value, fill='black')
            y += 40
    
    # Save the preview
    os.makedirs('assets', exist_ok=True)
    preview_path = f'assets/receipt_preview_{style}.png'
    image.save(preview_path)
    return preview_path

def create_thankyou_preview(theme="butterflies", settings=None):
    """Create a preview image for thank you note template"""
    if settings is None:
        settings = {}
    
    # Create a new image with a white background
    width = 800
    height = 1000
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Load organization logo
    logo = load_organization_logo()
    signature = load_signature()
    
    # Get organization details
    org_name = settings.get('org_name', "THE STRAY ARMY CHARITABLE TRUST")
    
    if theme == "butterflies":
        # Add decorative butterfly border
        for i in range(4):
            x = 50 + (i * 200)
            draw.ellipse([x, 50, x+30, 80], outline='#FFB6C1')
            draw.ellipse([x+20, 50, x+50, 80], outline='#FFB6C1')
            draw.ellipse([x, height-80, x+30, height-50], outline='#FFB6C1')
            draw.ellipse([x+20, height-80, x+50, height-50], outline='#FFB6C1')
        
        # Add logo if available
        if logo and settings.get('show_logo', True):
            logo_size = (100, 100)
            logo = logo.resize(logo_size)
            image.paste(logo, (width//2 - 50, 100))
        
        # Draw content
        y = 250
        draw.text((width//2, y), "Thank You", fill='#4A90E2', anchor="mm")
        
        y += 80
        message = [
            "Dear [Donor Name],",
            "",
            "We are deeply grateful for your generous contribution of",
            "[Amount] to The Stray Army Charitable Trust.",
            "",
            "Your support helps us continue our mission of providing care",
            "and shelter to stray animals in need. Every donation makes",
            "a significant impact in improving the lives of these animals.",
            "",
            "Thank you for being a part of our cause and helping us",
            "make a difference in the community.",
            "",
            "With gratitude,",
            f"Team {org_name}"
        ]
        
        for line in message:
            draw.text((width//2, y), line, fill='black', anchor="mm")
            y += 30
        
        # Add signature if available
        if signature and settings.get('include_signature', True):
            sig_size = (150, 80)
            signature = signature.resize(sig_size)
            image.paste(signature, (width//2 - 75, y+20), signature)
            
    elif theme == "minimal":
        # Simple, clean design
        if logo and settings.get('show_logo', True):
            logo_size = (80, 80)
            logo = logo.resize(logo_size)
            image.paste(logo, (width//2 - 40, 50))
        
        y = 180
        draw.text((width//2, y), "Thank You", fill='black', anchor="mm")
        draw.line([width//4, y+30, width*3//4, y+30], fill='black')
        
        y += 80
        message = [
            "Dear [Donor Name],",
            "",
            "Thank you for your contribution of [Amount].",
            "Your support means the world to us and the animals we serve.",
            "",
            "Best regards,",
            f"Team {org_name}"
        ]
        
        for line in message:
            draw.text((width//2, y), line, fill='black', anchor="mm")
            y += 30
        
    elif theme == "professional":
        # Professional layout with company colors
        header_color = settings.get('header_color', '#4A90E2')
        draw.rectangle([0, 0, width, 150], fill=header_color)
        
        if logo and settings.get('show_logo', True):
            logo_size = (80, 80)
            logo = logo.resize(logo_size)
            image.paste(logo, (50, 35))
        
        draw.text((width//2, 75), "Thank You", fill='white', anchor="mm")
        
        y = 200
        message = [
            "Dear [Donor Name],",
            "",
            f"On behalf of {org_name}, we extend our sincere",
            "gratitude for your generous contribution of [Amount].",
            "",
            "Your support is invaluable to our mission of providing care",
            "and protection to stray animals in need. We are committed to",
            "using your contribution effectively and transparently.",
            "",
            "Thank you for partnering with us in making a difference.",
            "",
            "Sincerely,",
            f"Team {org_name}"
        ]
        
        for line in message:
            draw.text((50, y), line, fill='black')
            y += 30
        
        if signature and settings.get('include_signature', True):
            sig_size = (150, 80)
            signature = signature.resize(sig_size)
            image.paste(signature, (50, y+20), signature)
    
    # Save the preview
    os.makedirs('assets', exist_ok=True)
    preview_path = f'assets/thankyou_preview_{theme}.png'
    image.save(preview_path)
    return preview_path

if __name__ == "__main__":
    # Generate all preview styles
    for style in ["classic", "modern", "minimal"]:
        create_receipt_preview(style)
    
    for theme in ["butterflies", "minimal", "professional"]:
        create_thankyou_preview(theme) 