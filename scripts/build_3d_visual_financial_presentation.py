import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_3d_visual_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # -------------------------------------------------------------
    # LIGHT 3D FINANCIAL PALETTE
    # -------------------------------------------------------------
    BG_LIGHT = RGBColor(247, 250, 248)       # #F7FAF8 (Slide canvas)
    WHITE = RGBColor(255, 255, 255)          # #FFFFFF (Card panels)
    PRIMARY_GREEN = RGBColor(37, 132, 91)    # #25845B (Brand green)
    SOFT_GREEN = RGBColor(228, 243, 234)     # #E4F3EA (Accent light green)
    DARK_TEXT = RGBColor(36, 53, 45)         # #24352D (Primary dark green text)
    SEC_TEXT = RGBColor(100, 115, 107)       # #64736B (Neutral grey)
    BORDER = RGBColor(225, 234, 228)         # #E1EAE4 (Card border)
    ACCENT_GREEN = RGBColor(167, 216, 184)   # #A7D8B8 (Border accent)
    
    # Financial Leakage / Indicator Colors
    CORAL_LOSS = RGBColor(217, 119, 112)     # #D97770 (Muted coral loss indicator)
    ALERT_RED = RGBColor(220, 38, 38)        # #DC2626 (Danger / exception)
    ALERT_BG = RGBColor(254, 242, 242)       # Soft coral fill
    ALERT_BORDER = RGBColor(252, 165, 165)   # #FCA5A5 (Coral border)
    AMBER = RGBColor(217, 119, 6)            # #D97706 (Warning)
    AMBER_BG = RGBColor(254, 243, 199)       # Soft amber
    BLUE = RGBColor(37, 99, 235)             # #2563EB
    BLUE_BG = RGBColor(239, 246, 255)
    
    ASSETS_DIR = r"c:\Users\ratho\fleetguard\presentation_assets"
    
    def create_base_slide(badge_text, title_text, subtitle_text="", slide_num=None):
        slide = prs.slides.add_slide(blank_layout)
        
        # Canvas Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_LIGHT
        bg.line.fill.background()
        
        # Header accent bar
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.38), Inches(0.06), Inches(0.72))
        bar.fill.solid()
        bar.fill.fore_color.rgb = PRIMARY_GREEN
        bar.line.fill.background()
        
        # Category Badge
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.96), Inches(0.38), Inches(2.8), Inches(0.28))
        badge_box.fill.solid()
        badge_box.fill.fore_color.rgb = SOFT_GREEN
        badge_box.line.color.rgb = ACCENT_GREEN
        badge_box.line.width = Pt(1)
        tf_b = badge_box.text_frame
        tf_b.word_wrap = False
        p_b = tf_b.paragraphs[0]
        p_b.text = badge_text.upper()
        p_b.font.size = Pt(8.5)
        p_b.font.bold = True
        p_b.font.color.rgb = PRIMARY_GREEN
        p_b.alignment = PP_ALIGN.CENTER
        
        # Header Title
        header_box = slide.shapes.add_textbox(Inches(0.96), Inches(0.68), Inches(11.5), Inches(0.75))
        tf_h = header_box.text_frame
        tf_h.word_wrap = True
        tf_h.margin_left = tf_h.margin_top = tf_h.margin_right = tf_h.margin_bottom = 0
        
        p_title = tf_h.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_TEXT
        
        if subtitle_text:
            p_sub = tf_h.add_paragraph()
            p_sub.text = subtitle_text
            p_sub.font.size = Pt(10.5)
            p_sub.font.color.rgb = SEC_TEXT
            p_sub.space_before = Pt(3)
            
        # Clean Footer
        ft_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.15), Inches(11.733), Inches(0.25))
        tf_f = ft_box.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        page_str = f"  |  SLIDE {slide_num:02d}" if slide_num else ""
        p_f.text = f"VAHAN FLEET PROFITABILITY & 3D FINANCIAL INTELLIGENCE{page_str}"
        p_f.font.size = Pt(8)
        p_f.font.color.rgb = SEC_TEXT
        
        return slide

    def add_card(slide, left, top, width, height, fill_color=WHITE, border_color=BORDER, border_width=1.2):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
        return card

    # =========================================================================
    # SLIDE 1: Cover — "Your Fleet Earns Revenue. But Where Is Your Profit Going?"
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_LIGHT
    bg1.line.fill.background()
    
    # 3D Floating Financial Dashboard visual on right
    cover_img = os.path.join(ASSETS_DIR, "visual_3d_cover_pnl.png")
    if os.path.exists(cover_img):
        slide1.shapes.add_picture(cover_img, Inches(5.9), Inches(0.8), Inches(6.8), Inches(5.8))
        
    add_card(slide1, Inches(0.8), Inches(0.9), Inches(5.0), Inches(5.7), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb1 = slide1.shapes.add_textbox(Inches(1.1), Inches(1.2), Inches(4.4), Inches(5.1))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "FLEET FINANCIAL INTELLIGENCE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    p2 = tf1.add_paragraph()
    p2.text = "Your Fleet Earns Revenue.\nBut Where Is Your Profit Going?"
    p2.font.size = Pt(26)
    p2.font.bold = True
    p2.font.color.rgb = DARK_TEXT
    p2.space_before = Pt(6)
    
    p3 = tf1.add_paragraph()
    p3.text = "Discover the hidden operational losses in your fleet and how VAHAN helps control them through connected telematics and financial intelligence."
    p3.font.size = Pt(11)
    p3.font.color.rgb = SEC_TEXT
    p3.space_before = Pt(12)
    
    p_div = tf1.add_paragraph()
    p_div.text = "────────────────────────────────────────"
    p_div.font.size = Pt(8)
    p_div.font.color.rgb = BORDER
    p_div.space_before = Pt(8)
    
    kpis = [
        ("Gross Revenue:", "100% Inflow (Trip Freight Invoices)"),
        ("Operational Costs:", "~92% Outflow (Diesel, Tolls, Crews, Maint)"),
        ("Net Operating Margin:", "Thin 8% (Highly Vulnerable to Leakage)"),
        ("VAHAN Value:", "Active Loss Identification & Profit Shield")
    ]
    for k, v in kpis:
        pk = tf1.add_paragraph()
        pk.text = f"• {k} {v}"
        pk.font.size = Pt(9.5)
        pk.font.color.rgb = DARK_TEXT
        pk.space_before = Pt(3)

    # =========================================================================
    # SLIDE 2: The Money Leakage Map (3D Ecosystem with 6 Leakage Points)
    # =========================================================================
    slide2 = create_base_slide(
        "Financial Leakage Ecosystem",
        "The Money Leakage Map: Where Unmonitored Fleets Lose Margin",
        "Six invisible operational leakage points continuously consume operating margins across trips and vehicles.",
        slide_num=2
    )
    leakages = [
        ("1. Fuel Siphoning & Fraud", "-48% of Operating Cost", "Unmonitored tank drops during parking, inflated receipts, and tank capacity fraud.", CORAL_LOSS, ALERT_BG),
        ("2. Route Detour Overruns", "Extra Kilometres Burn Cash", "Unapproved toll bypasses and unauthorized detours multiply fuel, tire, and transit costs.", CORAL_LOSS, ALERT_BG),
        ("3. Avoidable Vehicle Downtime", "Idle Assets Drag Margins", "Trucks parked idle due to poor status awareness still incur fixed financing and overhead.", CORAL_LOSS, ALERT_BG),
        ("4. Uncontrolled Driver Expenses", "Unrecorded Cash Advances", "Manual paper slips and missing delivery proofs delay freight invoicing by weeks.", AMBER, AMBER_BG),
        ("5. Manual Administration Drag", "High Labor & Error Overhead", "Managing 4+ disjointed GPS portals and spreadsheets creates transcription mistakes.", SEC_TEXT, RGBColor(241, 245, 249)),
        ("6. Hardware Mismanagement", "Ghost & Orphaned Devices", "Untracked GPS trackers lead to redundant replacements and blind-spot road assets.", BLUE, BLUE_BG)
    ]
    for idx, (title, sub, desc, col, bg_p) in enumerate(leakages):
        col_idx = idx % 3
        row_idx = idx // 3
        cx = Inches(0.8 + col_idx * 4.0)
        cy = Inches(1.65 + row_idx * 2.5)
        add_card(slide2, cx, cy, Inches(3.7), Inches(2.3), border_color=BORDER)
        
        # Top pill
        pill = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.15), cy + Inches(0.18), Inches(3.4), Inches(0.35))
        pill.fill.solid()
        pill.fill.fore_color.rgb = bg_p
        pill.line.fill.background()
        tf_p = pill.text_frame
        p = tf_p.paragraphs[0]
        p.text = title
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = col
        
        tb = slide2.shapes.add_textbox(cx + Inches(0.15), cy + Inches(0.65), Inches(3.4), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p_sub = tf.paragraphs[0]
        p_sub.text = sub
        p_sub.font.size = Pt(10)
        p_sub.font.bold = True
        p_sub.font.color.rgb = DARK_TEXT
        
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = SEC_TEXT
        p_d.space_before = Pt(4)

    # =========================================================================
    # SLIDE 3: Fleet Profit and Loss Waterfall Chart
    # =========================================================================
    slide3 = create_base_slide(
        "Financial P&L Waterfall",
        "Fleet Profit & Loss Waterfall: How Operating Expenses Erode Revenue",
        "Illustrative 50-Truck Fleet Baseline — Validated Arithmetic: Gross Revenue (100%) down to 8% Operating Profit.",
        slide_num=3
    )
    wf_img = os.path.join(ASSETS_DIR, "financial_pnl_waterfall.png")
    if os.path.exists(wf_img):
        slide3.shapes.add_picture(wf_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 4: Fuel Theft: Visualize the Money Going Out
    # =========================================================================
    slide4 = create_base_slide(
        "Fuel Intelligence AI",
        "Fuel Theft: Every Unnoticed Drop in Fuel Eats Into Your Profit",
        "3D Fuel Tank Siphoning Cutaway (Ignition OFF) vs Monthly Diesel Financial Loss by Fleet Size Cohort.",
        slide_num=4
    )
    fuel_img = os.path.join(ASSETS_DIR, "visual_3d_fuel_loss_tank.png")
    if os.path.exists(fuel_img):
        slide4.shapes.add_picture(fuel_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 5: Route Deviations: Every Extra Kilometre Costs Money
    # =========================================================================
    slide5 = create_base_slide(
        "Route Intelligence",
        "Route Deviations: Extra Distance Is Extra Operating Cost",
        "3D Isometric Highway Map (NH-48 Corridor vs Coral Unapproved Detour) and Extra Running Cost Chart.",
        slide_num=5
    )
    route_img = os.path.join(ASSETS_DIR, "visual_3d_route_deviation_map.png")
    if os.path.exists(route_img):
        slide5.shapes.add_picture(route_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 6: Vehicle Downtime: Idle Assets Consume Profit
    # =========================================================================
    slide6 = create_base_slide(
        "Asset Utilization",
        "Vehicle Downtime: Your Vehicle Is Parked, But Fixed Costs Continue",
        "3D Fleet Status Board vs Daily Contribution Margin Drag (₹2,400 / day / vehicle).",
        slide_num=6
    )
    down_img = os.path.join(ASSETS_DIR, "visual_3d_vehicle_downtime.png")
    if os.path.exists(down_img):
        slide6.shapes.add_picture(down_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 7: Driver Accountability and Compliance
    # =========================================================================
    slide7 = create_base_slide(
        "Workforce Compliance",
        "Driver Accountability: Control Expenses & Eliminate Compliance Risk",
        "3D Digital Document Verification Queue & Regulatory Protection against Police Impoundment.",
        slide_num=7
    )
    # 3 Verification Status Cards
    cards_kyc = [
        ("APPROVED CREDENTIALS", "Commercial DL & Fitness", "Driver approved for dispatch. 30/15-day proactive renewal alerts active.", PRIMARY_GREEN, SOFT_GREEN),
        ("PENDING AUDIT QUEUE", "Side-by-Side Review", "Compliance officer inspects document validity before granting dispatch access.", AMBER, AMBER_BG),
        ("REJECTED / BLOCKED", "Statutory Risk Prevented", "System strictly blocks dispatching vehicles to uncertified or expired drivers.", ALERT_RED, ALERT_BG)
    ]
    for idx, (head, sub, desc, col, bg_p) in enumerate(cards_kyc):
        cx = Inches(0.8 + idx * 4.0)
        add_card(slide7, cx, Inches(1.65), Inches(3.7), Inches(2.2), border_color=BORDER)
        pill = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.15), Inches(1.85), Inches(3.4), Inches(0.32))
        pill.fill.solid()
        pill.fill.fore_color.rgb = bg_p
        pill.line.fill.background()
        tf_p = pill.text_frame
        p = tf_p.paragraphs[0]
        p.text = head
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = col
        
        tb = slide7.shapes.add_textbox(cx + Inches(0.15), Inches(2.25), Inches(3.4), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p_s = tf.paragraphs[0]
        p_s.text = sub
        p_s.font.size = Pt(10)
        p_s.font.bold = True
        p_s.font.color.rgb = DARK_TEXT
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = SEC_TEXT
        p_d.space_before = Pt(3)

    # Bottom Calculation Card
    add_card(slide7, Inches(0.8), Inches(4.1), Inches(11.733), Inches(2.7), border_color=BORDER)
    tb_b7 = slide7.shapes.add_textbox(Inches(1.0), Inches(4.25), Inches(11.3), Inches(2.4))
    tf_b7 = tb_b7.text_frame
    tf_b7.word_wrap = True
    
    p = tf_b7.paragraphs[0]
    p.text = "REGULATORY RISK & FINANCIAL IMPACT MODELING"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    p_sub7 = tf_b7.add_paragraph()
    p_sub7.text = "• Statutory Impoundment Exposure: Fines of ₹25,000–₹50,000 per violation under Motor Vehicles Act provisions for non-compliant carriage."
    p_sub7.font.size = Pt(10)
    p_sub7.font.color.rgb = DARK_TEXT
    p_sub7.space_before = Pt(4)
    
    p_sub7_2 = tf_b7.add_paragraph()
    p_sub7_2.text = "• Insurance Policy Forfeiture: Accident insurance claims are rejected entirely if the operating driver held an expired commercial badge."
    p_sub7_2.font.size = Pt(10)
    p_sub7_2.font.color.rgb = DARK_TEXT
    p_sub7_2.space_before = Pt(4)

    p_sub7_3 = tf_b7.add_paragraph()
    p_sub7_3.text = "• Digital Pre-Trip Safety Checklists: Flutter driver app enforces 5-point inspection (brakes, tires, lights), preventing highway mechanical breakdowns."
    p_sub7_3.font.size = Pt(10)
    p_sub7_3.font.color.rgb = PRIMARY_GREEN
    p_sub7_3.space_before = Pt(4)

    # =========================================================================
    # SLIDE 8: Trip Management: Every Trip Has a Financial Story
    # =========================================================================
    slide8 = create_base_slide(
        "Logistics Execution",
        "Trip Management: Every Trip Has a Financial & Operational Story",
        "8-Stage Visual Timeline Binding Manifest Rates, Waypoint Telematics, and Proof of Delivery into Accounting.",
        slide_num=8
    )
    trip_img = os.path.join(ASSETS_DIR, "visual_3d_trip_journey.png")
    if os.path.exists(trip_img):
        slide8.shapes.add_picture(trip_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(3.6))
        
    add_card(slide8, Inches(0.8), Inches(5.4), Inches(11.733), Inches(1.45), border_color=BORDER)
    tb_t8 = slide8.shapes.add_textbox(Inches(1.0), Inches(5.5), Inches(11.3), Inches(1.25))
    tf_t8 = tb_t8.text_frame
    tf_t8.word_wrap = True
    p = tf_t8.paragraphs[0]
    p.text = "FINANCIAL RECONCILIATION ACCELERATION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    p_sub = tf_t8.add_paragraph()
    p_sub.text = "Capturing digital Proof of Delivery (POD) signatures and photo receipts en-route accelerates customer freight billing by 10 to 14 days. The post-trip audit cross-checks driver-reported odometer distance against verified GPS telematics, eliminating fraudulent mileage claims."
    p_sub.font.size = Pt(9.5)
    p_sub.font.color.rgb = DARK_TEXT
    p_sub.space_before = Pt(3)

    # =========================================================================
    # SLIDE 9: Hardware Management: Stop Losing Control of Your Devices
    # =========================================================================
    slide9 = create_base_slide(
        "Hardware Governance",
        "Hardware Management: Stop Losing Control of Your GPS Devices",
        "Centralized Device Master, Dynamic Vehicle Pairing Wizard, and Zero-Trust Quarantine Containment.",
        slide_num=9
    )
    hw_cards = [
        ("DEVICE MASTER REGISTRY", "IMEI & SIM Provenance", "Maintains complete device records: Serial, IMEI, protocol type (AIS-140/GT06), and SIM ICCID across maintenance hubs.", PRIMARY_GREEN, SOFT_GREEN),
        ("DYNAMIC PAIRING WIZARD", "3-Click Truck Pairing", "Assign or transfer trackers in seconds; previous vehicle pairings are automatically retired with timestamps.", BLUE, BLUE_BG),
        ("OUTAGE & HEARTBEAT ALERTS", "Real-Time Health Monitoring", "Automated alerts notify operators if a device ceases transmitting, loses external battery, or drops satellite lock.", AMBER, AMBER_BG),
        ("QUARANTINE ISOLATION VAULT", "Zero-Trust Security", "Unmapped or rogue devices are trapped in a dedicated quarantine tenant, protecting customer data streams.", ALERT_RED, ALERT_BG)
    ]
    for idx, (title, sub, desc, col, bg_p) in enumerate(hw_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        cx = Inches(0.8 + col_idx * 6.0)
        cy = Inches(1.7 + row_idx * 2.5)
        add_card(slide9, cx, cy, Inches(5.7), Inches(2.3), border_color=BORDER)
        
        pill = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.2), cy + Inches(0.2), Inches(3.6), Inches(0.32))
        pill.fill.solid()
        pill.fill.fore_color.rgb = bg_p
        pill.line.fill.background()
        tf_p = pill.text_frame
        p = tf_p.paragraphs[0]
        p.text = title
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = col
        
        tb = slide9.shapes.add_textbox(cx + Inches(0.2), cy + Inches(0.65), Inches(5.3), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p_s = tf.paragraphs[0]
        p_s.text = sub
        p_s.font.size = Pt(10.5)
        p_s.font.bold = True
        p_s.font.color.rgb = DARK_TEXT
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = SEC_TEXT
        p_d.space_before = Pt(4)

    # =========================================================================
    # SLIDE 10: Administrative Costs: One Platform Instead of Multiple Systems
    # =========================================================================
    slide10 = create_base_slide(
        "Administrative Optimization",
        "Administrative Costs: One Unified Platform Replaces Multi-Portal Drag",
        "Consolidate fragmented GPS vendor logins, paper trip slips, and manual Excel spreadsheets.",
        slide_num=10
    )
    add_card(slide10, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.1), fill_color=WHITE, border_color=ALERT_BORDER, border_width=1.5)
    tb_l10 = slide10.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.7))
    tf_l10 = tb_l10.text_frame
    tf_l10.word_wrap = True
    p = tf_l10.paragraphs[0]
    p.text = "✕  FRAGMENTED MULTI-PORTAL DRAG"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ALERT_RED
    frag_points = [
        ("4+ Vendor Logins: ", "Separate passwords and interfaces for GPS, Fastag, driver records, and maintenance."),
        ("Manual Excel Data Entry: ", "Staff spend 3 to 4 hours daily re-typing odometer numbers, fuel bills, and trip logs."),
        ("Data Transcription Errors: ", "Manual typos lead to disputed shipper statements and delayed invoice payments."),
        ("Slow Incident Response: ", "Dispatchers cannot answer customer freight inquiries without calling drivers repeatedly.")
    ]
    for h, b in frag_points:
        p_b = tf_l10.add_paragraph()
        p_b.text = "• " + h + b
        p_b.font.size = Pt(9.5)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(8)

    add_card(slide10, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.1), fill_color=WHITE, border_color=ACCENT_GREEN, border_width=1.5)
    tb_r10 = slide10.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(4.7))
    tf_r10 = tb_r10.text_frame
    tf_r10.word_wrap = True
    p = tf_r10.paragraphs[0]
    p.text = "✓  VAHAN UNIFIED FLEET COMMAND CENTER"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    vah_points = [
        ("Single Operational Console: ", "React 18 web console unifying vehicles, drivers, trips, telematics, and fuel."),
        ("Automated Data Pipelines: ", "GPS streams, fuel logs, and inspection checklists auto-bind to vehicle profiles."),
        ("Multi-Depot Filtering: ", "Segment views dynamically by hub, logistics contract, or operating branch."),
        ("Instant Decision Making: ", "Live Leaflet maps and reactive WebSocket tables provide immediate fleet visibility.")
    ]
    for h, b in vah_points:
        p_b = tf_r10.add_paragraph()
        p_b.text = "• " + h + b
        p_b.font.size = Pt(9.5)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 11: Compliance Risk: Prevent Problems Before Dispatch
    # =========================================================================
    slide11 = create_base_slide(
        "Compliance Workflow",
        "Compliance Risk: Prevent Operational & Statutory Problems Before Dispatch",
        "5-Step Compliance Architecture: Document Upload → Expiry Check → Review → Approval → Dispatch Gate.",
        slide_num=11
    )
    risk_steps = [
        ("1. Mobile Upload", "Commercial License & Fitness"),
        ("2. Expiry Tracking", "30 & 15-Day Renewal Alerts"),
        ("3. Review Queue", "Side-by-Side Document Audit"),
        ("4. Formal Action", "Approved or Rejection Notes"),
        ("5. Dispatch Gate", "Unverified Drivers Blocked")
    ]
    for idx, (s_title, s_sub) in enumerate(risk_steps):
        sx = Inches(0.8 + idx * 2.38)
        add_card(slide11, sx, Inches(1.7), Inches(2.25), Inches(2.2), border_color=BORDER)
        # Step number
        sn = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx + Inches(0.15), Inches(1.9), Inches(0.6), Inches(0.35))
        sn.fill.solid()
        sn.fill.fore_color.rgb = SOFT_GREEN
        sn.line.color.rgb = ACCENT_GREEN
        sn.line.width = Pt(1)
        tf_sn = sn.text_frame
        p_sn = tf_sn.paragraphs[0]
        p_sn.text = f"0{idx+1}"
        p_sn.font.size = Pt(11)
        p_sn.font.bold = True
        p_sn.font.color.rgb = PRIMARY_GREEN
        p_sn.alignment = PP_ALIGN.CENTER
        
        tb = slide11.shapes.add_textbox(sx + Inches(0.15), Inches(2.35), Inches(1.95), Inches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = s_title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = DARK_TEXT
        p_sub = tf.add_paragraph()
        p_sub.text = s_sub
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = SEC_TEXT
        p_sub.space_before = Pt(3)

    # Risk matrix bottom card
    add_card(slide11, Inches(0.8), Inches(4.1), Inches(11.733), Inches(2.7), border_color=BORDER)
    tb_rm = slide11.shapes.add_textbox(Inches(1.0), Inches(4.25), Inches(11.3), Inches(2.4))
    tf_rm = tb_rm.text_frame
    tf_rm.word_wrap = True
    p = tf_rm.paragraphs[0]
    p.text = "STATUTORY RISK MITIGATION & INSURANCE POLICY SHIELD"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    matrix_points = [
        ("Zero On-Road Seizures: ", "Mandatory dispatch gating blocks any driver without 100% verified credentials from commercial trips."),
        ("Protected Insurance Validity: ", "Eliminates repudiated accident claims caused by drivers holding lapsed or unendorsed licenses."),
        ("Regulatory Audit Readiness: ", "Immutable historical compliance records ready for state transport authority and corporate shipper inspections.")
    ]
    for h, b in matrix_points:
        p_b = tf_rm.add_paragraph()
        p_b.text = "• " + h + b
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(5)

    # =========================================================================
    # SLIDE 12: Financial Intelligence: Know Your Cost Per Kilometre
    # =========================================================================
    slide12 = create_base_slide(
        "Financial Analytics",
        "Financial Intelligence: Know Your Real Operating Cost Per Kilometre",
        "Consolidating Freight Revenue, Fuel, Tolls, and Maintenance into True Trip Contribution Margin.",
        slide_num=12
    )
    cpk_img = os.path.join(ASSETS_DIR, "financial_cost_per_km.png")
    if os.path.exists(cpk_img):
        slide12.shapes.add_picture(cpk_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 13: How Every VAHAN Feature Protects Business Profit
    # =========================================================================
    slide13 = create_base_slide(
        "Systemic Value Mapping",
        "Systemic Value Mapping: 8 Leakage Sources to VAHAN Financial Controls",
        "Mapping operational vulnerabilities to VAHAN architectural modules and profit protection outcomes.",
        slide_num=13
    )
    map_img = os.path.join(ASSETS_DIR, "financial_system_mapping.png")
    if os.path.exists(map_img):
        slide13.shapes.add_picture(map_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 14: Before VAHAN vs After VAHAN (3D Comparison Cards)
    # =========================================================================
    slide14 = create_base_slide(
        "Business Transformation",
        "The Operational Transformation: Before VAHAN vs. After VAHAN",
        "Contrasting reactive, fragmented fleet management against disciplined, connected profit protection.",
        slide_num=14
    )
    comp_dims = [
        ("1. Fleet Records & Visibility", "Fragmented across 4+ portals, paper slips, and Excel sheets.", "Single pane of glass: vehicles, drivers, trips, and telematics unified."),
        ("2. Fuel Expense Accountability", "Fuel bills paid without tank capacity checks or siphon monitoring.", "Automated siphoning anomaly alerts & tank capacity physics checks."),
        ("3. Route & Highway Corridor", "Drivers take unapproved detours; zero visibility into extra distance.", "Real-time geo-corridor monitoring with automated deviation alerts."),
        ("4. Vehicle Utilization", "Unclear vehicle availability; trucks idle in depots while loads wait.", "Deterministic lifecycle status machine; availability overview grid."),
        ("5. Driver & Regulatory KYC", "Expired licenses discovered during highway police impoundment.", "Digital document vault with 30-day alerts; unverified drivers blocked."),
        ("6. Post-Trip Reconciliation", "Manual, disputed distance claims; delayed client invoicing.", "Reconciles driver odometer against verified GPS kilometers instantly.")
    ]
    t_w = Inches(11.733)
    t_h = Inches(5.1)
    tbl_shape = slide14.shapes.add_table(7, 3, Inches(0.8), Inches(1.65), t_w, t_h)
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(3.2)
    tbl.columns[1].width = Inches(4.266)
    tbl.columns[2].width = Inches(4.266)
    
    headers = ["Operational Dimension", "✕  WITHOUT VAHAN (Operational Bleed)", "✓  WITH VAHAN (Active Profit Control)"]
    for c_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h_text
        cell.fill.solid()
        cell.fill.fore_color.rgb = PRIMARY_GREEN if c_idx == 2 else (ALERT_RED if c_idx == 1 else RGBColor(30, 41, 59))
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    for r_idx, (dim, without_v, with_v) in enumerate(comp_dims, 1):
        c0 = tbl.cell(r_idx, 0)
        c0.text = dim
        c0.fill.solid()
        c0.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else BG_LIGHT
        p0 = c0.text_frame.paragraphs[0]
        p0.font.size = Pt(9.5)
        p0.font.bold = True
        p0.font.color.rgb = DARK_TEXT
        
        c1 = tbl.cell(r_idx, 1)
        c1.text = without_v
        c1.fill.solid()
        c1.fill.fore_color.rgb = ALERT_BG if r_idx % 2 == 1 else WHITE
        p1 = c1.text_frame.paragraphs[0]
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = DARK_TEXT
        
        c2 = tbl.cell(r_idx, 2)
        c2.text = with_v
        c2.fill.solid()
        c2.fill.fore_color.rgb = SOFT_GREEN if r_idx % 2 == 1 else WHITE
        p2 = c2.text_frame.paragraphs[0]
        p2.font.size = Pt(9.5)
        p2.font.bold = True
        p2.font.color.rgb = PRIMARY_GREEN

    # =========================================================================
    # SLIDE 15: Interactive-Style Financial Scenario Calculator
    # =========================================================================
    slide15 = create_base_slide(
        "Financial Scenario Modeling",
        "Financial Impact Scenario: What Uncontrolled Leakage Costs Your Fleet",
        "Editable Scenario Simulator — Labeled: Illustrative Scenario Calculator, Not a Performance Guarantee.",
        slide_num=15
    )
    add_card(slide15, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.1), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb_inp15 = slide15.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
    tf_inp15 = tb_inp15.text_frame
    tf_inp15.word_wrap = True
    
    p = tf_inp15.paragraphs[0]
    p.text = "EDITABLE FLEET SCENARIO ASSUMPTIONS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    assump_lines = [
        ("Fleet Size (Commercial Trucks):", "50 Trucks in Active Service"),
        ("Monthly Fuel Spend / Truck:", "₹1,05,600 / truck / mo"),
        ("Estimated Unexplained Fuel Leakage:", "6.0% (Siphoning & Inflated Claims)"),
        ("Unapproved Extra Distance / Truck:", "180 km / truck / month"),
        ("Operating Cost Per Kilometre:", "₹28.50 / km (Fuel, Maintenance, Tires)"),
        ("Avoidable Idle Downtime Days:", "1.5 days / truck / month"),
        ("Daily Net Contribution Margin:", "₹2,400 / day / vehicle"),
        ("Flagged Loss Resolution Rate:", "60.0% (Operational Investigation)")
    ]
    for lbl, val in assump_lines:
        p_l = tf_inp15.add_paragraph()
        p_l.text = lbl + " " + val
        p_l.font.size = Pt(9.5)
        p_l.font.color.rgb = DARK_TEXT
        p_l.space_before = Pt(5)

    p_note = tf_inp15.add_paragraph()
    p_note.text = "All model inputs editable in VAHAN_Visual_Data_And_Assumptions.xlsx"
    p_note.font.size = Pt(8.5)
    p_note.font.color.rgb = SEC_TEXT
    p_note.space_before = Pt(12)

    add_card(slide15, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.1), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb_out15 = slide15.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_out15 = tb_out15.text_frame
    tf_out15.word_wrap = True
    
    p = tf_out15.paragraphs[0]
    p.text = "CALCULATED LEAKAGE & PROTECTED PROFIT"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ALERT_RED
    
    leak_calcs = [
        ("Potential Monthly Fuel Leakage Loss:", "₹3,16,800 / mo", ALERT_RED),
        ("Potential Unapproved Route Detour Cost:", "₹2,56,500 / mo", ALERT_RED),
        ("Potential Downtime Contribution Loss:", "₹1,80,000 / mo", ALERT_RED),
        ("────────────────────────────────────────", "───────────", BORDER),
        ("TOTAL ESTIMATED MONTHLY EXPOSURE:", "₹7,53,300 / mo", ALERT_RED),
        ("Total Annualized Leakage Exposure:", "₹90.4 Lakhs / yr", ALERT_RED),
        ("────────────────────────────────────────", "───────────", BORDER),
        ("Illustrative Monthly Protected Operating Profit:", "₹4,51,980 / mo", PRIMARY_GREEN),
        ("Illustrative Annualized Protected Profit (60%):", "₹54.2 Lakhs / yr", PRIMARY_GREEN)
    ]
    for lbl, val, col in leak_calcs:
        p_c = tf_out15.add_paragraph()
        p_c.text = f"{lbl:<42} {val:>15}"
        p_c.font.size = Pt(9.5)
        p_c.font.bold = "TOTAL" in lbl or "Protected" in lbl
        p_c.font.color.rgb = col
        p_c.space_before = Pt(3)

    p_gov = tf_out15.add_paragraph()
    p_gov.text = "Governance: Scenario simulation for financial planning. Not a performance guarantee."
    p_gov.font.size = Pt(8.5)
    p_gov.font.color.rgb = SEC_TEXT
    p_gov.space_before = Pt(8)

    # =========================================================================
    # SLIDE 16: Subscription Cost vs Potential Financial Exposure
    # =========================================================================
    slide16 = create_base_slide(
        "Commercial Value Evaluation",
        "Evaluating VAHAN: Subscription Investment vs. Avoidable Leakage Exposure",
        "Comparing Monthly Subscription Plans against Potential Avoidable Loss across 10, 50, and 100 Trucks.",
        slide_num=16
    )
    cost_img = os.path.join(ASSETS_DIR, "visual_3d_cost_vs_leakage.png")
    if os.path.exists(cost_img):
        slide16.shapes.add_picture(cost_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 17: Three Plans, Three Levels of Business Control
    # =========================================================================
    slide17 = create_base_slide(
        "Plan Selection Strategy",
        "Three Plans, Three Levels of Commercial Profit Protection",
        "Aligning platform tiers directly with specific business vulnerabilities and fleet outcomes.",
        slide_num=17
    )
    plan_cards = [
        ("STARTER PLAN", "₹500", "per truck / mo", "Protects Against: Administrative Disorganization & Regulatory KYC Fines", [
            ("Vehicle Master Registry", "Stops double-booking and tracking chaos."),
            ("Driver KYC Review Queue", "Stops vehicle impoundment from expired licenses."),
            ("Trip Dispatch Milestones", "Creates verifiable timelines for client billing."),
            ("Manual Expense Logging", "Eliminates unrecorded cash advances."),
            ("Company-Level Tenancy", "Ensures client data privacy.")
        ], BORDER, DARK_TEXT, False),
        ("PROFESSIONAL PLAN", "₹800", "per truck / mo", "Protects Against: Highway Detours, Unapproved Tolls & Driver Delays (Most Popular)", [
            ("EVERYTHING IN STARTER, PLUS:", "Comprehensive fleet management base."),
            ("Live Interactive GPS Tracking", "Stops blind-spot transit uncertainty."),
            ("Route Geo-Corridor Deviation Alerts", "Eliminates unauthorized detours & toll bypasses."),
            ("Historical Breadcrumb Playback", "Resolves shipper delivery disputes."),
            ("Flutter Driver Mobile Client", "Enforces digital pre-trip safety checklists."),
            ("Offline Event Queue", "Buffers milestones during rural signal drops.")
        ], PRIMARY_GREEN, PRIMARY_GREEN, True),
        ("ENTERPRISE PLAN", "₹1,000", "per truck / mo", "Protects Against: Fuel Theft, Invoice Fraud & Hardware Loss", [
            ("EVERYTHING IN PROFESSIONAL, PLUS:", "Full telematics and mobile tracking suite."),
            ("Fuel Siphoning Anomaly AI", "Flags sudden fuel drops while ignition is OFF."),
            ("Tank Capacity Physics Check", "Rejects fuel bills exceeding vehicle tank spec."),
            ("Cost Per Km Analytics", "Reveals real operating margin by vehicle."),
            ("Hardware Quarantine Vault", "Traps rogue or unmapped GPS trackers."),
            ("AES-256-GCM Vault & Dual Audit", "Guarantees bank-grade security governance.")
        ], BORDER, DARK_TEXT, False)
    ]
    for idx, (p_name, p_cost, p_sub, p_tag, p_feats, p_border, p_acc, is_pro) in enumerate(plan_cards):
        cx = Inches(0.8 + idx * 4.0)
        add_card(slide17, cx, Inches(1.65), Inches(3.7), Inches(5.1),
                 fill_color=WHITE,
                 border_color=PRIMARY_GREEN if is_pro else BORDER,
                 border_width=2.5 if is_pro else 1.2)
        
        if is_pro:
            banner = slide17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.8), Inches(1.48), Inches(2.1), Inches(0.28))
            banner.fill.solid()
            banner.fill.fore_color.rgb = PRIMARY_GREEN
            banner.line.fill.background()
            tf_bn = banner.text_frame
            p_bn = tf_bn.paragraphs[0]
            p_bn.text = "★ MOST POPULAR"
            p_bn.font.size = Pt(8.5)
            p_bn.font.bold = True
            p_bn.font.color.rgb = WHITE
            p_bn.alignment = PP_ALIGN.CENTER
        
        tb = slide17.shapes.add_textbox(cx + Inches(0.18), Inches(1.8), Inches(3.34), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_name
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = p_acc
        
        p_c = tf.add_paragraph()
        p_c.text = p_cost
        p_c.font.size = Pt(26)
        p_c.font.bold = True
        p_c.font.color.rgb = PRIMARY_GREEN if is_pro else DARK_TEXT
        p_c.space_before = Pt(4)
        
        p_s = tf.add_paragraph()
        p_s.text = p_sub
        p_s.font.size = Pt(9)
        p_s.font.color.rgb = SEC_TEXT
        
        p_t = tf.add_paragraph()
        p_t.text = p_tag
        p_t.font.size = Pt(9)
        p_t.font.bold = True
        p_t.font.color.rgb = ALERT_RED if not is_pro else PRIMARY_GREEN
        p_t.space_before = Pt(4)
        
        p_div = tf.add_paragraph()
        p_div.text = "────────────────────────────"
        p_div.font.size = Pt(8)
        p_div.font.color.rgb = BORDER
        p_div.space_before = Pt(4)
        
        for f_head, f_desc in p_feats:
            p_f = tf.add_paragraph()
            p_f.text = ("• " if not f_head.startswith("EVERYTHING") else "★ ") + f_head + ": " + f_desc
            p_f.font.size = Pt(8.5)
            p_f.font.bold = f_head.startswith("EVERYTHING")
            p_f.font.color.rgb = PRIMARY_GREEN if (f_head.startswith("EVERYTHING") or is_pro) else DARK_TEXT
            p_f.space_before = Pt(3)

    # =========================================================================
    # SLIDE 18: Final Profit Protection Message
    # =========================================================================
    slide18 = prs.slides.add_slide(blank_layout)
    bg18 = slide18.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg18.fill.solid()
    bg18.fill.fore_color.rgb = BG_LIGHT
    bg18.line.fill.background()
    
    # Left Card: Executive Call to Action
    add_card(slide18, Inches(0.8), Inches(1.0), Inches(5.7), Inches(5.5), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb_end = slide18.shapes.add_textbox(Inches(1.1), Inches(1.2), Inches(5.1), Inches(5.1))
    tf_end = tb_end.text_frame
    tf_end.word_wrap = True
    
    p = tf_end.paragraphs[0]
    p.text = "STOP GUESSING WHERE YOUR FLEET MONEY GOES"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    p2 = tf_end.add_paragraph()
    p2.text = "See the costs.\nIdentify the leakage.\nTake control with VAHAN."
    p2.font.size = Pt(28)
    p2.font.bold = True
    p2.font.color.rgb = DARK_TEXT
    p2.space_before = Pt(6)
    
    p3 = tf_end.add_paragraph()
    p3.text = "Every day your fleet operates without central visibility, avoidable losses in fuel, detours, and downtime eat away at your hard-earned operating profit."
    p3.font.size = Pt(11)
    p3.font.color.rgb = SEC_TEXT
    p3.space_before = Pt(12)
    
    actions = [
        "✓ 14-Day Production Pilot with 5 to 10 vehicles",
        "✓ Establish your fleet's true baseline cost-per-kilometer",
        "✓ Detect hidden fuel siphoning and tank capacity violations",
        "✓ Monitor driver route compliance on key highway corridors",
        "✓ Zero upfront hardware replacement required"
    ]
    for a in actions:
        pa = tf_end.add_paragraph()
        pa.text = a
        pa.font.size = Pt(9.5)
        pa.font.bold = True
        pa.font.color.rgb = DARK_TEXT
        pa.space_before = Pt(5)

    # Right Card: 4-Step Pilot Roadmap
    add_card(slide18, Inches(6.8), Inches(1.0), Inches(5.733), Inches(5.5), fill_color=SOFT_GREEN, border_color=ACCENT_GREEN, border_width=1.5)
    tb_stp = slide18.shapes.add_textbox(Inches(7.1), Inches(1.2), Inches(5.1), Inches(5.1))
    tf_stp = tb_stp.text_frame
    tf_stp.word_wrap = True
    
    p = tf_stp.paragraphs[0]
    p.text = "4-Step Pilot Implementation Roadmap"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_TEXT
    
    steps = [
        ("Step 1: Fleet Discovery & Onboarding", "Upload 10 vehicle profiles with tank specs and verify driver documents."),
        ("Step 2: Gateway Webhook Setup", "Point existing GPS trackers to VAHAN's multi-protocol gateway (AIS-140/GT06)."),
        ("Step 3: Driver Mobile Deployment", "Equip drivers with the Flutter mobile client for digital safety inspections."),
        ("Step 4: Operational P&L Review", "Review flagged fuel drops, route deviations, and cost-per-km analytics together.")
    ]
    for s_title, s_desc in steps:
        p_s = tf_stp.add_paragraph()
        p_s.text = s_title + ": " + s_desc
        p_s.font.size = Pt(9.5)
        p_s.font.color.rgb = DARK_TEXT
        p_s.space_before = Pt(8)
        
    p_close = tf_stp.add_paragraph()
    p_close.text = "Commercial Inquiries & Pilot Scheduling:\nWeb: www.vahanfleet.com  |  Email: enterprise@vahanfleet.com"
    p_close.font.size = Pt(10.5)
    p_close.font.bold = True
    p_close.font.color.rgb = PRIMARY_GREEN
    p_close.space_before = Pt(20)

    # Output PowerPoint
    out_pptx = r"c:\Users\ratho\fleetguard\VAHAN_3D_Visual_Financial_Presentation.pptx"
    prs.save(out_pptx)
    print(f"Successfully generated: {out_pptx} with {len(prs.slides)} slides.")

if __name__ == "__main__":
    build_3d_visual_presentation()
