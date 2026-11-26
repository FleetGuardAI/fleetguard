import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from PIL import Image, ImageOps

# -----------------------------------------------------------------------------
# PALETTE SPECIFICATION (VAHAN LIGHT THEME)
# -----------------------------------------------------------------------------
COLOR_BG = RGBColor(247, 250, 248)          # #F7FAF8 Clean Light Canvas
COLOR_CARD_BG = RGBColor(255, 255, 255)     # #FFFFFF Pure White
COLOR_CARD_BORDER = RGBColor(225, 234, 228) # #E1EAE4 Crisp Card Border
COLOR_PRIMARY = RGBColor(37, 132, 91)       # #25845B Emerald Green
COLOR_PRIMARY_DARK = RGBColor(27, 94, 32)   # #1B5E20 Deep Forest Green
COLOR_SOFT_GREEN = RGBColor(228, 243, 234)  # #E4F3EA Mint Highlight
COLOR_TEXT_DARK = RGBColor(36, 53, 45)      # #24352D Deep Slate Text
COLOR_TEXT_MUTED = RGBColor(100, 115, 107)  # #64736B Slate Muted
COLOR_LOSS_RED = RGBColor(217, 119, 112)    # #D97770 Coral Red (Loss Accent)
COLOR_LOSS_BG = RGBColor(254, 242, 242)     # Soft Pink Container
COLOR_NAV_BG = RGBColor(238, 244, 240)      # Nav pill default
COLOR_NAV_BORDER = RGBColor(210, 224, 216)  # Nav border

FONT_FAMILY = "Segoe UI"
WORKSPACE = os.getcwd()
IMAGE_DIR = os.path.join(WORKSPACE, "assets", "images")
CACHE_DIR = os.path.join(WORKSPACE, "assets", "cropped_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def fit_and_cache_image(filename, target_width_in, target_height_in):
    """Crops and resizes an image to exact dimensions without distortion."""
    src_path = os.path.join(IMAGE_DIR, filename)
    if not os.path.exists(src_path):
        alt_path = os.path.join(WORKSPACE, filename)
        if os.path.exists(alt_path):
            src_path = alt_path
        else:
            print(f"[WARN] Image not found: {filename}")
            return None

    target_w_px = max(50, int(target_width_in * 150))
    target_h_px = max(50, int(target_height_in * 150))
    cache_name = f"{os.path.splitext(filename)[0]}_{target_w_px}x{target_h_px}.jpg"
    cache_path = os.path.join(CACHE_DIR, cache_name)

    if not os.path.exists(cache_path):
        with Image.open(src_path) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            fitted = ImageOps.fit(im, (target_w_px, target_h_px), Image.Resampling.LANCZOS)
            fitted.save(cache_path, "JPEG", quality=92)

    return cache_path

def build_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    slides = []

    def add_base_slide():
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.fill.background()
        slides.append(slide)
        return slide

    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.2)
        else:
            card.line.fill.background()
        return card

    def add_framed_photo(slide, filename, left, top, width, height):
        card = add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
        inset = Inches(0.06)
        img_w = width - (inset * 2)
        img_h = height - (inset * 2)
        img_cached = fit_and_cache_image(filename, img_w / Inches(1), img_h / Inches(1))
        if img_cached:
            pic = slide.shapes.add_picture(img_cached, left + inset, top + inset, img_w, img_h)
            return pic
        return card

    def add_header(slide, title_text, category_text, subtitle_text):
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

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(8.5), Inches(0.55))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(19)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TEXT_DARK

        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.28), Inches(9.5), Inches(0.38))
        tf_s = sub_box.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = 0
        p_s = tf_s.paragraphs[0]
        p_s.text = subtitle_text
        p_s.font.name = FONT_FAMILY
        p_s.font.size = Pt(10.5)
        p_s.font.color.rgb = COLOR_TEXT_MUTED

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

    # =========================================================================
    # SLIDE 01: HERO COVER (Photo-Rich Split Layout)
    # =========================================================================
    s1 = add_base_slide()
    add_card(s1, Inches(0.8), Inches(1.0), Inches(6.4), Inches(5.5))
    add_button(s1, Inches(1.2), Inches(1.35), Inches(2.8), Inches(0.34), "ENTERPRISE FLEET INTELLIGENCE", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=9, bold=True)
    
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.85), Inches(5.6), Inches(2.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "VAHAN"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_PRIMARY

    p2 = tf.add_paragraph()
    p2.text = "Connected Fleet Management &\nFinancial Protection Platform"
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(21)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_TEXT_DARK

    p3 = tf.add_paragraph()
    p3.space_before = Pt(10)
    p3.text = "Transforming unmanaged fuel drainage, unauthorized detours, and preventable breakdowns into verified, measurable bottom-line profit."
    p3.font.name = FONT_FAMILY
    p3.font.size = Pt(11)
    p3.font.color.rgb = COLOR_TEXT_MUTED

    btn_s1_story = add_button(s1, Inches(1.2), Inches(5.35), Inches(2.5), Inches(0.52), "Explore Profit Story  ➔", bg_color=COLOR_PRIMARY, font_size=10.5)
    btn_s1_calc = add_button(s1, Inches(3.9), Inches(5.35), Inches(2.2), Inches(0.52), "ROI Calculator", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=10.5)

    add_framed_photo(s1, "hero_truck_highway.jpg", Inches(7.5), Inches(1.0), Inches(5.0), Inches(3.4))
    
    add_card(s1, Inches(7.5), Inches(4.6), Inches(5.0), Inches(1.9), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    tb_s1_f = s1.shapes.add_textbox(Inches(7.8), Inches(4.75), Inches(4.4), Inches(1.6))
    tf_s1_f = tb_s1_f.text_frame
    tf_s1_f.word_wrap = True
    p = tf_s1_f.paragraphs[0]
    p.text = "50-TRUCK FLEET FINANCIAL IMPACT"
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    p = tf_s1_f.add_paragraph()
    p.text = "₹7,53,300 Monthly Leakage Exposure"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK

    p = tf_s1_f.add_paragraph()
    p.space_before = Pt(4)
    p.text = "• 60% Verified Protection: ₹54,23,760 / year\n• Net Bottom-Line Gain: ₹49,43,760 / year\n• Return on Investment: 11.3x Multiple"
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 02: P&L STRUCTURE (Photo + Re-engineered Horizontal Bar Chart)
    # =========================================================================
    s2 = add_base_slide()
    add_header(s2, "Fleet Operating P&L Structure & Margin Exposure", "01. Executive Overview", "Commercial transport operates on razor-thin margins where unmonitored operational waste directly wipes out profit.")

    add_framed_photo(s2, "fleet_depot_yard.jpg", Inches(0.8), Inches(1.8), Inches(3.8), Inches(2.4))
    
    add_card(s2, Inches(0.8), Inches(4.35), Inches(3.8), Inches(2.25), bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
    tb_s2_l = s2.shapes.add_textbox(Inches(1.0), Inches(4.45), Inches(3.4), Inches(2.0))
    tf_s2_l = tb_s2_l.text_frame
    tf_s2_l.word_wrap = True
    p = tf_s2_l.paragraphs[0]
    p.text = "DIESEL PROFIT VULNERABILITY"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED
    p = tf_s2_l.add_paragraph()
    p.space_before = Pt(4)
    p.text = "Diesel represents ~48% of total operating expenses (₹1,05,600/truck/mo). An unmanaged 6% leakage consumes half of the entire fleet's 8% net profit margin."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_s2_l.add_paragraph()
    p.space_before = Pt(4)
    p.text = "Illustrative Fleet Model — Calibrate with Client P&L."
    p.font.size = Pt(8)
    p.font.italic = True
    p.font.color.rgb = COLOR_TEXT_MUTED

    add_card(s2, Inches(4.8), Inches(1.8), Inches(4.6), Inches(4.8))
    tb_c_title = s2.shapes.add_textbox(Inches(5.0), Inches(1.95), Inches(4.2), Inches(0.35))
    tb_c_title.text_frame.paragraphs[0].text = "Fleet Operating Cost Distribution (%)"
    tb_c_title.text_frame.paragraphs[0].font.size = Pt(11)
    tb_c_title.text_frame.paragraphs[0].font.bold = True
    tb_c_title.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    chart_data_s2 = CategoryChartData()
    chart_data_s2.categories = [
        'Overhead 4%',
        'Tax & PUC 5%',
        'Net Margin 8%',
        'Tolls 10%',
        'Maint 11%',
        'Crew 14%',
        'Diesel 48%'
    ]
    chart_data_s2.add_series('Operating Cost', (0.04, 0.05, 0.08, 0.10, 0.11, 0.14, 0.48))
    
    chart_shape_s2 = s2.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED,
        Inches(4.9), Inches(2.35), Inches(4.4), Inches(4.1),
        chart_data_s2
    )
    chart_s2 = chart_shape_s2.chart
    chart_s2.has_title = False
    chart_s2.has_legend = False
    
    cat_axis_s2 = chart_s2.category_axis
    cat_axis_s2.tick_labels.font.size = Pt(8.5)
    cat_axis_s2.tick_labels.font.name = FONT_FAMILY
    
    val_axis_s2 = chart_s2.value_axis
    val_axis_s2.tick_labels.font.size = Pt(8.5)
    val_axis_s2.tick_labels.font.name = FONT_FAMILY
    val_axis_s2.tick_labels.number_format = '0%'
    val_axis_s2.minimum_scale = 0.0
    val_axis_s2.maximum_scale = 0.50
    val_axis_s2.major_unit = 0.10

    add_card(s2, Inches(9.6), Inches(1.8), Inches(2.9), Inches(2.3), bg_color=COLOR_LOSS_BG, border_color=COLOR_LOSS_RED)
    tb_s2_r1 = s2.shapes.add_textbox(Inches(9.8), Inches(1.95), Inches(2.5), Inches(2.0))
    tf_s2_r1 = tb_s2_r1.text_frame
    tf_s2_r1.word_wrap = True
    tf_s2_r1.paragraphs[0].text = "MONTHLY LEAKAGE EXPOSURE"
    tf_s2_r1.paragraphs[0].font.size = Pt(8.5)
    tf_s2_r1.paragraphs[0].font.bold = True
    tf_s2_r1.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_s2_r1.add_paragraph()
    p.text = "₹7,53,300"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_s2_r1.add_paragraph()
    p.text = "• Fuel: ₹3,16,800/mo\n• Detours: ₹2,56,500/mo\n• Downtime: ₹1,80,000/mo\nAnnual Loss: ₹90,39,600"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_MUTED

    add_card(s2, Inches(9.6), Inches(4.3), Inches(2.9), Inches(2.3), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    tb_s2_r2 = s2.shapes.add_textbox(Inches(9.8), Inches(4.45), Inches(2.5), Inches(2.0))
    tf_s2_r2 = tb_s2_r2.text_frame
    tf_s2_r2.word_wrap = True
    tf_s2_r2.paragraphs[0].text = "60% PROTECTED RECOVERY"
    tf_s2_r2.paragraphs[0].font.size = Pt(8.5)
    tf_s2_r2.paragraphs[0].font.bold = True
    tf_s2_r2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s2_r2.add_paragraph()
    p.text = "₹4,51,980"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_s2_r2.add_paragraph()
    p.text = "• VAHAN Cost: ₹40,000/mo\n• Net Profit: ₹4,11,980/mo\n• Annual Gain: ₹49.44 Lakh\n• ROI: 11.3x Multiplier"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 03: THREE PILLARS (3 Photos + 3 Feature Cards)
    # =========================================================================
    s3 = add_base_slide()
    add_header(s3, "The Three Core Vectors of Fleet Financial Leakage", "02. Problem Diagnostic", "Every unmonitored commercial vehicle loses money across three predictable, measurable operational drivers.")

    card_w = Inches(3.7)
    card_h = Inches(4.4)
    c_y = Inches(1.8)

    add_card(s3, Inches(0.8), c_y, card_w, card_h)
    add_framed_photo(s3, "fuel_nozzle_dispense.jpg", Inches(1.0), Inches(2.0), Inches(3.3), Inches(1.5))
    tb_c1 = s3.shapes.add_textbox(Inches(1.0), Inches(3.6), Inches(3.3), Inches(1.9))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True
    tf_c1.paragraphs[0].text = "VECTOR 01: FUEL THEFT (42.1%)"
    tf_c1.paragraphs[0].font.size = Pt(9)
    tf_c1.paragraphs[0].font.bold = True
    tf_c1.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_c1.add_paragraph()
    p.text = "₹3,16,800 / Month"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_c1.add_paragraph()
    p.text = "• 6% unexplained fuel variance\n• Night-halt tank drainage\n• Bunk dispenser tampering\nAnnual Drain: ₹38,01,600"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_MUTED
    btn_drill1 = add_button(s3, Inches(1.0), Inches(5.65), Inches(3.3), Inches(0.42), "Inspect Fuel Leakage  ➔", bg_color=COLOR_PRIMARY, font_size=9)

    add_card(s3, Inches(4.8), c_y, card_w, card_h)
    add_framed_photo(s3, "highway_route_corridor.jpg", Inches(5.0), Inches(2.0), Inches(3.3), Inches(1.5))
    tb_c2 = s3.shapes.add_textbox(Inches(5.0), Inches(3.6), Inches(3.3), Inches(1.9))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True
    tf_c2.paragraphs[0].text = "VECTOR 02: ROUTE DETOURS (34.1%)"
    tf_c2.paragraphs[0].font.size = Pt(9)
    tf_c2.paragraphs[0].font.bold = True
    tf_c2.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_c2.add_paragraph()
    p.text = "₹2,56,500 / Month"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_c2.add_paragraph()
    p.text = "• 180 km unapproved running/mo\n• HCV running rate: ₹28.50/km\n• Off-corridor personal trips\nAnnual Drain: ₹30,78,000"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_MUTED
    btn_drill2 = add_button(s3, Inches(5.0), Inches(5.65), Inches(3.3), Inches(0.42), "Inspect Detour Loss  ➔", bg_color=COLOR_PRIMARY, font_size=9)

    add_card(s3, Inches(8.8), c_y, card_w, card_h)
    add_framed_photo(s3, "workshop_truck_service.jpg", Inches(9.0), Inches(2.0), Inches(3.3), Inches(1.5))
    tb_c3 = s3.shapes.add_textbox(Inches(9.0), Inches(3.6), Inches(3.3), Inches(1.9))
    tf_c3 = tb_c3.text_frame
    tf_c3.word_wrap = True
    tf_c3.paragraphs[0].text = "VECTOR 03: BREAKDOWN DOWNTIME (23.9%)"
    tf_c3.paragraphs[0].font.size = Pt(9)
    tf_c3.paragraphs[0].font.bold = True
    tf_c3.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_c3.add_paragraph()
    p.text = "₹1,80,000 / Month"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_c3.add_paragraph()
    p.text = "• 1.5 days avoidable downtime/mo\n• Daily margin: ₹2,400/truck\n• Missed oil/greasing intervals\nAnnual Drain: ₹21,60,000"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_MUTED
    btn_drill3 = add_button(s3, Inches(9.0), Inches(5.65), Inches(3.3), Inches(0.42), "Inspect Downtime Loss  ➔", bg_color=COLOR_PRIMARY, font_size=9)

    add_card(s3, Inches(0.8), Inches(6.35), Inches(11.7), Inches(0.55), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    tb_st = s3.shapes.add_textbox(Inches(1.0), Inches(6.42), Inches(11.3), Inches(0.4))
    tf_st = tb_st.text_frame
    p_st = tf_st.paragraphs[0]
    p_st.text = "TOTAL ANNUAL LEAKAGE ACROSS 50 TRUCKS: ₹90,39,600  |  VAHAN 60% RECOVERED PROFIT: ₹54,23,760 / YEAR (11.3x ROI)"
    p_st.alignment = PP_ALIGN.CENTER
    p_st.font.size = Pt(9.5)
    p_st.font.bold = True
    p_st.font.color.rgb = COLOR_PRIMARY

    # =========================================================================
    # SLIDE 04: FUEL DISCREPANCIES (Photo + Re-engineered Column Chart)
    # =========================================================================
    s4 = add_base_slide()
    add_header(s4, "Fuel Siphoning & Volumetric Tank Theft Prevention", "03. Leakage Deep Dive • Vector 1", "Stopping the ₹38.01 Lakh annual diesel drain through automated ultrasonic telemetry & sudden-drop algorithms.")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(4.8), Inches(4.8))
    add_framed_photo(s4, "fuel_nozzle_dispense.jpg", Inches(1.0), Inches(2.0), Inches(4.4), Inches(2.0))
    
    tb_s4_l = s4.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(4.4), Inches(2.3))
    tf_s4_l = tb_s4_l.text_frame
    tf_s4_l.word_wrap = True
    p = tf_s4_l.paragraphs[0]
    p.text = "THE DIESEL THEFT EQUATION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED
    p = tf_s4_l.add_paragraph()
    p.text = "• Fuel Spend: ₹1,05,600 / truck / month (1,100 L @ ₹96/L)\n• Unexplained Loss: 6.0% (~66 Litres / truck / mo)\n• Loss per Truck: ₹6,336 / month\n• 50-Truck Fleet Loss: ₹3,16,800 / mo (₹38,01,600 / yr)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s4, Inches(5.8), Inches(1.8), Inches(6.7), Inches(4.8))
    tb_c_s4 = s4.shapes.add_textbox(Inches(6.0), Inches(1.95), Inches(6.3), Inches(0.35))
    tb_c_s4.text_frame.paragraphs[0].text = "Monthly Unmanaged Fuel Siphoning Drain across Fleet Sizes (₹ in Lakhs)"
    tb_c_s4.text_frame.paragraphs[0].font.size = Pt(11)
    tb_c_s4.text_frame.paragraphs[0].font.bold = True
    tb_c_s4.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    chart_data_s4 = CategoryChartData()
    chart_data_s4.categories = ['10 Trucks', '25 Trucks', '50 Trucks (Baseline)', '100 Trucks']
    chart_data_s4.add_series('Monthly Fuel Loss (₹L)', (0.63, 1.58, 3.17, 6.34))

    col_chart_shape_s4 = s4.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(6.0), Inches(2.35), Inches(6.3), Inches(2.2),
        chart_data_s4
    )
    chart_s4 = col_chart_shape_s4.chart
    chart_s4.has_title = False
    chart_s4.has_legend = False
    chart_s4.value_axis.minimum_scale = 0.0
    chart_s4.value_axis.maximum_scale = 8.0
    chart_s4.value_axis.major_unit = 2.0
    chart_s4.category_axis.tick_labels.font.size = Pt(9)
    chart_s4.value_axis.tick_labels.font.size = Pt(8.5)

    tb_s4_r = s4.shapes.add_textbox(Inches(6.0), Inches(4.7), Inches(6.3), Inches(1.8))
    tf_s4_r = tb_s4_r.text_frame
    tf_s4_r.word_wrap = True
    p = tf_s4_r.paragraphs[0]
    p.text = "VAHAN AUTOMATED FUEL PROTECTION ENGINE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p = tf_s4_r.add_paragraph()
    p.text = "1. Ultrasonic & Capacitive Sensors: Real-time sampling accurate to ±1.5% volumetric capacity.\n" \
             "2. Sudden-Drop Detection (>5% drop in 10 min while engine is OFF triggers instant SMS alert).\n" \
             "3. Geofenced Refuel Reconciliation: Cross-verifies bunk location, volume filled & odometer delta."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 05: ROUTE DETOURS (Commercial Truck Photo + Detour Cost Chart)
    # =========================================================================
    s5 = add_base_slide()
    add_header(s5, "Unauthorized Detours & Off-Route Mileage Control", "04. Leakage Deep Dive • Vector 2", "Eliminating unapproved personal running and off-corridor mileage that adds ₹30.78 Lakh in annual operating cost.")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(4.8), Inches(4.8))
    add_framed_photo(s5, "indian_commercial_truck.jpg", Inches(1.0), Inches(2.0), Inches(4.4), Inches(2.0))
    
    tb_s5_l = s5.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(4.4), Inches(2.3))
    tf_s5_l = tb_s5_l.text_frame
    tf_s5_l.word_wrap = True
    p = tf_s5_l.paragraphs[0]
    p.text = "THE UNAPPROVED MILEAGE COST"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED
    p = tf_s5_l.add_paragraph()
    p.text = "• Unapproved Distance: 180 km / truck / month (~6 km/day)\n• Operating Cost: ₹28.50 / km (Fuel ₹23.50 + Wear ₹5.00)\n• Detour Waste per Truck: ₹5,130 / month\n• 50-Truck Fleet Waste: ₹2,56,500 / mo (₹30,78,000 / yr)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s5, Inches(5.8), Inches(1.8), Inches(6.7), Inches(4.8))
    tb_c_s5 = s5.shapes.add_textbox(Inches(6.0), Inches(1.95), Inches(6.3), Inches(0.35))
    tb_c_s5.text_frame.paragraphs[0].text = "Monthly Fleet Detour Waste by Unapproved Mileage Tier (50 Trucks)"
    tb_c_s5.text_frame.paragraphs[0].font.size = Pt(11)
    tb_c_s5.text_frame.paragraphs[0].font.bold = True
    tb_c_s5.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    chart_data_s5 = CategoryChartData()
    chart_data_s5.categories = ['100 km/mo', '180 km (Baseline)', '250 km/mo', '350 km/mo']
    chart_data_s5.add_series('Monthly Fleet Waste (₹L)', (1.43, 2.57, 3.56, 4.99))

    col_chart_shape_s5 = s5.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(6.0), Inches(2.35), Inches(6.3), Inches(2.2),
        chart_data_s5
    )
    chart_s5 = col_chart_shape_s5.chart
    chart_s5.has_title = False
    chart_s5.has_legend = False
    chart_s5.value_axis.minimum_scale = 0.0
    chart_s5.value_axis.maximum_scale = 6.0
    chart_s5.value_axis.major_unit = 1.5
    chart_s5.category_axis.tick_labels.font.size = Pt(9)
    chart_s5.value_axis.tick_labels.font.size = Pt(8.5)

    tb_s5_r = s5.shapes.add_textbox(Inches(6.0), Inches(4.7), Inches(6.3), Inches(1.8))
    tf_s5_r = tb_s5_r.text_frame
    tf_s5_r.word_wrap = True
    p = tf_s5_r.paragraphs[0]
    p.text = "VAHAN CORRIDOR & GEOFENCE ENFORCEMENT"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p = tf_s5_r.add_paragraph()
    p.text = "1. Polygonal Highway Corridors: Creates 500m operational corridor along authorized transit route.\n" \
             "2. Cross-Track Error Detection: Immediate notification when a truck deviates >500m off-route.\n" \
             "3. Unauthorized Halt Alerts: Flags stationary halts >30 min outside verified dhabas & toll plazas."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 06: DOWNTIME LOSS (Photo + Downtime Loss Chart)
    # =========================================================================
    s6 = add_base_slide()
    add_header(s6, "Avoidable Downtime & Unplanned Maintenance Recovery", "05. Leakage Deep Dive • Vector 3", "Transforming costly roadside breakdowns into scheduled preventive care to reclaim ₹21.60 Lakh in annual margin.")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(4.8), Inches(4.8))
    add_framed_photo(s6, "mechanic_engine_repair.jpg", Inches(1.0), Inches(2.0), Inches(4.4), Inches(2.0))
    
    tb_s6_l = s6.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(4.4), Inches(2.3))
    tf_s6_l = tb_s6_l.text_frame
    tf_s6_l.word_wrap = True
    p = tf_s6_l.paragraphs[0]
    p.text = "THE COST OF ROAD BREAKDOWNS"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_LOSS_RED
    p = tf_s6_l.add_paragraph()
    p.text = "• Avoidable Breakdown Days: 1.5 days / truck / month\n• Daily Vehicle Contribution Margin: ₹2,400 / day\n• Loss per Truck: ₹3,600 / month\n• 50-Truck Fleet Loss: ₹1,80,000 / mo (₹21,60,000 / yr)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s6, Inches(5.8), Inches(1.8), Inches(6.7), Inches(4.8))
    tb_c_s6 = s6.shapes.add_textbox(Inches(6.0), Inches(1.95), Inches(6.3), Inches(0.35))
    tb_c_s6.text_frame.paragraphs[0].text = "Annual Fleet Lost Contribution Margin by Breakdown Days (₹ Lakhs)"
    tb_c_s6.text_frame.paragraphs[0].font.size = Pt(11)
    tb_c_s6.text_frame.paragraphs[0].font.bold = True
    tb_c_s6.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    chart_data_s6 = CategoryChartData()
    chart_data_s6.categories = ['0.5 Days/mo', '1.0 Days/mo', '1.5 Days (Baseline)', '2.0 Days/mo', '2.5 Days/mo']
    chart_data_s6.add_series('Annual Lost Margin (₹L)', (7.20, 14.40, 21.60, 28.80, 36.00))

    col_chart_shape_s6 = s6.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(6.0), Inches(2.35), Inches(6.3), Inches(2.2),
        chart_data_s6
    )
    chart_s6 = col_chart_shape_s6.chart
    chart_s6.has_title = False
    chart_s6.has_legend = False
    chart_s6.value_axis.minimum_scale = 0.0
    chart_s6.value_axis.maximum_scale = 40.0
    chart_s6.value_axis.major_unit = 10.0
    chart_s6.category_axis.tick_labels.font.size = Pt(9)
    chart_s6.value_axis.tick_labels.font.size = Pt(8.5)

    tb_s6_r = s6.shapes.add_textbox(Inches(6.0), Inches(4.7), Inches(6.3), Inches(1.8))
    tf_s6_r = tb_s6_r.text_frame
    tf_s6_r.word_wrap = True
    p = tf_s6_r.paragraphs[0]
    p.text = "VAHAN PREVENTIVE MAINTENANCE ENGINE"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p = tf_s6_r.add_paragraph()
    p.text = "1. Rolling Odometer Sync: Actual distance logged directly from GPS into service schedules.\n" \
             "2. Dual Service Thresholds: Automated alerts at 10,000 km or 90 days (500 km / 7-day warning).\n" \
             "3. Workshop Accountability: Digital job-cards prevent duplicate part billings & track repair turnarounds."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 07: COMPLIANCE & KYC (Photo + 3 Columns)
    # =========================================================================
    s7 = add_base_slide()
    add_header(s7, "Driver e-KYC & Regulatory Compliance Protection", "06. Compliance & Risk Management", "Eliminating cascading statutory penalties, police detentions, and vehicle impoundment through proactive document controls.")

    col_w = Inches(3.7)
    col_h = Inches(4.8)

    add_card(s7, Inches(0.8), Inches(1.8), col_w, col_h)
    add_framed_photo(s7, "driver_document_kyc.jpg", Inches(1.0), Inches(2.0), Inches(3.3), Inches(1.9))
    tb_s7_1 = s7.shapes.add_textbox(Inches(1.0), Inches(4.05), Inches(3.3), Inches(2.4))
    tf_s7_1 = tb_s7_1.text_frame
    tf_s7_1.word_wrap = True
    tf_s7_1.paragraphs[0].text = "STATUTORY PENALTIES (MV ACT)"
    tf_s7_1.paragraphs[0].font.size = Pt(9.5)
    tf_s7_1.paragraphs[0].font.bold = True
    tf_s7_1.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_s7_1.add_paragraph()
    p.text = "• Fitness Lapse: ₹10,000 fine\n• Insurance Lapse: ₹4,000 + 3mo liability\n• National Permit: ₹10,000 to ₹25,000\n• Pollution (PUC): ₹10,000 per truck\n• DL Expiry: Immediate impoundment"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s7, Inches(4.8), Inches(1.8), col_w, col_h)
    tb_s7_2 = s7.shapes.add_textbox(Inches(5.0), Inches(2.1), Inches(3.3), Inches(4.3))
    tf_s7_2 = tb_s7_2.text_frame
    tf_s7_2.word_wrap = True
    tf_s7_2.paragraphs[0].text = "DIGITAL DRIVER e-KYC QUEUE"
    tf_s7_2.paragraphs[0].font.size = Pt(12)
    tf_s7_2.paragraphs[0].font.bold = True
    tf_s7_2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s7_2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• Automated OCR extraction of Aadhaar and Commercial Driving License (DL)\n\n" \
             "• Heavy Commercial Vehicle (TRANS) badge endorsement verification\n\n" \
             "• Driver behavioral incident tracking (overspeeding, harsh braking, night driving)\n\n" \
             "• Pre-trip safety declarations submitted via driver mobile app."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s7, Inches(8.8), Inches(1.8), col_w, col_h)
    tb_s7_3 = s7.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.3))
    tf_s7_3 = tb_s7_3.text_frame
    tf_s7_3.word_wrap = True
    tf_s7_3.paragraphs[0].text = "PROACTIVE RENEWAL ENGINE"
    tf_s7_3.paragraphs[0].font.size = Pt(12)
    tf_s7_3.paragraphs[0].font.bold = True
    tf_s7_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s7_3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• 30-Day Advance Notice: Early alert to fleet manager to schedule renewal inspections\n\n" \
             "• 15-Day Urgent Notice: Daily SMS and dashboard escalation badge\n\n" \
             "• Automated Dispatch Lock: Prevents trip creation if vehicle permit or insurance is expired\n\n" \
             "• Digital Document Vault: Central repository for all vehicle and driver compliance certificates."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 08: HARDWARE & TELEMATICS (Photo + 3 Pillars)
    # =========================================================================
    s8 = add_base_slide()
    add_header(s8, "Production-Verified Hardware & Telematics Ingestion", "07. IoT Infrastructure", "Multi-protocol device ingestion, isolation, and automated telemetry processing.")

    add_card(s8, Inches(0.8), Inches(1.8), col_w, col_h)
    add_framed_photo(s8, "telematics_gps_hardware.jpg", Inches(1.0), Inches(2.0), Inches(3.3), Inches(1.9))
    tb_s8_1 = s8.shapes.add_textbox(Inches(1.0), Inches(4.05), Inches(3.3), Inches(2.4))
    tf_s8_1 = tb_s8_1.text_frame
    tf_s8_1.word_wrap = True
    tf_s8_1.paragraphs[0].text = "MULTI-PROTOCOL HARDWARE"
    tf_s8_1.paragraphs[0].font.size = Pt(9.5)
    tf_s8_1.paragraphs[0].font.bold = True
    tf_s8_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s8_1.add_paragraph()
    p.text = "• AIS-140 Statutory GPS Trackers\n• Teltonika FMx CANbus & BLE sensors\n• Concox / GT06 protocol trackers\n• Staging-validated via socket harness;\non-road cellular SIM validation active."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s8, Inches(4.8), Inches(1.8), col_w, col_h)
    tb_s8_2 = s8.shapes.add_textbox(Inches(5.0), Inches(2.1), Inches(3.3), Inches(4.3))
    tf_s8_2 = tb_s8_2.text_frame
    tf_s8_2.word_wrap = True
    tf_s8_2.paragraphs[0].text = "TRACCAR 6.5 INGESTION"
    tf_s8_2.paragraphs[0].font.size = Pt(12)
    tf_s8_2.paragraphs[0].font.bold = True
    tf_s8_2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s8_2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• High-throughput TCP/UDP socket listeners decoding binary protocol packets\n\n" \
             "• HTTP Forwarder secured with X-Telematics-Secret HMAC authentication\n\n" \
             "• 10-30s commercial sampling cycle optimized for cellular data conservation\n\n" \
             "• Instant event webhooks for ignition on/off, speed triggers, and geofences."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s8, Inches(8.8), Inches(1.8), col_w, col_h)
    tb_s8_3 = s8.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.3))
    tf_s8_3 = tb_s8_3.text_frame
    tf_s8_3.word_wrap = True
    tf_s8_3.paragraphs[0].text = "QUARANTINE SECURITY POOL"
    tf_s8_3.paragraphs[0].font.size = Pt(12)
    tf_s8_3.paragraphs[0].font.bold = True
    tf_s8_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s8_3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• Unassigned GPS devices routed into isolated quarantine pool\n\n" \
             "• Regular company tenants cannot view, spoof, or claim unassigned hardware\n\n" \
             "• Super-admin approval required to allocate devices to fleet companies\n\n" \
             "• Full immutable audit logging for all hardware provisioning actions."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 09: DRIVER MOBILE APP (Cabin Steering Photo + Smartphone App Photo)
    # =========================================================================
    s9 = add_base_slide()
    add_header(s9, "Driver Mobile App: Native Flutter & Offline Sync", "08. Driver Operations", "Empowering highway drivers with digital inspections, trip lifecycle tracking, and offline resilience.")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(3.7), Inches(4.8))
    add_framed_photo(s9, "driver_steering_cabin.jpg", Inches(1.0), Inches(2.0), Inches(3.3), Inches(2.0))
    tb_s9_1 = s9.shapes.add_textbox(Inches(1.0), Inches(4.1), Inches(3.3), Inches(2.4))
    tf_s9_1 = tb_s9_1.text_frame
    tf_s9_1.word_wrap = True
    tf_s9_1.paragraphs[0].text = "DRIVER-FIRST DESIGN"
    tf_s9_1.paragraphs[0].font.size = Pt(10)
    tf_s9_1.paragraphs[0].font.bold = True
    tf_s9_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s9_1.add_paragraph()
    p.text = "• Built in driver_app/ with clean Flutter framework\n• Low RAM consumption for budget Android phones\n• Multi-lingual support (Hindi & English)\n• Single-tap vehicle inspection checklist"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s9, Inches(4.8), Inches(1.8), Inches(3.7), Inches(4.8))
    add_framed_photo(s9, "driver_smartphone_use.jpg", Inches(5.0), Inches(2.0), Inches(3.3), Inches(2.0))
    tb_s9_2 = s9.shapes.add_textbox(Inches(5.0), Inches(4.1), Inches(3.3), Inches(2.4))
    tf_s9_2 = tb_s9_2.text_frame
    tf_s9_2.word_wrap = True
    tf_s9_2.paragraphs[0].text = "FIELD MOBILE WORKFLOWS"
    tf_s9_2.paragraphs[0].font.size = Pt(10)
    tf_s9_2.paragraphs[0].font.bold = True
    tf_s9_2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s9_2.add_paragraph()
    p.text = "• Digital Pre-Trip Checklist: Walkaround inspection\n• Mobile Camera Proof of Delivery (POD) uploads\n• Expense logging for highway tolls & fuel vouchers\n• Instant dispatch push notifications & emergency SOS"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s9, Inches(8.8), Inches(1.8), Inches(3.7), Inches(4.8))
    tb_s9_3 = s9.shapes.add_textbox(Inches(9.0), Inches(2.1), Inches(3.3), Inches(4.3))
    tf_s9_3 = tb_s9_3.text_frame
    tf_s9_3.word_wrap = True
    tf_s9_3.paragraphs[0].text = "OFFLINE SQLITE RESILIENCE"
    tf_s9_3.paragraphs[0].font.size = Pt(12)
    tf_s9_3.paragraphs[0].font.bold = True
    tf_s9_3.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s9_3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "• Highway Blackspot Continuity: Local SQLite database caches all trip events during remote cellular drops.\n\n" \
             "• Automatic Background Sync: Uploads cached telematics and expense slips immediately upon network recovery.\n\n" \
             "• Digital Proof of Delivery: Camera capture with embedded timestamp and GPS coordinate tag.\n\n" \
             "• SMS Gateway Fallback: Critical SOS panic alerts transmit via GSM SMS if data packet fails."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 10: TRIP MANAGEMENT (Photo + Lifecycle Machine)
    # =========================================================================
    s10 = add_base_slide()
    add_header(s10, "Trip Management, Geofenced Corridors & SLA Tracking", "09. Operations & SLA Control", "Automated trip state machine, depot geofencing, and route compliance from dispatch to consignee receipt.")

    # Left: Large Framed Warehouse Photo & Milestones
    add_card(s10, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    add_framed_photo(s10, "logistics_warehouse_dock.jpg", Inches(1.0), Inches(2.0), Inches(5.2), Inches(2.3))
    tb_s10_l = s10.shapes.add_textbox(Inches(1.0), Inches(4.4), Inches(5.2), Inches(2.1))
    tf_s10_l = tb_s10_l.text_frame
    tf_s10_l.word_wrap = True
    p = tf_s10_l.paragraphs[0]
    p.text = "GEOFENCED LOGISTICS MILESTONES"
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p = tf_s10_l.add_paragraph()
    p.space_before = Pt(4)
    p.text = "• Depot Departure Gate: Automated exit timestamp logging upon leaving yard\n" \
             "• Highway Toll Plazas: Electronic arrival/departure verification\n" \
             "• Consignee Unloading Dock: Proactive arrival notifications sent to shippers\n" \
             "• Dwell Time Audit: Flags loading dock turnaround delays exceeding 45 minutes"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Right: 2 Structured Process Cards
    add_card(s10, Inches(6.8), Inches(1.8), Inches(5.7), Inches(2.3))
    tb_s10_r1 = s10.shapes.add_textbox(Inches(7.0), Inches(1.95), Inches(5.3), Inches(2.0))
    tf_s10_r1 = tb_s10_r1.text_frame
    tf_s10_r1.word_wrap = True
    p = tf_s10_r1.paragraphs[0]
    p.text = "5-STEP AUTOMATED TRIP STATE MACHINE"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p = tf_s10_r1.add_paragraph()
    p.space_before = Pt(4)
    p.text = "1. Draft: Consignment, weight & approved corridor defined\n" \
             "2. Assigned: Driver paired & digital pre-trip inspection confirmed\n" \
             "3. In-Transit: Real-time GPS corridor compliance & speed audit\n" \
             "4. Arrived: Consignee geofence entry timestamp logged\n" \
             "5. Completed: Digital POD signed and expenses settled"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s10, Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.3))
    tb_s10_r2 = s10.shapes.add_textbox(Inches(7.0), Inches(4.45), Inches(5.3), Inches(2.0))
    tf_s10_r2 = tb_s10_r2.text_frame
    tf_s10_r2.word_wrap = True
    p = tf_s10_r2.paragraphs[0]
    p.text = "CUSTOMER SLA TRUST & OTIF SCORING"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p = tf_s10_r2.add_paragraph()
    p.space_before = Pt(4)
    p.text = "• On-Time In-Full (OTIF) Delivery Scoring across shipper contracts\n" \
             "• Shareable live tracking links for enterprise cargo owners\n" \
             "• Detailed route replay with recorded halts and average speeds\n" \
             "• Objective digital records for defending detention charges against consignees."
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 11: PREVENTIVE MAINTENANCE (Photo + Service Cards)
    # =========================================================================
    s11 = add_base_slide()
    add_header(s11, "Preventive Maintenance & Workshop Lifecycle Management", "10. Asset Management", "Protecting capital asset longevity through automated interval triggers, tyre wear tracking, and spares management.")

    add_card(s11, Inches(0.8), Inches(1.8), Inches(3.5), Inches(4.8))
    add_framed_photo(s11, "truck_tyres_workshop.jpg", Inches(1.0), Inches(2.0), Inches(3.1), Inches(1.8))
    tb_s11_1 = s11.shapes.add_textbox(Inches(1.0), Inches(3.9), Inches(3.1), Inches(2.6))
    tf_s11_1 = tb_s11_1.text_frame
    tf_s11_1.word_wrap = True
    tf_s11_1.paragraphs[0].text = "WORKSHOP ACCOUNTABILITY"
    tf_s11_1.paragraphs[0].font.size = Pt(9.5)
    tf_s11_1.paragraphs[0].font.bold = True
    tf_s11_1.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s11_1.add_paragraph()
    p.text = "• Digital job-cards prevent duplicate part billings\n• Actual GPS rolling odometer integration\n• Tyre rotation & tread depth tracking\n• Battery voltage & alternator health logs"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s11, Inches(4.5), Inches(1.8), Inches(2.6), Inches(4.8))
    tb_s11_2 = s11.shapes.add_textbox(Inches(4.7), Inches(2.0), Inches(2.2), Inches(4.3))
    tf_s11_2 = tb_s11_2.text_frame
    tf_s11_2.word_wrap = True
    tf_s11_2.paragraphs[0].text = "Minor Service"
    tf_s11_2.paragraphs[0].font.size = Pt(13)
    tf_s11_2.paragraphs[0].font.bold = True
    tf_s11_2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s11_2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Trigger Threshold:\n10,000 km / 90 Days\n\nAdvance Alert:\n500 km / 7 Days prior\n\nScope:\n• Engine oil replacement\n• Fuel & oil filter swap\n• Chassis greasing\n• Fluid level checks"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s11, Inches(7.3), Inches(1.8), Inches(2.6), Inches(4.8))
    tb_s11_3 = s11.shapes.add_textbox(Inches(7.5), Inches(2.0), Inches(2.2), Inches(4.3))
    tf_s11_3 = tb_s11_3.text_frame
    tf_s11_3.word_wrap = True
    tf_s11_3.paragraphs[0].text = "Major Overhaul"
    tf_s11_3.paragraphs[0].font.size = Pt(13)
    tf_s11_3.paragraphs[0].font.bold = True
    tf_s11_3.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_s11_3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Trigger Threshold:\n40,000 km / 365 Days\n\nAdvance Alert:\n1,000 km / 15 Days\n\nScope:\n• Transmission oil flush\n• Differential lubrication\n• Brake drum replacement\n• Suspension overhaul"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s11, Inches(10.1), Inches(1.8), Inches(2.4), Inches(4.8))
    tb_s11_4 = s11.shapes.add_textbox(Inches(10.3), Inches(2.0), Inches(2.0), Inches(4.3))
    tf_s11_4 = tb_s11_4.text_frame
    tf_s11_4.word_wrap = True
    tf_s11_4.paragraphs[0].text = "Document Alerts"
    tf_s11_4.paragraphs[0].font.size = Pt(13)
    tf_s11_4.paragraphs[0].font.bold = True
    tf_s11_4.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s11_4.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Notification Window:\n• 30-Day early notice\n• 15-Day urgent alert\n\nMonitored Certificates:\n• Vehicle Fitness\n• Comprehensive Insurance\n• National Goods Permit\n• Road Tax & PUC"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 12: MULTI-COHORT SCALING (Zero Legend Collision + Photo + 4 Cards)
    # =========================================================================
    s12 = add_base_slide()
    add_header(s12, "Fleet Financial Exposure & ROI Scaling: 10 to 100 Trucks", "11. Scaled Financial Impact", "Empirical financial model proving consistent 9x to 11x net return on investment across commercial fleet tiers.")

    add_card(s12, Inches(0.8), Inches(1.8), Inches(8.3), Inches(2.65))
    
    tb_c_s12 = s12.shapes.add_textbox(Inches(1.0), Inches(1.92), Inches(7.9), Inches(0.28))
    tb_c_s12.text_frame.paragraphs[0].text = "Annual Financial Impact: Unmanaged Loss vs Net Savings vs VAHAN Cost (₹ in Lakhs)"
    tb_c_s12.text_frame.paragraphs[0].font.size = Pt(10.5)
    tb_c_s12.text_frame.paragraphs[0].font.bold = True
    tb_c_s12.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

    add_button(s12, Inches(1.0), Inches(2.20), Inches(2.4), Inches(0.25), "■ Annual Loss Exposure (₹L)", bg_color=RGBColor(68, 114, 196), text_color=RGBColor(255, 255, 255), font_size=8)
    add_button(s12, Inches(3.55), Inches(2.20), Inches(2.4), Inches(0.25), "■ Net Owner Profit Gain (₹L)", bg_color=RGBColor(237, 125, 49), text_color=RGBColor(255, 255, 255), font_size=8)
    add_button(s12, Inches(6.1), Inches(2.20), Inches(2.4), Inches(0.25), "■ VAHAN Subscription Fee (₹L)", bg_color=RGBColor(165, 165, 165), text_color=RGBColor(255, 255, 255), font_size=8)

    chart_data_s12 = CategoryChartData()
    chart_data_s12.categories = ['10 Trucks', '25 Trucks', '50 Trucks', '100 Trucks']
    chart_data_s12.add_series('Annual Loss Exposure (₹L)', (18.08, 45.20, 90.40, 180.79))
    chart_data_s12.add_series('Net Owner Profit Gain (₹L)', (9.89, 24.72, 49.44, 96.48))
    chart_data_s12.add_series('VAHAN Annual Fee (₹L)', (0.96, 2.40, 4.80, 12.00))

    col_chart_shape_s12 = s12.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(1.0), Inches(2.48), Inches(7.9), Inches(1.9),
        chart_data_s12
    )
    chart_s12 = col_chart_shape_s12.chart
    chart_s12.has_title = False
    chart_s12.has_legend = False
    chart_s12.value_axis.minimum_scale = 0.0
    chart_s12.value_axis.maximum_scale = 200.0
    chart_s12.value_axis.major_unit = 50.0
    chart_s12.category_axis.tick_labels.font.size = Pt(9)
    chart_s12.value_axis.tick_labels.font.size = Pt(8.5)

    add_framed_photo(s12, "fleet_control_center.jpg", Inches(9.3), Inches(1.8), Inches(3.2), Inches(2.65))

    c_y_cards = Inches(4.55)
    c_w_cohort = Inches(2.7)
    c_h_cohort = Inches(2.25)

    cohorts_data = [
        ("10 TRUCKS (Small)", "Professional Plan", "₹1,50,660 / mo", "₹8,000 / mo", "₹90,396 / mo", "₹82,396 / mo", "₹9,88,752 / yr", "11.3x ROI", "2.7 Days", Inches(0.8)),
        ("25 TRUCKS (Growing)", "Professional Plan", "₹3,76,650 / mo", "₹20,000 / mo", "₹2,25,990 / mo", "₹2,05,990 / mo", "₹24,71,880 / yr", "11.3x ROI", "2.7 Days", Inches(3.8)),
        ("50 TRUCKS (Benchmark)", "Professional Plan", "₹7,53,300 / mo", "₹40,000 / mo", "₹4,51,980 / mo", "₹4,11,980 / mo", "₹49,43,760 / yr", "11.3x ROI", "2.7 Days", Inches(6.8)),
        ("100 TRUCKS (Enterprise)", "Enterprise Plan", "₹15,06,600 / mo", "₹1,00,000 / mo", "₹9,03,960 / mo", "₹8,03,960 / mo", "₹96,47,520 / yr", "9.0x ROI", "3.3 Days", Inches(9.8))
    ]

    for c_title, c_plan, c_loss, c_cost, c_prot, c_net_mo, c_net_yr, c_roi, c_payback, c_left in cohorts_data:
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
        p.space_before = Pt(3)
        p.text = f"Protected 60%: {c_prot}\nNet Profit: {c_net_mo} ({c_net_yr})"
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY

        p = tf.add_paragraph()
        p.space_before = Pt(2)
        p.text = f"ROI: {c_roi}  |  Payback: {c_payback}"
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 13: MODULE VALUE MATRIX (6 Interactive Drilldown Cards)
    # =========================================================================
    s13 = add_base_slide()
    add_header(s13, "Platform Capability & Module Drilldown Matrix", "12. Functional Overview", "Click any module card below to drill down into operational mechanisms, algorithms, and financial leakage vectors.")

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
        add_card(s13, m_x, m_y, card_m_w, card_m_h)
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

        btn = add_button(s13, m_x + Inches(0.2), m_y + Inches(1.65), Inches(1.8), Inches(0.38), "Drilldown ➔", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=9)
        mod_buttons.append((btn, m_target))

    # =========================================================================
    # SLIDE 14: ONBOARDING ROADMAP (Photo + 4 Phased Milestones)
    # =========================================================================
    s14 = add_base_slide()
    add_header(s14, "Rapid Fleet Deployment: 30-Day Go-Live Roadmap", "13. Deployment Strategy", "Zero operational downtime rollout designed for commercial transport operations across four structured weekly phases.")

    add_card(s14, Inches(0.8), Inches(1.8), Inches(3.2), Inches(4.8))
    add_framed_photo(s14, "technician_installation.jpg", Inches(1.0), Inches(2.0), Inches(2.8), Inches(2.1))
    tb_s14_l = s14.shapes.add_textbox(Inches(1.0), Inches(4.2), Inches(2.8), Inches(2.3))
    tf_s14_l = tb_s14_l.text_frame
    tf_s14_l.word_wrap = True
    tf_s14_l.paragraphs[0].text = "FIELD INSTALLATION"
    tf_s14_l.paragraphs[0].font.size = Pt(9.5)
    tf_s14_l.paragraphs[0].font.bold = True
    tf_s14_l.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s14_l.add_paragraph()
    p.text = "• Certified technicians deploy on-site at your depot\n• Non-invasive fuel sensor immersion\n• Complete zero-downtime transition during regular maintenance"
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    w_ph = Inches(2.0)
    phases = [
        ("WEEK 01", "Master Data &\nTenant Setup", "• Master data ingestion\n• Driver document upload\n• Role permissions\n• Depot geofences", Inches(4.3), COLOR_CARD_BG, COLOR_TEXT_DARK),
        ("WEEK 02", "Hardware &\nSensor Calibration", "• AIS-140 installation\n• Fuel sensor calibration\n• Webhook validation\n• Quarantine pool audit", Inches(6.5), COLOR_CARD_BG, COLOR_TEXT_DARK),
        ("WEEK 03", "Driver App &\nStaff Training", "• Driver app rollout\n• Walkaround checklists\n• Offline POD training\n• Manager alert drills", Inches(8.7), COLOR_CARD_BG, COLOR_TEXT_DARK),
        ("WEEK 04", "Full Go-Live &\nP&L Dashboard", "• Live leakage alerts\n• Corridor enforcement\n• Scheduled maintenance\n• First weekly P&L audit", Inches(10.9), COLOR_SOFT_GREEN, COLOR_PRIMARY)
    ]

    for p_week, p_title, p_desc, p_x, p_bg, p_col in phases:
        add_card(s14, p_x, Inches(1.8), w_ph, Inches(4.8), bg_color=p_bg)
        add_button(s14, p_x + Inches(0.15), Inches(2.0), Inches(1.2), Inches(0.3), p_week, bg_color=COLOR_PRIMARY, font_size=8.5)
        
        tb = s14.shapes.add_textbox(p_x + Inches(0.15), Inches(2.45), w_ph - Inches(0.3), Inches(4.0))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = p_title
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = p_col

        p = tf.add_paragraph()
        p.space_before = Pt(8)
        p.text = p_desc
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 15: SCENARIO CALCULATOR (Clean Console & Generous Outputs)
    # =========================================================================
    s15 = add_base_slide()
    add_header(s15, "Interactive Fleet Financial Scenario Simulator", "14. ROI Calculator", "Simulate your fleet parameters below to evaluate custom monthly leakage exposure and net profit recovery.")

    add_card(s15, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    tb_calc_in = s15.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(3.6))
    tf_calc_in = tb_calc_in.text_frame
    tf_calc_in.word_wrap = True
    
    p = tf_calc_in.paragraphs[0]
    p.text = "FLEET OPERATIONAL PARAMETER INPUTS"
    p.font.size = Pt(11)
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

    btn_calc_run = add_button(s15, Inches(1.1), Inches(5.75), Inches(2.3), Inches(0.52), "Calculate ROI  ➔", bg_color=COLOR_PRIMARY, font_size=10.5)
    btn_calc_reset = add_button(s15, Inches(3.6), Inches(5.75), Inches(2.0), Inches(0.52), "Reset Baseline", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=10.5)

    add_card(s15, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    tb_calc_out = s15.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(0.35))
    tb_calc_out.text_frame.paragraphs[0].text = "Projected Financial Outcomes (50 Trucks)"
    tb_calc_out.text_frame.paragraphs[0].font.size = Pt(12)
    tb_calc_out.text_frame.paragraphs[0].font.bold = True
    tb_calc_out.text_frame.paragraphs[0].font.color.rgb = COLOR_PRIMARY

    add_card(s15, Inches(7.1), Inches(2.45), Inches(5.1), Inches(1.05), bg_color=COLOR_LOSS_BG, border_color=COLOR_LOSS_RED)
    tb_m1 = s15.shapes.add_textbox(Inches(7.3), Inches(2.52), Inches(4.7), Inches(0.9))
    tf_m1 = tb_m1.text_frame
    tf_m1.paragraphs[0].text = "UNMANAGED MONTHLY FINANCIAL LEAKAGE"
    tf_m1.paragraphs[0].font.size = Pt(8.5)
    tf_m1.paragraphs[0].font.bold = True
    tf_m1.paragraphs[0].font.color.rgb = COLOR_LOSS_RED
    p = tf_m1.add_paragraph()
    p.text = "₹7,53,300 / Month  (₹90,39,600 / Year)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s15, Inches(7.1), Inches(3.65), Inches(5.1), Inches(1.05), bg_color=COLOR_CARD_BG, border_color=COLOR_PRIMARY)
    tb_m2 = s15.shapes.add_textbox(Inches(7.3), Inches(3.72), Inches(4.7), Inches(0.9))
    tf_m2 = tb_m2.text_frame
    tf_m2.paragraphs[0].text = "VERIFIED 60% PROFIT PROTECTION RECOVERY"
    tf_m2.paragraphs[0].font.size = Pt(8.5)
    tf_m2.paragraphs[0].font.bold = True
    tf_m2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_m2.add_paragraph()
    p.text = "₹4,51,980 / Month  (₹54,23,760 / Year)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK

    add_card(s15, Inches(7.1), Inches(4.85), Inches(5.1), Inches(1.5), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    tb_m3 = s15.shapes.add_textbox(Inches(7.3), Inches(4.92), Inches(4.7), Inches(1.35))
    tf_m3 = tb_m3.text_frame
    tf_m3.paragraphs[0].text = "NET CASH FLOW ADDED TO OWNER BOTTOM LINE"
    tf_m3.paragraphs[0].font.size = Pt(9)
    tf_m3.paragraphs[0].font.bold = True
    tf_m3.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_m3.add_paragraph()
    p.text = "₹4,11,980 / Month  (₹49,43,760 / Year)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_DARK
    p = tf_m3.add_paragraph()
    p.text = "Return Multiple: 11.3x ROI  |  Payback Period: 2.7 Days"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_DARK

    # =========================================================================
    # SLIDE 16: PRICING PLANS (3 Spacious Cards + Hardware Strip)
    # =========================================================================
    s16 = add_base_slide()
    add_header(s16, "Transparent Subscription Pricing for Every Fleet Scale", "15. Commercial Plans", "Predictable per-vehicle investment with no hidden integration fees or lock-in contracts.")

    w_plan = Inches(3.7)
    h_plan = Inches(4.3)
    y_plan = Inches(1.8)

    add_card(s16, Inches(0.8), y_plan, w_plan, h_plan)
    add_button(s16, Inches(1.1), Inches(2.0), Inches(1.4), Inches(0.3), "STARTER", bg_color=COLOR_CARD_BORDER, text_color=COLOR_TEXT_DARK, font_size=8.5)
    tb_p1 = s16.shapes.add_textbox(Inches(1.1), Inches(2.4), Inches(3.1), Inches(3.4))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True
    tf_p1.paragraphs[0].text = "₹500"
    tf_p1.paragraphs[0].font.size = Pt(22)
    tf_p1.paragraphs[0].font.bold = True
    tf_p1.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_p1.add_paragraph()
    p.text = "per truck / month"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_MUTED
    p = tf_p1.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Core Fleet Visibility:\n\n• Real-time GPS vehicle tracking\n• Daily trip start/end logging\n• Driver document vault & expiry alerts\n• Standard speed and geofence alerts\n• Basic mobile driver application"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    btn_p1 = add_button(s16, Inches(1.1), Inches(5.45), Inches(3.1), Inches(0.42), "Select Starter Plan", bg_color=COLOR_CARD_BG, text_color=COLOR_PRIMARY, font_size=9, border_color=COLOR_PRIMARY)

    add_card(s16, Inches(4.8), y_plan, w_plan, h_plan, bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    add_button(s16, Inches(5.1), Inches(2.0), Inches(2.2), Inches(0.3), "PROFESSIONAL (FLAGSHIP)", bg_color=COLOR_PRIMARY, text_color=RGBColor(255, 255, 255), font_size=8.5)
    tb_p2 = s16.shapes.add_textbox(Inches(5.1), Inches(2.4), Inches(3.1), Inches(3.4))
    tf_p2 = tb_p2.text_frame
    tf_p2.word_wrap = True
    tf_p2.paragraphs[0].text = "₹800"
    tf_p2.paragraphs[0].font.size = Pt(22)
    tf_p2.paragraphs[0].font.bold = True
    tf_p2.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_p2.add_paragraph()
    p.text = "per truck / month (Recommended)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_PRIMARY_DARK
    p = tf_p2.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Full Financial Protection:\n\n• Everything in Starter Plan, plus:\n• Fuel siphoning anomaly detection (>5%)\n• Corridor detour alerts (>500m)\n• Preventive maintenance engine (10k km)\n• Fleet P&L financial leakage analytics"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    btn_p2 = add_button(s16, Inches(5.1), Inches(5.45), Inches(3.1), Inches(0.42), "Choose Professional Plan  ➔", bg_color=COLOR_PRIMARY, font_size=9)

    add_card(s16, Inches(8.8), y_plan, w_plan, h_plan)
    add_button(s16, Inches(9.1), Inches(2.0), Inches(1.6), Inches(0.3), "ENTERPRISE", bg_color=COLOR_CARD_BORDER, text_color=COLOR_TEXT_DARK, font_size=8.5)
    tb_p3 = s16.shapes.add_textbox(Inches(9.1), Inches(2.4), Inches(3.1), Inches(3.4))
    tf_p3 = tb_p3.text_frame
    tf_p3.word_wrap = True
    tf_p3.paragraphs[0].text = "₹1,000"
    tf_p3.paragraphs[0].font.size = Pt(22)
    tf_p3.paragraphs[0].font.bold = True
    tf_p3.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK
    p = tf_p3.add_paragraph()
    p.text = "per truck / month (100+ Fleets)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_MUTED
    p = tf_p3.add_paragraph()
    p.space_before = Pt(8)
    p.text = "Enterprise Scalability:\n\n• Everything in Professional Plan, plus:\n• Custom ERP & SAP webhooks integration\n• Dedicated Technical Account Manager\n• Multi-branch depot sub-tenancy\n• 99.9% uptime SLA & priority support"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK
    btn_p3 = add_button(s16, Inches(9.1), Inches(5.45), Inches(3.1), Inches(0.42), "Contact Enterprise Sales", bg_color=COLOR_CARD_BG, text_color=COLOR_PRIMARY, font_size=9, border_color=COLOR_PRIMARY)

    add_card(s16, Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.65), bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER)
    tb_hw = s16.shapes.add_textbox(Inches(1.0), Inches(6.38), Inches(11.3), Inches(0.5))
    tf_hw = tb_hw.text_frame
    p_hw = tf_hw.paragraphs[0]
    p_hw.text = "CERTIFIED HARDWARE ADD-ONS (Optional One-Time): AIS-140 GPS Tracker: ₹3,499 - ₹4,999  |  Digital Ultrasonic Fuel Sensor: ₹1,500  (Fleet owners may also bring existing Traccar-compatible hardware)"
    p_hw.alignment = PP_ALIGN.CENTER
    p_hw.font.size = Pt(9)
    p_hw.font.bold = True
    p_hw.font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 17: SECURITY & ARCHITECTURE (Photo + Balanced Pillars)
    # =========================================================================
    s17 = add_base_slide()
    add_header(s17, "Enterprise Security, Quarantine Isolation & Platform Trust", "16. Security & Infrastructure", "Multi-tenant architecture ensuring complete data privacy, cryptographic webhook security, and SOC2 readiness.")

    add_card(s17, Inches(0.8), Inches(1.8), Inches(4.0), Inches(4.8))
    add_framed_photo(s17, "datacenter_security.jpg", Inches(1.0), Inches(2.0), Inches(3.6), Inches(2.0))
    tb_s17_l = s17.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(3.6), Inches(2.3))
    tf_s17_l = tb_s17_l.text_frame
    tf_s17_l.word_wrap = True
    tf_s17_l.paragraphs[0].text = "ENTERPRISE CLOUD TRUST"
    tf_s17_l.paragraphs[0].font.size = Pt(10)
    tf_s17_l.paragraphs[0].font.bold = True
    tf_s17_l.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s17_l.add_paragraph()
    p.text = "• FastAPI high-performance asynchronous backend\n• PostgreSQL database with strict tenant isolation\n• Traccar 6.5 telematics ingestion cluster\n• End-to-end TLS 1.3 data encryption\n• Point-in-time automated disaster recovery backups"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    w_tr = Inches(7.4)
    add_card(s17, Inches(5.1), Inches(1.8), w_tr, Inches(4.8))
    
    pillars_content = [
        ("TENANT ISOLATION", "Company Tenancy Enforced", "Strict company_id row-level isolation across all PostgreSQL queries. Dispatchers never see another company's vehicles, trips, or reports. Full RBAC (Super-Admin, Company-Admin, Dispatcher, Driver).", Inches(1.95)),
        ("QUARANTINE SECURITY", "Hardware Isolation Pool", "Unassigned, rogue, or misconfigured GPS trackers route automatically into an isolated staging quarantine pool. Zero unauthorized telemetry injection into client dashboards.", Inches(3.10)),
        ("WEBHOOK SECURITY", "Cryptographic HMAC Signatures", "Traccar 6.5 forwarder secured with shared X-Telematics-Secret and HMAC verification. Prevents telemetry spoofing, replay attacks, and false location updates.", Inches(4.25)),
        ("AUDIT & GOVERNANCE", "SOC2 Readiness & Tamper-Proof Trail", "Comprehensive immutable audit logging for all telematics reassignments, user role modifications, and fuel variance overrides with forensic timestamping.", Inches(5.40))
    ]

    for p_badge, p_title, p_desc, p_top in pillars_content:
        add_button(s17, Inches(5.3), p_top, Inches(2.2), Inches(0.28), p_badge, bg_color=COLOR_PRIMARY, font_size=8)
        tb_p = s17.shapes.add_textbox(Inches(7.6), p_top - Inches(0.05), Inches(4.7), Inches(0.32))
        tf_p = tb_p.text_frame
        tf_p.paragraphs[0].text = p_title
        tf_p.paragraphs[0].font.size = Pt(10.5)
        tf_p.paragraphs[0].font.bold = True
        tf_p.paragraphs[0].font.color.rgb = COLOR_TEXT_DARK

        tb_d = s17.shapes.add_textbox(Inches(5.3), p_top + Inches(0.30), Inches(7.0), Inches(0.75))
        tf_d = tb_d.text_frame
        tf_d.word_wrap = True
        tf_d.paragraphs[0].text = p_desc
        tf_d.paragraphs[0].font.size = Pt(8.5)
        tf_d.paragraphs[0].font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 18: CLOSING CTA & PILOT ONBOARDING (Commercial Truck Photo + Offer)
    # =========================================================================
    s18 = add_base_slide()
    add_header(s18, "Protect Your Fleet Profit Margin Starting Today", "17. Next Steps & Pilot Program", "Experience the measurable financial impact of VAHAN with our 30-day risk-free benchmark diagnostic pilot.")

    add_card(s18, Inches(0.8), Inches(1.8), Inches(6.4), Inches(4.8), bg_color=COLOR_SOFT_GREEN, border_color=COLOR_PRIMARY)
    add_button(s18, Inches(1.2), Inches(2.1), Inches(2.6), Inches(0.35), "NO-RISK PROOF-OF-CONCEPT", bg_color=COLOR_PRIMARY, font_size=9)

    tb_s18_l = s18.shapes.add_textbox(Inches(1.2), Inches(2.6), Inches(5.6), Inches(2.6))
    tf_s18_l = tb_s18_l.text_frame
    tf_s18_l.word_wrap = True
    tf_s18_l.paragraphs[0].text = "30-Day Benchmark Pilot (5 Trucks)"
    tf_s18_l.paragraphs[0].font.size = Pt(18)
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

    btn_book_pilot = add_button(s18, Inches(1.2), Inches(5.35), Inches(2.7), Inches(0.55), "Book 5-Truck Pilot  ➔", bg_color=COLOR_PRIMARY, font_size=10.5)
    btn_calc_again = add_button(s18, Inches(4.1), Inches(5.35), Inches(2.3), Inches(0.55), "Recalculate ROI", bg_color=COLOR_CARD_BG, text_color=COLOR_PRIMARY, font_size=10, border_color=COLOR_PRIMARY)

    add_framed_photo(s18, "closing_commercial_truck.jpg", Inches(7.5), Inches(1.8), Inches(5.0), Inches(2.4))
    
    add_card(s18, Inches(7.5), Inches(4.35), Inches(5.0), Inches(2.25))
    tb_s18_r = s18.shapes.add_textbox(Inches(7.7), Inches(4.45), Inches(4.6), Inches(2.0))
    tf_s18_r = tb_s18_r.text_frame
    tf_s18_r.word_wrap = True
    tf_s18_r.paragraphs[0].text = "COMMERCIAL CONSULTATION & SUPPORT"
    tf_s18_r.paragraphs[0].font.size = Pt(9.5)
    tf_s18_r.paragraphs[0].font.bold = True
    tf_s18_r.paragraphs[0].font.color.rgb = COLOR_PRIMARY
    p = tf_s18_r.add_paragraph()
    p.text = "Email: pilot@vahanfleet.io  |  Sales: +91 98765 43210\nWeb: https://vahanfleet.io\n\nAccompanying Audit Workbooks:\n• VAHAN_Financial_Audit.xlsx (Claim Verification Register)\n• VAHAN_Scenario_Assumptions.xlsx (Dynamic Excel Model)"
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    btn_view_audit = add_button(s18, Inches(7.7), Inches(5.9), Inches(4.6), Inches(0.42), "Review Financial Audit Matrix  ➔", bg_color=COLOR_SOFT_GREEN, text_color=COLOR_PRIMARY, font_size=9.5)

    # =========================================================================
    # GLOBAL NAVIGATION SYSTEM: SECTION JUMP PILLS & BOTTOM CONTROLS
    # =========================================================================
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
            btn_s1_story.click_action.target_slide = slides[1]
            btn_s1_calc.click_action.target_slide = slides[14]
            continue

        for p_idx, (sec_name, sec_target) in enumerate(nav_sections):
            px = start_x + (p_idx * (pill_w + Inches(0.08)))
            
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

        btn_home = add_button(slide, Inches(0.8), Inches(6.9), Inches(1.1), Inches(0.35), "🏠 Home", bg_color=COLOR_CARD_BG, text_color=COLOR_TEXT_DARK, font_size=8.5, border_color=COLOR_CARD_BORDER)
        btn_home.click_action.target_slide = slides[0]

        if idx > 0:
            btn_prev = add_button(slide, Inches(2.0), Inches(6.9), Inches(1.0), Inches(0.35), "◀ Prev", bg_color=COLOR_CARD_BG, text_color=COLOR_TEXT_DARK, font_size=8.5, border_color=COLOR_CARD_BORDER)
            btn_prev.click_action.target_slide = slides[idx - 1]

        if idx < len(slides) - 1:
            btn_next = add_button(slide, Inches(3.1), Inches(6.9), Inches(1.0), Inches(0.35), "Next ▶", bg_color=COLOR_CARD_BG, text_color=COLOR_TEXT_DARK, font_size=8.5, border_color=COLOR_CARD_BORDER)
            btn_next.click_action.target_slide = slides[idx + 1]

        slide_num_box = slide.shapes.add_textbox(Inches(11.3), Inches(6.9), Inches(1.2), Inches(0.35))
        tf_num = slide_num_box.text_frame
        p_num = tf_num.paragraphs[0]
        p_num.text = f"{idx + 1:02d} / {len(slides):02d}"
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.font.name = FONT_FAMILY
        p_num.font.size = Pt(9.5)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_TEXT_MUTED

    # Specific slide hyperlinks
    btn_drill1.click_action.target_slide = slides[3]
    btn_drill2.click_action.target_slide = slides[4]
    btn_drill3.click_action.target_slide = slides[5]

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

    btn_calc_run.click_action.target_slide = slides[11]
    btn_calc_reset.click_action.target_slide = slides[14]

    btn_p1.click_action.target_slide = slides[17]
    btn_p2.click_action.target_slide = slides[17]
    btn_p3.click_action.target_slide = slides[17]

    btn_book_pilot.click_action.target_slide = slides[15]
    btn_calc_again.click_action.target_slide = slides[14]
    btn_view_audit.click_action.target_slide = slides[11]

    output_path = "VAHAN_Interactive_Presentation_Final.pptx"
    prs.save(output_path)
    print(f"Successfully generated {output_path} with 18 photo-rich slides and perfected graph layouts!")

if __name__ == "__main__":
    build_presentation()
