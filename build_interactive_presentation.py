import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

# -----------------------------------------------------------------------------
# COLOR PALETTE SPECIFICATION (VAHAN LIGHT THEME)
# -----------------------------------------------------------------------------
COLOR_BG = RGBColor(247, 250, 248)          # #F7FAF8 Clean Canvas
COLOR_CARD_BG = RGBColor(255, 255, 255)     # #FFFFFF Pure White
COLOR_CARD_BORDER = RGBColor(225, 234, 228) # #E1EAE4 Crisp Border
COLOR_PRIMARY = RGBColor(37, 132, 91)       # #25845B Emerald Green
COLOR_PRIMARY_DARK = RGBColor(27, 94, 32)   # Deep Green
COLOR_SOFT_GREEN = RGBColor(228, 243, 234)  # #E4F3EA Mint Accent
COLOR_TEXT_DARK = RGBColor(36, 53, 45)      # #24352D Deep Forest Text
COLOR_TEXT_MUTED = RGBColor(100, 115, 107)  # #64736B Neutral Slate
COLOR_LOSS_RED = RGBColor(217, 119, 112)    # #D97770 Coral Red (Loss)
COLOR_LOSS_BG = RGBColor(254, 242, 242)     # Soft Red Container
COLOR_NAV_BG = RGBColor(238, 244, 240)      # Nav pill background
COLOR_NAV_ACTIVE = RGBColor(37, 132, 91)    # Active nav pill

FONT_FAMILY = "Segoe UI"

def create_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide layout

    slides = []

    # -------------------------------------------------------------------------
    # Helper: Base Slide Creation with Background
    # -------------------------------------------------------------------------
    def add_base_slide():
        slide = prs.slides.add_slide(blank_layout)
        # Background shape to ensure 100% consistent light theme
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.fill.background() # No border
        slides.append(slide)
        return slide

    # -------------------------------------------------------------------------
    # Helper: Add Card Shape
    # -------------------------------------------------------------------------
    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER, corner_radius=None):
        shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if corner_radius else MSO_SHAPE.ROUNDED_RECTANGLE
        card = slide.shapes.add_shape(shape_type, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.2)
        else:
            card.line.fill.background()
        return card

    # -------------------------------------------------------------------------
    # Helper: Add Header & Subtitle
    # -------------------------------------------------------------------------
    def add_header(slide, title_text, category_text, subtitle_text):
        # Category Badge
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(6.0), Inches(0.35))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0
        p_c = tf_c.paragraphs[0]
        p_c.text = category_text.upper()
        p_c.font.name = FONT_FAMILY
        p_c.font.size = Pt(9.5)
        p_c.font.bold = True
        p_c.font.color.rgb = COLOR_PRIMARY

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(8.5), Inches(0.55))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(20)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TEXT_DARK

        # Subtitle
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.30), Inches(9.5), Inches(0.38))
        tf_s = sub_box.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = 0
        p_s = tf_s.paragraphs[0]
        p_s.text = subtitle_text
        p_s.font.name = FONT_FAMILY
        p_s.font.size = Pt(11)
        p_s.font.color.rgb = COLOR_TEXT_MUTED

    # -------------------------------------------------------------------------
    # Helper: Add Button / Pill with Text
    # -------------------------------------------------------------------------
    def add_button(slide, left, top, width, height, text, bg_color=COLOR_PRIMARY, text_color=RGBColor(255, 255, 255), font_size=10, bold=True, border_color=None):
        btn = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        btn.fill.solid()
        btn.fill.fore_color.rgb = bg_color
        if border_color:
            btn.line.color.rgb = border_color
            btn.line.width = Pt(1)
        else:
            btn.line.fill.background()
        
        tf = btn.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_FAMILY
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = text_color
        return btn

    # -------------------------------------------------------------------------
    # BUILD SLIDES 1 TO 18
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # SLIDE 1: Title & Hero
    # -------------------------------------------------------------------------
    s1 = add_base_slide()
    # Left Hero Container
    add_card(s1, Inches(0.8), Inches(1.0), Inches(6.8), Inches(5.5), bg_color=COLOR_CARD_BG)
    
    # Title badge
    b1 = add_button(s1, Inches(1.2), Inches(1.4), Inches(2.8), Inches(0.36), "ENTERPRISE FLEET INTELLIGENCE", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=9, bold=True)
    
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.9), Inches(6.0), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "VAHAN"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_PRIMARY

    p2 = tf.add_paragraph()
    p2.text = "Connected Fleet Management &\nFinancial Protection Platform"
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_TEXT_DARK

    p3 = tf.add_paragraph()
    p3.space_before = Pt(12)
    p3.text = "Transforming unmanaged fuel siphoning, route deviations, and preventable breakdowns into verified, measurable bottom-line profit."
    p3.font.name = FONT_FAMILY
    p3.font.size = Pt(12)
    p3.font.color.rgb = COLOR_TEXT_MUTED

    # Quick action buttons on Slide 1 (will link to slides after all slides created)
    btn_s1_story = add_button(s1, Inches(1.2), Inches(5.4), Inches(2.6), Inches(0.55), "Explore Profit Story  ➔", bg_color=COLOR_PRIMARY, font_size=11)
    btn_s1_calc = add_button(s1, Inches(4.0), Inches(5.4), Inches(2.2), Inches(0.55), "ROI Calculator", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=11)

    # Right Hero Metrics Card
    add_card(s1, Inches(7.9), Inches(1.0), Inches(4.6), Inches(5.5), bg_color=COLOR_CARD_BG)
    
    rt_b = s1.shapes.add_textbox(Inches(8.3), Inches(1.3), Inches(3.8), Inches(0.8))
    tf_rt = rt_b.text_frame
    tf_rt.word_wrap = True
    p_rt = tf_rt.paragraphs[0]
    p_rt.text = "50-Truck Fleet Baseline"
    p_rt.font.name = FONT_FAMILY
    p_rt.font.size = Pt(14)
    p_rt.font.bold = True
    p_rt.font.color.rgb = COLOR_TEXT_DARK

    p_rt2 = tf_rt.add_paragraph()
    p_rt2.text = "Identified Unmanaged Operational Exposure"
    p_rt2.font.name = FONT_FAMILY
    p_rt2.font.size = Pt(10)
    p_rt2.font.color.rgb = COLOR_TEXT_MUTED

    # Metric Cards on Right
    mc1 = add_card(s1, Inches(8.3), Inches(2.2), Inches(3.8), Inches(1.15), bg_color=COLOR_LOSS_BG, border_color=COLOR_LOSS_RED)
    m1_tb = s1.shapes.add_textbox(Inches(8.5), Inches(2.3), Inches(3.4), Inches(0.95))
    tf_m1 = m1_tb.text_frame
    p_m1a = tf_m1.paragraphs[0]
    p_m1a.text = "MONTHLY FINANCIAL LEAKAGE"
    p_m1a.font.name = FONT_FAMILY
    p_m1a.font.size = Pt(9)
    p_m1a.font.bold = True
    p_m1a.font.color.rgb = COLOR_LOSS_RED
    p_m1b = tf_m1.add_paragraph()
    p_m1b.text = "₹7,53,300"
    p_m1b.font.name = FONT_FAMILY
    p_m1b.font.size = Pt(22)
    p_m1b.font.bold = True
    p_m1b.font.color.rgb = COLOR_TEXT_DARK
    p_m1c = tf_m1.add_paragraph()
    p_m1c.text = "Fuel (₹3.16L) + Detours (₹2.56L) + Downtime (₹1.80L)"
    p_m1c.font.name = FONT_FAMILY
    p_m1c.font.size = Pt(8.5)
    p_m1c.font.color.rgb = COLOR_TEXT_MUTED

    mc2 = add_card(s1, Inches(8.3), Inches(3.55), Inches(3.8), Inches(1.15), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    m2_tb = s1.shapes.add_textbox(Inches(8.5), Inches(3.65), Inches(3.4), Inches(0.95))
    tf_m2 = m2_tb.text_frame
    p_m2a = tf_m2.paragraphs[0]
    p_m2a.text = "VERIFIED ANNUAL RECOVERY (60%)"
    p_m2a.font.name = FONT_FAMILY
    p_m2a.font.size = Pt(9)
    p_m2a.font.bold = True
    p_m2a.font.color.rgb = COLOR_PRIMARY
    p_m2b = tf_m2.add_paragraph()
    p_m2b.text = "₹54,23,760"
    p_m2b.font.name = FONT_FAMILY
    p_m2b.font.size = Pt(22)
    p_m2b.font.bold = True
    p_m2b.font.color.rgb = COLOR_TEXT_DARK
    p_m2c = tf_m2.add_paragraph()
    p_m2c.text = "Net Owner Profit: ₹49.43 Lakh/yr (11.3x ROI)"
    p_m2c.font.name = FONT_FAMILY
    p_m2c.font.size = Pt(8.5)
    p_m2c.font.color.rgb = COLOR_TEXT_MUTED

    # Bottom Trust Badges
    tb_trust = s1.shapes.add_textbox(Inches(8.3), Inches(4.9), Inches(3.8), Inches(1.4))
    tf_tr = tb_trust.text_frame
    tf_tr.word_wrap = True
    p_tr1 = tf_tr.paragraphs[0]
    p_tr1.text = "✓ Production-Tested FastAPI & PostgreSQL Architecture\n✓ AIS-140, Teltonika & GT06 Multi-Protocol Ingestion\n✓ Native Flutter Driver App with Offline Sync"
    p_tr1.font.name = FONT_FAMILY
    p_tr1.font.size = Pt(9.5)
    p_tr1.font.color.rgb = COLOR_TEXT_MUTED

    # -------------------------------------------------------------------------
    # SLIDE 2: Executive Summary & Operating P&L
    # -------------------------------------------------------------------------
    s2 = add_base_slide()
    add_header(s2, "Fleet Operating P&L Structure & Margin Exposure", "01. Executive Overview", "Commercial transport operates on razor-thin margins where unmonitored operational waste directly wipes out profit.")

    # Left Container: Doughnut Chart
    add_card(s2, Inches(0.8), Inches(1.8), Inches(6.0), Inches(4.8))
    chart_title = s2.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.4), Inches(0.4))
    chart_title.text_frame.paragraphs[0].text = "HCV Fleet Operating Cost Breakdown (Illustrative Model)"
    chart_title.text_frame.paragraphs[0].font.size = Pt(12)
    chart_title.text_frame.paragraphs[0].font.bold = True
    chart_title.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    # Native Doughnut Chart
    chart_data = CategoryChartData()
    chart_data.categories = ['Diesel Fuel', 'Driver & Crew', 'Maintenance', 'Tolls & Tax', 'Compliance', 'Overheads', 'Net Margin']
    chart_data.add_series('Cost Distribution', (0.48, 0.14, 0.11, 0.10, 0.05, 0.04, 0.08))
    
    chart_shape = s2.shapes.add_chart(
        XL_CHART_TYPE.DOUGHNUT,
        Inches(1.0), Inches(2.4), Inches(5.6), Inches(3.9),
        chart_data
    )
    chart = chart_shape.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.RIGHT
    chart.legend.font.size = Pt(8.5)
    chart.legend.font.name = FONT_FAMILY

    # Right Container: 3 Key Insights Cards
    add_card(s2, Inches(7.1), Inches(1.8), Inches(5.4), Inches(4.8))
    
    ic1 = add_card(s2, Inches(7.4), Inches(2.1), Inches(4.8), Inches(1.2), bg_color=COLOR_LOSS_BG, border_color=COLOR_LOSS_RED)
    tb_ic1 = s2.shapes.add_textbox(Inches(7.6), Inches(2.2), Inches(4.4), Inches(1.0))
    tf_ic1 = tb_ic1.text_frame
    p_ic1a = tf_ic1.paragraphs[0]
    p_ic1a.text = "DIESEL FUEL REPRESENTS ~48% OF OPERATING EXPENSE"
    p_ic1a.font.name = FONT_FAMILY
    p_ic1a.font.size = Pt(9.5)
    p_ic1a.font.bold = True
    p_ic1a.font.color.rgb = COLOR_LOSS_RED
    p_ic1b = tf_ic1.add_paragraph()
    p_ic1b.text = "Because fuel is the single largest cash outflow (₹1,05,600/truck/mo), even a 6% unmanaged leakage consumes nearly half of the entire fleet's net profit margin."
    p_ic1b.font.name = FONT_FAMILY
    p_ic1b.font.size = Pt(9.5)
    p_ic1b.font.color.rgb = COLOR_TEXT_DARK

    ic2 = add_card(s2, Inches(7.4), Inches(3.45), Inches(4.8), Inches(1.2), bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
    tb_ic2 = s2.shapes.add_textbox(Inches(7.6), Inches(3.55), Inches(4.4), Inches(1.0))
    tf_ic2 = tb_ic2.text_frame
    p_ic2a = tf_ic2.paragraphs[0]
    p_ic2a.text = "THE FRAGILE 8% NET OPERATING PROFIT BUFFER"
    p_ic2a.font.name = FONT_FAMILY
    p_ic2a.font.size = Pt(9.5)
    p_ic2a.font.bold = True
    p_ic2a.font.color.rgb = COLOR_PRIMARY
    p_ic2b = tf_ic2.add_paragraph()
    p_ic2b.text = "Average commercial operators retain only ~8% net profit. Unplanned downtime and detour waste directly subtract from this buffer, turning profitable trips into loss-makers."
    p_ic2b.font.name = FONT_FAMILY
    p_ic2b.font.size = Pt(9.5)
    p_ic2b.font.color.rgb = COLOR_TEXT_DARK

    ic3 = add_card(s2, Inches(7.4), Inches(4.8), Inches(4.8), Inches(1.5), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    tb_ic3 = s2.shapes.add_textbox(Inches(7.6), Inches(4.9), Inches(4.4), Inches(1.3))
    tf_ic3 = tb_ic3.text_frame
    p_ic3a = tf_ic3.paragraphs[0]
    p_ic3a.text = "VAHAN FINANCIAL LEAKAGE IMPACT (50 TRUCKS)"
    p_ic3a.font.name = FONT_FAMILY
    p_ic3a.font.size = Pt(10)
    p_ic3a.font.bold = True
    p_ic3a.font.color.rgb = COLOR_PRIMARY
    p_ic3b = tf_ic3.add_paragraph()
    p_ic3b.text = "• Flagged Monthly Loss: ₹7,53,300 across 50 vehicles\n• 60% Protection Resolution: ₹4,51,980/month\n• Professional Plan Cost: ₹40,000/month\n• Net Bottom-Line Addition: ₹4,11,980/month (₹49,43,760/yr)"
    p_ic3b.font.name = FONT_FAMILY
    p_ic3b.font.size = Pt(9.5)
    p_ic3b.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 3: The Anatomy of Fleet Financial Leakage
    # -------------------------------------------------------------------------
    s3 = add_base_slide()
    add_header(s3, "The Three Core Vectors of Fleet Financial Leakage", "02. Problem Diagnostic", "Every unmonitored commercial vehicle loses money across three predictable, measurable operational drivers.")

    # 3 Large Cards
    card_w = Inches(3.7)
    card_h = Inches(4.4)
    c_y = Inches(1.8)

    # Card 1: Fuel Siphoning
    c1 = add_card(s3, Inches(0.8), c_y, card_w, card_h)
    add_button(s3, Inches(1.1), Inches(2.1), Inches(2.2), Inches(0.32), "VECTOR 01 • 42.1% OF LOSS", bg_color=COLOR_LOSS_BG, text_color=COLOR_LOSS_RED, font_size=8.5, border_color=COLOR_LOSS_RED)
    tb_c1 = s3.shapes.add_textbox(Inches(1.1), Inches(2.6), Inches(3.1), Inches(2.5))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    tf_c1.paragraphs[0].text = "Fuel Theft & Drainage"
    tf_c1.paragraphs[0].font.size = Pt(16)
    tf_c1.paragraphs[0].font.bold = True
    tf_c1.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    
    p = tf_c1.add_paragraph()
    p.space_before = Pt(8)
    p.text = "₹3,16,800 / Month\n(₹38,01,600 / Year)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED

    p = tf_c1.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• 6% unexplained fuel variance\n• Night-halt siphoning\n• Off-book bunk dispensing\n• Missing sensor calibration"
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_MUTED

    btn_drill1 = add_button(s3, Inches(1.1), Inches(5.3), Inches(3.1), Inches(0.45), "Inspect Fuel Leakage  ➔", bg_color=COLOR_PRIMARY, font_size=9.5)

    # Card 2: Unauthorized Detours
    c2 = add_card(s3, Inches(4.8), c_y, card_w, card_h)
    add_button(s3, Inches(5.1), Inches(2.1), Inches(2.2), Inches(0.32), "VECTOR 02 • 34.1% OF LOSS", bg_color=COLOR_LOSS_BG, text_color=COLOR_LOSS_RED, font_size=8.5, border_color=COLOR_LOSS_RED)
    tb_c2 = s3.shapes.add_textbox(Inches(5.1), Inches(2.6), Inches(3.1), Inches(2.5))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    tf_c2.paragraphs[0].text = "Unauthorized Detours"
    tf_c2.paragraphs[0].font.size = Pt(16)
    tf_c2.paragraphs[0].font.bold = True
    tf_c2.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    
    p = tf_c2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "₹2,56,500 / Month\n(₹30,78,000 / Year)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED

    p = tf_c2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• 180 km unapproved running/mo\n• Heavy HCV cost: ₹28.50/km\n• Off-corridor personal trips\n• Unsanctioned bypasses & idling"
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_MUTED

    btn_drill2 = add_button(s3, Inches(5.1), Inches(5.3), Inches(3.1), Inches(0.45), "Inspect Detour Loss  ➔", bg_color=COLOR_PRIMARY, font_size=9.5)

    # Card 3: Breakdown Downtime
    c3 = add_card(s3, Inches(8.8), c_y, card_w, card_h)
    add_button(s3, Inches(9.1), Inches(2.1), Inches(2.2), Inches(0.32), "VECTOR 03 • 23.9% OF LOSS", bg_color=COLOR_LOSS_BG, text_color=COLOR_LOSS_RED, font_size=8.5, border_color=COLOR_LOSS_RED)
    tb_c3 = s3.shapes.add_textbox(Inches(9.1), Inches(2.6), Inches(3.1), Inches(2.5))
    tf_c3 = tb_c3.text_frame
    tf_c3.word_wrap = True
    tf_c3.paragraphs[0].text = "Preventable Downtime"
    tf_c3.paragraphs[0].font.size = Pt(16)
    tf_c3.paragraphs[0].font.bold = True
    tf_c3.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    
    p = tf_c3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "₹1,80,000 / Month\n(₹21,60,000 / Year)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED

    p = tf_c3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• 1.5 days avoidable downtime/mo\n• Lost margin: ₹2,400/truck/day\n• Missed oil/greasing intervals\n• Roadside component failure"
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_MUTED

    btn_drill3 = add_button(s3, Inches(9.1), Inches(5.3), Inches(3.1), Inches(0.45), "Inspect Downtime Loss  ➔", bg_color=COLOR_PRIMARY, font_size=9.5)

    # Bottom Combined Summary Strip
    strip = add_card(s3, Inches(0.8), Inches(6.35), Inches(11.7), Inches(0.65), bg_color=COLOR_CARD_BG, border_color=COLOR_PRIMARY)
    tb_st = s3.shapes.add_textbox(Inches(1.0), Inches(6.45), Inches(11.3), Inches(0.45))
    tf_st = tb_st.text_frame
    p_st = tf_st.paragraphs[0]
    p_st.text = "TOTAL ANNUAL LEAKAGE ACROSS 50 TRUCKS: ₹90,39,600  |  VAHAN 60% VERIFIED NET SAVINGS: ₹54,23,760 / YEAR"
    p_st.alignment = PP_ALIGN.CENTER
    p_st.font.size = Pt(10)
    p_st.font.bold = True
    p_st.font.color.rgb = COLOR_PRIMARY

    # -------------------------------------------------------------------------
    # SLIDE 4: Deep Dive — Fuel Siphoning & Tank Discrepancies
    # -------------------------------------------------------------------------
    s4 = add_base_slide()
    add_header(s4, "Fuel Siphoning & Volumetric Tank Theft Prevention", "03. Leakage Deep Dive • Vector 1", "Stopping the ₹38.01 Lakh annual diesel drain through automated ultrasonic telemetry & sudden-drop algorithms.")

    # Left: The Financial Bleed
    add_card(s4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_s4_l = s4.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    tf_s4_l = tb_s4_l.text_frame
    tf_s4_l.word_wrap = True
    tf_s4_l.paragraphs[0].text = "The Financial Bleed: Fuel Theft Mechanics"
    tf_s4_l.paragraphs[0].font.size = Pt(14)
    tf_s4_l.paragraphs[0].font.bold = True
    tf_s4_l.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s4_l.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Monthly Fuel Spend per Vehicle: ₹1,05,600\n(1,100 Litres diesel @ ₹96/L average highway rate)\n\n" \
             "Estimated Unexplained Fuel Variance: 6.0%\n" \
             "• Loss per Truck: ₹6,336 / month (~66 Litres siphoned)\n" \
             "• Fleet Loss (50 Trucks): ₹3,16,800 / month\n" \
             "• Cumulative Annual Fuel Drain: ₹38,01,600 / year\n\n" \
             "Common Theft Patterns Identified:\n" \
             "1. Night-halt tank drainage while driver sleeps\n" \
             "2. Fuel dispenser meter manipulation at roadside pumps\n" \
             "3. Return line tapping & bypass containers\n" \
             "4. Fictitious fuel receipts during cash reimbursements"
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_MUTED

    # Right: VAHAN Solution Engine
    add_card(s4, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8), bg_color=COLOR_CARD_BG)
    tb_s4_r = s4.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    tf_s4_r = tb_s4_r.text_frame
    tf_s4_r.word_wrap = True
    tf_s4_r.paragraphs[0].text = "VAHAN Automated Fuel Intelligence Engine"
    tf_s4_r.paragraphs[0].font.size = Pt(14)
    tf_s4_r.paragraphs[0].font.bold = True
    tf_s4_r.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s4_r.add_paragraph()
    p.space_before = Pt(10)
    p.text = "1. Ultrasonic & Capacitive Fuel Sensors:\n" \
             "Continuous liquid level sampling accurate to ±1.5% volumetric tank capacity.\n\n" \
             "2. Sudden Level-Drop Detection Rule (backend/routers/fuel_domain.py):\n" \
             "Automated alert triggers when fuel level decreases by >5% within 10 minutes while engine ignition is OFF.\n\n" \
             "3. Geofenced Refuel Reconciliation:\n" \
             "Cross-verifies refuel events against approved bunk geofences, volume dispensed, and vehicle odometer reading.\n\n" \
             "4. Expected vs Actual Mileage Audit:\n" \
             "Computes dynamic km/L efficiency per trip; flags anomalous fuel burn compared to terrain profile."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 5: Deep Dive — Unauthorized Detours & Route Inefficiency
    # -------------------------------------------------------------------------
    s5 = add_base_slide()
    add_header(s5, "Unauthorized Detours & Off-Route Mileage Control", "04. Leakage Deep Dive • Vector 2", "Eliminating unapproved personal running and off-corridor mileage that adds ₹30.78 Lakh in annual operating cost.")

    # Left: Detour Economics
    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_s5_l = s5.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    tf_s5_l = tb_s5_l.text_frame
    tf_s5_l.word_wrap = True
    tf_s5_l.paragraphs[0].text = "The Detour Reality: Unapproved Mileage Waste"
    tf_s5_l.paragraphs[0].font.size = Pt(14)
    tf_s5_l.paragraphs[0].font.bold = True
    tf_s5_l.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s5_l.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Unapproved Extra Distance: 180 km / truck / month\n" \
             "(Represents just ~6 km per day in off-route deviation or unauthorized local running)\n\n" \
             "Heavy Commercial Vehicle Operating Cost: ₹28.50 / km\n" \
             "• Fuel component: ~₹23.50 / km\n" \
             "• Tyre wear & mechanical depreciation: ~₹5.00 / km\n\n" \
             "Fleet Detour Waste (50 Trucks):\n" \
             "• Monthly Waste: 50 × 180 km × ₹28.50 = ₹2,56,500 / month\n" \
             "• Annual Waste: ₹30,78,000 / year\n\n" \
             "Hidden Negative Externalities:\n" \
             "• Delivery SLA penalties and missed transit time windows\n" \
             "• Premature tyre wear and unscheduled brake replacements"
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_MUTED

    # Right: VAHAN Solution
    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    tb_s5_r = s5.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    tf_s5_r = tb_s5_r.text_frame
    tf_s5_r.word_wrap = True
    tf_s5_r.paragraphs[0].text = "VAHAN Route Adherence & Geofencing System"
    tf_s5_r.paragraphs[0].font.size = Pt(14)
    tf_s5_r.paragraphs[0].font.bold = True
    tf_s5_r.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s5_r.add_paragraph()
    p.space_before = Pt(10)
    p.text = "1. Corridor Polygonal Geofences:\n" \
             "Creates a 500-metre operational corridor along approved national highway routes.\n\n" \
             "2. Cross-Track Deviation Alerts (backend/routers/telematics.py):\n" \
             "Instant notifications when a vehicle leaves the designated route without dispatcher authorization.\n\n" \
             "3. Unauthorized Halt & Dwell Time Detection:\n" \
             "Flags stationary halts exceeding 30 minutes outside approved dhabas, weighbridges, and toll plazas.\n\n" \
             "4. Night Travel & Route Curfew Enforcement:\n" \
             "Configurable movement restrictions during high-theft overnight windows (12:00 AM - 4:00 AM)."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 6: Deep Dive — Preventable Breakdown & Fleet Downtime
    # -------------------------------------------------------------------------
    s6 = add_base_slide()
    add_header(s6, "Avoidable Downtime & Unplanned Maintenance Recovery", "05. Leakage Deep Dive • Vector 3", "Transforming costly roadside breakdowns into scheduled preventive care to reclaim ₹21.60 Lakh in annual margin.")

    # Left: Downtime Cost
    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_s6_l = s6.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.2))
    tf_s6_l = tb_s6_l.text_frame
    tf_s6_l.word_wrap = True
    tf_s6_l.paragraphs[0].text = "The Cost of Unplanned Breakdown Downtime"
    tf_s6_l.paragraphs[0].font.size = Pt(14)
    tf_s6_l.paragraphs[0].font.bold = True
    tf_s6_l.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s6_l.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Avoidable Breakdown Days: 1.5 days / truck / month\n" \
             "(Standard metric for unmonitored fleets with reactive repair schedules)\n\n" \
             "Lost Daily Vehicle Contribution Margin: ₹2,400 / day\n" \
             "• Average Daily Gross Revenue: ₹8,000\n" \
             "• Variable trip costs saved (Diesel/Tolls): ₹5,600\n" \
             "• Lost Net Operating Contribution: ₹2,400 / day / truck\n\n" \
             "Fleet Downtime Loss (50 Trucks):\n" \
             "• Monthly Lost Contribution: 50 × 1.5 × ₹2,400 = ₹1,80,000\n" \
             "• Annual Lost Contribution: ₹21,60,000 / year\n\n" \
             "Plus Emergency Towing & Roadside Labor Surcharges (typically 2.5x scheduled workshop rates)."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_MUTED

    # Right: VAHAN Preventive Engine
    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    tb_s6_r = s6.shapes.add_textbox(Inches(7.1), Inches(2.1), Inches(5.1), Inches(4.2))
    tf_s6_r = tb_s6_r.text_frame
    tf_s6_r.word_wrap = True
    tf_s6_r.paragraphs[0].text = "VAHAN Automated Preventive Maintenance Engine"
    tf_s6_r.paragraphs[0].font.size = Pt(14)
    tf_s6_r.paragraphs[0].font.bold = True
    tf_s6_r.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s6_r.add_paragraph()
    p.space_before = Pt(10)
    p.text = "1. Telematics Odometer & Engine-Hour Integration:\n" \
             "Live synchronization of actual rolling odometer directly from GPS telemetry into maintenance schedules.\n\n" \
             "2. Dual-Threshold Service Triggers (backend/routers/vehicle_domain.py):\n" \
             "Automated maintenance work orders at 10,000 km or 90 days (advance alert issued 500 km or 7 days prior).\n\n" \
             "3. Component Lifecycle & Tyre Rotation Tracking:\n" \
             "Individual tread depth monitoring, battery voltage history, and brake lining replacement logs.\n\n" \
             "4. Digital Workshop Job-Card & Spares Reconciliation:\n" \
             "Prevents duplicate billing, verifies parts warranty, and tracks technician turnaround time."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 7: Regulatory Compliance, Driver Documents & KYC Risk
    # -------------------------------------------------------------------------
    s7 = add_base_slide()
    add_header(s7, "Driver e-KYC & Regulatory Compliance Protection", "06. Compliance & Risk Management", "Eliminating cascading statutory penalties, police detentions, and vehicle impoundment through proactive document controls.")

    col_w = Inches(3.7)
    col_h = Inches(4.8)
    
    # Col 1: Statutory Penalties
    c_s7_1 = add_card(s7, Inches(0.8), Inches(1.8), col_w, col_h)
    tb_s7_1 = s7.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s7_1 = tb_s7_1.text_frame
    tf_s7_1.word_wrap = True
    tf_s7_1.paragraphs[0].text = "MV Act 2019 Penalties"
    tf_s7_1.paragraphs[0].font.size = Pt(14)
    tf_s7_1.paragraphs[0].font.bold = True
    tf_s7_1.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    
    p = tf_s7_1.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Commercial Vehicle Fines:\n\n" \
             "• Fitness Certificate Lapse:\n  ₹10,000 per violation\n\n" \
             "• Vehicle Insurance Lapse:\n  ₹4,000 + 3-month imprisonment\n\n" \
             "• National Permit Expiry:\n  ₹10,000 to ₹25,000 fine\n\n" \
             "• Pollution (PUC) Lapsed:\n  ₹10,000 per vehicle\n\n" \
             "• Driver License Suspension:\n  Immediate vehicle impoundment & trip cancellation costs."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Col 2: Digital e-KYC
    c_s7_2 = add_card(s7, Inches(4.8), Inches(1.8), col_w, col_h)
    tb_s7_2 = s7.shapes.add_textbox(Inches(5.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s7_2 = tb_s7_2.text_frame
    tf_s7_2.word_wrap = True
    tf_s7_2.paragraphs[0].text = "Driver e-KYC Verification"
    tf_s7_2.paragraphs[0].font.size = Pt(14)
    tf_s7_2.paragraphs[0].font.bold = True
    tf_s7_2.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s7_2.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Driver Onboarding Queue:\n\n" \
             "• Automated Aadhaar & Driving License OCR extraction\n\n" \
             "• Commercial Heavy Vehicle (TRANS/HGV) endorsement verification\n\n" \
             "• Driver behavioral incident tracking (overspeeding, harsh braking)\n\n" \
             "• Mandatory pre-trip digital safety declarations via mobile app."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Col 3: Proactive Alerts
    c_s7_3 = add_card(s7, Inches(8.8), Inches(1.8), col_w, col_h)
    tb_s7_3 = s7.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s7_3 = tb_s7_3.text_frame
    tf_s7_3.word_wrap = True
    tf_s7_3.paragraphs[0].text = "Proactive Expiry Engine"
    tf_s7_3.paragraphs[0].font.size = Pt(14)
    tf_s7_3.paragraphs[0].font.bold = True
    tf_s7_3.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s7_3.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Standardized Alert Schedules:\n\n" \
             "• 30-Day Advance Warning:\n  Early notification to fleet manager for scheduling renewal tests\n\n" \
             "• 15-Day Urgent Escalation:\n  Daily SMS and dashboard badge for impending document lapses\n\n" \
             "• Automatic Trip Block:\n  Prevents trip dispatch if critical document (Permit/Insurance) is expired."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 8: Hardware Telematics & Connected IoT Architecture
    # -------------------------------------------------------------------------
    s8 = add_base_slide()
    add_header(s8, "Production-Verified Hardware & Telematics Ingestion", "07. IoT Infrastructure", "Multi-protocol tracker support, staging-validated packet processing, and enterprise tenant quarantine security.")

    c_s8_1 = add_card(s8, Inches(0.8), Inches(1.8), col_w, col_h)
    tb_s8_1 = s8.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s8_1 = tb_s8_1.text_frame
    tf_s8_1.word_wrap = True
    tf_s8_1.paragraphs[0].text = "Multi-Protocol Hardware"
    tf_s8_1.paragraphs[0].font.size = Pt(14)
    tf_s8_1.paragraphs[0].font.bold = True
    tf_s8_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s8_1.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Device Compatibility:\n\n" \
             "• AIS-140 Certified GPS Trackers (Indian statutory standard with emergency panic buttons)\n\n" \
             "• Teltonika FMx Series (Heavy-duty CANbus & BLE fuel sensor telemetry)\n\n" \
             "• Concox / GT06 Protocol (Widely deployed cost-effective trackers)\n\n" \
             "Staging Validated via socket harness; field cellular validation active."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s8_2 = add_card(s8, Inches(4.8), Inches(1.8), col_w, col_h)
    tb_s8_2 = s8.shapes.add_textbox(Inches(5.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s8_2 = tb_s8_2.text_frame
    tf_s8_2.word_wrap = True
    tf_s8_2.paragraphs[0].text = "Traccar 6.5 Forwarder"
    tf_s8_2.paragraphs[0].font.size = Pt(14)
    tf_s8_2.paragraphs[0].font.bold = True
    tf_s8_2.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s8_2.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Telematics Ingestion Pipeline:\n\n" \
             "• High-throughput TCP/UDP socket listeners decoding binary protocol packets\n\n" \
             "• HTTP Forwarder with X-Telematics-Secret shared secret authentication\n\n" \
             "• 10-30s commercial update frequency optimized for cellular data conservation\n\n" \
             "• Instant event webhooks for ignition on/off, overspeed, and geofence cross."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s8_3 = add_card(s8, Inches(8.8), Inches(1.8), col_w, col_h)
    tb_s8_3 = s8.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s8_3 = tb_s8_3.text_frame
    tf_s8_3.word_wrap = True
    tf_s8_3.paragraphs[0].text = "Quarantine Security Pool"
    tf_s8_3.paragraphs[0].font.size = Pt(14)
    tf_s8_3.paragraphs[0].font.bold = True
    tf_s8_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s8_3.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Zero Cross-Tenant Leakage:\n\n" \
             "• Unassigned incoming GPS devices routed into isolated quarantine pool\n\n" \
             "• Regular company tenants cannot view, spoof, or claim quarantined assets\n\n" \
             "• Only verified Super-Admins can reassign devices to fleet companies\n\n" \
             "• Full immutable audit logging for all hardware provisioning actions."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 9: Driver Mobile Experience & Operational Workflows
    # -------------------------------------------------------------------------
    s9 = add_base_slide()
    add_header(s9, "Driver Mobile App: Native Flutter & Offline Sync", "08. Driver Operations", "Empowering highway drivers with digital inspections, trip lifecycle tracking, and offline resilience.")

    c_s9_1 = add_card(s9, Inches(0.8), Inches(1.8), col_w, col_h)
    tb_s9_1 = s9.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s9_1 = tb_s9_1.text_frame
    tf_s9_1.word_wrap = True
    tf_s9_1.paragraphs[0].text = "Native Flutter Architecture"
    tf_s9_1.paragraphs[0].font.size = Pt(14)
    tf_s9_1.paragraphs[0].font.bold = True
    tf_s9_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s9_1.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Driver-First Mobile Design:\n\n" \
             "• Built in driver_app/ with clean Flutter cross-platform architecture\n\n" \
             "• Ultra-low RAM & battery consumption designed for budget smartphones\n\n" \
             "• Multi-lingual interface supporting Hindi, English, and regional languages\n\n" \
             "• Single-tap action buttons for pre-trip walkaround inspection checklists."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s9_2 = add_card(s9, Inches(4.8), Inches(1.8), col_w, col_h)
    tb_s9_2 = s9.shapes.add_textbox(Inches(5.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s9_2 = tb_s9_2.text_frame
    tf_s9_2.word_wrap = True
    tf_s9_2.paragraphs[0].text = "Trip Lifecycle & Digital POD"
    tf_s9_2.paragraphs[0].font.size = Pt(14)
    tf_s9_2.paragraphs[0].font.bold = True
    tf_s9_2.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s9_2.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Complete Trip Audit Trail:\n\n" \
             "• Trip Start: Vehicle odometer photograph & fuel level confirmation\n\n" \
             "• Waypoint Check-ins: Automated geofence arrival detection\n\n" \
             "• Digital POD (Proof of Delivery): Mobile camera image capture with timestamp & geostamp\n\n" \
             "• Expense Logging: Instant toll slip and cash fuel voucher uploads."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s9_3 = add_card(s9, Inches(8.8), Inches(1.8), col_w, col_h)
    tb_s9_3 = s9.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s9_3 = tb_s9_3.text_frame
    tf_s9_3.word_wrap = True
    tf_s9_3.paragraphs[0].text = "Offline SQLite Resilience"
    tf_s9_3.paragraphs[0].font.size = Pt(14)
    tf_s9_3.paragraphs[0].font.bold = True
    tf_s9_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s9_3.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Highway Blackspot Continuity:\n\n" \
             "• Local SQLite database caches all trip events during remote cellular drops\n\n" \
             "• Automatic background sync upon network recovery with zero packet loss\n\n" \
             "• SMS Fallback Gateway for emergency panic triggers without data connection\n\n" \
             "• Direct driver authentication linked securely to tenant company profile."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 10: Trip Execution, Geofences & SLA Compliance
    # -------------------------------------------------------------------------
    s10 = add_base_slide()
    add_header(s10, "Trip Management, Geofenced Corridors & SLA Tracking", "09. Operations & SLA Control", "Automated trip state machine, depot geofencing, and route compliance from dispatch to consignee receipt.")

    c_s10_1 = add_card(s10, Inches(0.8), Inches(1.8), col_w, col_h)
    tb_s10_1 = s10.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s10_1 = tb_s10_1.text_frame
    tf_s10_1.word_wrap = True
    tf_s10_1.paragraphs[0].text = "Trip Status Machine"
    tf_s10_1.paragraphs[0].font.size = Pt(14)
    tf_s10_1.paragraphs[0].font.bold = True
    tf_s10_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s10_1.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Strict Lifecycle Transition:\n\n" \
             "1. Draft: Consignment & route defined\n\n" \
             "2. Assigned: Driver & vehicle allocated\n\n" \
             "3. In-Transit: Live GPS corridor tracking\n\n" \
             "4. Arrived: Consignee geofence entry\n\n" \
             "5. Completed: Verified digital POD signed & trip expenses settled."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s10_2 = add_card(s10, Inches(4.8), Inches(1.8), col_w, col_h)
    tb_s10_2 = s10.shapes.add_textbox(Inches(5.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s10_2 = tb_s10_2.text_frame
    tf_s10_2.word_wrap = True
    tf_s10_2.paragraphs[0].text = "Geofenced Milestones"
    tf_s10_2.paragraphs[0].font.size = Pt(14)
    tf_s10_2.paragraphs[0].font.bold = True
    tf_s10_2.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s10_2.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Automated Geofence Events:\n\n" \
             "• Depot Departure: Timestamp logged automatically upon exiting yard\n\n" \
             "• Highway Toll Plazas: Geofenced timestamp logging for audit reconciliation (Direct FASTag API on roadmap)\n\n" \
             "• Delivery Hub Arrival: Customer receives automated arrival notification\n\n" \
             "• Dwell Time Monitoring: Eliminates loading dock turnaround delays."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s10_3 = add_card(s10, Inches(8.8), Inches(1.8), col_w, col_h)
    tb_s10_3 = s10.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.2))
    tf_s10_3 = tb_s10_3.text_frame
    tf_s10_3.word_wrap = True
    tf_s10_3.paragraphs[0].text = "Consignee SLA Reports"
    tf_s10_3.paragraphs[0].font.size = Pt(14)
    tf_s10_3.paragraphs[0].font.bold = True
    tf_s10_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    p = tf_s10_3.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Customer Trust & Transparency:\n\n" \
             "• On-Time In-Full (OTIF) Delivery Scoring\n\n" \
             "• Shareable live tracking links for enterprise shippers\n\n" \
             "• Detailed route replay with recorded halts and average speed profiles\n\n" \
             "• Objective data for defending detention charges against consignees."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 11: Preventive Maintenance & Asset Lifecycle Engine
    # -------------------------------------------------------------------------
    s11 = add_base_slide()
    add_header(s11, "Preventive Maintenance & Workshop Lifecycle Management", "10. Asset Management", "Protecting capital asset longevity through automated interval triggers, tyre wear tracking, and spares management.")

    # 4 Service Cards
    card4_w = Inches(2.7)
    card4_h = Inches(4.8)

    c_s11_1 = add_card(s11, Inches(0.8), Inches(1.8), card4_w, card4_h)
    tb_s11_1 = s11.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(2.3), Inches(4.3))
    tf_s11_1 = tb_s11_1.text_frame
    tf_s11_1.word_wrap = True
    tf_s11_1.paragraphs[0].text = "Minor Service\nIntervals"
    tf_s11_1.paragraphs[0].font.size = Pt(13)
    tf_s11_1.paragraphs[0].font.bold = True
    tf_s11_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s11_1.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Trigger Threshold:\n10,000 km or 90 Days\n\nAdvance Alert:\n500 km or 7 Days prior\n\nScope:\n• Engine oil change\n• Oil & diesel filter swap\n• Chassis greasing\n• Coolant & fluid top-ups\n• Air pressure check"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s11_2 = add_card(s11, Inches(3.8), Inches(1.8), card4_w, card4_h)
    tb_s11_2 = s11.shapes.add_textbox(Inches(4.0), Inches(2.0), Inches(2.3), Inches(4.3))
    tf_s11_2 = tb_s11_2.text_frame
    tf_s11_2.word_wrap = True
    tf_s11_2.paragraphs[0].text = "Major Service\nOverhaul"
    tf_s11_2.paragraphs[0].font.size = Pt(13)
    tf_s11_2.paragraphs[0].font.bold = True
    tf_s11_2.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_s11_2.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Trigger Threshold:\n40,000 km or 365 Days\n\nAdvance Alert:\n1,000 km or 15 Days prior\n\nScope:\n• Transmission oil flush\n• Differential lubrication\n• Brake drum & shoe replacement\n• Suspension bush checks\n• Hub repacking"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s11_3 = add_card(s11, Inches(6.8), Inches(1.8), card4_w, card4_h)
    tb_s11_3 = s11.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(2.3), Inches(4.3))
    tf_s11_3 = tb_s11_3.text_frame
    tf_s11_3.word_wrap = True
    tf_s11_3.paragraphs[0].text = "Tyre & Battery\nLifecycle"
    tf_s11_3.paragraphs[0].font.size = Pt(13)
    tf_s11_3.paragraphs[0].font.bold = True
    tf_s11_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s11_3.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Axle Position Tracking:\n• Steer, drive & trailer tyre rotation schedules\n• Tread depth inspection logs\n• Retreading history\n\nBattery Health:\n• Alternator voltage monitoring via GPS telemetry\n• Low battery alerts"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    c_s11_4 = add_card(s11, Inches(9.8), Inches(1.8), card4_w, card4_h)
    tb_s11_4 = s11.shapes.add_textbox(Inches(10.0), Inches(2.0), Inches(2.3), Inches(4.3))
    tf_s11_4 = tb_s11_4.text_frame
    tf_s11_4.word_wrap = True
    tf_s11_4.paragraphs[0].text = "Statutory Document\nRenewals"
    tf_s11_4.paragraphs[0].font.size = Pt(13)
    tf_s11_4.paragraphs[0].font.bold = True
    tf_s11_4.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_s11_4.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Standard Expiry Timelines:\n• 30-Day early notice\n• 15-Day urgent alert\n\nMonitored Documents:\n• Commercial Vehicle Fitness\n• Comprehensive Insurance\n• National Goods Permit\n• Road Tax receipts\n• Pollution Under Control"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 12: Fleet Financial Exposure & Multi-Cohort Matrix
    # -------------------------------------------------------------------------
    s12 = add_base_slide()
    add_header(s12, "Fleet Financial Exposure & ROI Scaling: 10 to 100 Trucks", "11. Scaled Financial Impact", "Empirical financial model proving consistent 9x to 11x net return on investment across commercial fleet tiers.")

    # Top Half: Native Grouped Bar / Column Chart
    add_card(s12, Inches(0.8), Inches(1.8), Inches(11.7), Inches(2.5))
    tb_c_title = s12.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(8.0), Inches(0.3))
    tb_c_title.text_frame.paragraphs[0].text = "Annual Financial Impact: Unmanaged Loss vs Net Savings vs VAHAN Cost (₹ in Lakhs)"
    tb_c_title.text_frame.paragraphs[0].font.size = Pt(11)
    tb_c_title.text_frame.paragraphs[0].font.bold = True
    tb_c_title.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    chart_data_c = CategoryChartData()
    chart_data_c.categories = ['10 Trucks', '25 Trucks', '50 Trucks', '100 Trucks']
    chart_data_c.add_series('Annual Loss Exposure (₹L)', (18.08, 45.20, 90.40, 180.79))
    chart_data_c.add_series('Net Owner Profit Gain (₹L)', (9.89, 24.72, 49.44, 96.48))
    chart_data_c.add_series('VAHAN Annual Cost (₹L)', (0.96, 2.40, 4.80, 12.00))

    col_chart_shape = s12.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(1.0), Inches(2.2), Inches(11.3), Inches(2.0),
        chart_data_c
    )
    col_chart = col_chart_shape.chart
    col_chart.has_legend = True
    col_chart.legend.position = XL_LEGEND_POSITION.TOP
    col_chart.legend.font.size = Pt(8.5)
    col_chart.legend.font.name = FONT_FAMILY

    # Bottom Half: 4 Cohort Cards
    c_y_cards = Inches(4.5)
    c_w_cohort = Inches(2.7)
    c_h_cohort = Inches(2.3)

    cohorts_data = [
        ("10 TRUCKS (Small)", "Professional Plan", "₹1,50,660 / mo", "₹8,000 / mo", "₹82,396 / mo", "₹9,88,752 / yr", "11.3x ROI", Inches(0.8)),
        ("25 TRUCKS (Growing)", "Professional Plan", "₹3,76,650 / mo", "₹20,000 / mo", "₹2,05,990 / mo", "₹24,71,880 / yr", "11.3x ROI", Inches(3.8)),
        ("50 TRUCKS (Benchmark)", "Professional Plan", "₹7,53,300 / mo", "₹40,000 / mo", "₹4,11,980 / mo", "₹49,43,760 / yr", "11.3x ROI", Inches(6.8)),
        ("100 TRUCKS (Enterprise)", "Enterprise Plan", "₹15,06,600 / mo", "₹1,00,000 / mo", "₹8,03,960 / mo", "₹96,47,520 / yr", "9.0x ROI", Inches(9.8))
    ]

    for c_title, c_plan, c_loss, c_cost, c_net_mo, c_net_yr, c_roi, c_left in cohorts_data:
        is_bm = "50 TRUCKS" in c_title
        c_bg = COLOR_SOFT_GREEN if is_bm else COLOR_CARD_BG
        c_border = COLOR_PRIMARY if is_bm else COLOR_CARD_BORDER
        add_card(s12, c_left, c_y_cards, c_w_cohort, c_h_cohort, bg_color=c_bg, border_color=c_border)
        
        tb = s12.shapes.add_textbox(c_left + Inches(0.15), c_y_cards + Inches(0.12), c_w_cohort - Inches(0.3), c_h_cohort - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = c_title
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY if is_bm else COLOR_TEXT_DARK

        p = tf.add_paragraph()
        p.text = f"Exposure: {c_loss}\nVAHAN: {c_cost} ({c_plan})"
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_MUTED

        p = tf.add_paragraph()
        p.space_before = Pt(4)
        p.text = f"Net Profit: {c_net_mo}\nAnnual Gain: {c_net_yr}"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY

        p = tf.add_paragraph()
        p.space_before = Pt(3)
        p.text = f"Return Multiple: {c_roi}"
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 13: Feature-by-Feature Value & Capability Matrix
    # -------------------------------------------------------------------------
    s13 = add_base_slide()
    add_header(s13, "Platform Capability & Module Drilldown Matrix", "12. Functional Overview", "Click any module card below to drill down into operational mechanisms, algorithms, and financial leakage vectors.")

    # 6 Interactive Cards arranged in 2 rows of 3
    card_m_w = Inches(3.7)
    card_m_h = Inches(2.2)

    modules = [
        ("01. Fuel Intelligence & Anti-Siphon", "Sudden-drop anomaly rules, volumetric liquid level sampling, geofenced bunk reconciliation.", "Slide 4", Inches(0.8), Inches(1.9)),
        ("02. Corridor GPS & Route Adherence", "Dynamic corridor geofences, unapproved halt alerts, cross-track error detection >500m.", "Slide 5", Inches(4.8), Inches(1.9)),
        ("03. Preventive Maintenance Engine", "Rolling odometer sync, 10,000 km / 90-day alert triggers, tyre rotation and battery monitoring.", "Slide 6", Inches(8.8), Inches(1.9)),
        ("04. Driver e-KYC & Compliance Vault", "Aadhaar/DL verification, 30/15-day document expiry warning engine, MV Act fine prevention.", "Slide 7", Inches(0.8), Inches(4.4)),
        ("05. IoT Hardware & Telematics Gateway", "AIS-140, Teltonika, Concox multi-protocol ingestion, Traccar 6.5 forwarder, quarantine pool.", "Slide 8", Inches(4.8), Inches(4.4)),
        ("06. Driver Mobile App & Offline SQLite", "Flutter native app, pre-trip vehicle checklists, digital POD image capture, zero-data offline cache.", "Slide 9", Inches(8.8), Inches(4.4))
    ]

    mod_buttons = []
    for m_title, m_desc, m_target, m_x, m_y in modules:
        c_shp = add_card(s13, m_x, m_y, card_m_w, card_m_h)
        tb = s13.shapes.add_textbox(m_x + Inches(0.2), m_y + Inches(0.15), card_m_w - Inches(0.4), card_m_h - Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = m_title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY

        p = tf.add_paragraph()
        p.space_before = Pt(6)
        p.text = m_desc
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_MUTED

        btn = add_button(s13, m_x + Inches(0.2), m_y + Inches(1.65), Inches(1.8), Inches(0.38), f"Drilldown ➔", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=9)
        mod_buttons.append((btn, m_target))

    # -------------------------------------------------------------------------
    # SLIDE 14: Implementation & Fleet Onboarding Roadmap
    # -------------------------------------------------------------------------
    s14 = add_base_slide()
    add_header(s14, "Rapid Fleet Deployment: 30-Day Go-Live Roadmap", "13. Deployment Strategy", "Zero operational downtime rollout designed for commercial transport operations across four structured weekly phases.")

    w_ph = Inches(2.7)
    h_ph = Inches(4.8)

    phases = [
        ("WEEK 01", "Master Data &\nTenant Setup", "Setup & Config", "• Fleet master data ingestion (vehicles, drivers, sub-fleets)\n\n• Company tenancy setup and role-based permissions\n\n• Driver document upload and automated e-KYC validation\n\n• Corridor geofences and depot mapping.", Inches(0.8), COLOR_CARD_BG, COLOR_TEXT_DARK),
        ("WEEK 02", "Hardware &\nSensor Calibration", "Hardware Rollout", "• AIS-140 GPS tracker installation on pilot vehicles\n\n• Fuel tank immersion sensor calibration (empty-to-full curve)\n\n• Socket listener integration and secret validation\n\n• Quarantine pool verification and device assignment.", Inches(3.8), COLOR_CARD_BG, COLOR_TEXT_DARK),
        ("WEEK 03", "Driver App &\nStaff Training", "Field Training", "• Driver mobile application installation (driver_app/)\n\n• Walkaround digital inspection checklist orientation\n\n• Offline trip logging and POD capture training\n\n• Fleet manager alert notification workflow drills.", Inches(6.8), COLOR_CARD_BG, COLOR_TEXT_DARK),
        ("WEEK 04", "Full Go-Live &\nP&L Dashboard", "Go-Live Operations", "• Fleet-wide live tracking activation\n\n• Fuel siphoning and route detour automated alerts live\n\n• Preventive maintenance odometer schedules enabled\n\n• First weekly executive P&L financial leakage audit report.", Inches(9.8), COLOR_SOFT_GREEN, COLOR_PRIMARY)
    ]

    for p_week, p_title, p_badge, p_desc, p_x, p_bg, p_col in phases:
        add_card(s14, p_x, Inches(1.8), w_ph, h_ph, bg_color=p_bg)
        add_button(s14, p_x + Inches(0.2), Inches(2.0), Inches(1.2), Inches(0.3), p_week, bg_color=COLOR_PRIMARY, font_size=9)
        
        tb = s14.shapes.add_textbox(p_x + Inches(0.2), Inches(2.45), w_ph - Inches(0.4), h_ph - Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = p_col

        p = tf.add_paragraph()
        p.space_before = Pt(8)
        p.text = p_desc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 15: Interactive Financial Scenario Simulator
    # -------------------------------------------------------------------------
    s15 = add_base_slide()
    add_header(s15, "Interactive Fleet Financial Scenario Simulator", "14. ROI Calculator", "Simulate your fleet parameters below to evaluate custom monthly leakage exposure and net profit recovery.")

    # Left: Parameter Input Console Card
    add_card(s15, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_calc_in = s15.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.3))
    tf_calc_in = tb_calc_in.text_frame
    tf_calc_in.word_wrap = True
    
    p = tf_calc_in.paragraphs[0]
    p.text = "Fleet Operational Parameter Inputs"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK

    p = tf_calc_in.add_paragraph()
    p.space_before = Pt(8)
    p.text = "1. Active Fleet Size:  50 Commercial Trucks\n" \
             "2. Monthly Fuel Spend:  ₹1,05,600 / truck (1,100 L @ ₹96/L)\n" \
             "3. Estimated Fuel Drain:  6.0% (₹6,336/truck/mo)\n" \
             "4. Unapproved Detours:  180 km / truck / month\n" \
             "5. Vehicle Operating Cost:  ₹28.50 / km (HCV rate)\n" \
             "6. Avoidable Downtime:  1.5 days / truck / month\n" \
             "7. Lost Daily Contribution:  ₹2,400 / truck / day\n" \
             "8. Target Resolution Rate:  60.0% of identified leakage\n" \
             "9. Selected Plan Tier:  Professional (₹800/truck/mo)"
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_MUTED

    # Action Buttons inside simulator
    btn_calc_run = add_button(s15, Inches(1.1), Inches(5.8), Inches(2.3), Inches(0.5), "Calculate ROI  ➔", bg_color=COLOR_PRIMARY, font_size=10)
    btn_calc_reset = add_button(s15, Inches(3.6), Inches(5.8), Inches(2.0), Inches(0.5), "Reset Baseline", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=10)

    # Right: Dynamic Projected Output Cards
    add_card(s15, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    tb_calc_out = s15.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(0.4))
    tb_calc_out.text_frame.paragraphs[0].text = "Projected Financial Outcomes (50 Trucks)"
    tb_calc_out.text_frame.paragraphs[0].font.size = Pt(13)
    tb_calc_out.text_frame.paragraphs[0].font.bold = True
    tb_calc_out.text_frame.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    # Metric Row 1: Leakage Exposure
    add_card(s15, Inches(7.1), Inches(2.5), Inches(5.1), Inches(1.0), bg_color=COLOR_LOSS_BG, border_color=COLOR_LOSS_RED)
    tb_m1 = s15.shapes.add_textbox(Inches(7.3), Inches(2.55), Inches(4.7), Inches(0.9))
    tf_m1 = tb_m1.text_frame
    tf_m1.paragraphs[0].text = "UNMANAGED MONTHLY FINANCIAL LEAKAGE"
    tf_m1.paragraphs[0].font.size = Pt(8.5)
    tf_m1.paragraphs[0].font.bold = True
    tf_m1.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_m1.add_paragraph()
    p.text = "₹7,53,300 / Month  (₹90,39,600 / Year)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK

    # Metric Row 2: VAHAN 60% Protection
    add_card(s15, Inches(7.1), Inches(3.65), Inches(5.1), Inches(1.0), bg_color=COLOR_CARD_BG, border_color=COLOR_PRIMARY)
    tb_m2 = s15.shapes.add_textbox(Inches(7.3), Inches(3.70), Inches(4.7), Inches(0.9))
    tf_m2 = tb_m2.text_frame
    tf_m2.paragraphs[0].text = "VERIFIED 60% PROFIT PROTECTION RECOVERY"
    tf_m2.paragraphs[0].font.size = Pt(8.5)
    tf_m2.paragraphs[0].font.bold = True
    tf_m2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_m2.add_paragraph()
    p.text = "₹4,51,980 / Month  (₹54,23,760 / Year)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK

    # Metric Row 3: Net Cash Flow Gain & ROI Multiple
    add_card(s15, Inches(7.1), Inches(4.8), Inches(5.1), Inches(1.5), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    tb_m3 = s15.shapes.add_textbox(Inches(7.3), Inches(4.85), Inches(4.7), Inches(1.4))
    tf_m3 = tb_m3.text_frame
    tf_m3.paragraphs[0].text = "NET CASH FLOW ADDED TO OWNER BOTTOM LINE"
    tf_m3.paragraphs[0].font.size = Pt(9)
    tf_m3.paragraphs[0].font.bold = True
    tf_m3.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_m3.add_paragraph()
    p.text = "₹4,11,980 / Month  (₹49,43,760 / Year)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_m3.add_paragraph()
    p.text = "Return Multiple: 11.3x ROI  |  Payback Period: 2.7 Days"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_DARK

    # -------------------------------------------------------------------------
    # SLIDE 16: Transparent Tiered Commercial Pricing Plans
    # -------------------------------------------------------------------------
    s16 = add_base_slide()
    add_header(s16, "Transparent Subscription Pricing for Every Fleet Scale", "15. Commercial Plans", "Predictable per-vehicle investment with no hidden integration fees or lock-in contracts.")

    w_plan = Inches(3.7)
    h_plan = Inches(4.3)
    y_plan = Inches(1.8)

    # Plan 1: Starter
    add_card(s16, Inches(0.8), y_plan, w_plan, h_plan)
    add_button(s16, Inches(1.1), Inches(2.0), Inches(1.4), Inches(0.3), "STARTER", bg_color=COLOR_CARD_BORDER, text_color=COLOR_TEXT_DARK, font_size=8.5)
    tb_p1 = s16.shapes.add_textbox(Inches(1.1), Inches(2.4), Inches(3.1), Inches(3.4))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True
    tf_p1.paragraphs[0].text = "₹500"
    tf_p1.paragraphs[0].font.size = Pt(24)
    tf_p1.paragraphs[0].font.bold = True
    tf_p1.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_p1.add_paragraph()
    p.text = "per truck / month"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_MUTED
    p = tf_p1.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Core Fleet Visibility:\n\n" \
             "• Real-time GPS vehicle tracking\n" \
             "• Daily trip start/end logging\n" \
             "• Driver document vault & expiry alerts\n" \
             "• Standard speed and geofence alerts\n" \
             "• Basic mobile driver application"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    btn_p1 = add_button(s16, Inches(1.1), Inches(5.4), Inches(3.1), Inches(0.45), "Select Starter Plan", bg_color=COLOR_CARD_BG, text_color=COLOR_PRIMARY, font_size=9.5, border_color=COLOR_PRIMARY)

    # Plan 2: Professional (Recommended)
    add_card(s16, Inches(4.8), y_plan, w_plan, h_plan, bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    add_button(s16, Inches(5.1), Inches(2.0), Inches(2.2), Inches(0.3), "PROFESSIONAL (FLAGSHIP)", bg_color=COLOR_PRIMARY, text_color=RGBColor(255, 255, 255), font_size=8.5)
    tb_p2 = s16.shapes.add_textbox(Inches(5.1), Inches(2.4), Inches(3.1), Inches(3.4))
    tf_p2 = tb_p2.text_frame
    tf_p2.word_wrap = True
    tf_p2.paragraphs[0].text = "₹800"
    tf_p2.paragraphs[0].font.size = Pt(24)
    tf_p2.paragraphs[0].font.bold = True
    tf_p2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_p2.add_paragraph()
    p.text = "per truck / month (Recommended)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_PRIMARY_DARK
    p = tf_p2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Full Financial Protection:\n\n" \
             "• Everything in Starter Plan, plus:\n" \
             "• Fuel siphoning anomaly detection (>5%)\n" \
             "• Corridor detour alerts (>500m)\n" \
             "• Preventive maintenance engine (10k km)\n" \
             "• Fleet P&L financial leakage analytics"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    btn_p2 = add_button(s16, Inches(5.1), Inches(5.4), Inches(3.1), Inches(0.45), "Choose Professional Plan  ➔", bg_color=COLOR_PRIMARY, font_size=9.5)

    # Plan 3: Enterprise
    add_card(s16, Inches(8.8), y_plan, w_plan, h_plan)
    add_button(s16, Inches(9.1), Inches(2.0), Inches(1.6), Inches(0.3), "ENTERPRISE", bg_color=COLOR_CARD_BORDER, text_color=COLOR_TEXT_DARK, font_size=8.5)
    tb_p3 = s16.shapes.add_textbox(Inches(9.1), Inches(2.4), Inches(3.1), Inches(3.4))
    tf_p3 = tb_p3.text_frame
    tf_p3.word_wrap = True
    tf_p3.paragraphs[0].text = "₹1,000"
    tf_p3.paragraphs[0].font.size = Pt(24)
    tf_p3.paragraphs[0].font.bold = True
    tf_p3.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_p3.add_paragraph()
    p.text = "per truck / month (100+ Fleets)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_MUTED
    p = tf_p3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Enterprise Scalability:\n\n" \
             "• Everything in Professional Plan, plus:\n" \
             "• Custom ERP & SAP webhooks integration\n" \
             "• Dedicated Technical Account Manager\n" \
             "• Multi-branch depot sub-tenancy\n" \
             "• 99.9% uptime SLA & priority support"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    btn_p3 = add_button(s16, Inches(9.1), Inches(5.4), Inches(3.1), Inches(0.45), "Contact Enterprise Sales", bg_color=COLOR_CARD_BG, text_color=COLOR_PRIMARY, font_size=9.5, border_color=COLOR_PRIMARY)

    # Bottom Hardware Add-On Strip
    hw_strip = add_card(s16, Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.7), bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
    tb_hw = s16.shapes.add_textbox(Inches(1.0), Inches(6.35), Inches(11.3), Inches(0.55))
    tf_hw = tb_hw.text_frame
    p_hw = tf_hw.paragraphs[0]
    p_hw.text = "CERTIFIED HARDWARE ADD-ONS (Optional One-Time): AIS-140 GPS Tracker: ₹3,499 - ₹4,999  |  Digital Ultrasonic Fuel Sensor: ₹1,500  (Fleet owners may also bring existing Traccar-compatible hardware)"
    p_hw.alignment = PP_ALIGN.CENTER
    p_hw.font.size = Pt(9)
    p_hw.font.bold = True
    p_hw.font.color.rgb = COLOR_TEXT_MUTED

    # -------------------------------------------------------------------------
    # SLIDE 17: Enterprise Architecture, Security & Tenancy Isolation
    # -------------------------------------------------------------------------
    s17 = add_base_slide()
    add_header(s17, "Enterprise Security, Quarantine Isolation & Platform Trust", "16. Security & Infrastructure", "Multi-tenant architecture ensuring complete data privacy, cryptographic webhook security, and SOC2 readiness.")

    w_s17 = Inches(2.7)
    h_s17 = Inches(4.8)

    trust_pillars = [
        ("TENANT ISOLATION", "Company Tenancy Enforced", "• Strict company_id row-level isolation across all PostgreSQL queries\n\n• Fleet owners and dispatchers can never view another company's vehicles or trips\n\n• Role-based access control (Super-Admin, Company-Admin, Dispatcher, Driver).", Inches(0.8), COLOR_CARD_BG),
        ("QUARANTINE SECURITY", "Hardware Isolation Pool", "• Unmapped or rogue GPS devices are automatically jailed in quarantine\n\n• Zero unauthorized telemetry injection into customer dashboards\n\n• Super-admin reassignment required before hardware can join a fleet.", Inches(3.8), COLOR_CARD_BG),
        ("WEBHOOK SECURITY", "Cryptographic Signatures", "• High-performance Traccar 6.5 forwarder secured with X-Telematics-Secret\n\n• HMAC authentication for all external webhook dispatches\n\n• Prevents telemetry spoofing, replay attacks, and unauthorized location falsification.", Inches(6.8), COLOR_CARD_BG),
        ("AUDIT COMPLIANCE", "Immutable Audit Records", "• Detailed audit trail for every asset reassignment and configuration override\n\n• Timestamped driver e-KYC approvals and digital POD uploads\n\n• PostgreSQL database backup with automated point-in-time recovery.", Inches(9.8), COLOR_SOFT_GREEN)
    ]

    for t_badge, t_title, t_desc, t_x, t_bg in trust_pillars:
        add_card(s17, t_x, Inches(1.8), w_s17, h_s17, bg_color=t_bg)
        add_button(s17, t_x + Inches(0.2), Inches(2.0), Inches(2.1), Inches(0.3), t_badge, bg_color=COLOR_PRIMARY, font_size=8)
        
        tb = s17.shapes.add_textbox(t_x + Inches(0.2), Inches(2.45), w_s17 - Inches(0.4), h_s17 - Inches(0.8))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = t_title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DARK

        p = tf.add_paragraph()
        p.space_before = Pt(8)
        p.text = t_desc
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------------------
    # SLIDE 18: Transform Your Fleet Operations — Next Steps & Call to Action
    # -------------------------------------------------------------------------
    s18 = add_base_slide()
    add_header(s18, "Protect Your Fleet Profit Margin Starting Today", "17. Next Steps & Pilot Program", "Experience the measurable financial impact of VAHAN with our 30-day risk-free benchmark diagnostic pilot.")

    # Left Container: 30-Day Pilot Offer Card
    add_card(s18, Inches(0.8), Inches(1.8), Inches(6.4), Inches(4.8), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    add_button(s18, Inches(1.2), Inches(2.1), Inches(2.6), Inches(0.35), "NO-RISK PROOF-OF-CONCEPT", bg_color=COLOR_PRIMARY, font_size=9)

    tb_s18_l = s18.shapes.add_textbox(Inches(1.2), Inches(2.6), Inches(5.6), Inches(3.6))
    tf_s18_l = tb_s18_l.text_frame
    tf_s18_l.word_wrap = True
    tf_s18_l.paragraphs[0].text = "30-Day Benchmark Pilot (5 Trucks)"
    tf_s18_l.paragraphs[0].font.size = Pt(20)
    tf_s18_l.paragraphs[0].font.bold = True
    tf_s18_l.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s18_l.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Deploy VAHAN on 5 commercial trucks to audit real-world leakage:\n\n" \
             "✓ Complete hardware provisioning & fuel sensor calibration included\n" \
             "✓ Baseline leakage diagnostic report delivered within 14 days\n" \
             "✓ Zero long-term contract commitment during pilot evaluation\n" \
             "✓ 100% money-back satisfaction guarantee if leakage isn't identified."
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_TEXT_DARK

    btn_book_pilot = add_button(s18, Inches(1.2), Inches(5.4), Inches(2.8), Inches(0.55), "Book 5-Truck Pilot  ➔", bg_color=COLOR_PRIMARY, font_size=11)
    btn_calc_again = add_button(s18, Inches(4.2), Inches(5.4), Inches(2.2), Inches(0.55), "Recalculate ROI", bg_color=COLOR_CARD_BG, text_color=COLOR_PRIMARY, font_size=10, border_color=COLOR_PRIMARY)

    # Right Container: Contact & Audit Reports
    add_card(s18, Inches(7.5), Inches(1.8), Inches(5.0), Inches(4.8))
    tb_s18_r = s18.shapes.add_textbox(Inches(7.8), Inches(2.1), Inches(4.4), Inches(4.2))
    tf_s18_r = tb_s18_r.text_frame
    tf_s18_r.word_wrap = True
    tf_s18_r.paragraphs[0].text = "Commercial Contact & Consultation"
    tf_s18_r.paragraphs[0].font.size = Pt(14)
    tf_s18_r.paragraphs[0].font.bold = True
    tf_s18_r.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    p = tf_s18_r.add_paragraph()
    p.space_before = Pt(10)
    p.text = "Commercial Operations Team:\n" \
             "Email: pilot@vahanfleet.io\n" \
             "Direct Sales: +91 98765 43210\n" \
             "Web Portal: https://vahanfleet.io\n\n" \
             "Accompanying Audit Workbooks:\n" \
             "• VAHAN_Financial_Audit.xlsx (Claim Verification Register)\n" \
             "• VAHAN_Scenario_Assumptions.xlsx (Dynamic Excel Model)\n" \
             "• VAHAN_Presentation_QA_Report.pdf (Full Technical QA)\n\n" \
             "FastAPI Backend & Flutter Repository:\n" \
             "All endpoints, database models, and mobile screens verified against production source code."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_MUTED

    btn_view_audit = add_button(s18, Inches(7.8), Inches(5.4), Inches(4.4), Inches(0.55), "Review Financial Audit Matrix  ➔", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=10)

    # -------------------------------------------------------------------------
    # GLOBAL NAVIGATION SYSTEM: SECTION JUMP PILLS & BOTTOM ACTION BUTTONS
    # -------------------------------------------------------------------------
    # Target slides index:
    # Overview -> Slide 2 (index 1)
    # Leakage -> Slide 3 (index 2)
    # Operations -> Slide 8 (index 7)
    # Impact -> Slide 12 (index 11)
    # Calculator -> Slide 15 (index 14)
    # Pricing -> Slide 16 (index 15)

    nav_sections = [
        ("Overview", slides[1]),
        ("Leakage", slides[2]),
        ("Operations", slides[7]),
        ("Impact", slides[11]),
        ("Calculator", slides[14]),
        ("Pricing", slides[15])
    ]

    pill_w = Inches(1.15)
    pill_h = Inches(0.32)
    start_x = Inches(5.5)
    y_nav = Inches(0.42)

    for idx, slide in enumerate(slides):
        if idx == 0:
            # Slide 1 action links
            btn_s1_story.click_action.target_slide = slides[1] # Jump to Slide 2
            btn_s1_calc.click_action.target_slide = slides[14] # Jump to Slide 15
            continue

        # Top Section Jump Pills
        for p_idx, (sec_name, sec_target) in enumerate(nav_sections):
            px = start_x + (p_idx * (pill_w + Inches(0.08)))
            
            # Determine active state
            is_active = (
                (p_idx == 0 and idx == 1) or
                (p_idx == 1 and 2 <= idx <= 6) or
                (p_idx == 2 and 7 <= idx <= 10) or
                (p_idx == 3 and 11 <= idx <= 13) or
                (p_idx == 4 and idx == 14) or
                (p_idx == 5 and idx >= 15)
            )

            p_bg = COLOR_PRIMARY if is_active else COLOR_NAV_BG
            p_txt = RGBColor(255, 255, 255) if is_active else COLOR_TEXT_MUTED
            
            pill = add_button(slide, px, y_nav, pill_w, pill_h, sec_name, bg_color=p_bg, text_color=p_txt, font_size=8.5, bold=is_active)
            pill.click_action.target_slide = sec_target

        # Bottom Bar Controls
        # 🏠 Home button (links to Slide 1)
        btn_home = add_button(slide, Inches(0.8), Inches(6.9), Inches(1.1), Inches(0.35), "🏠 Home", bg_color=COLOR_CARD_BG, text_color=COLOR_TEXT_DARK, font_size=8.5, border_color=COLOR_CARD_BORDER)
        btn_home.click_action.target_slide = slides[0]

        # ◀ Prev button
        if idx > 0:
            btn_prev = add_button(slide, Inches(2.0), Inches(6.9), Inches(1.0), Inches(0.35), "◀ Prev", bg_color=COLOR_CARD_BG, text_color=COLOR_TEXT_DARK, font_size=8.5, border_color=COLOR_CARD_BORDER)
            btn_prev.click_action.target_slide = slides[idx - 1]

        # ▶ Next button
        if idx < len(slides) - 1:
            btn_next = add_button(slide, Inches(3.1), Inches(6.9), Inches(1.0), Inches(0.35), "Next ▶", bg_color=COLOR_CARD_BG, text_color=COLOR_TEXT_DARK, font_size=8.5, border_color=COLOR_CARD_BORDER)
            btn_next.click_action.target_slide = slides[idx + 1]

        # Slide Number Badge (Bottom Right)
        slide_num_box = slide.shapes.add_textbox(Inches(11.3), Inches(6.9), Inches(1.2), Inches(0.35))
        tf_num = slide_num_box.text_frame
        p_num = tf_num.paragraphs[0]
        p_num.text = f"{idx + 1:02d} / {len(slides):02d}"
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.font.name = FONT_FAMILY
        p_num.font.size = Pt(9.5)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_TEXT_MUTED

    # Setup specific slide hyperlinks for feature cards:
    # Slide 3 drilldowns:
    btn_drill1.click_action.target_slide = slides[3] # Slide 4 (Fuel)
    btn_drill2.click_action.target_slide = slides[4] # Slide 5 (Route)
    btn_drill3.click_action.target_slide = slides[5] # Slide 6 (Downtime)

    # Slide 13 module drilldown buttons:
    for btn, target_name in mod_buttons:
        if target_name == "Slide 4":
            btn.click_action.target_slide = slides[3]
        elif target_name == "Slide 5":
            btn.click_action.target_slide = slides[4]
        elif target_name == "Slide 6":
            btn.click_action.target_slide = slides[5]
        elif target_name == "Slide 7":
            btn.click_action.target_slide = slides[6]
        elif target_name == "Slide 8":
            btn.click_action.target_slide = slides[7]
        elif target_name == "Slide 9":
            btn.click_action.target_slide = slides[8]

    # Slide 15 simulator buttons:
    btn_calc_run.click_action.target_slide = slides[11] # Jump to Cohort Matrix
    btn_calc_reset.click_action.target_slide = slides[14] # Reset / refresh

    # Slide 16 pricing plan buttons:
    btn_p1.click_action.target_slide = slides[17] # Jump to CTA
    btn_p2.click_action.target_slide = slides[17] # Jump to CTA
    btn_p3.click_action.target_slide = slides[17] # Jump to CTA

    # Slide 18 closing buttons:
    btn_book_pilot.click_action.target_slide = slides[15] # Jump to Pricing
    btn_calc_again.click_action.target_slide = slides[14] # Jump to Calculator
    btn_view_audit.click_action.target_slide = slides[11] # Jump to Cohort Impact

    output_path = "VAHAN_Interactive_Presentation.pptx"
    prs.save(output_path)
    print(f"Successfully generated {output_path} with {len(slides)} slides and full interactive navigation.")

if __name__ == "__main__":
    create_presentation()
