import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_3d_financial_graphics():
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
    CORAL_LOSS = (217, 119, 112, 255)     # #D97770 (Muted coral loss indicator)
    ALERT_BG = (254, 242, 242, 255)       # #FEF2F2
    ALERT_RED = (220, 38, 38, 255)        # #DC2626
    AMBER = (217, 119, 6, 255)            # #D97706
    AMBER_BG = (254, 243, 199, 255)       # #FEF3C7
    BLUE = (37, 99, 235, 255)             # #2563EB
    BLUE_BG = (239, 246, 255, 255)

    def draw_card(d, box, radius=14, fill=WHITE, outline=BORDER, width=2):
        d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    # -------------------------------------------------------------------------
    # 1. 3D COVER VISUAL: Floating Financial Dashboard with Leakage & Profit Shield
    # -------------------------------------------------------------------------
    img1 = Image.new("RGBA", (1400, 950), BG_LIGHT)
    d = ImageDraw.Draw(img1)
    
    # Background subtle grid pattern
    for x in range(0, 1400, 60):
        d.line([(x, 0), (x, 950)], fill=(235, 242, 238, 160), width=1)
    for y in range(0, 950, 60):
        d.line([(0, y), (1400, y)], fill=(235, 242, 238, 160), width=1)

    # Main Central 3D Platform (Isometric projection)
    center = (700, 480)
    # Isometric rings
    for r in [420, 320, 220]:
        d.ellipse([center[0]-r, center[1]-int(r*0.52), center[0]+r, center[1]+int(r*0.52)], outline=ACCENT, width=2)

    # Inflow stream from left (Gross Trip Revenue)
    d.line([(100, 480), (450, 480)], fill=PRIMARY_GREEN, width=8)
    draw_card(d, [60, 430, 280, 530], radius=12, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=2)
    d.text((85, 450), "GROSS REVENUE INFLOW", fill=PRIMARY_GREEN)
    d.text((85, 480), "₹1.10 Crore / month", fill=DARK_TEXT)
    d.text((85, 502), "50-Truck Fleet Baseline", fill=SEC_TEXT)

    # 3 Red Leakage Streams flowing outwards (Fuel, Detours, Downtime)
    leak_positions = [
        ((480, 260), "1. FUEL SIPHONING & FRAUD", "-₹3,16,800 / mo", CORAL_LOSS),
        ((940, 260), "2. ROUTE DETOUR OVERRUNS", "-₹2,56,500 / mo", CORAL_LOSS),
        ((960, 680), "3. AVOIDABLE IDLE DOWNTIME", "-₹1,80,000 / mo", CORAL_LOSS)
    ]
    for pos, lbl, val, col in leak_positions:
        d.line([center, pos], fill=CORAL_LOSS, width=4)
        draw_card(d, [pos[0]-140, pos[1]-45, pos[0]+140, pos[1]+45], radius=10, fill=ALERT_BG, outline=CORAL_LOSS, width=2)
        d.text((pos[0]-125, pos[1]-30), lbl, fill=CORAL_LOSS)
        d.text((pos[0]-125, pos[1]-5), val, fill=DARK_TEXT)

    # Central Core: VAHAN Profit Shield
    d.ellipse([center[0]-110, center[1]-65, center[0]+110, center[1]+65], fill=WHITE, outline=PRIMARY_GREEN, width=4)
    d.text((center[0]-60, center[1]-28), "VAHAN CORE", fill=PRIMARY_GREEN)
    d.text((center[0]-85, center[1]-2), "Profit Protection Shield", fill=DARK_TEXT)
    d.text((center[0]-75, center[1]+22), "Active Leakage Control", fill=SEC_TEXT)

    # Outflow to Right (Protected Net Operating Profit)
    d.line([(810, 480), (1220, 480)], fill=PRIMARY_GREEN, width=8)
    draw_card(d, [1120, 430, 1360, 530], radius=12, fill=WHITE, outline=PRIMARY_GREEN, width=3)
    d.text((1140, 450), "PROTECTED OPERATING PROFIT", fill=PRIMARY_GREEN)
    d.text((1140, 480), "+₹4,51,980 / month", fill=PRIMARY_GREEN)
    d.text((1140, 502), "₹54.2 Lakhs / year protected", fill=DARK_TEXT)

    img1.save(os.path.join(assets_dir, "visual_3d_cover_pnl.png"))
    print("Generated visual_3d_cover_pnl.png")

    # -------------------------------------------------------------------------
    # 2. 3D FUEL THEFT CUTAWAY & LOSS CHART
    # -------------------------------------------------------------------------
    img4 = Image.new("RGBA", (1300, 750), BG_LIGHT)
    d4 = ImageDraw.Draw(img4)
    
    draw_card(d4, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    d4.text((70, 55), "FUEL LOSS CUTAWAY & RECOVERY SENSITIVITY BY FLEET SIZE", fill=DARK_TEXT)
    d4.text((70, 80), "3D Tank Siphoning Detection (Ignition OFF) vs Monthly Diesel Financial Loss", fill=SEC_TEXT)

    # Left: 3D Fuel Tank Cutaway Illustration
    draw_card(d4, [70, 120, 620, 680], radius=12, fill=(252, 254, 253, 255), outline=CORAL_LOSS, width=2)
    d4.text((95, 145), "3D Cutaway: Diesel Siphoning Drop While Ignition OFF", fill=CORAL_LOSS)
    
    # 3D Tank Cylinder
    tank_center = (345, 300)
    # Outer Tank shell
    d4.rounded_rectangle([150, 200, 540, 400], radius=24, fill=(241, 245, 249, 255), outline=(203, 213, 225, 255), width=3)
    # Liquid fuel level (Dropping from 350L to 180L)
    d4.rounded_rectangle([155, 270, 535, 395], radius=20, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=2)
    d4.text((290, 310), "350L Capacity Spec", fill=PRIMARY_GREEN)
    
    # Coral Leakage Stream flowing down
    d4.line([(345, 380), (345, 520)], fill=CORAL_LOSS, width=8)
    d4.polygon([(345, 535), (335, 515), (355, 515)], fill=CORAL_LOSS)
    
    # Alert callout box below tank
    draw_card(d4, [110, 545, 580, 655], radius=10, fill=ALERT_BG, outline=CORAL_LOSS, width=1)
    d4.text((130, 560), "SIPHONING ANOMALY FLAGGED: 42.0 Liters Lost", fill=CORAL_LOSS)
    d4.text((130, 585), "• Location: Highway Rest Stop Km 118 (NH-48)", fill=DARK_TEXT)
    d4.text((130, 608), "• Engine State: Ignition OFF (Stationary for 18 min)", fill=DARK_TEXT)
    d4.text((130, 630), "• Validation: Tank Physics Check rejects 420L billed slip", fill=SEC_TEXT)

    # Right: Monthly Fuel Leakage Bar Chart by Fleet Size (10, 25, 50, 100 trucks)
    draw_card(d4, [650, 120, 1230, 680], radius=12, fill=WHITE, outline=BORDER, width=1)
    d4.text((680, 145), "Potential Monthly Fuel Leakage Loss by Fleet Size", fill=DARK_TEXT)
    d4.text((680, 170), "Formula: Fleet Size × Monthly Spend (₹1,05,600) × 6.0% Unmonitored Loss", fill=SEC_TEXT)
    
    # Chart bars
    cohorts = [
        ("10 Trucks", 63360, "₹63.3K / mo", 110, (254, 205, 211, 255)),
        ("25 Trucks", 158400, "₹1.58 Lakhs / mo", 210, (253, 164, 175, 255)),
        ("50 Trucks", 316800, "₹3.16 Lakhs / mo", 340, CORAL_LOSS),
        ("100 Trucks", 633600, "₹6.33 Lakhs / mo", 480, ALERT_RED)
    ]
    base_x = 700
    for idx, (cohort_name, loss_val, loss_str, bar_len, bar_col) in enumerate(cohorts):
        by = 220 + idx * 105
        d4.text((base_x, by), cohort_name, fill=DARK_TEXT)
        d4.text((base_x + 360, by), loss_str, fill=bar_col)
        # Background track
        d4.rounded_rectangle([base_x, by + 26, base_x + 490, by + 56], radius=8, fill=(245, 248, 246, 255))
        # Active bar
        d4.rounded_rectangle([base_x, by + 26, base_x + bar_len, by + 56], radius=8, fill=bar_col)
        # Annualized tag
        ann_loss = f"Annual: ₹{loss_val*12/100000:.1f} Lakhs"
        d4.text((base_x + 15, by + 34), ann_loss, fill=WHITE if bar_len > 200 else DARK_TEXT)

    # Bottom summary in right card
    draw_card(d4, [680, 595, 1200, 660], radius=8, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=1)
    d4.text((700, 610), "VAHAN FINANCIAL SHIELD (50-Truck Fleet):", fill=PRIMARY_GREEN)
    d4.text((700, 632), "Active investigation & physics validation protects up to ₹1.90L+ / mo.", fill=DARK_TEXT)

    img4.save(os.path.join(assets_dir, "visual_3d_fuel_loss_tank.png"))
    print("Generated visual_3d_fuel_loss_tank.png")

    # -------------------------------------------------------------------------
    # 3. 3D ROUTE DEVIATION HIGHWAY MAP & COST SENSITIVITY
    # -------------------------------------------------------------------------
    img5 = Image.new("RGBA", (1300, 750), BG_LIGHT)
    d5 = ImageDraw.Draw(img5)
    
    draw_card(d5, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    d5.text((70, 55), "ROUTE DEVIATIONS: HIGHWAY GEO-CORRIDORS & DETOUR OVERRUNS", fill=DARK_TEXT)
    d5.text((70, 80), "Approved Green Highway Corridor vs Coral Unapproved Detour • Running Cost Calculation", fill=SEC_TEXT)

    # Left: 3D Map View
    draw_card(d5, [70, 120, 630, 680], radius=12, fill=(250, 252, 251, 255), outline=BORDER, width=1)
    d5.text((95, 145), "3D Highway Corridor Visualization (NH-48)", fill=DARK_TEXT)
    
    # Approved Green Route
    green_pts = [(120, 560), (250, 460), (370, 360), (510, 240), (590, 180)]
    for i in range(len(green_pts)-1):
        d5.line([green_pts[i], green_pts[i+1]], fill=(228, 243, 234, 255), width=28)
        d5.line([green_pts[i], green_pts[i+1]], fill=PRIMARY_GREEN, width=6)
    for pt in green_pts:
        d5.ellipse([pt[0]-8, pt[1]-8, pt[0]+8, pt[1]+8], fill=WHITE, outline=PRIMARY_GREEN, width=3)

    # Unapproved Detour in Coral
    detour_pts = [(250, 460), (320, 580), (450, 620), (510, 240)]
    for i in range(len(detour_pts)-1):
        d5.line([detour_pts[i], detour_pts[i+1]], fill=ALERT_BG, width=20)
        d5.line([detour_pts[i], detour_pts[i+1]], fill=CORAL_LOSS, width=5)

    # Detour Pin
    d5.ellipse([385-12, 600-12, 385+12, 600+12], fill=CORAL_LOSS, outline=WHITE, width=3)
    
    # Map callout
    draw_card(d5, [110, 480, 580, 540], radius=8, fill=WHITE, outline=CORAL_LOSS, width=1)
    d5.text((125, 495), "UNAPPROVED TOLL BYPASS: +48.6 km Extra Distance", fill=CORAL_LOSS)
    d5.text((125, 518), "Cross-Track Error: 14.2 km • Extra Running Cost: ₹1,385 / trip", fill=DARK_TEXT)

    # Right: Monthly Route Detour Cost Chart (10, 25, 50, 100 trucks)
    draw_card(d5, [660, 120, 1230, 680], radius=12, fill=WHITE, outline=BORDER, width=1)
    d5.text((690, 145), "Extra Monthly Detour Cost by Fleet Size", fill=DARK_TEXT)
    d5.text((690, 170), "Formula: Fleet Size × Extra km (180 km/mo) × Cost/km (₹28.50)", fill=SEC_TEXT)

    detour_cohorts = [
        ("10 Commercial Trucks", 51300, "₹51.3K / mo", 100, (254, 205, 211, 255)),
        ("25 Commercial Trucks", 128250, "₹1.28 Lakhs / mo", 200, (253, 164, 175, 255)),
        ("50 Commercial Trucks", 256500, "₹2.56 Lakhs / mo", 330, CORAL_LOSS),
        ("100 Commercial Trucks", 513000, "₹5.13 Lakhs / mo", 470, ALERT_RED)
    ]
    base_x = 700
    for idx, (cohort_name, cost_val, cost_str, bar_len, bar_col) in enumerate(detour_cohorts):
        by = 220 + idx * 105
        d5.text((base_x, by), cohort_name, fill=DARK_TEXT)
        d5.text((base_x + 350, by), cost_str, fill=bar_col)
        # Background track
        d5.rounded_rectangle([base_x, by + 26, base_x + 480, by + 56], radius=8, fill=(245, 248, 246, 255))
        # Active bar
        d5.rounded_rectangle([base_x, by + 26, base_x + bar_len, by + 56], radius=8, fill=bar_col)
        ann_cost = f"Annual Overrun: ₹{cost_val*12/100000:.1f} Lakhs"
        d5.text((base_x + 15, by + 34), ann_cost, fill=WHITE if bar_len > 200 else DARK_TEXT)

    draw_card(d5, [690, 595, 1200, 660], radius=8, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=1)
    d5.text((710, 610), "VAHAN ROUTE PROTECTION (50-Truck Fleet):", fill=PRIMARY_GREEN)
    d5.text((710, 632), "Geo-corridor adherence alerts protect up to ₹1.54L+ / mo in fuel & tire wear.", fill=DARK_TEXT)

    img5.save(os.path.join(assets_dir, "visual_3d_route_deviation_map.png"))
    print("Generated visual_3d_route_deviation_map.png")

    # -------------------------------------------------------------------------
    # 4. 3D FLEET UTILIZATION & DOWNTIME DASHBOARD
    # -------------------------------------------------------------------------
    img6 = Image.new("RGBA", (1300, 750), BG_LIGHT)
    d6 = ImageDraw.Draw(img6)
    
    draw_card(d6, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    d6.text((70, 55), "VEHICLE DOWNTIME: ASSET UTILIZATION & CONTRIBUTION DRAG", fill=DARK_TEXT)
    d6.text((70, 80), "3D Status Grid vs Daily Contribution Margin Loss (₹2,400 / day / vehicle)", fill=SEC_TEXT)

    # 4 Status Cards across left-top
    statuses = [
        ("IN TRANSIT (ACTIVE)", "32 Vehicles", "64.0% Productive", PRIMARY_GREEN, SOFT_GREEN),
        ("READY IN DEPOT", "11 Vehicles", "22.0% Available", BLUE, BLUE_BG),
        ("SCHEDULED SERVICE", "4 Vehicles", "8.0% Maintenance", AMBER, AMBER_BG),
        ("AVOIDABLE IDLE DRAG", "3 Vehicles", "6.0% Profit Loss", CORAL_LOSS, ALERT_BG)
    ]
    for idx, (title, val, sub, col, bg_p) in enumerate(statuses):
        sx = 70 + idx * 295
        draw_card(d6, [sx, 120, sx + 275, 220], radius=10, fill=WHITE, outline=BORDER, width=1)
        d6.rounded_rectangle([sx + 15, 135, sx + 200, 160], radius=5, fill=bg_p)
        d6.text((sx + 25, 142), title, fill=col)
        d6.text((sx + 15, 170), val, fill=DARK_TEXT)
        d6.text((sx + 15, 195), sub, fill=SEC_TEXT)

    # Bottom Left: Productive vs Idle Days Comparison Chart
    draw_card(d6, [70, 240, 680, 680], radius=12, fill=WHITE, outline=BORDER, width=1)
    d6.text((95, 265), "Monthly Operational Days per Vehicle (30-Day Base)", fill=DARK_TEXT)
    
    days_breakdown = [
        ("Active Revenue-Earning Days", 22.5, "75.0%", 380, PRIMARY_GREEN),
        ("Scheduled Preventive Maintenance", 2.0, "6.7%", 90, AMBER),
        ("Loading & Unloading Dwell", 4.0, "13.3%", 140, BLUE),
        ("Avoidable Unscheduled Idle Days", 1.5, "5.0%", 75, CORAL_LOSS)
    ]
    for idx, (lbl, days_val, pct_str, bar_w, bar_col) in enumerate(days_breakdown):
        dy = 310 + idx * 85
        d6.text((95, dy), lbl, fill=DARK_TEXT)
        d6.text((95, dy + 22), f"{days_val:.1f} Days ({pct_str})", fill=bar_col)
        # Track
        d6.rounded_rectangle([360, dy + 6, 650, dy + 28], radius=6, fill=(241, 245, 249, 255))
        d6.rounded_rectangle([360, dy + 6, 360 + bar_w, dy + 28], radius=6, fill=bar_col)

    # Bottom Right: Avoidable Contribution Drag by Fleet Size
    draw_card(d6, [710, 240, 1230, 680], radius=12, fill=WHITE, outline=BORDER, width=1)
    d6.text((735, 265), "Monthly Contribution Loss from 1.5 Idle Days / Truck", fill=DARK_TEXT)
    d6.text((735, 290), "Formula: Fleet Size × 1.5 Idle Days × ₹2,400 Daily Contribution", fill=SEC_TEXT)

    downtime_cohorts = [
        ("10 Commercial Trucks", 36000, "₹36.0K / mo", 90, (254, 205, 211, 255)),
        ("25 Commercial Trucks", 90000, "₹90.0K / mo", 180, (253, 164, 175, 255)),
        ("50 Commercial Trucks", 180000, "₹1.80 Lakhs / mo", 310, CORAL_LOSS),
        ("100 Commercial Trucks", 360000, "₹3.60 Lakhs / mo", 440, ALERT_RED)
    ]
    base_x = 735
    for idx, (cohort_name, loss_val, loss_str, bar_len, bar_col) in enumerate(downtime_cohorts):
        by = 330 + idx * 75
        d6.text((base_x, by), cohort_name, fill=DARK_TEXT)
        d6.text((base_x + 320, by), loss_str, fill=bar_col)
        d6.rounded_rectangle([base_x, by + 22, base_x + 460, by + 46], radius=6, fill=(245, 248, 246, 255))
        d6.rounded_rectangle([base_x, by + 22, base_x + bar_len, by + 46], radius=6, fill=bar_col)

    draw_card(d6, [735, 615, 1200, 665], radius=8, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=1)
    d6.text((750, 625), "VAHAN DISPATCH OVERSIGHT (50-Truck Fleet):", fill=PRIMARY_GREEN)
    d6.text((750, 645), "Availability visibility recovers up to ₹1.08L+ / mo in contribution.", fill=DARK_TEXT)

    img6.save(os.path.join(assets_dir, "visual_3d_vehicle_downtime.png"))
    print("Generated visual_3d_vehicle_downtime.png")

    # -------------------------------------------------------------------------
    # 5. 3D TRIP JOURNEY PROCESS & CHECKPOINTS TIMELINE
    # -------------------------------------------------------------------------
    img8 = Image.new("RGBA", (1350, 550), BG_LIGHT)
    d8 = ImageDraw.Draw(img8)
    
    draw_card(d8, [40, 30, 1310, 510], radius=16, fill=WHITE, outline=BORDER, width=2)
    d8.text((70, 55), "TRIP MANAGEMENT: 8-STAGE OPERATIONAL & FINANCIAL TIMELINE", fill=DARK_TEXT)
    d8.text((70, 80), "Every Trip Checkpoint Binds Telematics, Expense Slips, and POD Invoicing into Accounting", fill=SEC_TEXT)

    journey_nodes = [
        ("01", "Creation", "Manifest & Rate"),
        ("02", "Assignment", "Truck & Driver"),
        ("03", "Dispatch", "Gate Out Timestamp"),
        ("04", "Transit", "Corridor GPS Stream"),
        ("05", "Checkpoints", "Expressway Tolls"),
        ("06", "Receiving", "Destination Gate In"),
        ("07", "Delivery POD", "Signed Customer Slip"),
        ("08", "P&L Audit", "Fuel & Odo Closed")
    ]
    node_w = 135
    node_space = 16
    start_x = 65

    for idx, (num, step_title, sub) in enumerate(journey_nodes):
        x = start_x + idx * (node_w + node_space)
        is_audit = idx == 7
        draw_card(d8, [x, 130, x + node_w, 440], radius=12, fill=WHITE, outline=PRIMARY_GREEN if is_audit else BORDER, width=2)
        
        # Step badge
        d8.rounded_rectangle([x + 15, 150, x + 65, 185], radius=6, fill=SOFT_GREEN if not is_audit else PRIMARY_GREEN)
        d8.text((x + 25, 160), num, fill=PRIMARY_GREEN if not is_audit else WHITE)
        
        d8.text((x + 15, 210), step_title, fill=DARK_TEXT)
        d8.text((x + 15, 240), sub, fill=SEC_TEXT)
        
        d8.line([(x + 15, 280), (x + node_w - 15, 280)], fill=BORDER, width=1)
        
        # Operational value
        vals = [
            "Client rate locked",
            "KYC driver gate",
            "Odo baseline set",
            "Deviation checks",
            "Fastag logged",
            "Dwell time start",
            "Zero dispute POD",
            "Odo vs GPS matched"
        ]
        d8.text((x + 15, 300), "Value Control:", fill=DARK_TEXT)
        d8.text((x + 15, 325), vals[idx], fill=PRIMARY_GREEN)

        if idx < len(journey_nodes) - 1:
            ax = x + node_w
            d8.line([(ax + 2, 280), (ax + node_space - 2, 280)], fill=PRIMARY_GREEN, width=3)

    img8.save(os.path.join(assets_dir, "visual_3d_trip_journey.png"))
    print("Generated visual_3d_trip_journey.png")

    # -------------------------------------------------------------------------
    # 6. SUBSCRIPTION COST VS FINANCIAL EXPOSURE COMPARISON CHART
    # -------------------------------------------------------------------------
    img16 = Image.new("RGBA", (1300, 750), BG_LIGHT)
    d16 = ImageDraw.Draw(img16)
    
    draw_card(d16, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    d16.text((70, 55), "COMMERCIAL VALUE: SUBSCRIPTION INVESTMENT VS. AVOIDABLE LEAKAGE", fill=DARK_TEXT)
    d16.text((70, 80), "Comparing Monthly VAHAN Plan Costs against Potential Leakage Exposure across 10, 50, and 100 Trucks", fill=SEC_TEXT)

    # 3 Grouped Bar Cohorts (10, 50, 100 Trucks)
    cohort_data = [
        ("10-Truck Fleet", [("Starter (₹500)", 5000, DARK_TEXT), ("Pro (₹800)", 8000, BLUE), ("Enterprise (₹1,000)", 10000, PRIMARY_GREEN)], 90396),
        ("50-Truck Fleet", [("Starter (₹500)", 25000, DARK_TEXT), ("Pro (₹800)", 40000, BLUE), ("Enterprise (₹1,000)", 50000, PRIMARY_GREEN)], 451980),
        ("100-Truck Fleet", [("Starter (₹500)", 50000, DARK_TEXT), ("Pro (₹800)", 80000, BLUE), ("Enterprise (₹1,000)", 100000, PRIMARY_GREEN)], 903960)
    ]

    for idx, (fleet_lbl, plans, avoid_val) in enumerate(cohort_data):
        bx = 70 + idx * 395
        draw_card(d16, [bx, 125, bx + 375, 680], radius=12, fill=WHITE, outline=BORDER, width=1)
        d16.text((bx + 20, 145), fleet_lbl, fill=DARK_TEXT)
        d16.text((bx + 20, 170), "Monthly Plan Investment vs Protected Profit", fill=SEC_TEXT)
        
        # Subscription bars
        for p_idx, (p_name, p_cost, p_col) in enumerate(plans):
            py = 220 + p_idx * 75
            d16.text((bx + 20, py), p_name, fill=DARK_TEXT)
            d16.text((bx + 240, py), f"₹{p_cost:,}", fill=p_col)
            # Track
            d16.rounded_rectangle([bx + 20, py + 22, bx + 350, py + 42], radius=6, fill=(241, 245, 249, 255))
            # Active Bar
            bar_w = int(p_cost / 100000 * 300) + 15
            d16.rounded_rectangle([bx + 20, py + 22, bx + 20 + bar_w, py + 42], radius=6, fill=p_col)

        # Large Avoidable Loss Card
        draw_card(d16, [bx + 15, 465, bx + 360, 655], radius=10, fill=SOFT_GREEN, outline=PRIMARY_GREEN, width=2)
        d16.text((bx + 30, 485), "ILLUSTRATIVE PROTECTED PROFIT:", fill=PRIMARY_GREEN)
        d16.text((bx + 30, 515), f"₹{avoid_val:,} / mo", fill=PRIMARY_GREEN)
        ann_val = f"₹{avoid_val*12/100000:.1f} Lakhs / year"
        d16.text((bx + 30, 550), ann_val, fill=DARK_TEXT)
        d16.text((bx + 30, 580), "• Based on 60% operational resolution", fill=SEC_TEXT)
        d16.text((bx + 30, 605), "• Exceeds subscription cost multiple times", fill=PRIMARY_GREEN)

    img16.save(os.path.join(assets_dir, "visual_3d_cost_vs_leakage.png"))
    print("Generated visual_3d_cost_vs_leakage.png")

if __name__ == "__main__":
    generate_3d_financial_graphics()
