from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    """Create a simple placeholder logo"""
    width = 200
    height = 200
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a simple circular logo
    draw.ellipse([10, 10, width-10, height-10], outline='#4A90E2', fill='white', width=3)
    
    # Draw a simple dog silhouette
    draw.ellipse([60, 50, 140, 130], fill='#4A90E2')  # Head
    draw.polygon([100, 90, 140, 150, 60, 150], fill='#4A90E2')  # Body
    
    # Save the logo
    os.makedirs('assets', exist_ok=True)
    image.save('assets/logo.png')

def create_signature():
    """Create a simple placeholder signature"""
    width = 300
    height = 100
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a simple signature-like curve
    points = [
        (50, 70),
        (100, 50),
        (150, 80),
        (200, 30),
        (250, 60)
    ]
    
    # Draw the main signature line
    draw.line(points, fill='#000000', width=2)
    
    # Add some decorative elements
    draw.line([40, 75, 260, 75], fill='#000000', width=1)
    
    # Save the signature
    os.makedirs('assets', exist_ok=True)
    image.save('assets/signature.png')

def create_butterfly(color='#FFB6C1'):
    """Create a simple butterfly decoration"""
    width = 100
    height = 100
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw butterfly wings
    draw.ellipse([10, 20, 45, 55], outline=color, width=2)
    draw.ellipse([55, 20, 90, 55], outline=color, width=2)
    draw.ellipse([20, 45, 45, 70], outline=color, width=2)
    draw.ellipse([55, 45, 80, 70], outline=color, width=2)
    
    # Draw body
    draw.line([50, 20, 50, 70], fill=color, width=2)
    
    # Save the butterfly
    os.makedirs('assets', exist_ok=True)
    image.save(f'assets/butterfly1.png')
    
    # Create a second butterfly with slight variations
    image2 = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw2 = ImageDraw.Draw(image2)
    
    # Draw slightly different wings
    draw2.ellipse([15, 25, 40, 50], outline=color, width=2)
    draw2.ellipse([60, 25, 85, 50], outline=color, width=2)
    draw2.ellipse([25, 40, 40, 65], outline=color, width=2)
    draw2.ellipse([60, 40, 75, 65], outline=color, width=2)
    
    # Draw body
    draw2.line([50, 25, 50, 65], fill=color, width=2)
    
    image2.save('assets/butterfly2.png')

if __name__ == "__main__":
    create_logo()
    create_signature()
    create_butterfly() 