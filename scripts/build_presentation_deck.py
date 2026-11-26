import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # Color Palette
    BG_DARK = RGBColor(11, 15, 25)         # Deep slate/black
    PANEL_BG = RGBColor(24, 34, 53)        # Card dark slate
    PANEL_BORDER = RGBColor(51, 65, 85)    # Subtle border
    EMERALD = RGBColor(16, 185, 129)       # Brand primary
    CYAN = RGBColor(56, 189, 248)          # Accent cyan
    AMBER = RGBColor(245, 158, 11)         # Warning / alert amber
    ROSE = RGBColor(244, 63, 94)           # Danger / anomaly rose
    PURPLE = RGBColor(168, 85, 247)        # Accent purple
    WHITE = RGBColor(255, 255, 255)        # Pure white text
    TEXT_MUTED = RGBColor(148, 163, 184)   # Slate 400
    TEXT_LIGHT = RGBColor(226, 232, 240)   # Slate 200
    
    ASSETS_DIR = r"c:\Users\ratho\fleetguard\presentation_assets"
    
    # Helper: Base slide background & header
    def create_base_slide(badge_text, title_text, subtitle_text=""):
        slide = prs.slides.add_slide(blank_layout)
        
        # Background canvas
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        
        # Subtle header accent line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.4), Inches(0.08), Inches(0.7))
        line.fill.solid()
        line.fill.fore_color.rgb = EMERALD
        line.line.fill.background()
        
        # Badge
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(0.4), Inches(2.2), Inches(0.3))
        badge_box.fill.solid()
        badge_box.fill.fore_color.rgb = PANEL_BG
        badge_box.line.color.rgb = EMERALD
        badge_box.line.width = Pt(1)
        tf_b = badge_box.text_frame
        tf_b.word_wrap = False
        p_b = tf_b.paragraphs[0]
        p_b.text = badge_text.upper()
        p_b.font.size = Pt(9)
        p_b.font.bold = True
        p_b.font.color.rgb = EMERALD
        p_b.alignment = PP_ALIGN.CENTER
        
        # Title & Subtitle text frame
        header_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.72), Inches(11.5), Inches(0.75))
        tf_h = header_box.text_frame
        tf_h.word_wrap = True
        tf_h.margin_left = tf_h.margin_top = tf_h.margin_right = tf_h.margin_bottom = 0
        
        p_title = tf_h.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE
        
        if subtitle_text:
            p_sub = tf_h.add_paragraph()
            p_sub.text = subtitle_text
            p_sub.font.size = Pt(12)
            p_sub.font.color.rgb = TEXT_MUTED
            p_sub.space_before = Pt(3)
            
        # Minimal Footer
        ft_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(11.7), Inches(0.3))
        tf_f = ft_box.text_frame
        p_f = tf_f.paragraphs[0]
        p_f.text = "VAHAN FLEET INTELLIGENCE  •  CONFIDENTIAL & PROPRIETARY  •  ALL RIGHTS RESERVED"
        p_f.font.size = Pt(8)
        p_f.font.color.rgb = RGBColor(71, 85, 105)
        
        return slide

    # Helper: Add card panel
    def add_card(slide, left, top, width, height, border_color=PANEL_BORDER, fill_color=PANEL_BG):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
        return card

    # =========================================================================
    # SLIDE 1: Title & Cover
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_DARK
    bg1.line.fill.background()
    
    # 3D Truck Image on right side
    hero_img_path = os.path.join(ASSETS_DIR, "vahan_3d_truck_hero.jpg")
    if os.path.exists(hero_img_path):
        slide1.shapes.add_picture(hero_img_path, Inches(6.2), Inches(1.0), Inches(6.5), Inches(5.5))
        
    # Left Content Box
    tb1 = slide1.shapes.add_textbox(Inches(0.8), Inches(1.2), Inches(5.2), Inches(5.2))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p1 = tf1.paragraphs[0]
    p1.text = "ENTERPRISE FLEET INTELLIGENCE"
    p1.font.size = Pt(11)
    p1.font.bold = True
    p1.font.color.rgb = EMERALD
    
    p2 = tf1.add_paragraph()
    p2.text = "VAHAN"
    p2.font.size = Pt(46)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.space_before = Pt(8)
    
    p3 = tf1.add_paragraph()
    p3.text = "Intelligent Fleet Management & Telematics Platform"
    p3.font.size = Pt(20)
    p3.font.color.rgb = CYAN
    p3.space_before = Pt(4)
    
    p4 = tf1.add_paragraph()
    p4.text = "Take complete command of your vehicles, drivers, live telematics, route deviations, and fuel economics on a single, high-security enterprise platform."
    p4.font.size = Pt(13)
    p4.font.color.rgb = TEXT_LIGHT
    p4.space_before = Pt(18)
    
    p5 = tf1.add_paragraph()
    p5.text = "✓ 166 Passing Automated Tests   ✓ Multi-Protocol Telematics   ✓ Fuel Siphon AI"
    p5.font.size = Pt(10)
    p5.font.bold = True
    p5.font.color.rgb = EMERALD
    p5.space_before = Pt(24)
    
    p6 = tf1.add_paragraph()
    p6.text = "Comprehensive B2B Product & Commercial Strategy Deck"
    p6.font.size = Pt(11)
    p6.font.color.rgb = TEXT_MUTED
    p6.space_before = Pt(14)

    # =========================================================================
    # SLIDE 2: The Industry Problem
    # =========================================================================
    slide2 = create_base_slide(
        "Industry Challenges",
        "The Operational & Financial Bleed in Commercial Fleets",
        "Modern transport operators navigate razor-thin margins compromised by 7 systemic failure points."
    )
    problems = [
        ("01. Rampant Fuel Siphoning & Fraud", "Fuel constitutes 45%+ of operating costs. Unmonitored tank drops, fake bills, and pump kickbacks bleed bottom lines.", ROSE),
        ("02. Blind-Spot Route Deviations", "Drivers taking unapproved detours, toll bypasses, and unauthorized side-deliveries inflate fuel burn and wear.", AMBER),
        ("03. Regulatory KYC & Document Exposure", "Expired commercial licenses, missing fitness certificates, and unverified drivers risk catastrophic impoundment.", CYAN),
        ("04. Disconnected Telematics Chaos", "Fleets juggle 3 to 5 proprietary GPS vendor portals with zero unified data, broken webhooks, and manual tracking.", EMERALD),
        ("05. Hardware Churn & Ghost Tracking", "Unassigned, stolen, or orphaned GPS trackers leak telemetry or sit idle without accountability.", PURPLE),
        ("06. Paper-Based Driver Coordination", "Trip dispatch, loading manifests, and maintenance checks via phone calls and paper slips cause daily miscommunication.", WHITE),
        ("07. Inadequate Multi-Tenant Security", "Legacy software exposes sensitive fleet routes and financial rates across sub-fleets without strict cryptographic boundaries.", ROSE)
    ]
    # Grid: 2 columns
    for idx, (p_title, p_desc, p_col) in enumerate(problems[:6]):
        col = idx % 2
        row = idx // 2
        c_left = Inches(0.8 + col * 6.0)
        c_top = Inches(1.6 + row * 1.7)
        add_card(slide2, c_left, c_top, Inches(5.7), Inches(1.5), border_color=p_col)
        
        tb = slide2.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.15), Inches(5.3), Inches(1.2))
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
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(4)

    # =========================================================================
    # SLIDE 3: The VAHAN Solution
    # =========================================================================
    slide3 = create_base_slide(
        "The Vahan Solution",
        "A Unified Operating System for Commercial Fleets",
        "Consolidating vehicles, telematics, drivers, routes, and financials into a single real-time platform."
    )
    pillars = [
        ("Fleet & Asset Operations", "Master registry for vehicles, dynamic status control, maintenance tracking, and document lifecycle control.", EMERALD),
        ("Multi-Protocol Telematics", "Wire-level protocol decoders for 7 major GPS standards (AIS-140, GT06, Teltonika) with HMAC-secured ingestion.", CYAN),
        ("Driver Mobile & KYC", "Flutter mobile client for drivers with pre-trip digital checklists, offline sync, and strict administrative KYC review.", AMBER),
        ("Route Intelligence", "Automated geo-corridor tracking, breadcrumb path playback, and instant deviation alerts for unauthorized detours.", PURPLE),
        ("Fuel Theft AI Engine", "Real-time siphoning detection, tank capacity physics check, and cost-per-kilometer fleet analytics.", ROSE),
        ("Quarantine Security Vault", "Zero-trust hardware isolation, AES-GCM credential vault, and company-level tenant security.", EMERALD)
    ]
    for idx, (p_title, p_desc, p_col) in enumerate(pillars):
        col = idx % 3
        row = idx // 3
        c_left = Inches(0.8 + col * 4.0)
        c_top = Inches(1.7 + row * 2.5)
        add_card(slide3, c_left, c_top, Inches(3.7), Inches(2.3), border_color=p_col)
        
        tb = slide3.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(3.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = p_col
        
        p_sub = tf.add_paragraph()
        p_sub.text = p_desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 4: Product Ecosystem Architecture
    # =========================================================================
    slide4 = create_base_slide(
        "System Architecture",
        "Connected End-to-End Fleet Infrastructure",
        "High-performance decoupled architecture designed for high throughput, data integrity, and multi-tenancy."
    )
    eco_img_path = os.path.join(ASSETS_DIR, "vahan_3d_ecosystem.png")
    if os.path.exists(eco_img_path):
        slide4.shapes.add_picture(eco_img_path, Inches(6.0), Inches(1.6), Inches(6.5), Inches(5.0))
        
    # Left description cards
    arch_points = [
        ("Fleet Owner Web Dashboard", "React 18, Tailwind CSS, Leaflet live maps, and reactive telemetry stores for high-density dispatch operations.", EMERALD),
        ("Driver Mobile Client (Flutter)", "Cross-platform mobile application featuring trip milestone tracking, inspection checklists, and offline local queueing.", CYAN),
        ("Telematics Webhook & Decoders", "FastAPI ingestion gateway supporting wire-level parsing of 7 GPS protocols, Traccar synchronization, and HMAC secrets.", AMBER),
        ("Enterprise Security & PostgreSQL", "Company-scoped multi-tenant database models, AES-256-GCM hardware vault, and dual-sided audit logging.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(arch_points):
        c_top = Inches(1.6 + idx * 1.25)
        add_card(slide4, Inches(0.8), c_top, Inches(5.0), Inches(1.15), border_color=col)
        tb = slide4.shapes.add_textbox(Inches(0.95), c_top + Inches(0.1), Inches(4.7), Inches(0.95))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(2)

    # =========================================================================
    # SLIDE 5: Fleet Owner Dashboard
    # =========================================================================
    slide5 = create_base_slide(
        "Executive Oversight",
        "Fleet Owner Command Center: Live Visibility & Metrics",
        "Unified operational pane of glass delivering real-time vehicle states, fleet utilization, and active alerts."
    )
    # 4 Metric Cards across top
    metrics = [
        ("ACTIVE FLEET", "94.2%", "Vehicles currently in service", EMERALD),
        ("IN-TRANSIT TRUCKS", "68 UNITS", "Active trips on highway", CYAN),
        ("SCHEDULED MAINTENANCE", "12 UNITS", "Odometer & engine hour alerts", AMBER),
        ("CRITICAL ANOMALIES", "03 ALERTS", "Fuel / route deviations flagged", ROSE)
    ]
    for idx, (m_title, m_val, m_desc, m_col) in enumerate(metrics):
        c_left = Inches(0.8 + idx * 2.95)
        add_card(slide5, c_left, Inches(1.6), Inches(2.8), Inches(1.3), border_color=m_col)
        tb = slide5.shapes.add_textbox(c_left + Inches(0.15), Inches(1.7), Inches(2.5), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = m_title
        p1.font.size = Pt(9.5)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_MUTED
        p2 = tf.add_paragraph()
        p2.text = m_val
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = m_col
        p3 = tf.add_paragraph()
        p3.text = m_desc
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = TEXT_LIGHT
        p3.space_before = Pt(2)

    # 2 Big Content Cards Below
    add_card(slide5, Inches(0.8), Inches(3.1), Inches(5.7), Inches(3.5))
    tb_l = slide5.shapes.add_textbox(Inches(1.0), Inches(3.25), Inches(5.3), Inches(3.2))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "Key Operational Features"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    bullets_l = [
        ("Real-time Fleet Status Grid: ", "Instant color-coded view of vehicle availability, active assignments, and downtime."),
        ("One-Click Vehicle Drill-Down: ", "Inspect speed, ignition status, driver details, and historical route traces instantly."),
        ("Multi-Branch Filtering: ", "Segment views by depot, operational region, vehicle classification, or customer account."),
        ("Responsive Telemetry Counters: ", "Auto-refreshing state streams backed by optimized FastAPI endpoints.")
    ]
    for b_title, b_desc in bullets_l:
        p_b = tf_l.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(10.5)
        p_b.font.color.rgb = TEXT_LIGHT
        p_b.space_before = Pt(8)

    add_card(slide5, Inches(6.8), Inches(3.1), Inches(5.7), Inches(3.5))
    tb_r = slide5.shapes.add_textbox(Inches(7.0), Inches(3.25), Inches(5.3), Inches(3.2))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Business Impact & Efficiency"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = CYAN
    bullets_r = [
        ("Eliminates Dispatch Lag: ", "Reduces fleet dispatch coordination time by up to 65% with digital status boards."),
        ("Zero Information Silos: ", "Operations, maintenance, and finance teams share the exact same source of truth."),
        ("Instant Exception Management: ", "Operators are alerted only when anomalies occur (speeding, delays, idling)."),
        ("Audited Codebase: ", "Verified via frontend/src/pages/DashboardOverview.jsx and backend/routers/vehicle_domain.py.")
    ]
    for b_title, b_desc in bullets_r:
        p_b = tf_r.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(10.5)
        p_b.font.color.rgb = TEXT_LIGHT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 6: Vehicle Management
    # =========================================================================
    slide6 = create_base_slide(
        "Asset Governance",
        "Vehicle Registry & Lifecycle State Management",
        "Comprehensive tracking of heavy commercial vehicles from onboarding to retirement."
    )
    v_cards = [
        ("Master Vehicle Specification Profile", "Full technical profile including Registration Number, VIN, Make, Model, Fuel Tank Capacity (Liters), Gross Vehicle Weight, and Axle configuration stored in PostgreSQL.", EMERALD),
        ("Operational Status State Machine", "Enforces strict status transitions (Active -> In Transit -> Maintenance -> Out of Service -> Decommissioned), preventing double-booking of assigned vehicles.", CYAN),
        ("Fleet Segmentation & Branch Tagging", "Group vehicles by operating hub, logistics client, or route corridor with company-scoped multi-tenant isolation.", AMBER),
        ("Maintenance & Fitness Compliance", "Automated tracking of odometer readings, scheduled engine servicing intervals, and fitness renewal deadlines.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(v_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide6, c_left, c_top, Inches(5.7), Inches(2.3), border_color=col)
        
        tb = slide6.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 7: Driver Management & KYC
    # =========================================================================
    slide7 = create_base_slide(
        "Workforce Compliance",
        "Driver Onboarding, Profiles & KYC Verification",
        "Mitigate operational risks with structured driver background and document compliance."
    )
    d_cards = [
        ("Digital Driver Profiles", "Centralized driver master capturing full legal name, permanent address, contact details, emergency contacts, and assigned fleet hub.", EMERALD),
        ("Commercial Document Vault", "Encrypted storage for Commercial Driving Licenses, Aadhaar / National ID, Medical Fitness certificates, and police verification reports.", CYAN),
        ("Regulatory Expiry Alerts", "Proactive dashboard notifications 30 and 15 days prior to license or medical clearance expiration, preventing illegal on-road operations.", AMBER),
        ("Driver Assignment History", "Full audit log of vehicle-driver pairings, trip completion rates, and safety inspection compliance records.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(d_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide7, c_left, c_top, Inches(5.7), Inches(2.3), border_color=col)
        
        tb = slide7.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 8: Driver Mobile Application
    # =========================================================================
    slide8 = create_base_slide(
        "Mobile Experience",
        "Driver Mobile Application: On-Road Operational Client",
        "Purpose-built Flutter mobile application connecting frontline drivers directly to dispatch."
    )
    m_pillars = [
        ("Trip Execution & Milestones", "Drivers view assigned trips, origin/destination coordinates, cargo details, and log departure, transit checkpoints, and delivery milestones.", EMERALD),
        ("Digital Vehicle Inspections", "Standardized pre-trip and post-trip digital checklists covering tires, brakes, lights, fluid levels, and emergency kits with instant pass/fail logging.", CYAN),
        ("Resilient Offline Event Sync", "Built-in local SQLite buffering queue that records driver actions in remote zero-network zones and auto-syncs when connectivity returns.", AMBER),
        ("Expense & Toll Capture", "Instant logging of en-route toll charges and verified fuel purchases with receipt image uploads directly tied to the active trip.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(m_pillars):
        c_left = Inches(0.8 + idx * 2.95)
        add_card(slide8, c_left, Inches(1.7), Inches(2.8), Inches(4.8), border_color=col)
        tb = slide8.shapes.add_textbox(c_left + Inches(0.15), Inches(1.85), Inches(2.5), Inches(4.5))
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
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(10)
        p_note = tf.add_paragraph()
        p_note.text = "Verified via mobile/ & backend/routers/driver_mobile.py"
        p_note.font.size = Pt(8.5)
        p_note.font.color.rgb = TEXT_MUTED
        p_note.space_before = Pt(16)

    # =========================================================================
    # SLIDE 9: GPS Tracking & Telematics Gateway
    # =========================================================================
    slide9 = create_base_slide(
        "IoT Telematics Gateway",
        "GPS Telematics Engine & Multi-Protocol Decoders",
        "High-throughput ingestion layer supporting industry-standard GPS protocols and Traccar integration."
    )
    dev_img_path = os.path.join(ASSETS_DIR, "vahan_3d_telematics_device.png")
    if os.path.exists(dev_img_path):
        slide9.shapes.add_picture(dev_img_path, Inches(6.5), Inches(1.6), Inches(6.0), Inches(4.8))
        
    add_card(slide9, Inches(0.8), Inches(1.6), Inches(5.4), Inches(4.8))
    tb_t = slide9.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.0), Inches(4.4))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    
    p = tf_t.paragraphs[0]
    p.text = "Telemetry Ingestion Capabilities"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    
    t_points = [
        ("Traccar Gateway Integration: ", "Automated HTTP forwarder ingestion accepting normalized GPS positions, speed, ignition, and battery levels."),
        ("Multi-Protocol Wire Decoders: ", "Built-in binary and ASCII decoders for 7 major protocols: AIS-140 (Govt standard), GT06, Teltonika Codec 8, TK103, Queclink, H02, and JT/T 808."),
        ("HMAC Webhook Authentication: ", "Protected by X-Telematics-Secret constant-time header validation; rejects unauthorized telemetry requests with 401."),
        ("Deduplication & Concurrency: ", "Prevents duplicate position writes while updating vehicle live coordinates in real-time."),
        ("Deployment Status Disclosure: ", "Decoders & webhooks validated via 56 master tests in Docker staging. Physical on-road GSM SIM field validation is underway.")
    ]
    for b_title, b_desc in t_points:
        p_b = tf_t.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(10.5)
        p_b.font.color.rgb = TEXT_LIGHT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 10: Trip Management & Dispatching
    # =========================================================================
    slide10 = create_base_slide(
        "Logistics Execution",
        "Trip Creation, Dispatching & Lifecycle Execution",
        "End-to-end trip dispatching connecting vehicle, driver, route corridor, and cargo manifest."
    )
    trip_steps = [
        ("1. Trip Creation", "Define Origin, Destination, Cargo consignment, planned departure time, and expected arrival window.", EMERALD),
        ("2. Resource Assignment", "Assign an available Active vehicle and verified KYC-approved driver with automatic conflict prevention.", CYAN),
        ("3. Dispatch & Transit", "Dispatch command notifies driver; status transitions to IN_TRANSIT with real-time GPS telemetry binding.", AMBER),
        ("4. Milestone Tracking", "Track waypoint arrival times, loading/unloading delays, and transit milestones via driver mobile or GPS.", PURPLE),
        ("5. Trip Completion & Audit", "Final delivery confirmation, odometer reconciliation, fuel consumption audit, and trip archival.", WHITE)
    ]
    for idx, (title, desc, col) in enumerate(trip_steps):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide10, c_left, Inches(1.8), Inches(2.25), Inches(4.6), border_color=col)
        tb = slide10.shapes.add_textbox(c_left + Inches(0.12), Inches(2.0), Inches(2.0), Inches(4.2))
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
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(10)

    # =========================================================================
    # SLIDE 11: Route Optimization & Deviations
    # =========================================================================
    slide11 = create_base_slide(
        "Route Intelligence",
        "Route Optimization & Real-Time Deviation Detection",
        "Eliminate unauthorized detours, toll bypasses, and unapproved side-trips automatically."
    )
    route_img_path = os.path.join(ASSETS_DIR, "vahan_3d_route_deviation.png")
    if os.path.exists(route_img_path):
        slide11.shapes.add_picture(route_img_path, Inches(6.5), Inches(1.6), Inches(6.0), Inches(4.8))
        
    add_card(slide11, Inches(0.8), Inches(1.6), Inches(5.4), Inches(4.8))
    tb_r = slide11.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.0), Inches(4.4))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    
    p = tf_r.paragraphs[0]
    p.text = "Route Intelligence Capabilities"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    
    r_points = [
        ("Geo-Corridor Boundary Rules: ", "Defines allowable travel corridors along primary national and state highways."),
        ("Automated Deviation Detection: ", "Backend engine calculates cross-track error distance from planned paths and flags deviations exceeding thresholds."),
        ("Historical Breadcrumb Playback: ", "Interactive map timeline allowing dispatchers to scrub through past trips with speed vectors and timestamps."),
        ("Toll & Fuel Bypass Prevention: ", "Stops drivers from taking unpaved, hazardous bypasses that damage tires and vehicle suspension."),
        ("Post-Trip Adherence Scoring: ", "Computes trip compliance metrics for driver performance appraisals and safety incentives.")
    ]
    for b_title, b_desc in r_points:
        p_b = tf_r.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(10.5)
        p_b.font.color.rgb = TEXT_LIGHT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 12: Financial Intelligence & Fuel Analytics
    # =========================================================================
    slide12 = create_base_slide(
        "Financial Intelligence",
        "Fuel Theft Detection & Cost-Per-Km Analytics",
        "Algorithmic fraud prevention that protects the largest line-item in transport operations."
    )
    fuel_img_path = os.path.join(ASSETS_DIR, "vahan_3d_fuel_gauge.png")
    if os.path.exists(fuel_img_path):
        slide12.shapes.add_picture(fuel_img_path, Inches(6.5), Inches(1.6), Inches(6.0), Inches(4.8))
        
    add_card(slide12, Inches(0.8), Inches(1.6), Inches(5.4), Inches(4.8))
    tb_f = slide12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.0), Inches(4.4))
    tf_f = tb_f.text_frame
    tf_f.word_wrap = True
    
    p = tf_f.paragraphs[0]
    p.text = "Fuel & Financial Protection"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = WHITE
    
    f_points = [
        ("Fuel Siphoning Detection: ", "Statistical anomaly detection identifies sudden drops in fuel volume while the vehicle engine ignition is OFF."),
        ("Tank Capacity Physics Validation: ", "Automated validation rejects fuel purchase receipts that exceed the physical fuel tank capacity of the vehicle."),
        ("Fleet Cost Per Kilometer: ", "Real-time calculation combining fuel purchase slips, tolls, maintenance, and GPS odometer deltas."),
        ("Odometer Reconciliation: ", "Cross-checks driver-reported kilometer logs against verified GPS telematics distance."),
        ("ROI Impact: ", "Recovers an estimated 8% to 15% in previously untracked fuel losses across commercial fleet operations.")
    ]
    for b_title, b_desc in f_points:
        p_b = tf_f.add_paragraph()
        p_b.text = "• " + b_title + b_desc
        p_b.font.size = Pt(10.5)
        p_b.font.color.rgb = TEXT_LIGHT
        p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 13: Hardware & Device Management
    # =========================================================================
    slide13 = create_base_slide(
        "Hardware Lifecycle",
        "Hardware Asset Management & Device Pairing",
        "Structured device inventory, dynamic vehicle pairing, and multi-provider gateway synchronization."
    )
    h_pillars = [
        ("Device Master Inventory", "Track GPS trackers, dashcams, and fuel sensors by Serial Number, IMEI, Protocol type, SIM card ICCID, and firmware version.", EMERALD),
        ("Dynamic Vehicle Pairing Wizard", "Seamlessly pair or reassign devices to vehicles in seconds; previous device assignments are automatically closed with historical timestamps.", CYAN),
        ("Provider Gateway Sync", "Direct API integration with Traccar and custom GPS servers to synchronize device registrations, device states, and telemetry ports.", AMBER),
        ("Device Health & Offline Monitoring", "Automated heartbeat monitoring flagging devices that stop transmitting, lose battery power, or experience GPS signal loss.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(h_pillars):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide13, c_left, c_top, Inches(5.7), Inches(2.3), border_color=col)
        
        tb = slide13.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 14: Quarantine Security & Super-Admin Governance
    # =========================================================================
    slide14 = create_base_slide(
        "Zero-Trust Architecture",
        "Quarantine Isolation & Hardware Security Governance",
        "Enterprise-grade zero-trust containment protecting customer tenants from rogue or orphaned devices."
    )
    q_cards = [
        ("Quarantine Tenant Isolation", "When unmapped, retired, or orphaned devices transmit telemetry, they are trapped in a dedicated quarantine tenant, preventing data leakage.", ROSE),
        ("Super-Admin Reassignment Workflow", "Only authenticated super-administrators can inspect quarantined hardware and reassign devices to verified client companies.", EMERALD),
        ("Dual-Sided Immutable Audit Trail", "Every hardware registration, quarantine capture, reassignment, and unpairing event writes an immutable audit record with timestamps.", CYAN),
        ("AES-GCM Credential Encryption", "Hardware provider API tokens and telematics credentials are encrypted at rest using AES-256-GCM and never exposed via client APIs.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(q_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide14, c_left, c_top, Inches(5.7), Inches(2.3), border_color=col)
        
        tb = slide14.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 15: Driver Document Verification Workflow
    # =========================================================================
    slide15 = create_base_slide(
        "Regulatory Compliance",
        "Driver Document Verification & KYC Approvals",
        "Streamlined audit queue ensuring only certified, legally compliant drivers operate commercial vehicles."
    )
    doc_steps = [
        ("Driver Uploads Documents", "Driver uploads commercial license, medical fitness certificate, and Aadhaar card via mobile app or portal.", EMERALD),
        ("Pending Review Queue", "Fleet compliance officer accesses centralized queue showing pending documents with side-by-side previews.", CYAN),
        ("Formal Verification Decision", "Auditor inspects validity dates, document authenticity, and issues formal APPROVED or REJECTED status.", AMBER),
        ("Rejection Notes & Audit Log", "Rejections require mandatory explanatory notes sent immediately to the driver with tamper-proof audit timestamps.", ROSE),
        ("Operational Activation", "Only drivers with 100% verified documents can be assigned to active commercial transport trips.", WHITE)
    ]
    for idx, (title, desc, col) in enumerate(doc_steps):
        c_left = Inches(0.8 + idx * 2.38)
        add_card(slide15, c_left, Inches(1.8), Inches(2.25), Inches(4.6), border_color=col)
        tb = slide15.shapes.add_textbox(c_left + Inches(0.12), Inches(2.0), Inches(2.0), Inches(4.2))
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
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(10)

    # =========================================================================
    # SLIDE 16: Reports, Analytics & Insights
    # =========================================================================
    slide16 = create_base_slide(
        "Operational Intelligence",
        "Fleet Analytics, Executive Reports & Insights",
        "Turn high-velocity telematics and dispatch events into actionable commercial decisions."
    )
    r_cards = [
        ("Fleet Utilization & Uptime Metrics", "Comprehensive breakdown of active driving hours, dwell time at warehouses, and unutilized idle days across vehicle categories.", EMERALD),
        ("Driver Performance & Safety Scoring", "Objective scoring based on route adherence, harsh braking / acceleration, inspection checklist completion, and speed limit violations.", CYAN),
        ("Fuel Economy & Cost Ranking", "Identifies top-performing and high-cost vehicles per kilometer, highlighting engines requiring mechanical maintenance or calibration.", AMBER),
        ("Executive Export & Audit Reports", "Downloadable audit logs, trip expense summaries, and compliance manifests formatted for accounting and board reporting.", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(r_cards):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.7 + row_idx * 2.5)
        add_card(slide16, c_left, c_top, Inches(5.7), Inches(2.3), border_color=col)
        
        tb = slide16.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.2), Inches(5.3), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = col
        p_sub = tf.add_paragraph()
        p_sub.text = desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(8)

    # =========================================================================
    # SLIDE 17: Enterprise Security & Multi-Tenancy
    # =========================================================================
    slide17 = create_base_slide(
        "Enterprise Architecture",
        "Enterprise Security, Encryption & Multi-Tenancy",
        "Engineered from the ground up for strict corporate data isolation and regulatory compliance."
    )
    s_pillars = [
        ("Company-Level Multi-Tenancy", "Every database query, API route, and telematics packet is strictly isolated by cryptographic company_id. Zero cross-company leakage.", EMERALD),
        ("AES-256-GCM Credential Vault", "Hardware provider API keys, webhook secrets, and sensitive tokens are encrypted using AES-GCM; credentials are never exposed via API responses.", CYAN),
        ("Granular Role-Based Access Control", "Enforces distinct permissions for Fleet Owners, Dispatch Managers, Safety Officers, Drivers, and System Super-Admins.", AMBER),
        ("High-Throughput FastAPI Engine", "Asynchronous Python backend with SQLAlchemy ORM, connection pooling, and continuous automated test verification (166 tests).", PURPLE)
    ]
    for idx, (title, desc, col) in enumerate(s_pillars):
        c_left = Inches(0.8 + idx * 2.95)
        add_card(slide17, c_left, Inches(1.7), Inches(2.8), Inches(4.8), border_color=col)
        tb = slide17.shapes.add_textbox(c_left + Inches(0.15), Inches(1.85), Inches(2.5), Inches(4.5))
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
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(10)

    # =========================================================================
    # SLIDE 18: Why Choose VAHAN?
    # =========================================================================
    slide18 = create_base_slide(
        "Strategic Value",
        "Why VAHAN? 7 Verified Enterprise Differentiators",
        "The clear strategic advantages that set VAHAN apart from generic GPS trackers and legacy software."
    )
    diffs = [
        ("1. Single Unified Platform", "Consolidates vehicles, drivers, hardware, routes, and fuel economics into one pane of glass.", EMERALD),
        ("2. Wire-Level Telematics", "Supports 7 major GPS protocols with built-in decoders, avoiding proprietary hardware lock-in.", CYAN),
        ("3. Proactive Fuel Siphoning AI", "Flags fuel theft instantly by correlating ignition states and sudden tank drops.", ROSE),
        ("4. Automated Route Auditing", "Geo-corridor boundary rules stop unauthorized detours, delays, and toll evasions.", PURPLE),
        ("5. Frontline Driver Mobile App", "Empowers drivers with digital vehicle inspections and offline event synchronization.", AMBER),
        ("6. Zero-Trust Hardware Vault", "Quarantine tenant and AES-GCM encryption prevent rogue device security breaches.", EMERALD),
        ("7. Honest, Audited Engineering", "Built on 166 passing automated tests with verifiable endpoints and zero marketing fluff.", WHITE)
    ]
    for idx, (title, desc, col) in enumerate(diffs):
        col_idx = idx % 2
        row_idx = idx // 2
        c_left = Inches(0.8 + col_idx * 6.0)
        c_top = Inches(1.65 + row_idx * 1.3)
        add_card(slide18, c_left, c_top, Inches(5.7), Inches(1.18), border_color=col)
        tb = slide18.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.1), Inches(5.3), Inches(0.98))
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
        p_sub.font.color.rgb = TEXT_LIGHT
        p_sub.space_before = Pt(2)

    # =========================================================================
    # SLIDE 19: Transparent Pricing Plans
    # =========================================================================
    slide19 = create_base_slide(
        "Commercial Tiers",
        "Transparent, Predictable Per-Truck Pricing",
        "Simple per-truck plans with zero hidden fees. Scale effortlessly as your commercial fleet expands."
    )
    plans = [
        ("STARTER PLAN", "₹500", "per truck / month", "Essential Fleet Ops & Compliance",
         ["Vehicle Master Registry & Profiles", "Driver Profiles & Contact Management", "Driver Document Archiving (KYC/DL)", "Document Verification Workflow", "Trip Dispatching & Milestones", "Manual Expense & Cost Recording", "Company-Level Multi-Tenancy", "Standard Role-Based Access Control"],
         PANEL_BORDER, WHITE),
        ("PROFESSIONAL PLAN", "₹800", "per truck / month", "Live GPS Tracking & Telematics",
         ["EVERYTHING IN STARTER, PLUS:", "Live Interactive GPS Tracking Map", "Telematics Webhook Ingestion", "Multi-Protocol Decoders (7 Standards)", "Historical Route Breadcrumb Playback", "Automated Route Deviation Alerts", "Driver Mobile Application (Flutter)", "Pre-Trip / Post-Trip Digital Inspections"],
         EMERALD, EMERALD),
        ("ENTERPRISE PLAN", "₹1,000", "per truck / month", "Financial Intelligence & Vault",
         ["EVERYTHING IN PROFESSIONAL, PLUS:", "Fuel Theft & Siphoning Anomaly AI", "Tank Capacity Physics Validation", "Fleet Cost Per Km Intelligence", "Super-Admin Quarantine Governance", "AES-GCM Provider Credential Vault", "Dual-Sided Immutable Audit Logging", "Dedicated Security & Priority SLA"],
         CYAN, CYAN)
    ]
    for idx, (p_name, p_cost, p_sub, p_tag, p_feats, p_border, p_acc) in enumerate(plans):
        c_left = Inches(0.8 + idx * 4.0)
        add_card(slide19, c_left, Inches(1.65), Inches(3.7), Inches(5.1), border_color=p_border)
        tb = slide19.shapes.add_textbox(c_left + Inches(0.2), Inches(1.8), Inches(3.3), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_name
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = p_acc
        
        p_t = tf.add_paragraph()
        p_t.text = p_tag
        p_t.font.size = Pt(9.5)
        p_t.font.color.rgb = TEXT_MUTED
        p_t.space_before = Pt(2)
        
        p_c = tf.add_paragraph()
        p_c.text = p_cost
        p_c.font.size = Pt(28)
        p_c.font.bold = True
        p_c.font.color.rgb = WHITE
        p_c.space_before = Pt(8)
        
        p_s = tf.add_paragraph()
        p_s.text = p_sub
        p_s.font.size = Pt(9.5)
        p_s.font.color.rgb = TEXT_MUTED
        
        p_div = tf.add_paragraph()
        p_div.text = "--------------------------------------"
        p_div.font.size = Pt(8)
        p_div.font.color.rgb = PANEL_BORDER
        p_div.space_before = Pt(6)
        
        for f in p_feats:
            p_f = tf.add_paragraph()
            p_f.text = ("• " if not f.startswith("EVERYTHING") else "★ ") + f
            p_f.font.size = Pt(9.5)
            p_f.font.bold = f.startswith("EVERYTHING")
            p_f.font.color.rgb = p_acc if f.startswith("EVERYTHING") else TEXT_LIGHT
            p_f.space_before = Pt(4)

    # =========================================================================
    # SLIDE 20: Comprehensive Plan Comparison Matrix
    # =========================================================================
    slide20 = create_base_slide(
        "Tier Comparison",
        "Feature Comparison Across Service Tiers",
        "Transparent side-by-side matrix showing genuine feature availability across all three tiers."
    )
    # Table shape
    rows = 9
    cols = 4
    t_left = Inches(0.8)
    t_top = Inches(1.65)
    t_width = Inches(11.7)
    t_height = Inches(5.1)
    
    table_shape = slide20.shapes.add_table(rows, cols, t_left, t_top, t_width, t_height)
    table = table_shape.table
    table.columns[0].width = Inches(4.5)
    table.columns[1].width = Inches(2.4)
    table.columns[2].width = Inches(2.4)
    table.columns[3].width = Inches(2.4)
    
    matrix_data = [
        ("Platform Capabilities & Features", "Starter (₹500)", "Professional (₹800)", "Enterprise (₹1,000)"),
        ("Vehicle Master & Lifecycle Status Registry", "✓ Included", "✓ Included", "✓ Included"),
        ("Driver Profiles & Document KYC Review Queue", "✓ Included", "✓ Included", "✓ Included"),
        ("Trip Creation, Dispatching & Milestones", "✓ Included", "✓ Included", "✓ Included"),
        ("GPS Telematics Ingestion & Live Leaflet Map", "— Not Available", "✓ Included", "✓ Included"),
        ("Multi-Protocol Decoders (AIS-140, GT06, Teltonika)", "— Not Available", "✓ Included", "✓ Included"),
        ("Driver Mobile App & Pre/Post-Trip Inspections", "— Not Available", "✓ Included", "✓ Included"),
        ("Fuel Siphoning Anomaly & Tank Physics Validation", "— Not Available", "— Not Available", "✓ Included"),
        ("Quarantine Security Vault & AES-GCM Encrypted Keys", "— Not Available", "— Not Available", "✓ Included")
    ]
    for r_idx, row_values in enumerate(matrix_data):
        for c_idx, val in enumerate(row_values):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
            
            if r_idx == 0:
                p.font.size = Pt(11)
                p.font.bold = True
                p.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
            else:
                p.font.size = Pt(10)
                if c_idx == 0:
                    p.font.color.rgb = TEXT_LIGHT
                    p.font.bold = True
                else:
                    if "✓" in val:
                        p.font.bold = True
                        p.font.color.rgb = EMERALD
                    else:
                        p.font.color.rgb = RGBColor(100, 116, 139)
                cell.fill.solid()
                cell.fill.fore_color.rgb = PANEL_BG if r_idx % 2 == 1 else RGBColor(18, 25, 40)

    # =========================================================================
    # SLIDE 21: Get Started Today / Call to Action
    # =========================================================================
    slide21 = prs.slides.add_slide(blank_layout)
    bg21 = slide21.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg21.fill.solid()
    bg21.fill.fore_color.rgb = BG_DARK
    bg21.line.fill.background()
    
    if os.path.exists(hero_img_path):
        slide21.shapes.add_picture(hero_img_path, Inches(6.8), Inches(1.1), Inches(6.0), Inches(5.2))
        
    tb21 = slide21.shapes.add_textbox(Inches(0.8), Inches(1.1), Inches(5.8), Inches(5.5))
    tf21 = tb21.text_frame
    tf21.word_wrap = True
    
    p = tf21.paragraphs[0]
    p.text = "MODERNIZE YOUR FLEET OPERATIONS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    
    p2 = tf21.add_paragraph()
    p2.text = "Take Total Control with VAHAN"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.space_before = Pt(6)
    
    p3 = tf21.add_paragraph()
    p3.text = "Transform fuel opacity, driver risks, and telematics chaos into predictable profits and operational excellence."
    p3.font.size = Pt(13)
    p3.font.color.rgb = TEXT_LIGHT
    p3.space_before = Pt(14)
    
    cta_points = [
        "✓ 14-Day Production Pilot with Active Fleet Hardware",
        "✓ Comprehensive Operational & Fuel Audit",
        "✓ Multi-Protocol Telematics Gateway Setup Assistance",
        "✓ Dedicated Onboarding Specialist & Driver Training"
    ]
    for cp in cta_points:
        p_cp = tf21.add_paragraph()
        p_cp.text = cp
        p_cp.font.size = Pt(11)
        p_cp.font.bold = True
        p_cp.font.color.rgb = CYAN
        p_cp.space_before = Pt(8)
        
    p_box = tf21.add_paragraph()
    p_box.text = "CONTACT & DEMO REQUESTS:\nEmail: enterprise@vahanfleet.com  |  Web: www.vahanfleet.com"
    p_box.font.size = Pt(11)
    p_box.font.color.rgb = EMERALD
    p_box.space_before = Pt(20)

    out_pptx = r"c:\Users\ratho\fleetguard\VAHAN_Product_Presentation.pptx"
    prs.save(out_pptx)
    print(f"Successfully generated: {out_pptx} with {len(prs.slides)} slides.")

if __name__ == "__main__":
    build_presentation()
