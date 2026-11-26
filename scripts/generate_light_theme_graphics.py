import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_light_theme_graphics():
    assets_dir = r"c:\Users\ratho\fleetguard\presentation_assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    # Palette
    BG_LIGHT = (247, 250, 248, 255)       # #F7FAF8
    WHITE = (255, 255, 255, 255)          # #FFFFFF
    PRIMARY_GREEN = (37, 132, 91, 255)    # #25845B
    SOFT_GREEN = (228, 243, 234, 255)     # #E4F3EA
    DARK_TEXT = (36, 53, 45, 255)         # #24352D
    SEC_TEXT = (100, 115, 107, 255)       # #64736B
    BORDER = (225, 234, 228, 255)         # #E1EAE4
    ACCENT = (167, 216, 184, 255)         # #A7D8B8
    ALERT_RED = (220, 38, 38, 255)        # #DC2626
    ALERT_BG = (254, 242, 242, 255)       # Soft red
    AMBER = (217, 119, 6, 255)            # #D97706
    AMBER_BG = (254, 243, 199, 255)       # Soft amber

    # Helper: draw subtle card with border & soft shadow
    def draw_card(draw, box, radius=16, fill=WHITE, outline=BORDER, width=2):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    # -------------------------------------------------------------
    # 1. COVER VISUAL: 3D Digital Logistics Network (No trucks!)
    # -------------------------------------------------------------
    img_cover = Image.new("RGBA", (1400, 1000), BG_LIGHT)
    d = ImageDraw.Draw(img_cover)
    
    # Background subtle grid pattern
    for x in range(0, 1400, 50):
        d.line([(x, 0), (x, 1000)], fill=(235, 242, 238, 180), width=1)
    for y in range(0, 1000, 50):
        d.line([(0, y), (1400, y)], fill=(235, 242, 238, 180), width=1)
        
    # Central isometric network platform
    center = (700, 520)
    # Isometric rings / planes
    for r in [380, 280, 180]:
        # Draw ellipse for isometric plane
        d.ellipse([center[0]-r, center[1]-r*0.55, center[0]+r, center[1]+r*0.55], outline=ACCENT, width=2)
        
    # Hub nodes
    nodes = [
        ((700, 320), "CENTRAL HUB", "FastAPI Core", PRIMARY_GREEN),
        ((440, 440), "FLEET PORTAL", "Web Dashboard", PRIMARY_GREEN),
        ((960, 440), "GATEWAY", "Traccar IoT", PRIMARY_GREEN),
        ((360, 620), "DRIVER CLIENT", "Flutter Mobile", (59, 130, 246, 255)),
        ((1040, 620), "TELEMATICS", "7 Protocol Decoders", PRIMARY_GREEN),
        ((540, 740), "FUEL ENGINE", "Siphoning AI", ALERT_RED),
        ((860, 740), "SECURITY VAULT", "Quarantine Isolation", PRIMARY_GREEN)
    ]
    
    # Draw glowing connection paths between nodes
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            if abs(nodes[i][0][0] - nodes[j][0][0]) < 450:
                d.line([nodes[i][0], nodes[j][0]], fill=(167, 216, 184, 140), width=2)

    # Connect to center
    for pos, _, _, _ in nodes:
        d.line([pos, center], fill=PRIMARY_GREEN, width=3)
        
    # Center core node
    d.ellipse([center[0]-50, center[1]-30, center[0]+50, center[1]+30], fill=WHITE, outline=PRIMARY_GREEN, width=4)
    d.text((center[0]-28, center[1]-10), "VAHAN", fill=PRIMARY_GREEN)

    # Node badges
    for pos, label, sub, col in nodes:
        bx = [pos[0]-90, pos[1]-35, pos[0]+90, pos[1]+35]
        draw_card(d, bx, radius=12, fill=WHITE, outline=col, width=2)
        # Node icon dot
        d.ellipse([pos[0]-75, pos[1]-10, pos[0]-55, pos[1]+10], fill=col)
        d.text((pos[0]-45, pos[1]-18), label, fill=DARK_TEXT)
        d.text((pos[0]-45, pos[1]+2), sub, fill=SEC_TEXT)

    # Floating telemetry metric cards around periphery
    cards_data = [
        ((150, 160), "MULTI-TENANCY", "Cryptographic Isolation", PRIMARY_GREEN),
        ((1050, 160), "HMAC WEBHOOKS", "Encrypted Ingestion", PRIMARY_GREEN),
        ((1060, 840), "FUEL PROTECTION", "Tank Physics Validation", ALERT_RED),
        ((140, 840), "GEO-CORRIDORS", "Automated Deviation Alerts", PRIMARY_GREEN)
    ]
    for pos, t1, t2, col in cards_data:
        box = [pos[0], pos[1], pos[0]+240, pos[1]+75]
        draw_card(d, box, radius=10, fill=WHITE, outline=BORDER, width=2)
        d.text((pos[0]+16, pos[1]+14), t1, fill=col)
        d.text((pos[0]+16, pos[1]+40), t2, fill=SEC_TEXT)

    img_cover.save(os.path.join(assets_dir, "light_cover_network.png"))
    print("Generated light_cover_network.png")

    # -------------------------------------------------------------
    # 2. DASHBOARD MOCKUP (Light Theme, Clean UI, Sample Data)
    # -------------------------------------------------------------
    img_dash = Image.new("RGBA", (1400, 950), BG_LIGHT)
    d = ImageDraw.Draw(img_dash)
    
    # Outer application window container
    draw_card(d, [40, 30, 1360, 920], radius=16, fill=WHITE, outline=BORDER, width=2)
    
    # Top navbar
    d.rounded_rectangle([40, 30, 1360, 100], radius=16, fill=SOFT_GREEN)
    d.rectangle([40, 80, 1360, 100], fill=SOFT_GREEN) # square off bottom
    d.line([(40, 100), (1360, 100)], fill=BORDER, width=1)
    
    # Logo text & Nav links
    d.text((70, 52), "VAHAN FLEET OPERATOR", fill=PRIMARY_GREEN)
    d.text((340, 55), "Dashboard    Vehicles    Drivers    Trips    Telematics    Fuel Analytics    Settings", fill=DARK_TEXT)
    
    # "Sample Dashboard Data" watermark badge
    d.rounded_rectangle([1120, 48, 1320, 82], radius=8, fill=WHITE, outline=ACCENT, width=1)
    d.text((1140, 57), "Sample Dashboard Data", fill=SEC_TEXT)
    
    # Left Sidebar (compact)
    d.rectangle([40, 101, 240, 918], fill=(250, 252, 251, 255))
    d.line([(240, 101), (240, 918)], fill=BORDER, width=1)
    menu_items = ["Overview", "Live GPS Map", "Active Trips (14)", "Vehicle Registry", "Driver Verification", "Fuel Siphon Alerts", "Hardware Devices", "Audit Reports"]
    for idx, item in enumerate(menu_items):
        y = 130 + idx * 45
        if idx == 0:
            d.rounded_rectangle([55, y-8, 225, y+24], radius=6, fill=SOFT_GREEN)
            d.text((70, y), item, fill=PRIMARY_GREEN)
        else:
            d.text((70, y), item, fill=DARK_TEXT)

    # Main Content Area: 4 Metric Cards across top
    kpis = [
        ("TOTAL FLEET", "128 Vehicles", "94% In Operation", PRIMARY_GREEN),
        ("ACTIVE HIGHWAY TRIPS", "42 In Transit", "On-Time: 96.4%", PRIMARY_GREEN),
        ("MAINTENANCE QUEUE", "6 Scheduled", "Preventive Service", AMBER),
        ("ACTIVE EXCEPTIONS", "2 Route Alerts", "1 Tank Flag", ALERT_RED)
    ]
    for idx, (title, val, sub, col) in enumerate(kpis):
        cx = 265 + idx * 270
        draw_card(d, [cx, 125, cx + 250, 220], radius=10, fill=WHITE, outline=BORDER, width=1)
        d.text((cx + 16, 140), title, fill=SEC_TEXT)
        d.text((cx + 16, 162), val, fill=col)
        d.text((cx + 16, 192), sub, fill=DARK_TEXT)

    # Middle Section: Active Trips Table (Left) & Mini Map (Right)
    # Table Box
    draw_card(d, [265, 240, 920, 560], radius=12, fill=WHITE, outline=BORDER, width=1)
    d.text((285, 255), "Live Fleet Telematics & Vehicle Status", fill=DARK_TEXT)
    d.text((760, 258), "Refreshes via WebSocket", fill=SEC_TEXT)
    d.line([(265, 285), (920, 285)], fill=BORDER, width=1)
    
    # Table Headers
    cols = [(285, "Vehicle Plate"), (420, "Assigned Driver"), (560, "Corridor"), (710, "Speed"), (810, "Status")]
    for x, h in cols:
        d.text((x, 295), h, fill=SEC_TEXT)
    d.line([(265, 320), (920, 320)], fill=BORDER, width=1)
    
    rows = [
        ("MH-12-RN-4821", "Rajesh Sharma", "Mumbai → Pune", "64 km/h", "IN TRANSIT", PRIMARY_GREEN, SOFT_GREEN),
        ("DL-01-AK-9042", "Gurpreet Singh", "Delhi → Jaipur", "58 km/h", "IN TRANSIT", PRIMARY_GREEN, SOFT_GREEN),
        ("KA-04-MB-1193", "Venkatesh Rao", "Bangalore Hub", "0 km/h", "IDLE / DEPOT", SEC_TEXT, (241, 245, 249, 255)),
        ("GJ-06-TR-7712", "Mohammad Arif", "Surat → Vadodara", "71 km/h", "OFF ROUTE", ALERT_RED, ALERT_BG),
        ("TN-09-CQ-3341", "Murugan K.", "Chennai → Salem", "62 km/h", "IN TRANSIT", PRIMARY_GREEN, SOFT_GREEN)
    ]
    for r_idx, (plate, drv, corr, spd, st, col, bg_pill) in enumerate(rows):
        ry = 335 + r_idx * 42
        d.text((285, ry), plate, fill=DARK_TEXT)
        d.text((420, ry), drv, fill=DARK_TEXT)
        d.text((560, ry), corr, fill=SEC_TEXT)
        d.text((710, ry), spd, fill=DARK_TEXT)
        # Status pill
        d.rounded_rectangle([805, ry-4, 905, ry+18], radius=6, fill=bg_pill)
        d.text((815, ry), st, fill=col)
        if r_idx < 4:
            d.line([(265, ry+30), (920, ry+30)], fill=(245, 248, 246, 255), width=1)

    # Mini Map Panel (Right)
    draw_card(d, [940, 240, 1340, 560], radius=12, fill=(244, 248, 246, 255), outline=BORDER, width=1)
    d.text((960, 255), "Highway Corridor Geo-Tracking", fill=DARK_TEXT)
    # Simulated map grid and route paths
    d.line([(960, 480), (1050, 420), (1160, 380), (1280, 320)], fill=PRIMARY_GREEN, width=4) # green corridor
    # Waypoint pins
    for px, py in [(960, 480), (1050, 420), (1160, 380), (1280, 320)]:
        d.ellipse([px-6, py-6, px+6, py+6], fill=WHITE, outline=PRIMARY_GREEN, width=2)
    # Active vehicle marker on map
    d.ellipse([1160-12, 380-12, 1160+12, 380+12], fill=PRIMARY_GREEN, outline=WHITE, width=2)
    d.rounded_rectangle([1110, 340, 1220, 365], radius=4, fill=DARK_TEXT)
    d.text((1120, 345), "MH-12-RN: 64 km/h", fill=WHITE)

    # Bottom Row: Fuel Anomaly Alert (Left) & Document Approval Queue (Right)
    draw_card(d, [265, 580, 790, 900], radius=12, fill=WHITE, outline=BORDER, width=1)
    d.text((285, 595), "Fuel Intelligence & Exception Monitor", fill=DARK_TEXT)
    d.rounded_rectangle([285, 630, 770, 710], radius=8, fill=ALERT_BG, outline=ALERT_RED, width=1)
    d.text((305, 642), "UNEXPECTED TANK DROP DETECTED (GJ-06-TR-7712)", fill=ALERT_RED)
    d.text((305, 668), "Drop: 38 Liters | Ignition: OFF | Location: NH-48 Km 182 | Anomaly Flagged", fill=DARK_TEXT)

    d.rounded_rectangle([285, 725, 770, 805], radius=8, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=1)
    d.text((305, 737), "TANK CAPACITY PHYSICS CHECK PASSED (MH-12-RN-4821)", fill=PRIMARY_GREEN)
    d.text((305, 763), "Receipt: 280L | Tank Spec: 350L | Distance Delta Reconciled: 920 km", fill=DARK_TEXT)

    d.rounded_rectangle([285, 820, 770, 885], radius=8, fill=(248, 250, 249, 255), outline=BORDER, width=1)
    d.text((305, 835), "Cost Per Km Metric: INR 28.4 / km (Fleet Average Baseline)", fill=SEC_TEXT)

    draw_card(d, [810, 580, 1340, 900], radius=12, fill=WHITE, outline=BORDER, width=1)
    d.text((830, 595), "Driver Document Verification Queue", fill=DARK_TEXT)
    doc_items = [
        ("Suresh Patil", "Commercial DL Renewal", "Exp: 2029", "PENDING REVIEW", AMBER, AMBER_BG),
        ("Amit Verma", "Medical Fitness Certificate", "Verified Doctor", "APPROVED", PRIMARY_GREEN, SOFT_GREEN),
        ("Kavita Yadav", "Heavy Transport License", "Missing Stamp", "REJECTED (Notes Sent)", ALERT_RED, ALERT_BG)
    ]
    for idx, (name, doc, exp, st, col, bg_p) in enumerate(doc_items):
        dy = 635 + idx * 75
        d.rounded_rectangle([830, dy, 1320, dy+65], radius=8, fill=(252, 254, 253, 255), outline=BORDER, width=1)
        d.text((845, dy+12), name, fill=DARK_TEXT)
        d.text((845, dy+35), doc + " • " + exp, fill=SEC_TEXT)
        d.rounded_rectangle([1150, dy+16, 1305, dy+44], radius=6, fill=bg_p)
        d.text((1160, dy+22), st, fill=col)

    img_dash.save(os.path.join(assets_dir, "light_dashboard_mockup.png"))
    print("Generated light_dashboard_mockup.png")

    # -------------------------------------------------------------
    # 3. DRIVER SMARTPHONE MOCKUP (Light Theme, Flutter Client)
    # -------------------------------------------------------------
    img_phone = Image.new("RGBA", (800, 1100), BG_LIGHT)
    dp = ImageDraw.Draw(img_phone)
    
    # Phone outer body
    phone_box = [180, 40, 620, 1060]
    dp.rounded_rectangle(phone_box, radius=48, fill=(36, 53, 45, 255), outline=(20, 30, 25, 255), width=4)
    # Phone screen
    screen_box = [200, 70, 600, 1030]
    dp.rounded_rectangle(screen_box, radius=36, fill=WHITE)
    
    # Top speaker notch & status bar
    dp.rounded_rectangle([340, 80, 460, 95], radius=8, fill=(36, 53, 45, 255))
    dp.text((225, 82), "09:41", fill=DARK_TEXT)
    dp.text((535, 82), "4G • 98%", fill=DARK_TEXT)
    
    # App Header
    dp.rectangle([200, 105, 600, 165], fill=PRIMARY_GREEN)
    dp.text((225, 122), "VAHAN DRIVER CLIENT", fill=WHITE)
    # Offline sync badge
    dp.rounded_rectangle([450, 120, 580, 148], radius=6, fill=WHITE)
    dp.text((465, 128), "● ONLINE (SYNCED)", fill=PRIMARY_GREEN)

    # Active Trip Card
    draw_card(dp, [215, 180, 585, 340], radius=12, fill=SOFT_GREEN, outline=ACCENT, width=1)
    dp.text((230, 195), "ACTIVE TRIP: TRP-88219", fill=PRIMARY_GREEN)
    dp.text((230, 222), "Origin: JNPT Port, Navi Mumbai", fill=DARK_TEXT)
    dp.text((230, 245), "Destination: Pune Chakan Industrial Hub", fill=DARK_TEXT)
    dp.text((230, 270), "Cargo: 22T Auto Components | Vehicle: MH-12-RN-4821", fill=SEC_TEXT)
    dp.rounded_rectangle([230, 298, 410, 328], radius=6, fill=PRIMARY_GREEN)
    dp.text((248, 306), "TRANSIT IN PROGRESS", fill=WHITE)

    # Pre-Trip Inspection Card
    draw_card(dp, [215, 355, 585, 570], radius=12, fill=WHITE, outline=BORDER, width=1)
    dp.text((230, 370), "Pre-Trip Safety Inspection", fill=DARK_TEXT)
    dp.text((485, 372), "5/5 PASSED", fill=PRIMARY_GREEN)
    
    check_items = [
        ("Tire Tread & Pressure Check", "✓ PASSED"),
        ("Air Brake & Hydraulic Pressure", "✓ PASSED"),
        ("Headlights, Turn Signals & Hazard", "✓ PASSED"),
        ("Engine Oil & Coolant Levels", "✓ PASSED"),
        ("Emergency Triangle & Fire Bottle", "✓ PASSED")
    ]
    for idx, (chk, st) in enumerate(check_items):
        cy = 405 + idx * 30
        dp.text((235, cy), chk, fill=DARK_TEXT)
        dp.text((505, cy), st, fill=PRIMARY_GREEN)

    # Milestone Progression
    draw_card(dp, [215, 585, 585, 760], radius=12, fill=WHITE, outline=BORDER, width=1)
    dp.text((230, 600), "Trip Milestones", fill=DARK_TEXT)
    m_steps = [
        ("JNPT Gate Out Departure", "06:15 AM (Logged)"),
        ("Khopoli Expressway Checkpoint", "08:30 AM (Logged)"),
        ("Chakan Warehouse Receiving", "Pending Arrival")
    ]
    for idx, (m_title, m_sub) in enumerate(m_steps):
        my = 630 + idx * 40
        # Bullet dot
        dot_col = PRIMARY_GREEN if "Logged" in m_sub else AMBER
        dp.ellipse([235, my+4, 247, my+16], fill=dot_col)
        dp.text((260, my), m_title, fill=DARK_TEXT)
        dp.text((260, my+18), m_sub, fill=SEC_TEXT)

    # Offline Event Buffer Status Card
    draw_card(dp, [215, 775, 585, 875], radius=12, fill=(250, 252, 251, 255), outline=BORDER, width=1)
    dp.text((230, 790), "Local Offline Event Queue", fill=DARK_TEXT)
    dp.text((230, 815), "0 Pending Events (Auto-buffered in SQLite)", fill=SEC_TEXT)
    dp.text((230, 840), "Auto-syncs GPS points & photos on 4G restore", fill=PRIMARY_GREEN)

    # Expense & Toll Upload Button
    draw_card(dp, [215, 890, 585, 960], radius=10, fill=WHITE, outline=PRIMARY_GREEN, width=2)
    dp.text((275, 915), "📸 LOG TOLL / FUEL EXPENSE RECEIPT", fill=PRIMARY_GREEN)

    # Bottom Phone Navigation
    dp.line([(200, 975), (600, 975)], fill=BORDER, width=1)
    dp.text((240, 990), "Trips", fill=PRIMARY_GREEN)
    dp.text((330, 990), "Inspections", fill=SEC_TEXT)
    dp.text((440, 990), "Expenses", fill=SEC_TEXT)
    dp.text((530, 990), "Profile", fill=SEC_TEXT)

    img_phone.save(os.path.join(assets_dir, "light_driver_smartphone_mockup.png"))
    print("Generated light_driver_smartphone_mockup.png")

    # -------------------------------------------------------------
    # 4. ROUTE DEVIATION MAP (Light Theme, Clear Contrast)
    # -------------------------------------------------------------
    img_route = Image.new("RGBA", (1300, 900), BG_LIGHT)
    dr = ImageDraw.Draw(img_route)
    
    # Outer Map container
    draw_card(dr, [40, 30, 1260, 870], radius=16, fill=WHITE, outline=BORDER, width=2)
    
    # Map title & legend bar
    dr.text((70, 55), "HIGHWAY GEO-CORRIDOR & ROUTE DEVIATION MONITOR", fill=DARK_TEXT)
    
    # Legend
    dr.rounded_rectangle([750, 48, 980, 82], radius=6, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=1)
    dr.text((770, 57), "Authorized Corridor (NH-48)", fill=PRIMARY_GREEN)
    
    dr.rounded_rectangle([1000, 48, 1230, 82], radius=6, fill=ALERT_BG, outline=ALERT_RED, width=1)
    dr.text((1020, 57), "Unapproved Detour / Bypass", fill=ALERT_RED)
    
    # Map background roads / terrain grid
    for x in range(70, 1230, 80):
        dr.line([(x, 110), (x, 830)], fill=(240, 245, 242, 255), width=1)
    for y in range(110, 830, 80):
        dr.line([(70, y), (1230, y)], fill=(240, 245, 242, 255), width=1)

    # Approved Planned Highway Ribbon (Thick Green Corridor)
    pts_approved = [(120, 720), (320, 600), (520, 500), (740, 380), (960, 260), (1160, 180)]
    for i in range(len(pts_approved)-1):
        # Semi-transparent buffer zone around corridor
        dr.line([pts_approved[i], pts_approved[i+1]], fill=(228, 243, 234, 255), width=32)
        # Main road line
        dr.line([pts_approved[i], pts_approved[i+1]], fill=PRIMARY_GREEN, width=8)

    # Waypoints
    wp_labels = ["Origin Hub (Mumbai)", "Toll Plaza 1", "Expressway Junction", "Depot Checkpoint", "Toll Plaza 2", "Destination (Pune)"]
    for idx, pt in enumerate(pts_approved):
        dr.ellipse([pt[0]-10, pt[1]-10, pt[0]+10, pt[1]+10], fill=WHITE, outline=PRIMARY_GREEN, width=3)
        dr.text((pt[0]-40, pt[1]+15), wp_labels[idx], fill=DARK_TEXT)

    # Deviation Detour Path (Contrasting Red / Orange Ribbon)
    pts_dev = [(520, 500), (620, 640), (760, 740), (900, 680), (960, 260)]
    for i in range(len(pts_dev)-1):
        dr.line([pts_dev[i], pts_dev[i+1]], fill=ALERT_BG, width=22)
        dr.line([pts_dev[i], pts_dev[i+1]], fill=ALERT_RED, width=5)

    # Deviation Pin & Ripple Alert
    dev_pin = (760, 740)
    for r in [20, 35, 50]:
        dr.ellipse([dev_pin[0]-r, dev_pin[1]-r, dev_pin[0]+r, dev_pin[1]+r], outline=(220, 38, 38, 160), width=2)
    dr.ellipse([dev_pin[0]-14, dev_pin[1]-14, dev_pin[0]+14, dev_pin[1]+14], fill=ALERT_RED, outline=WHITE, width=3)

    # Alert Callout Box
    draw_card(dr, [620, 770, 1050, 850], radius=10, fill=WHITE, outline=ALERT_RED, width=2)
    dr.text((640, 782), "ROUTE DEVIATION DETECTED: 14.8 km Off-Corridor", fill=ALERT_RED)
    dr.text((640, 808), "Cross-Track Distance Exceeded 5km threshold • Unapproved Toll Bypass", fill=DARK_TEXT)
    dr.text((640, 828), "Automated Event Flagged in FastAPI backend (models/route_intelligence.py)", fill=SEC_TEXT)

    # Adherence Scorecard Card (Top Left overlay)
    draw_card(dr, [80, 140, 420, 320], radius=12, fill=WHITE, outline=BORDER, width=1)
    dr.text((100, 155), "Trip Adherence Intelligence", fill=DARK_TEXT)
    dr.text((100, 185), "Planned Distance: 154.2 km", fill=SEC_TEXT)
    dr.text((100, 210), "Actual Logged GPS: 172.6 km (+18.4 km)", fill=DARK_TEXT)
    dr.text((100, 235), "Detour Cause: Rural Toll Bypass Avoidance", fill=ALERT_RED)
    dr.text((100, 260), "Corridor Adherence Score: 88.4%", fill=AMBER)
    dr.text((100, 285), "Post-Trip Audit Status: Flagged for Review", fill=DARK_TEXT)

    img_route.save(os.path.join(assets_dir, "light_route_deviation_map.png"))
    print("Generated light_route_deviation_map.png")

    # -------------------------------------------------------------
    # 5. TELEMATICS ARCHITECTURE DIAGRAM (6-Stage Pipeline)
    # -------------------------------------------------------------
    img_arch = Image.new("RGBA", (1400, 700), BG_LIGHT)
    da = ImageDraw.Draw(img_arch)
    
    stages = [
        ("1. GPS Device", "Hardware In Vehicle", "AIS-140 / GT06 / Teltonika\nBinary & ASCII Packets", PRIMARY_GREEN),
        ("2. Traccar / Socket", "IoT Ingestion Gateway", "TCP / UDP Port Listening\nDevice Heartbeat Check", PRIMARY_GREEN),
        ("3. Vahan Webhook", "FastAPI Secure Ingest", "X-Telematics-Secret Auth\nConstant-time HMAC Check", PRIMARY_GREEN),
        ("4. Processing Engine", "Backend Decoders", "Deduplication Filter\nSpeed, Ignition, Battery", PRIMARY_GREEN),
        ("5. Data Core & DB", "PostgreSQL Database", "Company Tenancy Binding\nPosition Time-Series Log", PRIMARY_GREEN),
        ("6. Owner Console", "Dispatcher Dashboard", "Real-time Leaflet Map\nInstant Anomaly Alerts", (59, 130, 246, 255))
    ]
    
    card_w = 190
    spacing = 30
    start_x = 45
    
    for idx, (title, sub, details, col) in enumerate(stages):
        x = start_x + idx * (card_w + spacing)
        # Stage card
        draw_card(da, [x, 150, x + card_w, 480], radius=14, fill=WHITE, outline=col, width=2)
        
        # Step number badge
        da.rounded_rectangle([x + 15, 170, x + 60, 205], radius=6, fill=SOFT_GREEN)
        da.text((x + 28, 180), f"0{idx+1}", fill=PRIMARY_GREEN)
        
        da.text((x + 15, 220), title, fill=DARK_TEXT)
        da.text((x + 15, 245), sub, fill=col)
        
        da.line([(x + 15, 275), (x + card_w - 15, 275)], fill=BORDER, width=1)
        
        # Details text
        da.text((x + 15, 290), details, fill=SEC_TEXT)
        
        # Horizontal flow arrows between stages
        if idx < len(stages) - 1:
            ax = x + card_w
            da.line([(ax + 5, 315), (ax + spacing - 5, 315)], fill=PRIMARY_GREEN, width=3)
            # Arrow head
            da.polygon([(ax + spacing - 5, 315), (ax + spacing - 14, 308), (ax + spacing - 14, 322)], fill=PRIMARY_GREEN)

    # Disclosure Banner across bottom
    draw_card(da, [80, 540, 1320, 630], radius=10, fill=WHITE, outline=AMBER, width=2)
    da.text((110, 555), "TECHNICAL STATUS & VALIDATION DISCLOSURE", fill=AMBER)
    da.text((110, 582), "• Wire-level decoders for 7 protocols and HMAC-secured Traccar webhooks are fully functional & verified via automated tests.", fill=DARK_TEXT)
    da.text((110, 602), "• Live physical on-road GSM SIM field validation is currently underway in our staging pilot.", fill=SEC_TEXT)

    img_arch.save(os.path.join(assets_dir, "light_telematics_architecture.png"))
    print("Generated light_telematics_architecture.png")

    # -------------------------------------------------------------
    # 6. FUEL INTELLIGENCE & THEFT ANOMALY DIAGRAM
    # -------------------------------------------------------------
    img_fuel = Image.new("RGBA", (1300, 850), BG_LIGHT)
    df = ImageDraw.Draw(img_fuel)
    
    # Outer card
    draw_card(df, [40, 30, 1260, 810], radius=16, fill=WHITE, outline=BORDER, width=2)
    df.text((70, 55), "FINANCIAL INTELLIGENCE: FUEL THEFT DETECTION & INVOICE AUDIT", fill=DARK_TEXT)
    
    # Left Card: Fuel Siphoning Anomaly
    draw_card(df, [70, 110, 630, 770], radius=14, fill=WHITE, outline=ALERT_RED, width=2)
    df.rounded_rectangle([90, 130, 270, 160], radius=6, fill=ALERT_BG)
    df.text((105, 138), "SIPHONING ANOMALY AI", fill=ALERT_RED)
    
    df.text((90, 180), "Abrupt Fuel Drop Detection", fill=DARK_TEXT)
    df.text((90, 205), "Correlates tank telemetry with engine ignition states", fill=SEC_TEXT)
    
    # Fuel curve chart illustration
    chart_box = [90, 240, 610, 480]
    df.rectangle(chart_box, fill=(250, 252, 251, 255), outline=BORDER, width=1)
    
    # Grid lines inside chart
    for y in range(260, 480, 40):
        df.line([(90, y), (610, y)], fill=(235, 240, 238, 255), width=1)
    df.text((100, 250), "350L (100%)", fill=SEC_TEXT)
    df.text((100, 360), "180L (50%)", fill=SEC_TEXT)
    df.text((100, 450), "0L (Empty)", fill=SEC_TEXT)
    
    # Normal driving consumption curve (gentle slope)
    df.line([(180, 280), (320, 320)], fill=PRIMARY_GREEN, width=4)
    df.text((200, 290), "Normal Highway Consumption", fill=PRIMARY_GREEN)
    
    # Steep siphoning drop while Ignition OFF!
    df.line([(320, 320), (350, 420)], fill=ALERT_RED, width=5)
    df.text((365, 365), "⚡ 42L Drop in 12 min\nIgnition: OFF (Stationary)", fill=ALERT_RED)
    
    # Event resolution details
    draw_card(df, [90, 500, 610, 740], radius=10, fill=ALERT_BG, outline=ALERT_RED, width=1)
    df.text((110, 515), "INCIDENT LOG: SIPH-2026-0819", fill=ALERT_RED)
    df.text((110, 545), "Vehicle: MH-12-RN-4821 | Location: Highway Rest Stop Km 94", fill=DARK_TEXT)
    df.text((110, 570), "Timestamp: 02:44 AM IST | Duration: 14 Minutes", fill=DARK_TEXT)
    df.text((110, 595), "Audit Flag: Automatic SMS/Email alert dispatched to fleet owner", fill=DARK_TEXT)
    df.text((110, 620), "Action: Fuel receipt cross-matched and operator notified", fill=SEC_TEXT)

    # Right Card: Tank Capacity Physics Validation & Cost Per Km
    draw_card(df, [670, 110, 1230, 770], radius=14, fill=WHITE, outline=PRIMARY_GREEN, width=2)
    df.rounded_rectangle([690, 130, 930, 160], radius=6, fill=SOFT_GREEN)
    df.text((705, 138), "PHYSICS RECONCILIATION", fill=PRIMARY_GREEN)
    
    df.text((690, 180), "Tank Capacity Violation Check", fill=DARK_TEXT)
    df.text((690, 205), "Prevents fraudulent fuel invoices exceeding vehicle specs", fill=SEC_TEXT)
    
    # Comparison comparison box
    draw_card(df, [690, 240, 1210, 480], radius=10, fill=(252, 254, 253, 255), outline=BORDER, width=1)
    df.text((710, 260), "RULE: Maximum Billed Liters <= Vehicle Spec Capacity", fill=DARK_TEXT)
    
    df.rounded_rectangle([710, 300, 1190, 370], radius=8, fill=ALERT_BG, outline=ALERT_RED, width=1)
    df.text((730, 315), "VIOLATION DETECTED: Fuel Pump Receipt Invoice #48192", fill=ALERT_RED)
    df.text((730, 340), "Billed Liters: 420.0 Liters  |  Truck Max Tank Spec: 350.0 Liters (EXCEEDED BY 70L)", fill=DARK_TEXT)

    df.rounded_rectangle([710, 390, 1190, 460], radius=8, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=1)
    df.text((730, 405), "ODOMETER RECONCILIATION AUDIT: Passed Validation", fill=PRIMARY_GREEN)
    df.text((730, 430), "Driver Reported Odo: 840 km | GPS Telematics Odo: 834.6 km (0.6% Delta)", fill=DARK_TEXT)

    # Fleet Financial Cost Per Km Summary
    draw_card(df, [690, 500, 1210, 740], radius=10, fill=WHITE, outline=BORDER, width=1)
    df.text((710, 520), "Fleet Financial Intelligence Summary", fill=DARK_TEXT)
    
    cost_rows = [
        ("Fleet Average Cost Per Km:", "INR 28.40 / km", PRIMARY_GREEN),
        ("Monthly Diesel Burn Rate:", "Sample Fleet Baseline", SEC_TEXT),
        ("Toll & En-Route Trip Costs:", "Tracked via Driver App", DARK_TEXT),
        ("Audit Savings (Simulated Rule Engine):", "Recovers 8–15% untracked loss", PRIMARY_GREEN)
    ]
    for idx, (lbl, val, col) in enumerate(cost_rows):
        cy = 560 + idx * 40
        df.text((710, cy), lbl, fill=DARK_TEXT)
        df.text((1010, cy), val, fill=col)

    img_fuel.save(os.path.join(assets_dir, "light_fuel_intelligence.png"))
    print("Generated light_fuel_intelligence.png")

    # -------------------------------------------------------------
    # 7. HARDWARE QUARANTINE & SECURITY DIAGRAM
    # -------------------------------------------------------------
    img_sec = Image.new("RGBA", (1300, 750), BG_LIGHT)
    ds = ImageDraw.Draw(img_sec)
    
    draw_card(ds, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    ds.text((70, 55), "ZERO-TRUST HARDWARE SECURITY & QUARANTINE ISOLATION", fill=DARK_TEXT)
    
    # 3 Pillars of Security
    sec_pillars = [
        ("1. Ingestion Isolation", "Unmapped & Rogue Trackers", "When an unrecognized IMEI or retired device sends telemetry, it is quarantined immediately. Data is strictly blocked from client dashboards.", ALERT_RED, ALERT_BG),
        ("2. Super-Admin Vault", "Quarantine Review Queue", "Only authenticated system super-administrators can view quarantined devices, verify device provenance, and reassign hardware.", PRIMARY_GREEN, SOFT_GREEN),
        ("3. Cryptographic Core", "AES-256-GCM & Tenancy", "All provider tokens are encrypted at rest with AES-GCM. All database queries enforce company_id tenant boundaries.", (59, 130, 246, 255), (239, 246, 255, 255))
    ]
    for idx, (title, sub, body, col, bg_p) in enumerate(sec_pillars):
        px = 70 + idx * 395
        draw_card(ds, [px, 120, px + 375, 480], radius=14, fill=WHITE, outline=col, width=2)
        
        ds.rounded_rectangle([px + 20, 140, px + 220, 175], radius=6, fill=bg_p)
        ds.text((px + 30, 150), title.upper(), fill=col)
        
        ds.text((px + 20, 195), sub, fill=DARK_TEXT)
        ds.line([(px + 20, 225), (px + 355, 225)], fill=BORDER, width=1)
        
        ds.text((px + 20, 245), body, fill=SEC_TEXT)

    # Immutable Audit Log Card across bottom
    draw_card(ds, [70, 510, 1230, 670], radius=12, fill=(250, 252, 251, 255), outline=BORDER, width=1)
    ds.text((95, 528), "DUAL-SIDED IMMUTABLE AUDIT TRAIL", fill=PRIMARY_GREEN)
    ds.text((95, 555), "• Every device registration, pairing, unpairing, and quarantine transfer is immutably logged with actor, timestamp & IP.", fill=DARK_TEXT)
    ds.text((95, 580), "• Full regulatory compliance audit log accessible via backend/routers/asset_domain.py and admin console.", fill=SEC_TEXT)
    ds.text((95, 605), "• Zero secret exposure: Provider tokens and API keys are masked and never returned in API payloads.", fill=DARK_TEXT)

    img_sec.save(os.path.join(assets_dir, "light_hardware_quarantine.png"))
    print("Generated light_hardware_quarantine.png")

    # -------------------------------------------------------------
    # 8. 10-STEP TRIP LIFECYCLE HORIZONTAL DIAGRAM
    # -------------------------------------------------------------
    img_trip = Image.new("RGBA", (1400, 500), BG_LIGHT)
    dt = ImageDraw.Draw(img_trip)
    
    trip_steps = [
        ("01", "Creation", "Origin/Dest"),
        ("02", "Cargo", "Manifest"),
        ("03", "Vehicle", "Active Truck"),
        ("04", "Driver", "KYC Approved"),
        ("05", "Dispatch", "Transit Start"),
        ("06", "Telematics", "GPS Stream"),
        ("07", "Milestones", "Waypoints"),
        ("08", "Deviation", "Corridor Check"),
        ("09", "Delivery", "POD Signed"),
        ("10", "Audit", "Odo & Fuel Close")
    ]
    step_w = 115
    step_space = 15
    s_start_x = 40
    
    for idx, (num, title, sub) in enumerate(trip_steps):
        x = s_start_x + idx * (step_w + step_space)
        # Chevron / Card
        draw_card(dt, [x, 120, x + step_w, 340], radius=10, fill=WHITE, outline=PRIMARY_GREEN, width=2)
        
        dt.rounded_rectangle([x + 10, 135, x + 50, 170], radius=6, fill=SOFT_GREEN)
        dt.text((x + 18, 145), num, fill=PRIMARY_GREEN)
        
        dt.text((x + 10, 190), title, fill=DARK_TEXT)
        dt.text((x + 10, 220), sub, fill=SEC_TEXT)
        
        if idx < len(trip_steps) - 1:
            ax = x + step_w
            dt.line([(ax + 2, 230), (ax + step_space - 2, 230)], fill=PRIMARY_GREEN, width=2)

    img_trip.save(os.path.join(assets_dir, "light_trip_lifecycle.png"))
    print("Generated light_trip_lifecycle.png")

if __name__ == "__main__":
    create_light_theme_graphics()
