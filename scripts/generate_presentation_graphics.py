import os
import shutil
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_graphics():
    assets_dir = r"c:\Users\ratho\fleetguard\presentation_assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Copy hero image
    src_hero = r"C:\Users\ratho\.gemini\antigravity\brain\5f8cefa9-a2ba-4666-be93-03868252a9b0\vahan_3d_truck_hero_1795469576341.jpg"
    dst_hero = os.path.join(assets_dir, "vahan_3d_truck_hero.jpg")
    if os.path.exists(src_hero):
        shutil.copy(src_hero, dst_hero)
        print(f"Copied hero image to {dst_hero}")
    else:
        print(f"Source hero image not found at {src_hero}")

    # Helper: create rounded rectangle with gradient & glow
    def draw_glow_box(draw, xy, fill_color, glow_color, radius=20, glow_width=8):
        x1, y1, x2, y2 = xy
        for i in range(glow_width, 0, -2):
            alpha = int(40 * (1 - i / glow_width))
            draw.rounded_rectangle([x1 - i, y1 - i, x2 + i, y2 + i], radius=radius + i, outline=glow_color)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill_color, outline=glow_color, width=2)

    # 2. 3D Telematics Hardware Asset Graphic
    img_dev = Image.new("RGBA", (1200, 900), (15, 23, 42, 255))
    d_dev = ImageDraw.Draw(img_dev)
    
    # Subtle background grid lines
    for x in range(0, 1200, 60):
        d_dev.line([(x, 0), (x, 900)], fill=(30, 41, 59, 120), width=1)
    for y in range(0, 900, 60):
        d_dev.line([(0, y), (1200, y)], fill=(30, 41, 59, 120), width=1)

    # Main 3D Box (Isometric Tracker Unit)
    # Base shadow
    d_dev.polygon([(300, 620), (600, 770), (900, 620), (600, 470)], fill=(5, 10, 20, 200))
    # Top face
    d_dev.polygon([(600, 260), (880, 400), (600, 540), (320, 400)], fill=(30, 41, 59, 255), outline=(16, 185, 129, 255))
    # Left face
    d_dev.polygon([(320, 400), (600, 540), (600, 660), (320, 520)], fill=(15, 23, 42, 255), outline=(16, 185, 129, 200))
    # Right face
    d_dev.polygon([(600, 540), (880, 400), (880, 520), (600, 660)], fill=(20, 30, 48, 255), outline=(16, 185, 129, 200))
    
    # Status LEDs on Top Face
    led_positions = [(520, 390, (16, 185, 129)), (600, 430, (59, 130, 246)), (680, 470, (234, 179, 8))]
    for lx, ly, col in led_positions:
        d_dev.ellipse([lx - 16, ly - 16, lx + 16, ly + 16], fill=col)
        d_dev.ellipse([lx - 26, ly - 26, lx + 26, ly + 26], outline=col, width=2)
        
    # Telemetry Signal Rings radiating upwards
    for r in range(40, 180, 35):
        d_dev.arc([600 - r*2, 220 - r, 600 + r*2, 220 + r], start=180, end=360, fill=(16, 185, 129, 255 - r), width=3)
        
    # Floating Holographic Data Badges
    d_dev.rounded_rectangle([150, 150, 420, 240], radius=12, fill=(15, 23, 42, 230), outline=(16, 185, 129), width=2)
    d_dev.text((170, 170), "IMEI: 864201048821932", fill=(255, 255, 255))
    d_dev.text((170, 200), "STATUS: ACTIVE TELEMETRY", fill=(16, 185, 129))

    d_dev.rounded_rectangle([780, 150, 1070, 240], radius=12, fill=(15, 23, 42, 230), outline=(59, 130, 246), width=2)
    d_dev.text((800, 170), "PROTOCOLS: 7 SUPPORTED", fill=(255, 255, 255))
    d_dev.text((800, 200), "AIS-140 / GT06 / TELTONIKA", fill=(59, 130, 246))

    d_dev.rounded_rectangle([750, 680, 1050, 770], radius=12, fill=(15, 23, 42, 230), outline=(245, 158, 11), width=2)
    d_dev.text((770, 700), "SECURITY: AES-GCM ENCRYPTED", fill=(255, 255, 255))
    d_dev.text((770, 730), "QUARANTINE PROTECTION", fill=(245, 158, 11))

    dev_path = os.path.join(assets_dir, "vahan_3d_telematics_device.png")
    img_dev.save(dev_path)
    print(f"Generated {dev_path}")

    # 3. 3D Route Deviation Graphic
    img_route = Image.new("RGBA", (1200, 900), (15, 23, 42, 255))
    d_route = ImageDraw.Draw(img_route)
    
    # Grid
    for x in range(0, 1200, 50):
        d_route.line([(x, 0), (x, 900)], fill=(30, 41, 59, 100), width=1)
    for y in range(0, 900, 50):
        d_route.line([(0, y), (1200, y)], fill=(30, 41, 59, 100), width=1)

    # Approved Corridor (Green Glow Ribbon)
    approved_points = [(150, 700), (350, 580), (550, 480), (750, 360), (950, 220), (1050, 180)]
    for i in range(len(approved_points) - 1):
        # Outer glow
        d_route.line([approved_points[i], approved_points[i+1]], fill=(16, 185, 129, 60), width=28)
        # Main corridor
        d_route.line([approved_points[i], approved_points[i+1]], fill=(16, 185, 129, 255), width=8)

    # Deviation Path (Red / Orange Warning)
    deviated_points = [(550, 480), (620, 600), (750, 700), (880, 650)]
    for i in range(len(deviated_points) - 1):
        d_route.line([deviated_points[i], deviated_points[i+1]], fill=(239, 68, 68, 80), width=22)
        d_route.line([deviated_points[i], deviated_points[i+1]], fill=(239, 68, 68, 255), width=6)

    # Waypoints & Markers
    for pt in approved_points:
        d_route.ellipse([pt[0]-12, pt[1]-12, pt[0]+12, pt[1]+12], fill=(16, 185, 129), outline=(255, 255, 255), width=3)
    
    # Deviation Alert Pin
    d_route.ellipse([880-18, 650-18, 880+18, 650+18], fill=(239, 68, 68), outline=(255, 255, 255), width=4)
    for r in range(25, 70, 15):
        d_route.ellipse([880-r, 650-r, 880+r, 650+r], outline=(239, 68, 68, 255 - r*3), width=2)

    # Floating Alert Box
    d_route.rounded_rectangle([720, 720, 1100, 830], radius=14, fill=(15, 23, 42, 240), outline=(239, 68, 68), width=2)
    d_route.text((750, 740), "ROUTE DEVIATION DETECTED", fill=(239, 68, 68))
    d_route.text((750, 770), "Off-Corridor Delta: 14.8 km | Toll Bypass", fill=(255, 255, 255))
    d_route.text((750, 795), "Trigger: Automated Rule Engine (FastAPI)", fill=(148, 163, 184))

    # Approved Corridor Legend Box
    d_route.rounded_rectangle([120, 140, 500, 230], radius=14, fill=(15, 23, 42, 240), outline=(16, 185, 129), width=2)
    d_route.text((140, 160), "AUTHORIZED HIGHWAY CORRIDOR", fill=(16, 185, 129))
    d_route.text((140, 190), "Geo-corridor adherence: 98.4% Baseline", fill=(255, 255, 255))

    route_path = os.path.join(assets_dir, "vahan_3d_route_deviation.png")
    img_route.save(route_path)
    print(f"Generated {route_path}")

    # 4. 3D Fuel Intelligence & Anomaly Graphic
    img_fuel = Image.new("RGBA", (1200, 900), (15, 23, 42, 255))
    d_fuel = ImageDraw.Draw(img_fuel)
    
    # Grid
    for x in range(0, 1200, 50):
        d_fuel.line([(x, 0), (x, 900)], fill=(30, 41, 59, 100), width=1)
    for y in range(0, 900, 50):
        d_fuel.line([(0, y), (1200, y)], fill=(30, 41, 59, 100), width=1)

    # 3D Fuel Gauge Arc
    gauge_center = (600, 450)
    for r in range(220, 260, 4):
        d_fuel.arc([gauge_center[0]-r, gauge_center[1]-r, gauge_center[0]+r, gauge_center[1]+r], start=140, end=400, fill=(30, 41, 59, 200), width=4)
    # Active fuel arc (Green to Amber)
    for r in range(224, 256, 4):
        d_fuel.arc([gauge_center[0]-r, gauge_center[1]-r, gauge_center[0]+r, gauge_center[1]+r], start=140, end=320, fill=(16, 185, 129, 255), width=4)
        
    # Needle
    needle_angle = math.radians(310)
    nx = gauge_center[0] + 190 * math.cos(needle_angle)
    ny = gauge_center[1] + 190 * math.sin(needle_angle)
    d_fuel.line([gauge_center, (nx, ny)], fill=(245, 158, 11), width=8)
    d_fuel.ellipse([gauge_center[0]-24, gauge_center[1]-24, gauge_center[0]+24, gauge_center[1]+24], fill=(245, 158, 11), outline=(255, 255, 255), width=3)

    # Center Text
    d_fuel.text((540, 400), "68%", fill=(255, 255, 255))
    d_fuel.text((515, 435), "CURRENT LEVEL", fill=(148, 163, 184))

    # Anomaly Alert Box
    d_fuel.rounded_rectangle([680, 580, 1100, 720], radius=14, fill=(15, 23, 42, 240), outline=(239, 68, 68), width=2)
    d_fuel.text((710, 605), "SIPHONING / THEFT ANOMALY", fill=(239, 68, 68))
    d_fuel.text((710, 635), "Sudden 42L Drop While Ignition OFF", fill=(255, 255, 255))
    d_fuel.text((710, 665), "Validated by backend/routers/fuel_domain.py", fill=(148, 163, 184))

    # Capacity Rule Card
    d_fuel.rounded_rectangle([120, 580, 540, 720], radius=14, fill=(15, 23, 42, 240), outline=(16, 185, 129), width=2)
    d_fuel.text((150, 605), "TANK CAPACITY PHYSICS CHECK", fill=(16, 185, 129))
    d_fuel.text((150, 635), "Max Spec: 350L | Billed: 420L (FLAGGED)", fill=(255, 255, 255))
    d_fuel.text((150, 665), "Automated Invoice Reconciliation Engine", fill=(148, 163, 184))

    fuel_path = os.path.join(assets_dir, "vahan_3d_fuel_gauge.png")
    img_fuel.save(fuel_path)
    print(f"Generated {fuel_path}")

    # 5. 3D Ecosystem Architecture Graphic
    img_eco = Image.new("RGBA", (1200, 900), (15, 23, 42, 255))
    d_eco = ImageDraw.Draw(img_eco)
    
    # Grid
    for x in range(0, 1200, 50):
        d_eco.line([(x, 0), (x, 900)], fill=(30, 41, 59, 100), width=1)
    for y in range(0, 900, 50):
        d_eco.line([(0, y), (1200, y)], fill=(30, 41, 59, 100), width=1)

    # 4 Nodes: Web Console (Top), Driver App (Left), Telematics Gateway (Right), Core API & DB (Center)
    center_hub = (600, 450)
    nodes = [
        ((600, 160), "FLEET OWNER DASHBOARD", "React 18 + Tailwind + Leaflet", (16, 185, 129)),
        ((220, 540), "DRIVER MOBILE CLIENT", "Flutter Mobile App + Offline Queue", (59, 130, 246)),
        ((980, 540), "TELEMATICS GATEWAY", "Traccar + Multi-Protocol Decoders", (245, 158, 11)),
        ((600, 720), "SECURITY & VAULT", "AES-GCM Encryption + Quarantine", (168, 85, 247))
    ]

    # Connecting data pipes with glowing streams
    for pos, _, _, col in nodes:
        d_eco.line([pos, center_hub], fill=(*col[:3], 120), width=8)
        d_eco.line([pos, center_hub], fill=(*col[:3], 255), width=2)

    # Central Hub
    d_eco.ellipse([center_hub[0]-80, center_hub[1]-80, center_hub[0]+80, center_hub[1]+80], fill=(30, 41, 59), outline=(16, 185, 129), width=4)
    d_eco.text((center_hub[0]-55, center_hub[1]-20), "VAHAN CORE", fill=(255, 255, 255))
    d_eco.text((center_hub[0]-50, center_hub[1]+5), "FastAPI + PG", fill=(16, 185, 129))

    # Node Boxes
    for pos, title, sub, col in nodes:
        w, h = 320, 100
        box = [pos[0]-w//2, pos[1]-h//2, pos[0]+w//2, pos[1]+h//2]
        d_eco.rounded_rectangle(box, radius=14, fill=(15, 23, 42, 245), outline=col, width=2)
        d_eco.text((box[0]+20, box[1]+25), title, fill=col)
        d_eco.text((box[0]+20, box[1]+55), sub, fill=(226, 232, 240))

    eco_path = os.path.join(assets_dir, "vahan_3d_ecosystem.png")
    img_eco.save(eco_path)
    print(f"Generated {eco_path}")

if __name__ == "__main__":
    create_graphics()
