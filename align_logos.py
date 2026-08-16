import os
from PIL import Image, ImageDraw, ImageFont

def create_logo(title, output_path):
    # Canvas size
    width, height = 1024, 1024
    
    # Background color
    bg_color = (200, 255, 190, 255) # Lighter green to match image
    img = Image.new("RGBA", (width, height), bg_color)
    
    # Load assets
    truck = Image.open('frontend/public/assets/indian_truck.png').convert("RGBA")
    logo = Image.open('frontend/public/assets/fleetguard-logo.png').convert("RGBA")
    
    # Resize truck (make it fit well)
    truck = truck.resize((550, 550), Image.Resampling.LANCZOS)
    
    # Resize logo (make it fit well)
    logo = logo.resize((450, 450), Image.Resampling.LANCZOS)
    
    # Calculate positions
    # We want logo on the left, truck on the right, with truck overlapping the logo.
    overlap = 150
    total_width = logo.width + truck.width - overlap
    start_x = (width - total_width) // 2
    
    logo_x = start_x
    truck_x = start_x + logo.width - overlap
    
    # Center vertically in the top portion
    center_y = 400
    logo_y = center_y - (logo.height // 2)
    truck_y = center_y - (truck.height // 2) + 20 # Truck slightly lower for perspective
    
    # Paste logo first (behind)
    img.paste(logo, (logo_x, logo_y), logo)
    
    # Paste truck second (in front)
    img.paste(truck, (truck_x, truck_y), truck)
    
    # Add text
    draw = ImageDraw.Draw(img)
    try:
        # Use a bold font
        font_path = "C:/Windows/Fonts/arialbd.ttf"
        font = ImageFont.truetype(font_path, 90)
        font_sub = ImageFont.truetype(font_path, 80)
    except:
        font = ImageFont.load_default()
        font_sub = font
        
    text1 = "FleetGuard"
    text2 = title
    
    # Text color: match the green from the logo
    text_color = (38, 145, 80, 255)
    
    # text1
    bbox1 = draw.textbbox((0, 0), text1, font=font)
    t1_width = bbox1[2] - bbox1[0]
    t1_x = (width - t1_width) // 2
    t1_y = 680
    draw.text((t1_x, t1_y), text1, fill=text_color, font=font)
    
    # text2
    bbox2 = draw.textbbox((0, 0), text2, font=font_sub)
    t2_width = bbox2[2] - bbox2[0]
    t2_x = (width - t2_width) // 2
    t2_y = 800
    draw.text((t2_x, t2_y), text2, fill=text_color, font=font_sub)
    
    img.save(output_path)
    print(f"Saved {output_path}")

create_logo("Owner", "owner_logo.png")
create_logo("Driver", "driver_logo.png")
