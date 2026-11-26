import os
from PIL import Image, ImageDraw, ImageFont

def generate_financial_graphics():
    assets_dir = r"c:\Users\ratho\fleetguard\presentation_assets"
    os.makedirs(assets_dir, exist_ok=True)
    
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
    BLUE = (37, 99, 235, 255)             # #2563EB

    def draw_card(d, box, radius=14, fill=WHITE, outline=BORDER, width=2):
        d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

    # -------------------------------------------------------------------------
    # 1. P&L WATERFALL DIAGRAM: Gross Revenue to Operating Profit
    # -------------------------------------------------------------------------
    img_wf = Image.new("RGBA", (1300, 750), BG_LIGHT)
    d = ImageDraw.Draw(img_wf)
    
    draw_card(d, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    d.text((70, 55), "COMMERCIAL FLEET EXPENSE WATERFALL & OPERATING MARGIN BLEED", fill=DARK_TEXT)
    d.text((70, 80), "Illustrative 50-Truck Fleet: Gross Freight Revenue (100%) vs Cumulative Operating Costs", fill=SEC_TEXT)
    d.rounded_rectangle([920, 50, 1230, 85], radius=6, fill=ALERT_BG, outline=ALERT_RED, width=1)
    d.text((935, 60), "Thin 8.0% Net Operating Margin", fill=ALERT_RED)

    # Waterfall bars
    bars = [
        ("Gross Revenue", 100.0, PRIMARY_GREEN, SOFT_GREEN, "₹2,20,000 / mo", "+100%"),
        ("1. Diesel / Fuel", -48.0, ALERT_RED, ALERT_BG, "-₹1,05,600", "48%"),
        ("2. Driver Salaries", -14.0, (234, 88, 12, 255), (255, 237, 213, 255), "-₹30,800", "14%"),
        ("3. Maintenance", -11.0, AMBER, AMBER_BG, "-₹24,200", "11%"),
        ("4. Tolls / Transit", -10.0, (147, 51, 234, 255), (243, 232, 255, 255), "-₹22,000", "10%"),
        ("5. Permits & Taxes", -5.0, (75, 85, 99, 255), (243, 244, 246, 255), "-₹11,000", "5%"),
        ("6. Admin Overhead", -4.0, (107, 114, 128, 255), (243, 244, 246, 255), "-₹8,800", "4%"),
        ("Net Operating Profit", 8.0, PRIMARY_GREEN, SOFT_GREEN, "₹17,600 / mo", "8.0%")
    ]

    base_y = 520
    col_w = 115
    col_gap = 32
    start_x = 75

    # Zero baseline
    d.line([(60, base_y), (1240, base_y)], fill=(203, 213, 225, 255), width=2)
    
    # Running cumulative level
    curr_level = 0.0
    for idx, (label, val, bar_col, fill_col, cost_str, pct_str) in enumerate(bars):
        x = start_x + idx * (col_w + col_gap)
        
        if idx == 0:
            top_y = base_y - int(val * 3.6)
            bot_y = base_y
            curr_level = val
        elif idx == len(bars) - 1:
            top_y = base_y - int(val * 3.6)
            bot_y = base_y
        else:
            prev_level = curr_level
            curr_level += val
            top_y = base_y - int(prev_level * 3.6)
            bot_y = base_y - int(curr_level * 3.6)
            
        draw_card(d, [x, min(top_y, bot_y), x + col_w, max(top_y, bot_y)], radius=8, fill=fill_col, outline=bar_col, width=2)
        
        # Text above bar
        d.text((x + 10, min(top_y, bot_y) - 38), pct_str, fill=bar_col)
        d.text((x + 10, min(top_y, bot_y) - 18), cost_str, fill=DARK_TEXT)
        
        # Label below baseline
        d.text((x + 2, base_y + 12), label, fill=DARK_TEXT)

    # Leakage vulnerability callout box
    draw_card(d, [70, 580, 1230, 680], radius=10, fill=WHITE, outline=ALERT_RED, width=1)
    d.text((90, 595), "OPERATIONAL REALITY: WHERE DOES THE 8% NET PROFIT VANISH?", fill=ALERT_RED)
    d.text((90, 622), "• In an unmonitored 50-truck fleet, a mere 5% to 6% leakage in fuel + 150 km monthly detour per truck equals ₹4.5+ Lakhs/month.", fill=DARK_TEXT)
    d.text((90, 646), "• That single operational leakage stream exceeds 50% of the entire fleet's monthly operating profit.", fill=SEC_TEXT)

    img_wf.save(os.path.join(assets_dir, "financial_pnl_waterfall.png"))
    print("Generated financial_pnl_waterfall.png")

    # -------------------------------------------------------------------------
    # 2. P&L COMPARISON DASHBOARD: Know Your Real Cost Per Km
    # -------------------------------------------------------------------------
    img_cpk = Image.new("RGBA", (1300, 750), BG_LIGHT)
    dc = ImageDraw.Draw(img_cpk)
    
    draw_card(dc, [40, 30, 1260, 710], radius=16, fill=WHITE, outline=BORDER, width=2)
    dc.text((70, 55), "FINANCIAL INTELLIGENCE: REAL-TIME OPERATING COST PER KILOMETRE", fill=DARK_TEXT)
    dc.text((70, 80), "Consolidating Fuel Slips, GPS Distance, Tolls, and Maintenance into Actual Trip Profitability", fill=SEC_TEXT)

    # 4 Financial KPI Cards
    kpis = [
        ("GROSS FREIGHT RATE", "₹38.50 / km", "Average client billing rate", PRIMARY_GREEN),
        ("TOTAL OPERATING COST", "₹28.40 / km", "Consolidated trip expenditure", ALERT_RED),
        ("NET CONTRIBUTION SPREAD", "₹10.10 / km", "Actual operating margin", PRIMARY_GREEN),
        ("RECONCILED GPS DISTANCE", "1,248.6 km", "0.4% Delta vs Driver Odometer", BLUE)
    ]
    for idx, (title, val, sub, col) in enumerate(kpis):
        x = 70 + idx * 295
        draw_card(dc, [x, 115, x + 275, 215], radius=10, fill=WHITE, outline=BORDER, width=1)
        dc.text((x + 15, 130), title, fill=SEC_TEXT)
        dc.text((x + 15, 155), val, fill=col)
        dc.text((x + 15, 185), sub, fill=DARK_TEXT)

    # Cost Breakdown Bar Table
    draw_card(dc, [70, 235, 750, 680], radius=12, fill=WHITE, outline=BORDER, width=1)
    dc.text((90, 255), "Trip Operating Cost Breakdown (₹ / Kilometre)", fill=DARK_TEXT)
    
    cost_components = [
        ("Diesel Fuel Expenditure", "₹14.80 / km", "52.1% of cost", 240, PRIMARY_GREEN),
        ("Driver Trip Allowances & Batas", "₹4.60 / km", "16.2% of cost", 140, BLUE),
        ("Highway Tolls & Fastag", "₹3.80 / km", "13.4% of cost", 110, (147, 51, 234, 255)),
        ("Maintenance & Tire Depreciation", "₹3.40 / km", "12.0% of cost", 95, AMBER),
        ("Vehicle Insurance & Permits", "₹1.80 / km", "6.3% of cost", 60, SEC_TEXT)
    ]
    for idx, (lbl, c_val, c_pct, bar_len, bar_col) in enumerate(cost_components):
        cy = 300 + idx * 72
        dc.text((90, cy), lbl, fill=DARK_TEXT)
        dc.text((90, cy + 22), c_val + "  •  " + c_pct, fill=SEC_TEXT)
        # Bar track
        dc.rounded_rectangle([380, cy + 6, 720, cy + 24], radius=6, fill=(241, 245, 249, 255))
        dc.rounded_rectangle([380, cy + 6, 380 + bar_len, cy + 24], radius=6, fill=bar_col)

    # Right Card: Sample Trip P&L Statement
    draw_card(dc, [780, 235, 1230, 680], radius=12, fill=(252, 254, 253, 255), outline=BORDER, width=1)
    dc.text((805, 255), "Sample Trip P&L Audit Statement", fill=DARK_TEXT)
    dc.text((805, 280), "Trip ID: TRP-88219 (Mumbai → Pune Chakan)", fill=SEC_TEXT)
    
    trip_pnl_lines = [
        ("Client Freight Invoiced:", "₹18,400", PRIMARY_GREEN),
        ("Reconciled Fuel Cost (Receipt Validated):", "-₹7,104", ALERT_RED),
        ("Fastag Tolls (Verified GPS Fastag):", "-₹1,824", ALERT_RED),
        ("Driver Trip Allowance:", "-₹2,200", DARK_TEXT),
        ("Maintenance Reserve Allocation:", "-₹1,632", DARK_TEXT),
        ("───────────────────────────────────", "───────", BORDER),
        ("Total Verified Trip Expenditure:", "₹12,760", DARK_TEXT),
        ("Net Trip Contribution Margin:", "₹5,640 (30.6%)", PRIMARY_GREEN)
    ]
    for idx, (lbl, val, col) in enumerate(trip_pnl_lines):
        ly = 320 + idx * 42
        dc.text((805, ly), lbl, fill=DARK_TEXT if "Trip" in lbl else SEC_TEXT)
        dc.text((1090, ly), val, fill=col)

    img_cpk.save(os.path.join(assets_dir, "financial_cost_per_km.png"))
    print("Generated financial_cost_per_km.png")

    # -------------------------------------------------------------------------
    # 3. MAPPING DIAGRAM: 8 Leakages to Vahan Modules to Financial Outcomes
    # -------------------------------------------------------------------------
    img_map = Image.new("RGBA", (1350, 780), BG_LIGHT)
    dm = ImageDraw.Draw(img_map)
    
    draw_card(dm, [40, 30, 1310, 740], radius=16, fill=WHITE, outline=BORDER, width=2)
    dm.text((70, 55), "ONE CONNECTED SYSTEM: 8 LEAKAGE SOURCES TO FINANCIAL CONTROLS", fill=DARK_TEXT)
    dm.text((70, 80), "Mapping every unmonitored operational leak to its VAHAN architectural control and profit protection outcome", fill=SEC_TEXT)

    # 3 Column Titles
    dm.rounded_rectangle([70, 115, 410, 150], radius=8, fill=ALERT_BG)
    dm.text((85, 125), "OPERATIONAL LEAKAGE (WITHOUT VAHAN)", fill=ALERT_RED)
    
    dm.rounded_rectangle([440, 115, 830, 150], radius=8, fill=SOFT_GREEN)
    dm.text((455, 125), "VAHAN CONTROL MODULE", fill=PRIMARY_GREEN)
    
    dm.rounded_rectangle([860, 115, 1280, 150], radius=8, fill=(239, 246, 255, 255))
    dm.text((875, 125), "FINANCIAL PROFIT PROTECTION", fill=BLUE)

    mapping_rows = [
        ("Fuel Siphoning & Inflated Receipts", "Fuel Intelligence AI & Physics Engine", "Stops paying for unreceived diesel; alerts on drops"),
        ("Unauthorized Highway Detours & Toll Bypasses", "Route Intelligence & Geo-Corridors", "Cuts extra km running cost; protects tires & schedule"),
        ("Unmonitored Depot Vehicle Downtime", "Vehicle Lifecycle State Machine", "Recovers lost contribution margin; boosts utilization"),
        ("Unverified Drivers & Compliance Risk", "Driver KYC & Document Review Queue", "Prevents statutory fines, impoundments & policy loss"),
        ("Paper-Based Dispatch & Lost Invoices", "Trip Management & Milestone Engine", "Accelerates billing; ensures post-trip expense audit"),
        ("Ghost & Misplaced GPS Trackers", "Hardware Registry & Dynamic Pairing", "Eliminates hardware replacement costs & ghost units"),
        ("Multi-Portal Administrative Overhead", "Unified Fleet Command Center", "Eliminates duplicate software costs & manual excel"),
        ("Rogue Trackers & Data Leakage", "Quarantine Isolation & Security Vault", "Zero-trust privacy; prevents client route data leaks")
    ]
    for idx, (leak, mod, val_out) in enumerate(mapping_rows):
        my = 165 + idx * 68
        # Left card
        draw_card(dm, [70, my, 410, my + 56], radius=8, fill=(255, 250, 250, 255), outline=ALERT_RED, width=1)
        dm.text((85, my + 18), leak, fill=DARK_TEXT)
        
        # Center card
        draw_card(dm, [440, my, 830, my + 56], radius=8, fill=(250, 254, 251, 255), outline=PRIMARY_GREEN, width=1)
        dm.text((455, my + 18), mod, fill=PRIMARY_GREEN)
        
        # Right card
        draw_card(dm, [860, my, 1280, my + 56], radius=8, fill=(250, 252, 255, 255), outline=BLUE, width=1)
        dm.text((875, my + 18), val_out, fill=DARK_TEXT)
        
        # Connecting lines
        dm.line([(410, my + 28), (440, my + 28)], fill=PRIMARY_GREEN, width=2)
        dm.line([(830, my + 28), (860, my + 28)], fill=BLUE, width=2)

    img_map.save(os.path.join(assets_dir, "financial_system_mapping.png"))
    print("Generated financial_system_mapping.png")

if __name__ == "__main__":
    generate_financial_graphics()
