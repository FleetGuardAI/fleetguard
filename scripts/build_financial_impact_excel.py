import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_financial_impact_workbook():
    wb = openpyxl.Workbook()
    
    # Palette
    EMERALD = "25845B"
    SOFT_GREEN = "E4F3EA"
    DARK_TEXT = "24352D"
    SEC_TEXT = "64736B"
    BORDER_COLOR = "E1EAE4"
    WHITE = "FFFFFF"
    GRAY_LIGHT = "F7FAF8"
    INPUT_FILL = "FEF9C3"       # Soft yellow for editable inputs
    INPUT_FONT = "854D0E"       # Amber text for inputs
    FORMULA_FILL = "ECFDF5"     # Soft green for calculated cells
    ALERT_FILL = "FEF2F2"       # Soft red for loss exposure
    ALERT_TEXT = "991B1B"
    
    title_font = Font(name="Segoe UI", size=15, bold=True, color=WHITE)
    subtitle_font = Font(name="Segoe UI", size=10, italic=True, color="E2E8F0")
    header_font = Font(name="Segoe UI", size=10, bold=True, color=WHITE)
    cat_font = Font(name="Segoe UI", size=11, bold=True, color=DARK_TEXT)
    data_font = Font(name="Segoe UI", size=10, color=DARK_TEXT)
    bold_data_font = Font(name="Segoe UI", size=10, bold=True, color=DARK_TEXT)
    input_data_font = Font(name="Segoe UI", size=10, bold=True, color=INPUT_FONT)
    formula_font = Font(name="Segoe UI", size=10, bold=True, color="065F46")
    alert_font = Font(name="Segoe UI", size=10, bold=True, color=ALERT_TEXT)
    
    thin_border = Border(
        left=Side(style='thin', color=BORDER_COLOR),
        right=Side(style='thin', color=BORDER_COLOR),
        top=Side(style='thin', color=BORDER_COLOR),
        bottom=Side(style='thin', color=BORDER_COLOR)
    )
    double_bottom_border = Border(
        left=Side(style='thin', color=BORDER_COLOR),
        right=Side(style='thin', color=BORDER_COLOR),
        top=Side(style='thin', color=BORDER_COLOR),
        bottom=Side(style='double', color=DARK_TEXT)
    )

    # =========================================================================
    # SHEET 1: Fleet P&L Baseline Model
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Fleet P&L Baseline Model"
    ws1.views.sheetView[0].showGridLines = True
    
    # Title Banner
    ws1.merge_cells("A1:G1")
    ws1["A1"] = "ILLUSTRATIVE COMMERCIAL FLEET P&L & EXPENSE WATERFALL"
    ws1["A1"].font = title_font
    ws1["A1"].fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.merge_cells("A2:G2")
    ws1["A2"] = "Illustrative Business Scenario — Not Actual Customer Data | 50-Truck Long-Haul Fleet Baseline"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws1["A2"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.row_dimensions[1].height = 32
    ws1.row_dimensions[2].height = 20
    ws1.row_dimensions[3].height = 26

    pnl_headers = [
        "Line Item / Operational Category",
        "% of Gross Revenue",
        "Per Vehicle / Month (₹)",
        "50-Truck Fleet / Month (₹)",
        "50-Truck Fleet / Annual (₹)",
        "Operational Risk & Leakage Mechanism",
        "VAHAN Control Module"
    ]
    for col_idx, h in enumerate(pnl_headers, 1):
        cell = ws1.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    pnl_data = [
        ("Gross Freight Trip Revenue", "100.0%", 220000, "=C4*50", "=D4*12", "Trip freight billings from contracted shippers", "Trip Management"),
        ("1. Diesel / Fuel Expenditure", "48.0%", 105600, "=C5*50", "=D5*12", "Fuel siphoning, pump kickbacks, tank capacity fraud", "Fuel Intelligence AI"),
        ("2. Tolls & En-Route Transit Expenses", "10.0%", 22000, "=C6*50", "=D6*12", "Unapproved highway toll bypasses, unverified slips", "Driver Mobile & Expenses"),
        ("3. Driver Salaries, Trip Batas & Allowances", "14.0%", 30800, "=C7*50", "=D7*12", "Manual attendance, unrecorded cash advances", "Driver KYC & Mobile"),
        ("4. Vehicle Maintenance, Tires & Lubricants", "11.0%", 24200, "=C8*50", "=D8*12", "Premature tire wear from off-corridor dirt roads", "Route Intelligence"),
        ("5. Insurance, Permits, Road Taxes & Fitness", "5.0%", 11000, "=C9*50", "=D9*12", "Statutory fines, expired fitness impoundments", "Document KYC Review"),
        ("6. Administrative, Dispatch & Office Overhead", "4.0%", 8800, "=C10*50", "=D10*12", "Manual spreadsheets, 4+ separate GPS portals", "Unified Owner Console"),
        ("TOTAL OPERATING EXPENSES", "92.0%", "=SUM(C5:C10)", "=SUM(D5:D10)", "=SUM(E5:E10)", "Total operational bleed consuming revenue", "Full Platform Suite"),
        ("NET OPERATING PROFIT MARGIN", "8.0%", "=C4-C11", "=D4-D11", "=E4-E11", "Thin margin vulnerable to unmonitored leakage", "Profit Protection")
    ]

    for r_idx, row in enumerate(pnl_data, 4):
        ws1.row_dimensions[r_idx].height = 24
        is_total = r_idx in [11, 12]
        is_rev = r_idx == 4
        
        row_fill = PatternFill(start_color=SOFT_GREEN if is_rev else (INPUT_FILL if is_total else (GRAY_LIGHT if r_idx % 2 == 0 else WHITE)),
                               end_color=SOFT_GREEN if is_rev else (INPUT_FILL if is_total else (GRAY_LIGHT if r_idx % 2 == 0 else WHITE)),
                               fill_type="solid")
        
        for c_idx, val in enumerate(row, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.border = double_bottom_border if r_idx == 12 else thin_border
            cell.fill = row_fill
            cell.font = bold_data_font if is_total or is_rev else data_font
            
            if c_idx in [1, 6, 7]:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif c_idx == 2:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                if isinstance(val, (int, float)) or (isinstance(val, str) and val.startswith("=")):
                    cell.number_format = "₹#,##0"

    # Auto-adjust column widths
    col_w1 = {1: 34, 2: 18, 3: 24, 4: 26, 5: 28, 6: 45, 7: 24}
    for c, w in col_w1.items():
        ws1.column_dimensions[get_column_letter(c)].width = w

    # =========================================================================
    # SHEET 2: Financial Impact Scenario Calculator
    # =========================================================================
    ws2 = wb.create_sheet(title="Financial Impact Calculator")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:G1")
    ws2["A1"] = "VAHAN FLEET LEAKAGE & FINANCIAL RECOVERY CALCULATOR"
    ws2["A1"].font = title_font
    ws2["A1"].fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws2.merge_cells("A2:G2")
    ws2["A2"] = "Editable Scenario Simulator — Adjust Yellow Cells to Match Specific Fleet Operations"
    ws2["A2"].font = subtitle_font
    ws2["A2"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws2["A2"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws2.row_dimensions[1].height = 32
    ws2.row_dimensions[2].height = 20

    # Section 1: Inputs
    ws2.merge_cells("A4:G4")
    sec1 = ws2.cell(row=4, column=1, value="1. EDITABLE FLEET OPERATIONAL INPUTS & ASSUMPTIONS")
    sec1.font = Font(name="Segoe UI", size=11, bold=True, color=WHITE)
    sec1.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    sec1.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[4].height = 24

    inputs = [
        ("Fleet Size (Commercial Vehicles in Active Operation)", "fleet_size", 50, "Units", "Total number of trucks in active service"),
        ("Average Monthly Fuel Expenditure per Vehicle", "fuel_spend", 105600, "₹ / vehicle / mo", "Estimated monthly diesel bill per truck"),
        ("Estimated Unexplained Fuel Leakage Exposure", "fuel_leak_pct", 0.06, "% of fuel spend", "Estimated loss from siphoning & inflated receipts (e.g. 6.0%)"),
        ("Average Unapproved Extra Distance per Vehicle per Month", "extra_km", 180, "km / vehicle / mo", "Detours, toll bypasses, off-corridor kilometers"),
        ("Operating Cost per Kilometer (Fuel, Maintenance, Tires)", "cost_per_km", 28.5, "₹ / km", "Direct running cost per kilometer"),
        ("Avoidable Unscheduled Downtime Days per Vehicle per Month", "idle_days", 1.5, "days / vehicle / mo", "Avoidable idle days from dispatch/maintenance lag"),
        ("Daily Net Contribution Margin per Vehicle", "daily_contrib", 2400, "₹ / day / vehicle", "Daily contribution (Freight Revenue minus Direct Fuel/Tolls)"),
        ("Percentage of Flagged Anomalies Successfully Investigated & Controlled", "recovery_rate", 0.60, "% success rate", "Realistic operational investigation resolution rate (e.g. 60.0%)")
    ]

    for idx, (lbl, var_name, def_val, unit, note) in enumerate(inputs, 5):
        ws2.row_dimensions[idx].height = 22
        ws2.cell(row=idx, column=1, value=lbl).font = bold_data_font
        ws2.cell(row=idx, column=1).border = thin_border
        
        c_val = ws2.cell(row=idx, column=2, value=def_val)
        c_val.font = input_data_font
        c_val.fill = PatternFill(start_color=INPUT_FILL, end_color=INPUT_FILL, fill_type="solid")
        c_val.alignment = Alignment(horizontal="right", vertical="center")
        c_val.border = thin_border
        if isinstance(def_val, float) and def_val < 1.0:
            c_val.number_format = "0.0%"
        elif isinstance(def_val, (int, float)) and def_val > 100:
            c_val.number_format = "₹#,##0"
            
        c_unit = ws2.cell(row=idx, column=3, value=unit)
        c_unit.font = data_font
        c_unit.border = thin_border
        
        ws2.merge_cells(start_row=idx, start_column=4, end_row=idx, end_column=7)
        c_note = ws2.cell(row=idx, column=4, value=note)
        c_note.font = Font(name="Segoe UI", size=9, italic=True, color=SEC_TEXT)
        c_note.border = thin_border

    # Section 2: Calculated Leakage Exposure
    curr = 14
    ws2.merge_cells(f"A{curr}:G{curr}")
    sec2 = ws2.cell(row=curr, column=1, value="2. ESTIMATED FINANCIAL LEAKAGE EXPOSURE (WITHOUT VAHAN)")
    sec2.font = Font(name="Segoe UI", size=11, bold=True, color=WHITE)
    sec2.fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
    sec2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[curr].height = 24
    curr += 1

    leak_items = [
        ("A. Potential Monthly Fuel Leakage Loss", "=B5*B6*B7", "Fleet Size × Fuel Spend × Leakage %", "=B15*12"),
        ("B. Potential Unapproved Route Detour Cost", "=B5*B8*B9", "Fleet Size × Extra km × Cost/km", "=B16*12"),
        ("C. Potential Downtime Contribution Loss", "=B5*B10*B11", "Fleet Size × Avoidable Days × Daily Contribution", "=B17*12"),
        ("TOTAL ESTIMATED MONTHLY FINANCIAL EXPOSURE", "=SUM(B15:B17)", "Total potential unmonitored operational leakage", "=B18*12")
    ]

    for lbl, formula_mo, expl, formula_yr in leak_items:
        ws2.row_dimensions[curr].height = 23
        is_tot = "TOTAL" in lbl
        
        c_lbl = ws2.cell(row=curr, column=1, value=lbl)
        c_lbl.font = alert_font if is_tot else bold_data_font
        c_lbl.fill = PatternFill(start_color=ALERT_FILL, end_color=ALERT_FILL, fill_type="solid") if is_tot else PatternFill(fill_type=None)
        c_lbl.border = thin_border
        
        c_mo = ws2.cell(row=curr, column=2, value=formula_mo)
        c_mo.font = alert_font if is_tot else bold_data_font
        c_mo.fill = PatternFill(start_color=ALERT_FILL, end_color=ALERT_FILL, fill_type="solid") if is_tot else PatternFill(fill_type=None)
        c_mo.number_format = "₹#,##0"
        c_mo.alignment = Alignment(horizontal="right", vertical="center")
        c_mo.border = thin_border
        
        c_unit = ws2.cell(row=curr, column=3, value="₹ / month")
        c_unit.font = data_font
        c_unit.border = thin_border
        
        ws2.merge_cells(start_row=curr, start_column=4, end_row=curr, end_column=5)
        c_expl = ws2.cell(row=curr, column=4, value=expl)
        c_expl.font = Font(name="Segoe UI", size=9, color=SEC_TEXT)
        c_expl.border = thin_border
        
        ws2.cell(row=curr, column=6, value="Annualized:").font = bold_data_font
        ws2.cell(row=curr, column=6).border = thin_border
        
        c_yr = ws2.cell(row=curr, column=7, value=formula_yr)
        c_yr.font = alert_font if is_tot else bold_data_font
        c_yr.fill = PatternFill(start_color=ALERT_FILL, end_color=ALERT_FILL, fill_type="solid") if is_tot else PatternFill(fill_type=None)
        c_yr.number_format = "₹#,##0"
        c_yr.alignment = Alignment(horizontal="right", vertical="center")
        c_yr.border = thin_border
        curr += 1

    # Section 3: Recoverable Amount under Assumptions
    curr += 1
    ws2.merge_cells(f"A{curr}:G{curr}")
    sec3 = ws2.cell(row=curr, column=1, value="3. ILLUSTRATIVE AVOIDABLE / PROTECTED PROFIT (WITH VAHAN)")
    sec3.font = Font(name="Segoe UI", size=11, bold=True, color=WHITE)
    sec3.fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    sec3.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[curr].height = 24
    curr += 1

    recovery_items = [
        ("Illustrative Monthly Protected Operating Profit", "=B18*B12", "Total Exposure × Investigation Success Rate (60%)", "=B21*12"),
        ("Illustrative Annualized Protected Operating Profit", "=B21*12", "Annualized savings under selected scenario", "—")
    ]
    for lbl, formula, expl, ann_form in recovery_items:
        ws2.row_dimensions[curr].height = 23
        c_lbl = ws2.cell(row=curr, column=1, value=lbl)
        c_lbl.font = formula_font
        c_lbl.fill = PatternFill(start_color=FORMULA_FILL, end_color=FORMULA_FILL, fill_type="solid")
        c_lbl.border = thin_border
        
        c_val = ws2.cell(row=curr, column=2, value=formula)
        c_val.font = formula_font
        c_val.fill = PatternFill(start_color=FORMULA_FILL, end_color=FORMULA_FILL, fill_type="solid")
        c_val.number_format = "₹#,##0"
        c_val.alignment = Alignment(horizontal="right", vertical="center")
        c_val.border = thin_border
        
        c_unit = ws2.cell(row=curr, column=3, value="₹ / month" if "Monthly" in lbl else "₹ / year")
        c_unit.font = data_font
        c_unit.border = thin_border
        
        ws2.merge_cells(start_row=curr, start_column=4, end_row=curr, end_column=7)
        c_expl = ws2.cell(row=curr, column=4, value=expl)
        c_expl.font = Font(name="Segoe UI", size=9, bold=True, color="065F46")
        c_expl.border = thin_border
        curr += 1

    # Section 4: Software Investment Comparison
    curr += 1
    ws2.merge_cells(f"A{curr}:G{curr}")
    sec4 = ws2.cell(row=curr, column=1, value="4. SOFTWARE SUBSCRIPTION INVESTMENT COMPARISON")
    sec4.font = Font(name="Segoe UI", size=11, bold=True, color=WHITE)
    sec4.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    sec4.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[curr].height = 24
    curr += 1

    plans_calc = [
        ("STARTER PLAN (₹500 / truck / mo)", "=B5*500", "50 Trucks × ₹500", "=B21-B25", "Basic fleet organization, KYC & manual trip ops"),
        ("PROFESSIONAL PLAN (₹800 / truck / mo)", "=B5*800", "50 Trucks × ₹800", "=B21-B26", "Live GPS tracking, route deviation alerts, driver app"),
        ("ENTERPRISE PLAN (₹1,000 / truck / mo)", "=B5*1000", "50 Trucks × ₹1000", "=B21-B27", "Full fuel anomaly AI, tank physics check, hardware vault")
    ]
    for lbl, cost_form, cost_expl, net_form, plan_scope in plans_calc:
        ws2.row_dimensions[curr].height = 24
        is_ent = "ENTERPRISE" in lbl
        
        c_lbl = ws2.cell(row=curr, column=1, value=lbl)
        c_lbl.font = bold_data_font
        c_lbl.border = thin_border
        
        c_cost = ws2.cell(row=curr, column=2, value=cost_form)
        c_cost.font = bold_data_font
        c_cost.number_format = "₹#,##0"
        c_cost.alignment = Alignment(horizontal="right", vertical="center")
        c_cost.border = thin_border
        
        c_unit = ws2.cell(row=curr, column=3, value="₹ / month")
        c_unit.font = data_font
        c_unit.border = thin_border
        
        c_net_lbl = ws2.cell(row=curr, column=4, value="Net Profit Shield:")
        c_net_lbl.font = Font(name="Segoe UI", size=9, bold=True, color=DARK_TEXT)
        c_net_lbl.border = thin_border
        
        c_net = ws2.cell(row=curr, column=5, value=net_form)
        c_net.font = formula_font
        c_net.fill = PatternFill(start_color=FORMULA_FILL, end_color=FORMULA_FILL, fill_type="solid")
        c_net.number_format = "₹#,##0"
        c_net.alignment = Alignment(horizontal="right", vertical="center")
        c_net.border = thin_border
        
        ws2.merge_cells(start_row=curr, start_column=6, end_row=curr, end_column=7)
        c_scope = ws2.cell(row=curr, column=6, value=plan_scope)
        c_scope.font = Font(name="Segoe UI", size=9, italic=True, color=SEC_TEXT)
        c_scope.border = thin_border
        curr += 1

    # Disclaimer Note at Bottom
    curr += 1
    ws2.merge_cells(f"A{curr}:G{curr+2}")
    c_disc = ws2.cell(row=curr, column=1)
    c_disc.value = (
        "IMPORTANT GOVERNANCE & METHODOLOGY NOTICE:\n"
        "• This financial calculator models illustrative business scenarios and does not represent guaranteed performance results or proven universal savings.\n"
        "• Not all flagged anomalies constitute proven theft or recoverable loss. Actual recovery depends on fleet operator investigation protocols and route conditions.\n"
        "• All calculations distinguish freight revenue, operating expenses, and contribution margins transparently without double-counting losses."
    )
    c_disc.font = Font(name="Segoe UI", size=8.5, italic=True, color="475569")
    c_disc.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    c_disc.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    col_w2 = {1: 44, 2: 20, 3: 16, 4: 20, 5: 20, 6: 22, 7: 24}
    for c, w in col_w2.items():
        ws2.column_dimensions[get_column_letter(c)].width = w

    # =========================================================================
    # SHEET 3: Feature-to-Profitability Matrix
    # =========================================================================
    ws3 = wb.create_sheet(title="Feature-to-Profitability Matrix")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:F1")
    ws3["A1"] = "VAHAN FEATURE-TO-PROFITABILITY VALUE MAPPING"
    ws3["A1"].font = title_font
    ws3["A1"].fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws3.merge_cells("A2:F2")
    ws3["A2"] = "Every Feature Addresses a Specific Source of Operational Loss — Audited Codebase Alignment"
    ws3["A2"].font = subtitle_font
    ws3["A2"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws3["A2"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws3.row_dimensions[1].height = 32
    ws3.row_dimensions[2].height = 20
    ws3.row_dimensions[3].height = 26

    matrix_headers = [
        "Business Problem",
        "Financial Consequence / Loss Mechanism",
        "VAHAN Solution Feature",
        "How Feature Works (Mechanism)",
        "Expected Business Benefit",
        "Relevant Subscription Plan"
    ]
    for col_idx, h in enumerate(matrix_headers, 1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    matrix_rows = [
        ("Unnoticed fuel volume drops during highway rest stops", "Direct diesel loss (₹90+/L); inflates running cost per km", "Fuel Siphoning Anomaly AI", "Correlates tank level drops with engine ignition OFF states; flags sudden drops", "Detects fuel loss incidents in real-time with timestamps & GPS coordinates", "Enterprise (₹1,000)"),
        ("Inflated fuel purchase invoices submitted by drivers", "Operators pay for diesel that never entered the vehicle tank", "Tank Capacity Physics Validation", "Validates fuel receipts against vehicle master physical tank capacity spec in Liters", "Rejects/flags receipts exceeding tank volume (e.g. 420L billed on 350L tank)", "Enterprise (₹1,000)"),
        ("Unapproved route detours & toll bypass shortcuts", "Extra distance burns excess diesel, increases tire wear, delays delivery", "Route Geo-Corridor Detection", "Calculates cross-track error from planned highway corridor; flags detours > threshold", "Alerts dispatchers to unauthorized detours; historical breadcrumb audit", "Professional (₹800)"),
        ("Vehicles sitting idle in depots due to poor status awareness", "Lost contribution margin (₹2,000–₹3,000/day); fixed overhead continues", "Vehicle Lifecycle State Machine", "Deterministic state control (Active, In Transit, Maintenance); availability grid", "Improves fleet availability oversight; stops double-booking and dispatch lag", "Starter (₹500)"),
        ("Dispatching drivers with expired licenses or medical fitness", "Vehicle police impoundment, statutory fines, insurance policy forfeiture", "Driver KYC & Document Review Queue", "Digital document submission with formal review queue; proactive 30/15-day alerts", "Blocks unverified drivers from dispatch; eliminates regulatory exposure", "Starter (₹500)"),
        ("Paper-based pre-trip vehicle safety inspection slips", "Unaddressed brake/tire defects cause catastrophic breakdown delays on highway", "Digital Pre-Trip Mobile Inspection", "Driver completes standardized 5-point safety check on Flutter mobile client", "Enforces roadworthiness compliance before vehicle leaves origin depot", "Professional (₹800)"),
        ("Unstructured trip coordination & lost delivery proofs", "Delayed client freight invoicing, lost toll receipts, customer disputes", "Trip Management & Milestone Tracking", "Complete manifest lifecycle: Draft → Dispatched → In Transit → Delivery POD", "Creates verifiable operational timeline for billing and post-trip expense audit", "Starter (₹500)"),
        ("Lost or ghost GPS hardware units across maintenance workshops", "Unnecessary repurchase of trackers; unmonitored trucks leak revenue", "Hardware Device Registry & Pairing", "Dynamic IMEI pairing wizard; automatic closure of previous truck assignments", "Maintains complete device provenance; eliminates ghost hardware churn", "Professional (₹800)"),
        ("Rogue or unmapped GPS trackers transmitting into system", "Data contamination, unauthorized telemetry, cross-company leakage", "Quarantine Isolation Vault", "Unmapped devices are trapped in dedicated quarantine tenant; Super-Admin review", "Zero-trust security; ensures telemetry integrity and regulatory isolation", "Enterprise (₹1,000)"),
        ("Managing multiple disjointed vendor portals & spreadsheets", "High administrative labor cost, data transcription errors, slow coordination", "Unified Fleet Command Center", "Consolidates vehicles, drivers, trips, telematics, and fuel in React 18 dashboard", "Single source of truth; reduces administrative overhead and information silos", "Starter (₹500)")
    ]

    for r_idx, row in enumerate(matrix_rows, 4):
        ws3.row_dimensions[r_idx].height = 26
        row_fill = PatternFill(start_color=GRAY_LIGHT if r_idx % 2 == 0 else WHITE,
                               end_color=GRAY_LIGHT if r_idx % 2 == 0 else WHITE,
                               fill_type="solid")
        
        for c_idx, val in enumerate(row, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.border = thin_border
            cell.fill = row_fill
            cell.font = data_font
            
            if c_idx in [1, 2, 3, 4, 5]:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if "Enterprise" in val:
                    cell.font = Font(name="Segoe UI", size=9.5, bold=True, color="1E1B4B")
                elif "Professional" in val:
                    cell.font = Font(name="Segoe UI", size=9.5, bold=True, color="065F46")
                else:
                    cell.font = Font(name="Segoe UI", size=9.5, bold=True, color="334155")

    col_w3 = {1: 30, 2: 32, 3: 26, 4: 42, 5: 38, 6: 22}
    for c, w in col_w3.items():
        ws3.column_dimensions[get_column_letter(c)].width = w

    out_xlsx = r"c:\Users\ratho\fleetguard\VAHAN_Financial_Impact_Assumptions.xlsx"
    wb.save(out_xlsx)
    print(f"Successfully generated: {out_xlsx}")

if __name__ == "__main__":
    build_financial_impact_workbook()
