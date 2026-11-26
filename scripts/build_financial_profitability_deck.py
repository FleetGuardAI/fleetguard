import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_profitability_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # -------------------------------------------------------------
    # LIGHT THEME DESIGN PALETTE (Strict adherence to guidelines)
    # -------------------------------------------------------------
    BG_LIGHT = RGBColor(247, 250, 248)       # #F7FAF8 (Slide canvas)
    WHITE = RGBColor(255, 255, 255)          # #FFFFFF (Card panels)
    PRIMARY_GREEN = RGBColor(37, 132, 91)    # #25845B (Brand green)
    SOFT_GREEN = RGBColor(228, 243, 234)     # #E4F3EA (Accent light green)
    DARK_TEXT = RGBColor(36, 53, 45)         # #24352D (Primary dark text)
    SEC_TEXT = RGBColor(100, 115, 107)       # #64736B (Secondary muted text)
    BORDER = RGBColor(225, 234, 228)         # #E1EAE4 (Card border)
    ACCENT_GREEN = RGBColor(167, 216, 184)   # #A7D8B8 (Border accent)
    
    # Financial Storytelling Indicators (Muted coral/red for loss, soft green for savings)
    ALERT_RED = RGBColor(220, 38, 38)        # #DC2626 (Financial loss / leakage)
    ALERT_BG = RGBColor(254, 242, 242)       # #FEF2F2 (Soft coral fill)
    ALERT_BORDER = RGBColor(252, 165, 165)   # #FCA5A5 (Coral border)
    AMBER = RGBColor(217, 119, 6)            # #D97706 (Warning / risk)
    AMBER_BG = RGBColor(254, 243, 199)       # #FEF3C7 (Soft amber fill)
    BLUE_ACCENT = RGBColor(37, 99, 235)      # #2563EB (Operational indicator)
    BLUE_BG = RGBColor(239, 246, 255)        # Soft blue fill
    
    ASSETS_DIR = r"c:\Users\ratho\fleetguard\presentation_assets"
    
    # Base slide creator
    def create_base_slide(badge_text, title_text, subtitle_text="", slide_num=None):
        slide = prs.slides.add_slide(blank_layout)
        
        # Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_LIGHT
        bg.line.fill.background()
        
        # Vertical accent line
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.42), Inches(0.06), Inches(0.72))
        bar.fill.solid()
        bar.fill.fore_color.rgb = PRIMARY_GREEN
        bar.line.fill.background()
        
        # Badge
        badge_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.96), Inches(0.42), Inches(2.8), Inches(0.28))
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
        
        # Title & Subtitle
        header_box = slide.shapes.add_textbox(Inches(0.96), Inches(0.72), Inches(11.5), Inches(0.75))
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
            p_sub.font.size = Pt(11)
            p_sub.font.color.rgb = SEC_TEXT
            p_sub.space_before = Pt(3)
            
        # Footer
        ft_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.15), Inches(11.733), Inches(0.25))
        tf_f = ft_box.text_frame
        tf_f.margin_left = tf_f.margin_top = tf_f.margin_right = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        page_str = f"  |  SLIDE {slide_num:02d}" if slide_num else ""
        p_f.text = f"VAHAN FLEET PROFITABILITY & P&L PROTECTION STRATEGY{page_str}"
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

    # Standard Feature Storytelling Layout: Left (Without), Right (With), Bottom (Calculation)
    def create_feature_story_slide(badge, title, subtitle, slide_num,
                                   left_title, left_bullets,
                                   right_title, right_bullets,
                                   calc_title, calc_formula, calc_explanation,
                                   right_img_path=None):
        slide = create_base_slide(badge, title, subtitle, slide_num=slide_num)
        
        # Layout metrics
        top_y = Inches(1.65)
        card_h = Inches(3.65)
        col_w = Inches(5.7)
        left_x = Inches(0.8)
        right_x = Inches(6.833)
        
        # 1. LEFT CARD: WITHOUT VAHAN (Financial Loss & Problem)
        add_card(slide, left_x, top_y, col_w, card_h, fill_color=WHITE, border_color=ALERT_BORDER, border_width=1.5)
        # Header banner for Left Card
        lb = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_x + Inches(0.2), top_y + Inches(0.18), Inches(5.3), Inches(0.35))
        lb.fill.solid()
        lb.fill.fore_color.rgb = ALERT_BG
        lb.line.color.rgb = ALERT_BORDER
        lb.line.width = Pt(1)
        tf_lb = lb.text_frame
        p_lbt = tf_lb.paragraphs[0]
        p_lbt.text = f"✕  WITHOUT VAHAN: {left_title.upper()}"
        p_lbt.font.size = Pt(9.5)
        p_lbt.font.bold = True
        p_lbt.font.color.rgb = ALERT_RED
        
        tb_l = slide.shapes.add_textbox(left_x + Inches(0.2), top_y + Inches(0.65), Inches(5.3), Inches(2.85))
        tf_l = tb_l.text_frame
        tf_l.word_wrap = True
        for idx, (b_head, b_desc) in enumerate(left_bullets):
            p = tf_l.paragraphs[0] if idx == 0 else tf_l.add_paragraph()
            p.text = "• " + b_head + ": " + b_desc
            p.font.size = Pt(9.5)
            p.font.color.rgb = DARK_TEXT
            p.space_before = Pt(6)

        # 2. RIGHT CARD: WITH VAHAN (Solution & Revenue Protection)
        add_card(slide, right_x, top_y, col_w, card_h, fill_color=WHITE, border_color=ACCENT_GREEN, border_width=1.5)
        rb = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x + Inches(0.2), top_y + Inches(0.18), Inches(5.3), Inches(0.35))
        rb.fill.solid()
        rb.fill.fore_color.rgb = SOFT_GREEN
        rb.line.color.rgb = ACCENT_GREEN
        rb.line.width = Pt(1)
        tf_rb = rb.text_frame
        p_rbt = tf_rb.paragraphs[0]
        p_rbt.text = f"✓  WITH VAHAN: {right_title.upper()}"
        p_rbt.font.size = Pt(9.5)
        p_rbt.font.bold = True
        p_rbt.font.color.rgb = PRIMARY_GREEN
        
        tb_r = slide.shapes.add_textbox(right_x + Inches(0.2), top_y + Inches(0.65), Inches(5.3), Inches(2.85))
        tf_r = tb_r.text_frame
        tf_r.word_wrap = True
        for idx, (b_head, b_desc) in enumerate(right_bullets):
            p = tf_r.paragraphs[0] if idx == 0 else tf_r.add_paragraph()
            p.text = "• " + b_head + ": " + b_desc
            p.font.size = Pt(9.5)
            p.font.color.rgb = DARK_TEXT
            p.space_before = Pt(6)

        # 3. BOTTOM CARD: FINANCIAL CALCULATION & BUSINESS VALUE
        calc_y = Inches(5.45)
        calc_h = Inches(1.5)
        add_card(slide, left_x, calc_y, Inches(11.733), calc_h, fill_color=WHITE, border_color=BORDER, border_width=1.2)
        
        tb_c = slide.shapes.add_textbox(left_x + Inches(0.2), calc_y + Inches(0.1), Inches(11.3), Inches(1.3))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        
        p_ct = tf_c.paragraphs[0]
        p_ct.text = f"FINANCIAL LEAKAGE CALCULATION: {calc_title.upper()}"
        p_ct.font.size = Pt(10)
        p_ct.font.bold = True
        p_ct.font.color.rgb = PRIMARY_GREEN
        
        p_form = tf_c.add_paragraph()
        p_form.text = f"Formula: {calc_formula}"
        p_form.font.size = Pt(10.5)
        p_form.font.bold = True
        p_form.font.color.rgb = DARK_TEXT
        p_form.space_before = Pt(3)
        
        p_exp = tf_c.add_paragraph()
        p_exp.text = f"Business Impact: {calc_explanation}"
        p_exp.font.size = Pt(9.5)
        p_exp.font.color.rgb = SEC_TEXT
        p_exp.space_before = Pt(3)
        
        return slide

    # =========================================================================
    # SLIDE 1: Cover — "Your Fleet Earns Revenue. But Where Is Your Profit Going?"
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_LIGHT
    bg1.line.fill.background()
    
    # Financial network visual on right
    net_img = os.path.join(ASSETS_DIR, "light_cover_network.png")
    if os.path.exists(net_img):
        slide1.shapes.add_picture(net_img, Inches(6.2), Inches(0.8), Inches(6.5), Inches(5.8))
        
    add_card(slide1, Inches(0.8), Inches(0.9), Inches(5.2), Inches(5.7), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb1 = slide1.shapes.add_textbox(Inches(1.1), Inches(1.2), Inches(4.6), Inches(5.1))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "FLEET PROFITABILITY & P&L PROTECTION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    p2 = tf1.add_paragraph()
    p2.text = "Your Fleet Earns Revenue.\nBut Where Is Your Profit Going?"
    p2.font.size = Pt(28)
    p2.font.bold = True
    p2.font.color.rgb = DARK_TEXT
    p2.space_before = Pt(6)
    
    p3 = tf1.add_paragraph()
    p3.text = "Discover the hidden operational losses in your fleet and how VAHAN helps identify, control and reduce that leakage."
    p3.font.size = Pt(12)
    p3.font.color.rgb = SEC_TEXT
    p3.space_before = Pt(14)
    
    p_div = tf1.add_paragraph()
    p_div.text = "────────────────────────────────────────"
    p_div.font.size = Pt(8)
    p_div.font.color.rgb = BORDER
    p_div.space_before = Pt(10)
    
    story_bullets = [
        "• Commercial fleets operate on thin 6% to 10% net margins.",
        "• Invisible leakage across fuel, detours, and downtime erodes profit.",
        "• Small undetected losses accumulate into Lakhs across trucks & trips.",
        "• VAHAN transforms disconnected tracking into active financial control."
    ]
    for b in story_bullets:
        p_b = tf1.add_paragraph()
        p_b.text = b
        p_b.font.size = Pt(9.5)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_before = Pt(4)

    # =========================================================================
    # SLIDE 2: The Profit Leakage Problem
    # =========================================================================
    slide2 = create_base_slide(
        "Commercial Fleet Economics",
        "Your Revenue Is Growing. Is Your Operating Profit Growing Too?",
        "Revenue alone does not reveal operational profitability; unmonitored costs consume operating margins.",
        slide_num=2
    )
    # Financial Flow Horizontal Ribbon across top
    flow_steps = [
        ("Gross Trip Revenue", "+100%", PRIMARY_GREEN, SOFT_GREEN),
        ("Fuel Expenses", "-48%", ALERT_RED, ALERT_BG),
        ("Route Inefficiencies", "-10%", ALERT_RED, ALERT_BG),
        ("Vehicle Downtime", "Idle Drag", AMBER, AMBER_BG),
        ("Driver & Trip Costs", "-14%", DARK_TEXT, RGBColor(241, 245, 249)),
        ("Maintenance & Tax", "-16%", DARK_TEXT, RGBColor(241, 245, 249)),
        ("Net Operating Profit", "Thin 8%", PRIMARY_GREEN, SOFT_GREEN)
    ]
    f_w = 1.45
    f_gap = 0.2
    for idx, (lbl, val, col, bg_col) in enumerate(flow_steps):
        fx = Inches(0.8 + idx * (f_w + f_gap))
        add_card(slide2, fx, Inches(1.65), Inches(f_w), Inches(1.0), fill_color=bg_col, border_color=BORDER)
        t_f = slide2.shapes.add_textbox(fx + Inches(0.08), Inches(1.72), Inches(f_w - 0.16), Inches(0.85))
        tf = t_f.text_frame
        tf.word_wrap = True
        p_v = tf.paragraphs[0]
        p_v.text = val
        p_v.font.size = Pt(13)
        p_v.font.bold = True
        p_v.font.color.rgb = col
        p_v.alignment = PP_ALIGN.CENTER
        p_l = tf.add_paragraph()
        p_l.text = lbl
        p_l.font.size = Pt(8.5)
        p_l.font.color.rgb = DARK_TEXT
        p_l.alignment = PP_ALIGN.CENTER

    # 6 Sources of Financial Leakage below
    leakage_sources = [
        ("1. Fuel Siphoning & Fraudulent Claims", "Unmonitored drops during rest stops, inflated fuel bills exceeding tank specs, and pump kickbacks directly bleed profits.", ALERT_RED),
        ("2. Unauthorized Route Deviations", "Extra unapproved kilometres burn diesel, cause unnecessary toll charges, damage tires, and cause customer delivery delays.", AMBER),
        ("3. Vehicle Downtime & Poor Utilization", "Trucks parked idle due to poor status awareness or maintenance delays still incur fixed financing, depreciation, and insurance.", ALERT_RED),
        ("4. Uncontrolled Driver & Trip Expenses", "Unverified paper slips, unrecorded transit expenses, and uncollected proof-of-delivery delay freight billing by weeks.", DARK_TEXT),
        ("5. Disconnected Software & Manual Work", "Managing 4+ separate GPS vendor portals and spreadsheets forces staff into manual data entry rather than active dispatch control.", SEC_TEXT),
        ("6. Hardware Churn & Lost Accountability", "Misplaced or swapped GPS devices create ghost tracking, redundant hardware purchases, and unmonitored road assets.", BLUE_ACCENT)
    ]
    for idx, (title, desc, col) in enumerate(leakage_sources):
        col_idx = idx % 3
        row_idx = idx // 3
        cx = Inches(0.8 + col_idx * 4.0)
        cy = Inches(2.9 + row_idx * 2.0)
        add_card(slide2, cx, cy, Inches(3.7), Inches(1.85), border_color=BORDER)
        
        pill = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.15), cy + Inches(0.15), Inches(3.4), Inches(0.3))
        pill.fill.solid()
        pill.fill.fore_color.rgb = SOFT_GREEN if col == PRIMARY_GREEN else (ALERT_BG if col == ALERT_RED else AMBER_BG)
        pill.line.fill.background()
        tf_p = pill.text_frame
        p = tf_p.paragraphs[0]
        p.text = title
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = col
        
        tb = slide2.shapes.add_textbox(cx + Inches(0.15), cy + Inches(0.55), Inches(3.4), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p_d = tf.paragraphs[0]
        p_d.text = desc
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = DARK_TEXT

    # =========================================================================
    # SLIDE 3: The Cost of an Unmanaged Fleet (P&L Waterfall Chart)
    # =========================================================================
    slide3 = create_base_slide(
        "Financial P&L Baseline",
        "The Cost of an Unmanaged Fleet: Where Margins Vanish",
        "Illustrative 50-Truck Commercial Fleet P&L — Labeled: Illustrative Business Scenario, Not Actual Customer Data.",
        slide_num=3
    )
    wf_img = os.path.join(ASSETS_DIR, "financial_pnl_waterfall.png")
    if os.path.exists(wf_img):
        slide3.shapes.add_picture(wf_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 4: Fuel Theft — Small Losses Become Large Expenses
    # =========================================================================
    create_feature_story_slide(
        badge="Fuel Intelligence",
        title="Fuel Theft: Every Unnoticed Drop in Fuel Eats Into Your Profit",
        subtitle="Diesel represents ~48% of operating costs; unmonitored tank drops directly destroy operating margins.",
        slide_num=4,
        left_title="Uncontrolled Fuel Losses",
        left_bullets=[
            ("Unexpected Tank Drops", "Fuel siphoned at unmonitored highway rest stops while drivers sleep."),
            ("Inflated Purchase Claims", "Drivers submit fuel bills exceeding the actual fuel added to the tank."),
            ("Tank Capacity Fraud", "Submitting fuel bills for 420 Liters on a truck with only a 350-Liter tank."),
            ("No Verification Link", "Accounts pays fuel invoices without cross-verifying GPS kilometer logs.")
        ],
        right_title="VAHAN Fuel Intelligence AI",
        right_bullets=[
            ("Siphoning Anomaly AI", "Correlates rapid fuel volume drops with engine ignition OFF states; logs alert."),
            ("Tank Capacity Physics Check", "Validation engine rejects or flags purchase receipts exceeding tank spec in Liters."),
            ("Odometer Reconciliation", "Cross-checks driver odometer receipts against verified GPS telematics distance."),
            ("Cost Per Km Visibility", "Calculates exact fuel economy and flags low-performing or suspicious vehicles.")
        ],
        calc_title="Potential Monthly Fuel Leakage",
        calc_formula="Potential Fuel Loss = Fleet Size (50 Trucks) × Monthly Spend (₹1,05,600) × Unmonitored Leakage (6.0%) = ₹3,16,800 / month",
        calc_explanation="A modest 6% leakage in fuel spend across 50 trucks equals ₹3.16 Lakhs per month (₹38.0 Lakhs annually). Investigating flagged siphoning alerts and enforcing tank capacity physics protects operating capital."
    )

    # =========================================================================
    # SLIDE 5: Route Deviations — Extra Kilometres Cost Money
    # =========================================================================
    create_feature_story_slide(
        badge="Route Intelligence",
        title="Route Deviations: An Unauthorized Detour Is Extra Operating Cost",
        subtitle="Unapproved shortcuts, toll bypasses, and unauthorized detours multiply fuel, tire, and transit costs.",
        slide_num=5,
        left_title="Unmonitored Detour Leakage",
        left_bullets=[
            ("Unapproved Detours", "Drivers deviate off authorized national highways for personal errands or side-loads."),
            ("Extra Kilometre Burn", "Every additional 50 km driven consumes 15+ Liters of extra diesel per trip."),
            ("Toll Bypass Damage", "Bypassing highway tolls via unpaved rural tracks severely degrades tires and axles."),
            ("Customer Delivery Lag", "Unplanned detours cause delivery penalties and warehouse dwell delays.")
        ],
        right_title="VAHAN Route Geo-Corridors",
        right_bullets=[
            ("Geo-Corridor Boundary Rules", "Defines strict authorized highway corridors with custom tolerance buffers."),
            ("Real-Time Deviation Alerts", "Backend engine detects cross-track errors and flags detours exceeding threshold."),
            ("Historical Breadcrumb Playback", "Scrub through past trip paths with speed vectors and timestamps to audit detours."),
            ("Adherence Compliance Scoring", "Scores driver corridor compliance for performance appraisals and safety bonuses.")
        ],
        calc_title="Potential Additional Route Cost",
        calc_formula="Potential Route Detour Cost = Fleet Size (50 Trucks) × Extra Unapproved km (180 km/mo) × Cost/km (₹28.50) = ₹2,56,500 / month",
        calc_explanation="Just 180 km of unapproved extra distance per truck per month costs an illustrative 50-truck fleet ₹2.56 Lakhs monthly (₹30.7 Lakhs/year). Geo-corridor alerts empower operators to take corrective action."
    )

    # =========================================================================
    # SLIDE 6: Vehicle Downtime — An Idle Vehicle Is Lost Earning Potential
    # =========================================================================
    create_feature_story_slide(
        badge="Asset Utilization",
        title="Vehicle Downtime: Your Vehicle Is Parked, But Fixed Costs Continue",
        subtitle="Trucks sitting idle in depots still incur fixed financing, depreciation, and insurance every day.",
        slide_num=6,
        left_title="Unmonitored Depot Downtime",
        left_bullets=[
            ("Unclear Status Awareness", "Dispatchers don't know which vehicles are available, leading to missed loads."),
            ("Delayed Servicing Awareness", "Maintenance issues discovered during loading rather than scheduled off-hours."),
            ("Double-Booking & Confusion", "Assigning a vehicle that is already committed or undergoing mechanical repair."),
            ("Depot Idling Drag", "Vehicles sitting parked in depots while freight shippers wait for capacity.")
        ],
        right_title="VAHAN Vehicle Lifecycle Management",
        right_bullets=[
            ("Deterministic Status Machine", "Strict lifecycle states: Active, In Transit, Maintenance, Out of Service, Decommissioned."),
            ("Fleet Availability Overview", "Real-time dashboard grid showing available ready-to-dispatch units across depots."),
            ("Maintenance & Fitness Reminders", "Automated tracking of odometer service intervals and statutory fitness renewals."),
            ("Operational Utilization Tracking", "Monitors active highway running hours versus warehouse loading and depot dwell.")
        ],
        calc_title="Potential Lost Contribution from Avoidable Downtime",
        calc_formula="Potential Lost Contribution = Fleet Size (50 Trucks) × Avoidable Idle Days (1.5 days/mo) × Daily Contribution (₹2,400) = ₹1,80,000 / month",
        calc_explanation="Recovering just 1.5 avoidable idle days per truck per month preserves ₹1.80 Lakhs in monthly contribution margin (₹21.6 Lakhs/year). Note: VAHAN improves visibility to optimize scheduling; it does not repair trucks."
    )

    # =========================================================================
    # SLIDE 7: Driver Accountability — Control Expenses at the Source
    # =========================================================================
    create_feature_story_slide(
        badge="Workforce Compliance",
        title="Driver Accountability: Unverified Drivers and Unrecorded Expenses",
        subtitle="Unrecorded trip expenses and expired regulatory credentials expose fleets to severe operational liability.",
        slide_num=7,
        left_title="Workforce & Expense Risks",
        left_bullets=[
            ("Expired Commercial Licenses", "Driving with expired credentials risks police impoundment and insurance forfeiture."),
            ("Unrecorded En-Route Cash", "Trip cash advances for tolls and minor repairs paid without verifiable receipts."),
            ("Paper Vehicle Inspection Slips", "Safety defects in brakes or tires ignored until catastrophic breakdown on road."),
            ("Inconsistent Communication", "Relying on phone calls and WhatsApp messages that cannot be audited later.")
        ],
        right_title="VAHAN Driver Mobile & KYC Review",
        right_bullets=[
            ("Centralized Document Vault", "Commercial license and medical fitness stored digitally with 30/15-day expiry alerts."),
            ("Formal Review Queue", "Compliance officer approves or rejects documents with audit notes before dispatch."),
            ("Digital Pre-Trip Inspections", "Driver completes standardized 5-point safety check on Flutter mobile client."),
            ("Mobile Expense & Toll Capture", "Driver photographs receipt slips en-route; immediately attached to active trip audit.")
        ],
        calc_title="Administrative & Regulatory Risk Exposure",
        calc_formula="Business Exposure = Statutory Impoundment Penalties + Delayed Trip Invoicing + Unverified En-Route Cash Claims",
        calc_explanation="Preventing a single vehicle impoundment saves ₹25,000–₹50,000 in statutory penalties and protects contracted customer delivery schedules, while digital receipts eliminate unverified cash claims."
    )

    # =========================================================================
    # SLIDE 8: Trip Management — Every Trip Needs Financial Accountability
    # =========================================================================
    create_feature_story_slide(
        badge="Trip Operations",
        title="Trip Management: A Trip Is Not Profitable Just Because It Reaches Destination",
        subtitle="Uncontrolled trip execution leads to delayed billing, lost receipts, and unverified distance claims.",
        slide_num=8,
        left_title="Unstructured Trip Chaos",
        left_bullets=[
            ("Manual Dispatch Slips", "Trips launched without clear binding of vehicle, driver, and cargo manifest."),
            ("Missing Transit Milestones", "Dispatchers cannot confirm when a truck entered or departed customer loading gates."),
            ("Lost Proof of Delivery (POD)", "Paper delivery notes lost or soiled, delaying customer invoice payment by weeks."),
            ("Unreconciled Post-Trip Costs", "Trip closed without matching driver odometer claims against actual GPS kilometers.")
        ],
        right_title="VAHAN 10-Step Trip Lifecycle",
        right_bullets=[
            ("Structured 10-Step Pipeline", "Creation → Cargo → Resource Check → Dispatch → Telematics → Milestones → Delivery → Audit."),
            ("Automated Resource Gating", "Prevents dispatching vehicles under repair or drivers with pending/expired documents."),
            ("Real-Time Gate Timestamps", "Captures exact loading arrival, transit expressway checkpoints, and delivery times."),
            ("Automated Trip Audit", "Cross-checks driver odometer logs against GPS telematics distance before closing manifest.")
        ],
        calc_title="Working Capital & Billing Acceleration",
        calc_formula="Billing Acceleration = 100% Verifiable PODs + GPS Distance Reconciliation = 10–14 Days Faster Freight Invoice Collection",
        calc_explanation="Capturing digital delivery proofs and validating trip expenses at destination arrival eliminates billing disputes, shortening invoice-to-cash cycles by up to two full weeks."
    )

    # =========================================================================
    # SLIDE 9: Hardware Management — Stop Losing Control of Your Devices
    # =========================================================================
    create_feature_story_slide(
        badge="Hardware Governance",
        title="Hardware Management: Stop Losing Control of Your GPS Devices",
        subtitle="Misplaced trackers, unmapped SIM cards, and ghost devices lead to unnecessary replacement purchases.",
        slide_num=9,
        left_title="Unmanaged Hardware Chaos",
        left_bullets=[
            ("Orphaned Trackers", "GPS devices removed during workshop maintenance and forgotten on workshop shelves."),
            ("Ghost Vehicle Tracking", "Telematics streams assigned to wrong vehicles, distorting mileage and route records."),
            ("Redundant Hardware Purchases", "Buying new GPS units because previous hardware inventory is untracked."),
            ("Unmonitored Device Outages", "Failing to notice that a tracker has lost battery power or stopped transmitting.")
        ],
        right_title="VAHAN Hardware Registry & Vault",
        right_bullets=[
            ("Device Master Inventory", "Complete tracking by IMEI, Serial Number, Protocol type, and SIM card ICCID."),
            ("Dynamic Pairing Wizard", "Pair or reassign trackers to vehicles in seconds; previous pairings auto-retired."),
            ("Device Heartbeat & Outage Alerts", "Automated monitoring alerts managers when a device ceases transmitting."),
            ("Zero-Trust Quarantine Vault", "Unmapped or retired devices are isolated in a quarantine tenant to protect data.")
        ],
        calc_title="Hardware Inventory & Capital Preservation",
        calc_formula="Hardware Capital Risk = Replaced Tracker Costs (₹3,500/unit) + Unmonitored Vehicle Risk Exposure",
        calc_explanation="Maintaining complete device provenance eliminates redundant tracker replacements and ensures 100% of commercial vehicles remain visible and accounted for."
    )

    # =========================================================================
    # SLIDE 10: Disconnected Systems — Hidden Administrative Costs
    # =========================================================================
    create_feature_story_slide(
        badge="Administrative Efficiency",
        title="Disconnected Systems: Hidden Administrative Labor Costs",
        subtitle="Managing multiple GPS vendor portals and manual spreadsheets drains operational staff productivity.",
        slide_num=10,
        left_title="Fragmented Tool Fatigue",
        left_bullets=[
            ("4+ Vendor GPS Portals", "Operators log into separate systems for tracking, maintenance, and driver files."),
            ("Manual Spreadsheet Logging", "Staff spend hours transcribing odometer numbers, fuel bills, and trip dates into Excel."),
            ("Data Transcription Errors", "Incorrect mileage entries lead to erroneous billing and disputed client statements."),
            ("Slow Decision Making", "Dispatchers cannot answer shipper location queries without calling multiple drivers.")
        ],
        right_title="VAHAN Unified Fleet Command Center",
        right_bullets=[
            ("Single Pane of Glass", "Consolidates vehicles, drivers, trips, telematics, and fuel in one responsive React 18 console."),
            ("Automated Data Pipelines", "GPS telemetry, fuel entries, and inspection checklists sync directly to vehicle profiles."),
            ("Multi-Depot Filtering", "Segment views by operational region, client contract, or fleet branch seamlessly."),
            ("Instant Operational Search", "Look up any vehicle, driver, or past trip in seconds with complete audit history.")
        ],
        calc_title="Administrative Productivity Optimization",
        calc_formula="Operational Optimization = Elimination of Multi-Portal Context Switching + Automated Record Consolidation",
        calc_explanation="Consolidating operations into a single platform frees dispatchers to focus on optimizing routes and client service rather than routine spreadsheet data entry."
    )

    # =========================================================================
    # SLIDE 11: Compliance — One Missing Document Becomes an Expensive Problem
    # =========================================================================
    create_feature_story_slide(
        badge="Regulatory Compliance",
        title="Compliance: One Missing Document Can Become an Expensive Problem",
        subtitle="Operating commercial transport with expired licenses or missing fitness invites severe statutory exposure.",
        slide_num=11,
        left_title="Regulatory Non-Compliance Risk",
        left_bullets=[
            ("On-Road Police Impoundment", "Vehicles seized at highway state borders due to expired driver licenses."),
            ("Insurance Claim Rejection", "Accident claims rejected entirely because the operating driver held an expired badge."),
            ("Statutory Penalties", "Heavy fines under Motor Vehicles Act provisions for non-compliant commercial carriage."),
            ("Reputational Shipper Loss", "Major corporate logistics clients blacklisting transport vendors after compliance failures.")
        ],
        right_title="VAHAN Digital KYC & Approval Queue",
        right_bullets=[
            ("Proactive Expiration Alerts", "Automated system alerts 30 and 15 days prior to license or fitness expiry."),
            ("Formal Review Queue", "Compliance officers review documents with side-by-side previews and issue formal approval."),
            ("Mandatory Dispatch Gating", "System strictly blocks dispatching any vehicle to a driver without verified documents."),
            ("Immutable Compliance Audit Trail", "Complete historical compliance records ready for regulatory and insurance audits.")
        ],
        calc_title="Statutory Risk & Business Continuity Protection",
        calc_formula="Compliance Protection = Zero Statutory Impoundment Penalties + Protected Insurance Claim Validity",
        calc_explanation="Automated compliance gating ensures zero unverified drivers operate on highways, protecting the business from catastrophic insurance claim forfeitures and statutory impoundment."
    )

    # =========================================================================
    # SLIDE 12: Financial Intelligence — Know Your Real Cost Per Kilometre
    # =========================================================================
    slide12 = create_base_slide(
        "Financial Analytics",
        "Financial Intelligence: Revenue Per Trip Means Nothing Without Cost Per Km",
        "Consolidating fuel expenses, tolls, maintenance, and GPS distance into actual trip profitability.",
        slide_num=12
    )
    cpk_img = os.path.join(ASSETS_DIR, "financial_cost_per_km.png")
    if os.path.exists(cpk_img):
        slide12.shapes.add_picture(cpk_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 13: One Connected System — Multiple Sources of Financial Control
    # =========================================================================
    slide13 = create_base_slide(
        "Systemic Value Mapping",
        "One Connected System: 8 Sources of Leakage Mapped to Controls",
        "Every VAHAN module directly addresses an operational vulnerability to safeguard commercial profit margins.",
        slide_num=13
    )
    map_img = os.path.join(ASSETS_DIR, "financial_system_mapping.png")
    if os.path.exists(map_img):
        slide13.shapes.add_picture(map_img, Inches(0.8), Inches(1.65), Inches(11.733), Inches(5.1))

    # =========================================================================
    # SLIDE 14: Before VAHAN vs After VAHAN (Visual Comparison)
    # =========================================================================
    slide14 = create_base_slide(
        "Business Transformation",
        "The Operational Transformation: Before VAHAN vs. After VAHAN",
        "Transforming fragmented, reactive fleet operations into a disciplined, data-driven profit center.",
        slide_num=14
    )
    # Comparison Table
    dim_rows = [
        ("1. Fleet Records & Visibility", "Fragmented across 4+ portals, paper slips, and Excel sheets.", "Single pane of glass: vehicles, drivers, trips, and telematics unified.", ALERT_RED, PRIMARY_GREEN),
        ("2. Fuel Expense Accountability", "Fuel bills paid without tank capacity checks or siphon monitoring.", "Automated siphoning anomaly alerts & tank capacity physics checks.", ALERT_RED, PRIMARY_GREEN),
        ("3. Route & Highway Corridor", "Drivers take unapproved detours; zero visibility into extra distance.", "Real-time geo-corridor monitoring with automated deviation alerts.", ALERT_RED, PRIMARY_GREEN),
        ("4. Vehicle Utilization", "Unclear vehicle availability; trucks idle in depots while loads wait.", "Deterministic lifecycle status machine; availability overview grid.", ALERT_RED, PRIMARY_GREEN),
        ("5. Driver & Regulatory KYC", "Expired licenses discovered during highway police impoundment.", "Digital document vault with 30-day alerts; unverified drivers blocked.", ALERT_RED, PRIMARY_GREEN),
        ("6. Post-Trip Reconciliation", "Manual, disputed distance claims; delayed client invoicing.", "Reconciles driver odometer against verified GPS kilometers instantly.", ALERT_RED, PRIMARY_GREEN)
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
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    for r_idx, (dim, without_v, with_v, col_w, col_v) in enumerate(dim_rows, 1):
        # Col 0
        c0 = tbl.cell(r_idx, 0)
        c0.text = dim
        c0.fill.solid()
        c0.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else BG_LIGHT
        p0 = c0.text_frame.paragraphs[0]
        p0.font.size = Pt(9.5)
        p0.font.bold = True
        p0.font.color.rgb = DARK_TEXT
        
        # Col 1 (Without)
        c1 = tbl.cell(r_idx, 1)
        c1.text = without_v
        c1.fill.solid()
        c1.fill.fore_color.rgb = ALERT_BG if r_idx % 2 == 1 else WHITE
        p1 = c1.text_frame.paragraphs[0]
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = DARK_TEXT
        
        # Col 2 (With)
        c2 = tbl.cell(r_idx, 2)
        c2.text = with_v
        c2.fill.solid()
        c2.fill.fore_color.rgb = SOFT_GREEN if r_idx % 2 == 1 else WHITE
        p2 = c2.text_frame.paragraphs[0]
        p2.font.size = Pt(9.5)
        p2.font.bold = True
        p2.font.color.rgb = PRIMARY_GREEN

    # =========================================================================
    # SLIDE 15: Illustrative Financial Impact Calculator
    # =========================================================================
    slide15 = create_base_slide(
        "Financial Scenario Modeling",
        "Illustrative Financial Impact Scenario: What Uncontrolled Leakage Costs",
        "Editable Scenario Simulator — Labeled: Illustrative Scenario Calculator, Not a Performance Guarantee.",
        slide_num=15
    )
    # Left Box: Editable Inputs Card
    add_card(slide15, Inches(0.8), Inches(1.65), Inches(5.6), Inches(5.1), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb_inp = slide15.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
    tf_inp = tb_inp.text_frame
    tf_inp.word_wrap = True
    
    p = tf_inp.paragraphs[0]
    p.text = "EDITABLE FLEET SCENARIO ASSUMPTIONS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    assump_lines = [
        ("Commercial Fleet Size:", "50 Trucks in Active Service"),
        ("Average Fuel Spend / Truck / Month:", "₹1,05,600 / truck / mo"),
        ("Estimated Unexplained Fuel Leakage:", "6.0% (Siphoning & Inflated Claims)"),
        ("Average Unapproved Extra Distance:", "180 km / truck / month"),
        ("Operating Cost Per Kilometre:", "₹28.50 / km (Fuel, Maintenance, Tires)"),
        ("Avoidable Idle Downtime Days:", "1.5 days / truck / month"),
        ("Daily Net Contribution Margin:", "₹2,400 / day / vehicle"),
        ("Flagged Loss Investigation Success Rate:", "60.0% (Operational Resolution)")
    ]
    for lbl, val in assump_lines:
        p_l = tf_inp.add_paragraph()
        p_l.text = lbl + " " + val
        p_l.font.size = Pt(9.5)
        p_l.font.color.rgb = DARK_TEXT
        p_l.space_before = Pt(5)

    p_note = tf_inp.add_paragraph()
    p_note.text = "All model inputs editable in VAHAN_Financial_Impact_Assumptions.xlsx"
    p_note.font.size = Pt(8.5)
    p_note.font.color.rgb = SEC_TEXT
    p_note.space_before = Pt(12)

    # Right Box: Calculated Financial Exposure & Protected Profit
    add_card(slide15, Inches(6.8), Inches(1.65), Inches(5.733), Inches(5.1), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb_out = slide15.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
    tf_out = tb_out.text_frame
    tf_out.word_wrap = True
    
    p = tf_out.paragraphs[0]
    p.text = "CALCULATED OPERATIONAL LEAKAGE EXPOSURE"
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
        p_c = tf_out.add_paragraph()
        p_c.text = f"{lbl:<42} {val:>15}"
        p_c.font.size = Pt(9.5)
        p_c.font.bold = "TOTAL" in lbl or "Protected" in lbl
        p_c.font.color.rgb = col
        p_c.space_before = Pt(3)

    p_gov = tf_out.add_paragraph()
    p_gov.text = "Governance: Scenario simulation for financial planning. Not a performance guarantee."
    p_gov.font.size = Pt(8.5)
    p_gov.font.color.rgb = SEC_TEXT
    p_gov.space_before = Pt(8)

    # =========================================================================
    # SLIDE 16: What Does VAHAN Cost Compared to Your Potential Loss?
    # =========================================================================
    slide16 = create_base_slide(
        "Commercial Value Evaluation",
        "Evaluating VAHAN: Software Investment vs. Financial Leakage Protection",
        "Evaluate subscription costs directly against the monthly operational leakage VAHAN helps identify and control.",
        slide_num=16
    )
    # Pricing comparison table for 10, 50, 100 trucks
    t_w = Inches(11.733)
    t_h = Inches(5.1)
    tbl_p_shape = slide16.shapes.add_table(5, 5, Inches(0.8), Inches(1.65), t_w, t_h)
    tbl_p = tbl_p_shape.table
    tbl_p.columns[0].width = Inches(2.933)
    tbl_p.columns[1].width = Inches(2.2)
    tbl_p.columns[2].width = Inches(2.2)
    tbl_p.columns[3].width = Inches(2.2)
    tbl_p.columns[4].width = Inches(2.2)
    
    headers_p = ["Fleet Size Cohort", "STARTER (₹500/mo)", "PROFESSIONAL (₹800/mo)", "ENTERPRISE (₹1,000/mo)", "Illustrative Avoidable Loss"]
    for c_idx, h in enumerate(headers_p):
        cell = tbl_p.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = ALERT_RED if c_idx == 4 else PRIMARY_GREEN
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    price_rows = [
        ("10 Commercial Vehicles", "₹5,000 / month", "₹8,000 / month", "₹10,000 / month", "₹90,396 / month"),
        ("50 Commercial Vehicles", "₹25,000 / month", "₹40,000 / month", "₹50,000 / month", "₹4,51,980 / month"),
        ("100 Commercial Vehicles", "₹50,000 / month", "₹80,000 / month", "₹1,00,000 / month", "₹9,03,960 / month"),
        ("Protection Scope & Focus", "Core fleet registry, KYC compliance & dispatching", "Live GPS tracking, route deviation alerts, driver mobile app", "Fuel siphoning AI, tank physics check, quarantine hardware vault", "Based on 60% investigated resolution rate under assumptions")
    ]
    for r_idx, row_vals in enumerate(price_rows, 1):
        for c_idx, val in enumerate(row_vals):
            cell = tbl_p.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = ALERT_BG if c_idx == 4 else (WHITE if r_idx % 2 == 1 else BG_LIGHT)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if (c_idx == 0 or r_idx == 4) else PP_ALIGN.CENTER
            p.font.size = Pt(9.5)
            p.font.bold = c_idx == 0 or r_idx < 4
            p.font.color.rgb = ALERT_RED if c_idx == 4 else (PRIMARY_GREEN if c_idx == 3 else DARK_TEXT)

    # =========================================================================
    # SLIDE 17: Which Plan Protects Which Part of Your Business?
    # =========================================================================
    slide17 = create_base_slide(
        "Plan Selection Strategy",
        "Aligning Platform Tiers with Business Protection Priorities",
        "Choose the plan that matches your primary operational vulnerabilities and fleet profile.",
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
    # SLIDE 18: The Financial Value of Every VAHAN Feature (Matrix)
    # =========================================================================
    slide18 = create_base_slide(
        "Feature Profitability Matrix",
        "The Profitability Matrix: How Every Feature Protects Operating Capital",
        "Mapping platform capabilities directly to business loss mechanisms, operational gains, and subscription tiers.",
        slide_num=18
    )
    t_w = Inches(11.733)
    t_h = Inches(5.1)
    tbl_m_shape = slide18.shapes.add_table(11, 5, Inches(0.8), Inches(1.65), t_w, t_h)
    tbl_m = tbl_m_shape.table
    tbl_m.columns[0].width = Inches(2.6)
    tbl_m.columns[1].width = Inches(2.4)
    tbl_m.columns[2].width = Inches(2.4)
    tbl_m.columns[3].width = Inches(2.533)
    tbl_m.columns[4].width = Inches(1.8)
    
    m_headers = ["Business Problem", "Mechanism of Financial Loss", "VAHAN Solution Feature", "Expected Business Benefit", "Plan Tier"]
    for c_idx, h in enumerate(m_headers):
        cell = tbl_m.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = PRIMARY_GREEN
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    m_rows = [
        ("Unnoticed fuel volume drops during rest stops", "Direct diesel loss (₹90+/L) inflating running costs", "Fuel Siphoning Anomaly AI", "Detects fuel drops while ignition is OFF with GPS coords", "Enterprise (₹1,000)"),
        ("Inflated fuel bills submitted by drivers", "Paying for diesel that never entered vehicle fuel tank", "Tank Capacity Physics Check", "Rejects fuel receipts exceeding tank capacity spec (L)", "Enterprise (₹1,000)"),
        ("Unapproved highway detours & toll bypasses", "Extra km burns diesel, degrades tires, causes delays", "Route Geo-Corridor Detection", "Alerts dispatchers to off-corridor detours > threshold", "Professional (₹800)"),
        ("Vehicles idle in depots due to poor awareness", "Lost contribution margin (₹2,400/day); fixed overhead continues", "Vehicle Lifecycle State Machine", "Improves fleet availability; stops double-booking", "Starter (₹500)"),
        ("Drivers operating with expired licenses/fitness", "Police impoundment, statutory fines, insurance loss", "Driver KYC Document Review Queue", "Blocks unverified drivers from dispatch; 30-day alerts", "Starter (₹500)"),
        ("Paper-based pre-trip safety inspection slips", "Unaddressed defects cause highway mechanical breakdowns", "Digital Pre-Trip Mobile Inspection", "5-point digital checklist on Flutter client before trip", "Professional (₹800)"),
        ("Lost delivery receipts & disputed distance", "Delayed freight invoice payment; disputed billings", "Trip Management & Milestone Engine", "Digital PODs & GPS distance audit accelerate billing", "Starter (₹500)"),
        ("Lost or ghost GPS hardware units across shops", "Redundant tracker repurchase; unmonitored road trucks", "Hardware Registry & Dynamic Pairing", "Tracks IMEI provenance; dynamic pairing in 3 clicks", "Professional (₹800)"),
        ("Rogue trackers transmitting into database", "Data leakage, unassigned telemetry contamination", "Quarantine Isolation Vault", "Traps unmapped devices; Super-Admin review queue", "Enterprise (₹1,000)"),
        ("Managing multiple disjointed GPS portals", "High administrative labor cost & spreadsheet errors", "Unified Fleet Command Center", "Consolidates all fleet ops in single React 18 console", "Starter (₹500)")
    ]
    for r_idx, (p_txt, l_txt, f_txt, b_txt, tier_txt) in enumerate(m_rows, 1):
        for c_idx, val in enumerate([p_txt, l_txt, f_txt, b_txt, tier_txt]):
            cell = tbl_m.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r_idx % 2 == 1 else BG_LIGHT
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx == 4 else PP_ALIGN.LEFT
            p.font.size = Pt(8.5)
            p.font.bold = c_idx in [0, 2, 4]
            if c_idx == 4:
                p.font.color.rgb = PRIMARY_GREEN if "Professional" in val else (ALERT_RED if "Enterprise" in val else DARK_TEXT)
            elif c_idx == 1:
                p.font.color.rgb = ALERT_RED
            else:
                p.font.color.rgb = DARK_TEXT

    # =========================================================================
    # SLIDE 19: Final Sales Message
    # =========================================================================
    slide19 = create_base_slide(
        "Commercial Partnership",
        "Don't Just Manage Your Fleet. Protect Its Profitability.",
        "VAHAN gives you the visibility and control to identify operational leakage and protect operating margins.",
        slide_num=19
    )
    # Left Card: Executive Call to Action
    add_card(slide19, Inches(0.8), Inches(1.65), Inches(5.7), Inches(5.0), fill_color=WHITE, border_color=BORDER, border_width=1.5)
    tb_end = slide19.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(5.3), Inches(4.6))
    tf_end = tb_end.text_frame
    tf_end.word_wrap = True
    
    p = tf_end.paragraphs[0]
    p.text = "Start Understanding Where Your Fleet Money Goes."
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_GREEN
    
    p_sub = tf_end.add_paragraph()
    p_sub.text = "Every day your fleet operates without centralized visibility, avoidable leakage in diesel, extra distance, and unscheduled downtime erodes your thin operating profit."
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = DARK_TEXT
    p_sub.space_before = Pt(8)
    
    core_actions = [
        "✓ 14-Day Production Pilot with a 5 to 10 vehicle test cohort",
        "✓ Establish your fleet's true baseline cost-per-kilometer",
        "✓ Identify hidden fuel siphoning and tank capacity violations",
        "✓ Audit driver route compliance on key national highway corridors",
        "✓ Zero upfront hardware replacement required"
    ]
    for ca in core_actions:
        p_ca = tf_end.add_paragraph()
        p_ca.text = ca
        p_ca.font.size = Pt(10)
        p_ca.font.bold = True
        p_ca.font.color.rgb = DARK_TEXT
        p_ca.space_before = Pt(8)

    # Right Card: Structured Pilot Roadmap
    add_card(slide19, Inches(6.8), Inches(1.65), Inches(5.7), Inches(5.0), fill_color=SOFT_GREEN, border_color=ACCENT_GREEN, border_width=1.5)
    tb_stp = slide19.shapes.add_textbox(Inches(7.0), Inches(1.85), Inches(5.3), Inches(4.6))
    tf_stp = tb_stp.text_frame
    tf_stp.word_wrap = True
    
    p = tf_stp.paragraphs[0]
    p.text = "4-Step Pilot Implementation Roadmap"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = DARK_TEXT
    
    roadmap_steps = [
        ("Step 1: Fleet Discovery & Onboarding", "Upload 10 vehicle profiles with tank specs and verify driver documents."),
        ("Step 2: Gateway Webhook Setup", "Point existing GPS trackers to VAHAN's multi-protocol gateway (AIS-140/GT06)."),
        ("Step 3: Driver Mobile Deployment", "Equip drivers with the Flutter mobile client for digital safety inspections."),
        ("Step 4: Operational P&L Review", "Review flagged fuel drops, route deviations, and cost-per-km analytics together.")
    ]
    for s_title, s_desc in roadmap_steps:
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
    p_close.space_before = Pt(16)

    # Output file
    out_pptx = r"c:\Users\ratho\fleetguard\VAHAN_Profitability_And_Business_Impact_Presentation.pptx"
    prs.save(out_pptx)
    print(f"Successfully generated: {out_pptx} with {len(prs.slides)} slides.")

if __name__ == "__main__":
    build_profitability_presentation()
