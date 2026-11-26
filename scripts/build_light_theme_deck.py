import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_light_theme_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # -------------------------------------------------------------
    # LIGHT THEME COLOR PALETTE (Strict adherence to guidelines)
    # -------------------------------------------------------------
    BG_LIGHT = RGBColor(247, 250, 248)       # #F7FAF8 (Primary background)
    WHITE = RGBColor(255, 255, 255)          # #FFFFFF (Card background)
    PRIMARY_GREEN = RGBColor(37, 132, 91)    # #25845B (Brand green)
    SOFT_GREEN = RGBColor(228, 243, 234)     # #E4F3EA (Accent light green)
    DARK_TEXT = RGBColor(36, 53, 45)         # #24352D (Primary dark text)
    SEC_TEXT = RGBColor(100, 115, 107)       # #64736B (Secondary muted text)
    BORDER = RGBColor(225, 234, 228)         # #E1EAE4 (Card border)
    ACCENT_GREEN = RGBColor(167, 216, 184)   # #A7D8B8 (Border accent)
    
    # Functional Alert / Highlight accents (restrained, high contrast)
    ALERT_RED = RGBColor(220, 38, 38)        # #DC2626 (Danger / exception)
    ALERT_BG = RGBColor(254, 242, 242)       # Soft red pill
    AMBER = RGBColor(217, 119, 6)            # #D97706 (Warning / pending)
    AMBER_BG = RGBColor(254, 243, 199)       # Soft amber pill
    BLUE_ACCENT = RGBColor(37, 99, 235)      # Soft blue accent for mobile/data
    BLUE_BG = RGBColor(239, 246, 255)        # Soft blue pill
    
    ASSETS_DIR = r"c:\Users\ratho\fleetguard\presentation_assets"
    
    # Helper: Create clean light-theme base slide with consistent header & footer
    def create_base_slide(badge_text, title_text, subtitle_text="", slide_num=None):
        slide = prs.slides.add_slide(blank_layout)
        
        # Slide Background (Light #F7FAF8)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_LIGHT
        bg.line.fill.background()
        
        # Subtle header accent vertical bar
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.42), Inches(0.06), Inches(0.72))
        bar.fill.solid()
        bar.fill.fore_color.rgb = PRIMARY_GREEN
        bar.line.fill.background()
        
        # Category Badge Box
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.96), Inches(0.42), Inches(2.5), Inches(0.28))
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
        
        # Title & Subtitle text frame
        header_box = slide.shapes.add_textbox(Inches(0.96), Inches(0.72), Inches(11.5), Inches(0.75))
        tf_h = header_box.text_frame
        tf_h.word_wrap = True
        tf_h.margin_left = tf_h.margin_top = tf_h.margin_right = tf_h.margin_bottom = 0
        
        p_title = tf_h.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(21)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_TEXT
        
        if subtitle_text:
            p_sub = tf_h.add_paragraph()
            p_sub.text = subtitle_text
            p_sub.font.size = Pt(11)
            p_sub.font.color.rgb = SEC_TEXT
            p_sub.space_before = Pt(3)
            
        # Clean Footer with metadata and page number
        ft_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.15), Inches(11.733), Inches(0.25))
        tf_f = ft_box.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        page_str = f"  |  SLIDE {slide_num:02d}" if slide_num else ""
        p_f.text = f"VAHAN FLEET INTELLIGENCE PLATFORM  •  ENTERPRISE PRODUCT STRATEGY{page_str}"
        p_f.font.size = Pt(8)
        p_f.font.color.rgb = SEC_TEXT
        
        return slide

    # Helper: Add rounded card panel with soft border
    def add_card(slide, left, top, width, height, fill_color=WHITE, border_color=BORDER, border_width=1.2):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
        return card

    # =========================================================================
    # SLIDE 1: Cover Slide (Light Theme, 3D Digital Logistics Network, No Trucks)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_LIGHT
    bg1.line.fill.background()
    
    # 3D Digital Logistics Network Graphic on Right
    cover_img_path = os.path.join(ASSETS_DIR, "light_cover_network.png")
    if os.path.exists(cover_img_path):
        slide1.shapes.add_picture(cover_img_path, Inches(6.1), Inches(0.8), Inches(6.6), Inches(5.8))
        
    # Left Content Container Card
    add_card(slide1, Inches(0.8), Inches(1.0), Inches(5.2), Inches(5.5), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    
    tb1 = slide1.shapes.add_textbox(Inches(1.1), Inches(1.3), Inches(4.6), Inches(4.9))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p_brand = tf1.paragraphs[0]
    p_brand.text = "VAHAN"
    p_brand.font.size = Pt(44)
    p_brand.font.bold = True
    p_brand.font.color.rgb = PRIMARY_GREEN
    
    p_tagline = tf1.add_paragraph()
    p_tagline.text = "Intelligent Fleet Management & Telematics Platform"
    p_tagline.font.size = Pt(18)
    p_tagline.font.bold = True
    p_tagline.font.color.rgb = DARK_TEXT
    p_tagline.space_before = Pt(4)
    
    p_sub = tf1.add_paragraph()
    p_sub.text = "One connected platform for fleet operations, GPS visibility, driver management, trip execution and financial intelligence."
    p_sub.font.size = Pt(12)
    p_sub.font.color.rgb = SEC_TEXT
    p_sub.space_before = Pt(14)
    
    p_div = tf1.add_paragraph()
    p_div.text = "────────────────────────────────────────"
    p_div.font.size = Pt(8)
    p_div.font.color.rgb = BORDER
    p_div.space_before = Pt(12)
    
    highlights = [
        "✓ Master Fleet Registry & Driver KYC Compliance",
        "✓ 7 Open Telematics Wire Protocols (AIS-140, GT06, Teltonika)",
        "✓ Algorithmic Fuel Siphoning & Tank Capacity Checks",
        "✓ Real-Time Geo-Corridor Deviation Detection",
        "✓ Tested & Audited: 166 Automated Passing Tests"
    ]
    for h in highlights:
        p_h = tf1.add_paragraph()
        p_h.text = h
        p_h.font.size = Pt(10)
        p_h.font.color.rgb = DARK_TEXT
        p_h.space_before = Pt(4)

    # =========================================================================
    # SLIDE 2: The Industry Problem (The Operational & Financial Bleed)
    # =========================================================================
    slide2 = create_base_slide(
        "Commercial Road Transport Challenges",
        "The Operational & Financial Bleed in Commercial Fleets",
        "Commercial transport operators face razor-thin margins eroded by 7 systemic operational failure points.",
        slide_num=2
    )
    problems = [
        ("01. Fuel Siphoning & Unchecked Invoices", "Fuel represents 45%+ of operating costs. Unmonitored tank drops during stops and invoices exceeding physical tank capacity drain operating margins.", ALERT_RED),
        ("02. Blind-Spot Route Deviations", "Drivers taking unapproved toll bypasses or unpaved detours cause excessive tire wear, delays, and unauthorized side-deliveries without dispatcher knowledge.", AMBER),
        ("03. Regulatory KYC & Document Exposure", "Expired commercial driving licenses and unverified driver credentials risk immediate vehicle impoundment, hefty statutory fines, and insurance nullification.", PRIMARY_GREEN),
        ("04. Disconnected Telematics Chaos", "Operators juggle 3 to 5 separate GPS vendor portals with zero central data consolidation, broken forwarders, and manual Excel tracking.", DARK_TEXT),
        ("05. Hardware Churn & Ghost Tracking", "Unassigned, swapped, or orphaned GPS trackers send phantom telemetry or sit idle without accountability across maintenance hubs.", SEC_TEXT),
        ("06. Paper-Based Driver Coordination", "Trip dispatch, loading manifests, and maintenance checks via phone calls and paper slips cause daily miscommunication and loading delays.", BLUE_ACCENT),
        ("07. Multi-Tenant Data Leakage Risks", "Legacy fleet systems lack cryptographic company-level data isolation, risking client confidentiality and sensitive route leakage across sub-fleets.", ALERT_RED)
    ]
    for idx, (p_title, p_desc, p_col) in enumerate(problems[:6]):
        col = idx % 3
        row = idx // 3
        c_left = Inches(0.8 + col * 4.0)
        c_top = Inches(1.65 + row * 2.5)
        add_card(slide2, c_left, c_top, Inches(3.7), Inches(2.3), border_color=BORDER)
        
        # Pill header
        pill = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.2), c_top + Inches(0.2), Inches(3.3), Inches(0.32))
        pill.fill.solid()
        pill.fill.fore_color.rgb = SOFT_GREEN if p_col == PRIMARY_GREEN else (ALERT_BG if p_col == ALERT_RED else AMBER_BG)
        pill.line.fill.background()
        tf_p = pill.text_frame
        p_pt = tf_p.paragraphs[0]
        p_pt.text = p_title
        p_pt.font.size = Pt(10)
        p_pt.font.bold = True
        p_pt.font.color.rgb = p_col
        
        tb = slide2.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.6), Inches(3.3), Inches(1.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p_sub = tf.paragraphs[0]
        p_sub.text = p_desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT

    # =========================================================================
    # SLIDE 3: The VAHAN Solution (Unified Operating System)
    # =========================================================================
    slide3 = create_base_slide(
        "Unified Architecture",
        "The VAHAN Solution: A Unified Fleet Operating System",
        "Consolidating vehicles, telematics, drivers, routes, and financials into a single real-time source of truth.",
        slide_num=3
    )
    pillars = [
        ("Fleet & Asset Operations", "Master registry for heavy commercial vehicles, dynamic operational status lifecycle, and scheduled preventive maintenance reminders.", PRIMARY_GREEN),
        ("Multi-Protocol Telematics", "Wire-level protocol decoders for 7 major GPS standards (AIS-140, GT06, Teltonika) with HMAC secret-authenticated webhook ingestion.", PRIMARY_GREEN),
        ("Driver Mobile & KYC Governance", "Dedicated Flutter mobile app with pre-trip digital inspections, offline buffering queue, and formal administrative document review.", BLUE_ACCENT),
        ("Route Intelligence & Deviations", "Automated geo-corridor boundary monitoring, historical breadcrumb playback, and instant alerts for unauthorized toll bypasses.", AMBER),
        ("Financial Intelligence & Fuel AI", "Real-time siphoning anomaly detection, tank capacity physics validation, and automated fleet cost-per-kilometer calculation.", ALERT_RED),
        ("Quarantine Security Vault", "Zero-trust hardware isolation for unmapped trackers, AES-256-GCM credential encryption, and cryptographic company-level tenancy.", PRIMARY_GREEN)
    ]
    for idx, (p_title, p_desc, p_col) in enumerate(pillars):
        col = idx % 3
        row = idx // 3
        c_left = Inches(0.8 + col * 4.0)
        c_top = Inches(1.65 + row * 2.5)
        add_card(slide3, c_left, c_top, Inches(3.7), Inches(2.3), border_color=BORDER)
        
        tb = slide3.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(3.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = p_title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = p_col
        
        p_sub = tf.add_paragraph()
        p_sub.text = p_desc
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 4: How VAHAN Works (Complete End-to-End Workflow)
    # =========================================================================
    slide4 = create_base_slide(
        "Product Workflow",
        "How VAHAN Works: Complete Operational Workflow",
        "From foundational asset onboarding to real-time en-route telematics and post-trip financial reconciliation.",
        slide_num=4
    )
    workflow_steps = [
        ("1. Asset & Driver Setup", "Onboard vehicles with VIN and tank specs in Liters. Drivers submit commercial KYC documents for administrative approval.", PRIMARY_GREEN),
        ("2. Hardware Dynamic Pairing", "Register GPS devices by IMEI. Dynamic pairing wizard links trackers to trucks, automatically retiring former pairings.", PRIMARY_GREEN),
        ("3. Trip Dispatching", "Dispatchers create trips with origin, destination, cargo manifest, and assign verified vehicles and approved drivers.", BLUE_ACCENT),
        ("4. Real-Time Telematics", "Gateway ingests GPS points via HMAC webhooks. Engine tracks speed, ignition, battery, and checks geo-corridors.", AMBER),
        ("5. Reconciliation & Audit", "Reconcile fuel receipts against tank capacity specs and cross-check driver odometer logs against GPS distance.", ALERT_RED)
    ]
    for idx, (s_title, s_desc, s_col) in enumerate(workflow_steps):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide4, c_left, Inches(1.8), Inches(2.25), Inches(4.7), border_color=BORDER)
        
        # Step number badge
        step_box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.15), Inches(2.0), Inches(0.6), Inches(0.35))
        step_box.fill.solid()
        step_box.fill.fore_color.rgb = SOFT_GREEN
        step_box.line.color.rgb = ACCENT_GREEN
        step_box.line.width = Pt(1)
        tf_sb = step_box.text_frame
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = f"0{idx+1}"
        p_sb.font.size = Pt(11)
        p_sb.font.bold = True
        p_sb.font.color.rgb = PRIMARY_GREEN
        p_sb.alignment = PP_ALIGN.CENTER
        
        tb = slide4.shapes.add_textbox(c_left + Inches(0.15), Inches(2.5), Inches(1.95), Inches(3.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = s_title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = s_col
        
        p_sub = tf.add_paragraph()
        p_sub.text = s_desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 5: Product Ecosystem Architecture
    # =========================================================================
    slide5 = create_base_slide(
        "Technical Infrastructure",
        "Product Ecosystem Architecture: Decoupled & Enterprise-Grade",
        "Modern cloud infrastructure engineered for low-latency dispatching, high IoT throughput, and cryptographic isolation.",
        slide_num=5
    )
    arch_nodes = [
        ("Fleet Owner Web Dashboard", "React 18 + Tailwind CSS + Leaflet maps. Delivers real-time fleet overview, reactive telematics tables, and exception alerts.", PRIMARY_GREEN),
        ("Driver Mobile Client (Flutter)", "Cross-platform mobile client featuring digital inspection checklists, transit milestones, and local SQLite offline queueing.", BLUE_ACCENT),
        ("Telematics Ingestion Gateway", "FastAPI ingestion service decoding 7 GPS protocols, Traccar HTTP forwarder integration, and HMAC header secret verification.", PRIMARY_GREEN),
        ("Enterprise Security & PostgreSQL", "Company-scoped multi-tenant database models, AES-256-GCM hardware vault, and dual-sided immutable audit trails.", ALERT_RED)
    ]
    for idx, (title, desc, col) in enumerate(arch_nodes):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide5, c_left, c_top, Inches(5.7), Inches(2.3), border_color=BORDER)
        
        tb = slide5.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 6: Operational Visibility (What an Owner Monitors in One Place)
    # =========================================================================
    slide6 = create_base_slide(
        "Executive Oversight",
        "Operational Visibility: Multi-Dimensional Fleet Oversight",
        "Everything a fleet operator needs to monitor, coordinate, and safeguard across regional logistics networks.",
        slide_num=6
    )
    vis_cards = [
        ("Fleet Availability & Status", "Instant visibility into total fleet readiness: vehicles actively moving on highways, parked in depots, or held in maintenance.", PRIMARY_GREEN),
        ("Trip Progress & ETAs", "Real-time tracking of active shipments with milestone timestamps, transit checkpoints, and expected delivery arrival windows.", BLUE_ACCENT),
        ("Critical Maintenance & Fitness", "Automated tracking of odometer intervals, scheduled preventive servicing, and regulatory fitness certificate expiry deadlines.", AMBER),
        ("Exception & Anomaly Alerts", "Real-time notifications triggered exclusively when operational thresholds are breached (speeding, siphoning, route detours).", ALERT_RED),
        ("Multi-Depot Fleet Filtering", "Segment views dynamically by regional hub, client contract, vehicle classification, or operating branch without data overlap.", PRIMARY_GREEN),
        ("Cost & Fuel Accounting", "Comprehensive burn rates, cost-per-kilometer metrics, and validated fuel invoices consolidated into executive dashboards.", DARK_TEXT)
    ]
    for idx, (title, desc, col) in enumerate(vis_cards):
        col_idx = idx % 3
        row_idx = idx // 3
        c_left = Inches(0.8 + col_idx * 4.0)
        c_top = Inches(1.65 + row_idx * 2.5)
        add_card(slide6, c_left, c_top, Inches(3.7), Inches(2.3), border_color=BORDER)
        
        tb = slide6.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(3.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 7: Fleet Owner Dashboard: Deep Dive (With UI Mockup)
    # =========================================================================
    slide7 = create_base_slide(
        "Dashboard Interface",
        "Fleet Owner Dashboard: Core Operational Command Center",
        "Comprehensive operational interface delivering fleet overview, active trips, and exception monitoring.",
        slide_num=7
    )
    # Dashboard Mockup image on Right
    dash_img_path = os.path.join(ASSETS_DIR, "light_dashboard_mockup.png")
    if os.path.exists(dash_img_path):
        slide7.shapes.add_picture(dash_img_path, Inches(5.6), Inches(1.6), Inches(7.0), Inches(5.0))
        
    # Left Content explanation
    add_card(slide7, Inches(0.8), Inches(1.6), Inches(4.5), Inches(5.0), border_color=BORDER)
    tb_d = slide7.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(4.1), Inches(4.6))
    tf_d = tb_d.text_frame
    tf_d.word_wrap = True
    
    p = tf_d.paragraphs[0]
    p.text = "Dashboard Functional Scope"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    dash_bullets = [
        ("Fleet Overview & Availability: ", "Color-coded vehicle status counters showing operational vehicles, trucks in transit, and units in maintenance."),
        ("Real-Time Telematics Grid: ", "High-density vehicle list showing live speed, assigned driver, highway corridor, and status pills."),
        ("Interactive Corridor Map: ", "Leaflet-based live vehicle positioning with speed vectors and waypoint tracking."),
        ("Automated Exception Feeds: ", "Real-time alerts for unapproved route detours and ignition-off fuel drops."),
        ("Driver Document Queue: ", "Side-by-side verification queue for commercial licenses and medical clearances."),
        ("Sample Dashboard Data Note: ", "Visual values on right illustrate application layout and operational structure.")
    ]
    for b_title, b_desc in dash_bullets:
        p_b = tf_d.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(9.5)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(6)

    # =========================================================================
    # SLIDE 8: Fleet Owner Daily Workflow
    # =========================================================================
    slide8 = create_base_slide(
        "Standard Operating Procedures",
        "Fleet Owner Daily Workflow: Operational Routine",
        "A disciplined daily sequence from morning fleet inspection to real-time dispatch and evening audit.",
        slide_num=8
    )
    owner_sop = [
        ("08:00 AM — Morning Fleet Readiness", "Open dashboard to review vehicle availability, driver attendance, and verify that all scheduled trucks have passed pre-trip digital safety inspections.", PRIMARY_GREEN),
        ("09:30 AM — Trip Dispatch & Resource Check", "Create trips for the day's cargo manifests. Assign verified vehicles and KYC-approved drivers; system auto-blocks uncertified drivers.", BLUE_ACCENT),
        ("01:00 PM — Live En-Route Exception Handling", "Monitor active corridor tracking. Investigate any automated route deviation alerts, toll bypasses, or unscheduled long-duration stops.", AMBER),
        ("06:30 PM — Financial & Trip Reconciliation", "Reconcile closed trips: match driver-submitted fuel purchase slips against vehicle tank capacity specs and cross-check GPS odometer distance.", ALERT_RED)
    ]
    for idx, (title, desc, col) in enumerate(owner_sop):
        c_top = Inches(1.65 + idx * 1.3)
        add_card(slide8, Inches(0.8), c_top, Inches(11.733), Inches(1.15), border_color=BORDER)
        
        # Pill
        p_box = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), c_top + Inches(0.12), Inches(3.2), Inches(0.3))
        p_box.fill.solid()
        p_box.fill.fore_color.rgb = SOFT_GREEN if col == PRIMARY_GREEN else (ALERT_BG if col == ALERT_RED else (AMBER_BG if col == AMBER else BLUE_BG))
        p_box.line.fill.background()
        tf_pb = p_box.text_frame
        p_pbt = tf_pb.paragraphs[0]
        p_pbt.text = title
        p_pbt.font.size = Pt(9.5)
        p_pbt.font.bold = True
        p_pbt.font.color.rgb = col
        
        tb = slide8.shapes.add_textbox(Inches(4.4), c_top + Inches(0.1), Inches(7.9), Inches(0.95))
        tf = tb.text_frame
        tf.word_wrap = True
        p_desc_p = tf.paragraphs[0]
        p_desc_p.text = desc
        p_desc_p.font.size = Pt(10.5)
        p_desc_p.font.color.rgb = DARK_TEXT

    # =========================================================================
    # SLIDE 9: Vehicle Management & Master Lifecycle
    # =========================================================================
    slide9 = create_base_slide(
        "Asset Governance",
        "Vehicle Management: Technical Profiles & Lifecycle States",
        "Complete technical governance of commercial vehicles from initial onboarding to decommissioning.",
        slide_num=9
    )
    v_cards = [
        ("Technical Vehicle Specifications", "Maintains comprehensive technical records: License Plate, VIN, Make, Model, Fuel Tank Capacity (in Liters), Gross Vehicle Weight, and Axle configuration stored in PostgreSQL.", PRIMARY_GREEN),
        ("Deterministic Status State Machine", "Enforces strict status transitions (Active -> In Transit -> Maintenance -> Out of Service -> Decommissioned), preventing double-booking of assigned vehicles.", BLUE_ACCENT),
        ("Driver & Device Assignment", "Dynamic pairing of vehicles with approved drivers and active GPS trackers with automatic closure of previous assignments.", PRIMARY_GREEN),
        ("Maintenance & Fitness Tracking", "Automated tracking of odometer readings, scheduled engine servicing intervals, and fitness renewal deadlines preventing illegal operations.", AMBER)
    ]
    for idx, (title, desc, col) in enumerate(v_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide9, c_left, c_top, Inches(5.7), Inches(2.3), border_color=BORDER)
        
        tb = slide9.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 10: Driver Management & KYC Verification
    # =========================================================================
    slide10 = create_base_slide(
        "Workforce Compliance",
        "Driver Management: Profiles, KYC & Regulatory Compliance",
        "Mitigate operational liabilities through structured driver background records and compliance tracking.",
        slide_num=10
    )
    d_cards = [
        ("Digital Driver Master Profiles", "Centralized driver master capturing legal name, permanent address, contact details, emergency contacts, blood group, and assigned fleet hub.", PRIMARY_GREEN),
        ("Commercial Document Archiving", "Secure encrypted storage for Commercial Driving Licenses, Aadhaar / National ID, Medical Fitness certificates, and police verification reports.", BLUE_ACCENT),
        ("Automated Expiration Alerts", "Proactive dashboard notifications 30 and 15 days prior to commercial driving license or medical fitness expirations, preventing impoundment.", AMBER),
        ("Driver Assignment History", "Full audit log of vehicle-driver pairings, trip completion rates, safety inspection records, and past route compliance performance.", PRIMARY_GREEN)
    ]
    for idx, (title, desc, col) in enumerate(d_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide10, c_left, c_top, Inches(5.7), Inches(2.3), border_color=BORDER)
        
        tb = slide10.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 11: Driver Document Verification Workflow
    # =========================================================================
    slide11 = create_base_slide(
        "Compliance Workflow",
        "Driver Document Review & Verification Queue",
        "Structured compliance workflow ensuring only certified, legally verified drivers are dispatched.",
        slide_num=11
    )
    doc_steps = [
        ("1. Driver Uploads Documents", "Driver uploads commercial license, medical fitness certificate, and national ID via mobile app or depot terminal.", PRIMARY_GREEN),
        ("2. Pending Review Queue", "Fleet compliance officer accesses centralized queue showing pending documents with side-by-side previews.", BLUE_ACCENT),
        ("3. Formal Verification Decision", "Auditor inspects validity dates, authenticity, and issues formal APPROVED or REJECTED status.", AMBER),
        ("4. Rejection Notes & Resubmission", "Rejections require mandatory explanatory notes sent immediately to the driver with audit timestamps.", ALERT_RED),
        ("5. Dispatch Gate Enforced", "System strictly blocks any driver without 100% verified documents from being assigned to active trips.", PRIMARY_GREEN)
    ]
    for idx, (title, desc, col) in enumerate(doc_steps):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide11, c_left, Inches(1.8), Inches(2.25), Inches(4.7), border_color=BORDER)
        
        step_box = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.15), Inches(2.0), Inches(0.6), Inches(0.35))
        step_box.fill.solid()
        step_box.fill.fore_color.rgb = SOFT_GREEN
        step_box.line.color.rgb = ACCENT_GREEN
        step_box.line.width = Pt(1)
        tf_sb = step_box.text_frame
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = f"0{idx+1}"
        p_sb.font.size = Pt(11)
        p_sb.font.bold = True
        p_sb.font.color.rgb = PRIMARY_GREEN
        p_sb.alignment = PP_ALIGN.CENTER
        
        tb = slide11.shapes.add_textbox(c_left + Inches(0.15), Inches(2.5), Inches(1.95), Inches(3.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 12: Driver Daily Workflow (Shift Start to Trip Completion)
    # =========================================================================
    slide12 = create_base_slide(
        "Driver Experience",
        "Driver Daily Workflow: Shift Start to Trip Completion",
        "Intuitive mobile flow guiding commercial drivers through pre-trip compliance, transit, and delivery proof.",
        slide_num=12
    )
    driver_sop = [
        ("Step 1: Secure Mobile Login & QR Verification", "Driver signs in using registered mobile phone OTP or depot QR code scan; active vehicle pairing confirmed.", PRIMARY_GREEN),
        ("Step 2: Digital Pre-Trip Safety Inspection", "Completes 5-point checklist: tire pressure, air brake pressure, lights, engine oil, and emergency triangle.", BLUE_ACCENT),
        ("Step 3: Trip Acceptance & Waypoint Navigation", "Inspects assigned origin, destination, cargo manifest, and highway corridor route instructions.", PRIMARY_GREEN),
        ("Step 4: Transit Checkpoints & Milestone Logging", "Logs gate departure, transit expressway checkpoints, and destination arrival timestamps.", AMBER),
        ("Step 5: Proof of Delivery & Expense Logging", "Captures customer consignee signature, photos of signed Proof of Delivery (POD), and en-route toll receipts.", ALERT_RED)
    ]
    for idx, (title, desc, col) in enumerate(driver_sop):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide12, c_left, Inches(1.8), Inches(2.25), Inches(4.7), border_color=BORDER)
        
        step_box = slide12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.15), Inches(2.0), Inches(0.6), Inches(0.35))
        step_box.fill.solid()
        step_box.fill.fore_color.rgb = SOFT_GREEN
        step_box.line.color.rgb = ACCENT_GREEN
        step_box.line.width = Pt(1)
        tf_sb = step_box.text_frame
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = f"0{idx+1}"
        p_sb.font.size = Pt(11)
        p_sb.font.bold = True
        p_sb.font.color.rgb = PRIMARY_GREEN
        p_sb.alignment = PP_ALIGN.CENTER
        
        tb = slide12.shapes.add_textbox(c_left + Inches(0.15), Inches(2.5), Inches(1.95), Inches(3.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 13: Driver Mobile Application (Smartphone Mockup)
    # =========================================================================
    slide13 = create_base_slide(
        "Mobile Application",
        "Driver Mobile Application: Frontline Operational Client",
        "Purpose-built Flutter application connecting frontline commercial drivers directly to dispatchers.",
        slide_num=13
    )
    phone_img_path = os.path.join(ASSETS_DIR, "light_driver_smartphone_mockup.png")
    if os.path.exists(phone_img_path):
        slide13.shapes.add_picture(phone_img_path, Inches(6.8), Inches(1.5), Inches(4.6), Inches(5.3))
        
    add_card(slide13, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1), border_color=BORDER)
    tb_m = slide13.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.7))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    
    p = tf_m.paragraphs[0]
    p.text = "Key Mobile Capabilities"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    mob_points = [
        ("Assigned Trip Overview: ", "Drivers view origin/destination coordinates, cargo manifest, and real-time transit instructions."),
        ("Digital Safety Inspections: ", "Standardized pre-trip/post-trip safety checklists (tires, brakes, lights, fluids) with instant pass/fail validation."),
        ("Offline SQLite Event Buffer: ", "Resilient local event queue buffers milestones, inspections, and GPS coordinates during low-signal highway stretches, auto-syncing when 4G resumes."),
        ("En-Route Expense & Toll Logging: ", "Drivers photograph physical toll receipts and fuel purchase slips, instantly attaching them to active trip audits."),
        ("Verification Evidence: ", "Verified via driver_app/ source code and backend/routers/driver_mobile.py.")
    ]
    for b_title, b_desc in mob_points:
        p_b = tf_m.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 14: GPS Tracking & Telematics (Complete Architecture)
    # =========================================================================
    slide14 = create_base_slide(
        "IoT Telematics Gateway",
        "GPS Tracking & Telematics: Complete End-to-End Architecture",
        "The complete ingestion chain: GPS Device → Traccar Gateway → Vahan Webhook → Backend → DB → Dashboard.",
        slide_num=14
    )
    arch_diag_path = os.path.join(ASSETS_DIR, "light_telematics_architecture.png")
    if os.path.exists(arch_diag_path):
        slide14.shapes.add_picture(arch_diag_path, Inches(0.8), Inches(1.7), Inches(11.733), Inches(5.0))

    # =========================================================================
    # SLIDE 15: The GPS Data Journey (From Satellite to Dashboard)
    # =========================================================================
    slide15 = create_base_slide(
        "Data Pipeline",
        "The GPS Data Journey: Satellite Signal to Owner Dashboard",
        "A high-throughput, sub-second telemetry pipeline engineered for data integrity and duplicate prevention.",
        slide_num=15
    )
    journey_steps = [
        ("Step 1: Satellite Fix & Hardware Sensor Ingest", "Vehicle GPS tracker captures latitude, longitude, speed, heading, altitude, and ignition sensor status.", PRIMARY_GREEN),
        ("Step 2: Binary/ASCII Protocol Transmission", "Tracker transmits wire packets over cellular network to gateway listening on designated TCP/UDP ports.", PRIMARY_GREEN),
        ("Step 3: Webhook Forwarding with HMAC Secret", "Gateway normalizes position JSON and pushes to Vahan webhook with X-Telematics-Secret header.", BLUE_ACCENT),
        ("Step 4: FastAPI Validation & Deduplication", "Backend performs constant-time secret comparison, drops duplicate timestamps, and binds to company tenant.", AMBER),
        ("Step 5: Live Map Streaming & Anomaly Evaluation", "Updates PostgreSQL vehicle position and pushes coordinates to dispatcher browser via WebSocket.", ALERT_RED)
    ]
    for idx, (title, desc, col) in enumerate(journey_steps):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide15, c_left, Inches(1.8), Inches(2.25), Inches(4.7), border_color=BORDER)
        
        step_box = slide15.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.15), Inches(2.0), Inches(0.6), Inches(0.35))
        step_box.fill.solid()
        step_box.fill.fore_color.rgb = SOFT_GREEN
        step_box.line.color.rgb = ACCENT_GREEN
        step_box.line.width = Pt(1)
        tf_sb = step_box.text_frame
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = f"0{idx+1}"
        p_sb.font.size = Pt(11)
        p_sb.font.bold = True
        p_sb.font.color.rgb = PRIMARY_GREEN
        p_sb.alignment = PP_ALIGN.CENTER
        
        tb = slide15.shapes.add_textbox(c_left + Inches(0.15), Inches(2.5), Inches(1.95), Inches(3.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 16: Trip Management (Full 10-Step Lifecycle)
    # =========================================================================
    slide16 = create_base_slide(
        "Logistics Execution",
        "Trip Management: Full 10-Step Operational Lifecycle",
        "End-to-end trip execution pipeline linking vehicles, drivers, route corridors, and consignment manifests.",
        slide_num=16
    )
    trip_diag_path = os.path.join(ASSETS_DIR, "light_trip_lifecycle.png")
    if os.path.exists(trip_diag_path):
        slide16.shapes.add_picture(trip_diag_path, Inches(0.8), Inches(1.65), Inches(11.733), Inches(3.5))
        
    add_card(slide16, Inches(0.8), Inches(5.3), Inches(11.733), Inches(1.5), border_color=BORDER)
    tb_tl = slide16.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(11.3), Inches(1.3))
    tf_tl = tb_tl.text_frame
    tf_tl.word_wrap = True
    p = tf_tl.paragraphs[0]
    p.text = "Operational Lifecycle Governance"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    p_sub = tf_tl.add_paragraph()
    p_sub.text = "Each trip follows an enforceable status state machine: DRAFT → DISPATCHED → IN_TRANSIT → COMPLETED. The engine prevents dispatching unverified drivers, auto-binds GPS telematics streams during transit, logs waypoint milestones, and automates post-trip fuel and distance reconciliation."
    p_sub.font.size = Pt(10)
    p_sub.font.color.rgb = DARK_TEXT
    p_sub.space_before = Pt(3)

    # =========================================================================
    # SLIDE 17: Route Intelligence & Deviation Detection
    # =========================================================================
    slide17 = create_base_slide(
        "Route Intelligence",
        "Route Intelligence: Geo-Corridors & Real-Time Detour Detection",
        "Eliminate unauthorized detours, delays, and toll bypasses with automated geo-corridor tracking.",
        slide_num=17
    )
    route_map_path = os.path.join(ASSETS_DIR, "light_route_deviation_map.png")
    if os.path.exists(route_map_path):
        slide17.shapes.add_picture(route_map_path, Inches(5.4), Inches(1.6), Inches(7.1), Inches(5.1))
        
    add_card(slide17, Inches(0.8), Inches(1.6), Inches(4.3), Inches(5.1), border_color=BORDER)
    tb_r = slide17.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.9), Inches(4.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    
    p = tf_r.paragraphs[0]
    p.text = "Route Intelligence Capabilities"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    r_points = [
        ("Geo-Corridor Boundary Rules: ", "Defines approved highway corridors with configurable buffer widths (e.g., 5 km)."),
        ("Automated Deviation Engine: ", "FastAPI backend calculates cross-track error distance; alerts dispatchers when vehicles stray off authorized highways."),
        ("Historical Breadcrumb Playback: ", "Scrub through past trip paths with speed vectors and timestamps to investigate driver detours."),
        ("Toll Bypass Prevention: ", "Stops drivers from taking unpaved, hazardous bypasses that damage vehicle suspension and tires."),
        ("Adherence Scoring: ", "Computes post-trip corridor adherence scores for driver appraisal and safety incentives.")
    ]
    for b_title, b_desc in r_points:
        p_b = tf_r.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(9.5)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 18: Financial Intelligence Engine (Fuel Fraud & Analytics)
    # =========================================================================
    slide18 = create_base_slide(
        "Financial Protection",
        "Financial Intelligence: Fuel Siphoning AI & Physics Validation",
        "Algorithmic fraud prevention that protects the single largest operating expense in road logistics.",
        slide_num=18
    )
    fuel_diag_path = os.path.join(ASSETS_DIR, "light_fuel_intelligence.png")
    if os.path.exists(fuel_diag_path):
        slide18.shapes.add_picture(fuel_diag_path, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 19: Fuel Intelligence Workflow (Entry to Anomaly Resolution)
    # =========================================================================
    slide19 = create_base_slide(
        "Audit Pipeline",
        "Fuel Intelligence Workflow: Fuel Entry to Anomaly Resolution",
        "Step-by-step audit trail protecting against fuel siphoning, inflated pump bills, and odometer tampering.",
        slide_num=19
    )
    fuel_sop = [
        ("1. Fuel Purchase Logging", "Driver or depot manager logs liters, total cost, fuel pump receipt photo, and odometer reading via mobile app or web.", PRIMARY_GREEN),
        ("2. Tank Capacity Physics Check", "Validation engine automatically checks liters purchased against the physical fuel tank capacity stored in vehicle profile.", ALERT_RED),
        ("3. Siphoning AI Telemetry Scan", "Engine continuously cross-checks fuel level drops against ignition state; sudden drops with ignition OFF flag siphoning.", ALERT_RED),
        ("4. Flagged Exception Queue", "Violations enter compliance queue with incident coordinates, duration, and volume lost for supervisor review.", AMBER),
        ("5. Odometer Reconciliation", "Reconciles reported odometer against verified GPS trip distance, computing precise Cost Per Kilometer metrics.", PRIMARY_GREEN)
    ]
    for idx, (title, desc, col) in enumerate(fuel_sop):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide19, c_left, Inches(1.8), Inches(2.25), Inches(4.7), border_color=BORDER)
        
        step_box = slide19.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.15), Inches(2.0), Inches(0.6), Inches(0.35))
        step_box.fill.solid()
        step_box.fill.fore_color.rgb = SOFT_GREEN
        step_box.line.color.rgb = ACCENT_GREEN
        step_box.line.width = Pt(1)
        tf_sb = step_box.text_frame
        p_sb = tf_sb.paragraphs[0]
        p_sb.text = f"0{idx+1}"
        p_sb.font.size = Pt(11)
        p_sb.font.bold = True
        p_sb.font.color.rgb = PRIMARY_GREEN
        p_sb.alignment = PP_ALIGN.CENTER
        
        tb = slide19.shapes.add_textbox(c_left + Inches(0.15), Inches(2.5), Inches(1.95), Inches(3.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 20: Hardware Asset Management (Device Inventory & Pairing)
    # =========================================================================
    slide20 = create_base_slide(
        "Hardware Lifecycle",
        "Hardware Asset Management: Device Registry & Pairing Wizard",
        "Complete hardware inventory control, dynamic vehicle pairing, and gateway synchronization.",
        slide_num=20
    )
    h_cards = [
        ("Device Master Inventory", "Maintains complete device records: Serial Number, IMEI, Protocol type, SIM card ICCID, and firmware version across hubs.", PRIMARY_GREEN),
        ("Dynamic Vehicle Pairing Wizard", "Pair or transfer GPS trackers between vehicles in seconds; previous device assignments are automatically retired with historical timestamps.", BLUE_ACCENT),
        ("Provider Gateway Synchronization", "Direct API integration with Traccar and custom GPS servers to synchronize device registrations, device states, and telemetry ports.", PRIMARY_GREEN),
        ("Heartbeat & Health Monitoring", "Automated monitoring flagging devices that stop transmitting telemetry, experience power loss, or lose satellite lock.", AMBER)
    ]
    for idx, (title, desc, col) in enumerate(h_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide20, c_left, c_top, Inches(5.7), Inches(2.3), border_color=BORDER)
        
        tb = slide20.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 21: Hardware Lifecycle & Quarantine Security
    # =========================================================================
    slide21 = create_base_slide(
        "Zero-Trust Containment",
        "Hardware Lifecycle & Quarantine Security Governance",
        "Zero-trust isolation protecting customer tenant dashboards from rogue or unmapped hardware.",
        slide_num=21
    )
    sec_diag_path = os.path.join(ASSETS_DIR, "light_hardware_quarantine.png")
    if os.path.exists(sec_diag_path):
        slide21.shapes.add_picture(sec_diag_path, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 22: Enterprise Security & Cloud Administration
    # =========================================================================
    slide22 = create_base_slide(
        "Enterprise Security",
        "Enterprise Security, Encryption & Multi-Tenancy",
        "Engineered for bank-grade corporate data isolation, cryptographic privacy, and regulatory compliance.",
        slide_num=22
    )
    s_pillars = [
        ("Company-Level Multi-Tenancy", "Every database query, API route, and telematics packet is strictly isolated by cryptographic company_id. Zero cross-company leakage.", PRIMARY_GREEN),
        ("AES-256-GCM Credential Vault", "Hardware provider API keys, webhook secrets, and sensitive tokens are encrypted using AES-GCM; credentials are never exposed via API responses.", BLUE_ACCENT),
        ("Granular Role-Based Access Control", "Enforces distinct permissions for Fleet Owners, Dispatch Managers, Safety Officers, Drivers, and System Super-Admins.", PRIMARY_GREEN),
        ("Tested Asynchronous Engine", "FastAPI Python backend with SQLAlchemy ORM, connection pooling, and continuous automated test verification (166 tests).", ALERT_RED)
    ]
    for idx, (title, desc, col) in enumerate(s_pillars):
        c_left = Inches(0.8 + idx * 2.95)
        add_card(slide22, c_left, Inches(1.7), Inches(2.8), Inches(4.8), border_color=BORDER)
        tb = slide22.shapes.add_textbox(c_left + Inches(0.15), Inches(1.85), Inches(2.5), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(10)

    # =========================================================================
    # SLIDE 23: Why Choose VAHAN? 7 Core Differentiators
    # =========================================================================
    slide23 = create_base_slide(
        "Strategic Value",
        "Why VAHAN? 7 Verified Enterprise Differentiators",
        "The clear technical and commercial advantages that distinguish VAHAN from legacy GPS providers.",
        slide_num=23
    )
    diffs = [
        ("1. Single Unified Platform", "Consolidates vehicles, drivers, hardware, routes, and fuel economics into one pane of glass.", PRIMARY_GREEN),
        ("2. Wire-Level Telematics", "Supports 7 major GPS protocols with built-in decoders, avoiding proprietary hardware lock-in.", BLUE_ACCENT),
        ("3. Proactive Fuel Siphoning AI", "Flags fuel theft instantly by correlating ignition states and sudden tank drops.", ALERT_RED),
        ("4. Automated Route Auditing", "Geo-corridor boundary rules stop unauthorized detours, delays, and toll evasions.", AMBER),
        ("5. Frontline Driver Mobile App", "Empowers drivers with digital vehicle inspections and offline event synchronization.", PRIMARY_GREEN),
        ("6. Zero-Trust Hardware Vault", "Quarantine tenant and AES-GCM encryption prevent rogue device security breaches.", PRIMARY_GREEN),
        ("7. Honest, Audited Engineering", "Built on 166 passing automated tests with verifiable endpoints and zero marketing exaggeration.", DARK_TEXT)
    ]
    for idx, (title, desc, col) in enumerate(diffs):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.65 + row_idx * 1.3)
        add_card(slide23, c_left, c_top, Inches(5.7), Inches(1.18), border_color=BORDER)
        tb = slide23.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.1), Inches(5.3), Inches(0.98))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = DARK_TEXT
        p_sub.space_before = Pt(2)

    # =========================================================================
    # SLIDE 24: Product Roadmap & Capability Status
    # =========================================================================
    slide24 = create_base_slide(
        "Product Roadmap",
        "Product Roadmap & Verified Engineering Status",
        "Honest, transparent distinction between operational capabilities, active validation, and future features.",
        slide_num=24
    )
    roadmap_cols = [
        ("AVAILABLE TODAY (VERIFIED)", [
            "• Complete Vehicle Master Registry & Lifecycle",
            "• Driver Profiles & Document KYC Verification Queue",
            "• Trip Creation, Dispatching & Milestone Engine",
            "• 7 Telematics Wire Decoders (AIS-140, GT06, Teltonika)",
            "• Traccar Webhook HMAC-Authenticated Ingestion",
            "• Route Geo-Corridor Deviation Detection",
            "• Fuel Siphoning AI & Tank Capacity Physics Validation",
            "• Quarantine Isolation & AES-256-GCM Hardware Vault",
            "• 166 Automated Passing Test Suite"
        ], PRIMARY_GREEN, SOFT_GREEN),
        ("UNDER FIELD VALIDATION", [
            "• Live Physical On-Road GSM Cellular SIM Field Testing",
            "• Real-World Harsh Environmental Bench Endurance",
            "• High-Vibration Road Hardware Calibration",
            "• Low-Signal Highway Reconnection Optimization",
            "• Multi-Regional Cellular Roaming Benchmarks"
        ], AMBER, AMBER_BG),
        ("PLANNED FUTURE ENHANCEMENTS", [
            "• Continuous MQTT Broker Background Daemon (Spec complete in docs/mqtt_production_subscriber_spec.md)",
            "• Autonomous AI Dispatching Agents",
            "• Predictive Mechanical Failure Forecasting",
            "• Advanced Telematics CAN-Bus Sensor Integration"
        ], SEC_TEXT, RGBColor(241, 245, 249))
    ]
    for idx, (col_title, items, col, bg_pill) in enumerate(roadmap_cols):
        c_left = Inches(0.8 + idx * 4.0)
        add_card(slide24, c_left, Inches(1.65), Inches(3.7), Inches(5.1), border_color=BORDER)
        
        # Header pill
        p_box = slide24.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.2), Inches(1.85), Inches(3.3), Inches(0.35))
        p_box.fill.solid()
        p_box.fill.fore_color.rgb = bg_pill
        p_box.line.fill.background()
        tf_pb = p_box.text_frame
        p_pbt = tf_pb.paragraphs[0]
        p_pbt.text = col_title
        p_pbt.font.size = Pt(9.5)
        p_pbt.font.bold = True
        p_pbt.font.color.rgb = col
        p_pbt.alignment = PP_ALIGN.CENTER
        
        tb = slide24.shapes.add_textbox(c_left + Inches(0.2), Inches(2.3), Inches(3.3), Inches(4.3))
        tf = tb.text_frame
        tf.word_wrap = True
        for i_text in items:
            p_i = tf.add_paragraph()
            p_i.text = i_text
            p_i.font.size = Pt(9.5)
            p_i.font.color.rgb = DARK_TEXT
            p_i.space_before = Pt(6)

    # =========================================================================
    # SLIDE 25: Transparent Pricing Plans (Starter, Pro [Featured], Enterprise)
    # =========================================================================
    slide25 = create_base_slide(
        "Commercial Tiers",
        "Transparent, Predictable Per-Truck Pricing",
        "Simple per-truck plans with zero hidden fees. Scale effortlessly as your commercial fleet expands.",
        slide_num=25
    )
    plans = [
        ("STARTER PLAN", "₹500", "per truck / month", "Essential Fleet Ops & Compliance",
         ["Vehicle Master Registry & Profiles", "Driver Profiles & KYC Document Vault", "Document Verification Workflow Queue", "Trip Dispatching & Milestones", "Manual Expense & Toll Recording", "Company-Level Multi-Tenancy", "Standard Role-Based Access Control"],
         BORDER, DARK_TEXT, False),
        ("PROFESSIONAL PLAN", "₹800", "per truck / month", "Live GPS Tracking & Telematics (Most Popular)",
         ["EVERYTHING IN STARTER, PLUS:", "Live Interactive GPS Tracking Map", "Telematics Webhook Ingestion (Traccar)", "7 Open Wire Protocol Decoders", "Historical Route Breadcrumb Playback", "Automated Route Deviation Alerts", "Driver Mobile Application (Flutter)", "Pre-Trip / Post-Trip Digital Inspections"],
         PRIMARY_GREEN, PRIMARY_GREEN, True),
        ("ENTERPRISE PLAN", "₹1,000", "per truck / month", "Financial Intelligence & Hardware Vault",
         ["EVERYTHING IN PROFESSIONAL, PLUS:", "Fuel Siphoning Anomaly AI Engine", "Tank Capacity Physics Validation", "Fleet Cost Per Km Intelligence", "Super-Admin Quarantine Governance", "AES-256-GCM Provider Credential Vault", "Dual-Sided Immutable Audit Logging", "Dedicated 24/7 Security SLA"],
         BORDER, DARK_TEXT, False)
    ]
    for idx, (p_name, p_cost, p_sub, p_tag, p_feats, p_border, p_acc, is_pro) in enumerate(plans):
        c_left = Inches(0.8 + idx * 4.0)
        # Card container
        card = add_card(slide25, c_left, Inches(1.65), Inches(3.7), Inches(5.1),
                        fill_color=WHITE,
                        border_color=PRIMARY_GREEN if is_pro else BORDER,
                        border_width=2.5 if is_pro else 1.2)
        
        # If Professional, add "MOST POPULAR" banner badge on top
        if is_pro:
            banner = slide25.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left + Inches(0.8), Inches(1.48), Inches(2.1), Inches(0.28))
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
        
        tb = slide25.shapes.add_textbox(c_left + Inches(0.2), Inches(1.8), Inches(3.3), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_name
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = p_acc
        
        p_t = tf.add_paragraph()
        p_t.text = p_tag
        p_t.font.size = Pt(9)
        p_t.font.color.rgb = SEC_TEXT
        p_t.space_before = Pt(2)
        
        p_c = tf.add_paragraph()
        p_c.text = p_cost
        p_c.font.size = Pt(28)
        p_c.font.bold = True
        p_c.font.color.rgb = PRIMARY_GREEN if is_pro else DARK_TEXT
        p_c.space_before = Pt(6)
        
        p_s = tf.add_paragraph()
        p_s.text = p_sub
        p_s.font.size = Pt(9)
        p_s.font.color.rgb = SEC_TEXT
        
        p_div = tf.add_paragraph()
        p_div.text = "────────────────────────────"
        p_div.font.size = Pt(8)
        p_div.font.color.rgb = BORDER
        p_div.space_before = Pt(4)
        
        for f in p_feats:
            p_f = tf.add_paragraph()
            p_f.text = ("• " if not f.startswith("EVERYTHING") else "★ ") + f
            p_f.font.size = Pt(9)
            p_f.font.bold = f.startswith("EVERYTHING")
            p_f.font.color.rgb = PRIMARY_GREEN if (f.startswith("EVERYTHING") or is_pro) else DARK_TEXT
            p_f.space_before = Pt(4)

    # =========================================================================
    # SLIDE 26: Comprehensive Plan Comparison Matrix
    # =========================================================================
    slide26 = create_base_slide(
        "Feature Matrix",
        "Comprehensive Plan Comparison: Feature Availability",
        "Detailed side-by-side comparison across all 12 platform functional modules.",
        slide_num=26
    )
    # Table shape
    rows = 13
    cols = 4
    t_left = Inches(0.8)
    t_top = Inches(1.65)
    t_width = Inches(11.733)
    t_height = Inches(5.1)
    
    table_shape = slide26.shapes.add_table(rows, cols, t_left, t_top, t_width, t_height)
    table = table_shape.table
    table.columns[0].width = Inches(4.533)
    table.columns[1].width = Inches(2.4)
    table.columns[2].width = Inches(2.4)
    table.columns[3].width = Inches(2.4)
    
    matrix_data = [
        ("Platform Capabilities & Features", "Starter (₹500)", "Professional (₹800)", "Enterprise (₹1,000)"),
        ("Vehicle Master & Lifecycle Status Registry", "✓ Included", "✓ Included", "✓ Included"),
        ("Driver Profiles & Document KYC Review Queue", "✓ Included", "✓ Included", "✓ Included"),
        ("Trip Creation, Dispatching & Milestones", "✓ Included", "✓ Included", "✓ Included"),
        ("Company-Level Multi-Tenancy & RBAC", "✓ Included", "✓ Included", "✓ Included"),
        ("GPS Telematics Ingestion & Live Map Tracking", "— Not Available", "✓ Included", "✓ Included"),
        ("7 Telematics Wire Decoders (AIS-140, GT06, etc.)", "— Not Available", "✓ Included", "✓ Included"),
        ("Driver Mobile App & Digital Inspections", "— Not Available", "✓ Included", "✓ Included"),
        ("Route Geo-Corridor Deviation Detection", "— Not Available", "✓ Included", "✓ Included"),
        ("Fuel Siphoning Anomaly AI Engine", "— Not Available", "— Not Available", "✓ Included"),
        ("Tank Capacity Physics Validation", "— Not Available", "— Not Available", "✓ Included"),
        ("Hardware Quarantine Vault & AES-256-GCM Keys", "— Not Available", "— Not Available", "✓ Included"),
        ("Dual-Sided Immutable Audit Logging", "— Not Available", "— Not Available", "✓ Included")
    ]
    for r_idx, row_values in enumerate(matrix_data):
        for c_idx, val in enumerate(row_values):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            
            if r_idx == 0:
                p.font.size = Pt(10)
                p.font.bold = True
                p.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = PRIMARY_GREEN
            else:
                p.font.size = Pt(9)
                if c_idx == 0:
                    p.font.color.rgb = DARK_TEXT
                    p.font.bold = True
                else:
                    if "✓" in val:
                        p.font.bold = True
                        p.font.color.rgb = PRIMARY_GREEN
                    else:
                        p.font.color.rgb = SEC_TEXT
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else BG_LIGHT

    # =========================================================================
    # SLIDE 27: Get Started / Enterprise Pilot
    # =========================================================================
    slide27 = create_base_slide(
        "Next Steps",
        "Modernize Your Fleet Operations with VAHAN",
        "Take total operational command. Connect your fleet, eliminate fuel loss, and streamline driver compliance.",
        slide_num=27
    )
    # Left Card: Pilot Offer
    add_card(slide27, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.0), border_color=BORDER)
    tb_p = slide27.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.6))
    tf_p = tb_p.text_frame
    tf_p.word_wrap = True
    
    p = tf_p.paragraphs[0]
    p.text = "14-Day Production Pilot"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    pilot_points = [
        "✓ Onboard a live test cohort of 5 to 10 vehicles",
        "✓ Point existing GPS trackers to VAHAN's multi-protocol gateway",
        "✓ Run the fuel siphoning and tank capacity engine on live trips",
        "✓ Test the Driver Mobile App with offline digital inspections",
        "✓ Establish a clear baseline of operational fuel & route savings",
        "✓ Zero upfront hardware replacement required"
    ]
    for pt in pilot_points:
        p_pt = tf_p.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = Pt(10.5)
        p_pt.font.color.rgb = DARK_TEXT
        p_pt.space_before = Pt(8)

    # Right Card: Contact & Next Steps
    add_card(slide27, Inches(6.8), Inches(1.65), Inches(5.7), Inches(5.0), fill_color=SOFT_GREEN, border_color=ACCENT_GREEN, border_width=1.5)
    tb_c = slide27.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(4.6))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    
    p = tf_c.paragraphs[0]
    p.text = "Initiate Your Operational Audit"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_TEXT
    
    p_desc = tf_c.add_paragraph()
    p_desc.text = "Schedule a technical consultation and dispatch workflow review with our engineering and operations team."
    p_desc.font.size = Pt(11)
    p_desc.font.color.rgb = DARK_TEXT
    p_desc.space_before = Pt(8)
    
    steps = [
        "1. Technical Discovery: Review fleet size, GPS tracker models & depots.",
        "2. Gateway Configuration: Configure Traccar / webhook secrets.",
        "3. Driver App Onboarding: Distribute Android Flutter APK to drivers.",
        "4. Live Telematics & Fuel Audit: Review initial exception logs."
    ]
    for st in steps:
        p_st = tf_c.add_paragraph()
        p_st.text = st
        p_st.font.size = Pt(10)
        p_st.font.color.rgb = DARK_TEXT
        p_st.space_before = Pt(6)
        
    p_contact = tf_c.add_paragraph()
    p_contact.text = "Enterprise Inquiries & Pilot Scheduling:\nWeb: www.vahanfleet.com  |  Email: pilot@vahanfleet.com"
    p_contact.font.size = Pt(10.5)
    p_contact.font.bold = True
    p_contact.font.color.rgb = PRIMARY_GREEN
    p_contact.space_before = Pt(16)

    # Output path
    out_pptx = r"c:\Users\ratho\fleetguard\VAHAN_Product_Presentation_Light_Theme.pptx"
    prs.save(out_pptx)
    print(f"Successfully generated: {out_pptx} with {len(prs.slides)} slides.")

if __name__ == "__main__":
    build_light_theme_presentation()
