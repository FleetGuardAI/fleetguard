import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_visual_data_workbook():
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
    ALERT_FILL = "FEF2F2"       # Soft coral for loss exposure
    ALERT_TEXT = "D97770"
    
    title_font = Font(name="Segoe UI", size=15, bold=True, color=WHITE)
    subtitle_font = Font(name="Segoe UI", size=10, italic=True, color="E2E8F0")
    header_font = Font(name="Segoe UI", size=10, bold=True, color=WHITE)
    cat_font = Font(name="Segoe UI", size=11, bold=True, color=DARK_TEXT)
    data_font = Font(name="Segoe UI", size=10, color=DARK_TEXT)
    bold_data_font = Font(name="Segoe UI", size=10, bold=True, color=DARK_TEXT)
    input_data_font = Font(name="Segoe UI", size=10, bold=True, color=INPUT_FONT)
    formula_font = Font(name="Segoe UI", size=10, bold=True, color="065F46")
    alert_font = Font(name="Segoe UI", size=10, bold=True, color="991B1B")
    
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
    # SHEET 1: Fleet P&L Waterfall
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Fleet P&L Waterfall"
    ws1.views.sheetView[0].showGridLines = True
    
    ws1.merge_cells("A1:G1")
    ws1["A1"] = "50-TRUCK COMMERCIAL FLEET P&L & PROFIT WATERFALL MODEL"
    ws1["A1"].font = title_font
    ws1["A1"].fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.merge_cells("A2:G2")
    ws1["A2"] = "Illustrative Business Scenario — Not Actual Customer Data | Direct Mathematical Formulas"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws1["A2"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.row_dimensions[1].height = 32
    ws1.row_dimensions[2].height = 20
    ws1.row_dimensions[3].height = 26

    pnl_headers = [
        "P&L Operational Line Item",
        "% of Gross Revenue",
        "Per Vehicle / Month (₹)",
        "50-Truck Fleet / Month (₹)",
        "50-Truck Fleet / Annual (₹)",
        "Primary Operational Vulnerability",
        "VAHAN Control Module"
    ]
    for col_idx, h in enumerate(pnl_headers, 1):
        cell = ws1.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    pnl_rows = [
        ("Gross Freight Trip Revenue", "100.0%", 220000, "=C4*50", "=D4*12", "Contracted freight invoices from corporate shippers", "Trip Management"),
        ("1. Diesel / Fuel Expenditure", "48.0%", 105600, "=C5*50", "=D5*12", "Fuel siphoning, pump kickbacks, tank capacity fraud", "Fuel Intelligence AI"),
        ("2. Route Inefficiencies & Detours", "5.0%", 11000, "=C6*50", "=D6*12", "Unauthorized extra kilometers, unapproved detours", "Route Intelligence"),
        ("3. Tolls & Fastag Transit Costs", "10.0%", 22000, "=C7*50", "=D7*12", "Unapproved toll bypasses, unverified slips", "Driver Mobile & Expenses"),
        ("4. Driver Salaries & Allowances", "14.0%", 30800, "=C8*50", "=D8*12", "Unrecorded cash advances, trip bata discrepancies", "Driver KYC & Mobile"),
        ("5. Maintenance, Tires & Lubricants", "11.0%", 24200, "=C9*50", "=D9*12", "Excessive tire wear from off-corridor dirt roads", "Vehicle Lifecycle"),
        ("6. Insurance, Permits & Road Taxes", "5.0%", 11000, "=C10*50", "=D10*12", "Statutory fines, expired license impoundments", "Document KYC Review"),
        ("7. Administration & Dispatch Overhead", "4.0%", 8800, "=C11*50", "=D11*12", "Manual spreadsheets, 4+ separate GPS vendor logins", "Unified Owner Console"),
        ("TOTAL OPERATING EXPENDITURES", "97.0%", "=SUM(C5:C11)", "=SUM(D5:D11)", "=SUM(E5:E11)", "Cumulative operational cost drag consuming revenue", "Full VAHAN Platform"),
        ("NET OPERATING PROFIT MARGIN", "3.0%", "=C4-C12", "=D4-D12", "=E4-E12", "Thin margin vulnerable to unmonitored leakage", "Profit Protection Shield")
    ]

    for r_idx, row in enumerate(pnl_rows, 4):
        ws1.row_dimensions[r_idx].height = 24
        is_tot = r_idx in [12, 13]
        is_rev = r_idx == 4
        
        row_fill = PatternFill(start_color=SOFT_GREEN if is_rev else (INPUT_FILL if is_tot else (GRAY_LIGHT if r_idx % 2 == 0 else WHITE)),
                               end_color=SOFT_GREEN if is_rev else (INPUT_FILL if is_tot else (GRAY_LIGHT if r_idx % 2 == 0 else WHITE)),
                               fill_type="solid")
        
        for c_idx, val in enumerate(row, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.border = double_bottom_border if r_idx == 13 else thin_border
            cell.fill = row_fill
            cell.font = bold_data_font if is_tot or is_rev else data_font
            
            if c_idx in [1, 6, 7]:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif c_idx == 2:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                if isinstance(val, (int, float)) or (isinstance(val, str) and val.startswith("=")):
                    cell.number_format = "₹#,##0"

    col_w1 = {1: 34, 2: 18, 3: 24, 4: 26, 5: 28, 6: 48, 7: 24}
    for c, w in col_w1.items():
        ws1.column_dimensions[get_column_letter(c)].width = w

    # =========================================================================
    # SHEET 2: Scenario Calculator & Cohorts
    # =========================================================================
    ws2 = wb.create_sheet(title="Scenario Calculator & Cohorts")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:G1")
    ws2["A1"] = "FLEET FINANCIAL LEAKAGE & COHORT SENSITIVITY CALCULATOR"
    ws2["A1"].font = title_font
    ws2["A1"].fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    ws2["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws2.merge_cells("A2:G2")
    ws2["A2"] = "Sensitivity Analysis across 10, 25, 50, and 100 Commercial Vehicle Fleets"
    ws2["A2"].font = subtitle_font
    ws2["A2"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws2["A2"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws2.row_dimensions[1].height = 32
    ws2.row_dimensions[2].height = 20

    # Section 1: Baseline Unit Assumptions
    ws2.merge_cells("A4:G4")
    sec1 = ws2.cell(row=4, column=1, value="1. BASELINE UNIT ECONOMIC ASSUMPTIONS (EDITABLE YELLOW CELLS)")
    sec1.font = Font(name="Segoe UI", size=11, bold=True, color=WHITE)
    sec1.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    sec1.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[4].height = 24

    unit_assumps = [
        ("Monthly Fuel Spend per Commercial Truck", 105600, "₹ / truck / mo", "Estimated monthly diesel expense per vehicle"),
        ("Estimated Unexplained Fuel Leakage Exposure", 0.06, "% of fuel spend", "Loss from unmonitored siphoning & inflated pump slips (6.0%)"),
        ("Average Unapproved Extra Distance per Truck", 180, "km / truck / mo", "Detours, toll bypasses, off-corridor kilometers"),
        ("Operating Running Cost per Kilometre", 28.5, "₹ / km", "Direct variable operating cost per km (fuel + tires + wear)"),
        ("Avoidable Unscheduled Downtime Days", 1.5, "days / truck / mo", "Avoidable idle days from dispatching lag & maintenance delays"),
        ("Daily Net Contribution Margin per Vehicle", 2400, "₹ / day / truck", "Daily net margin contribution (Freight Revenue minus Direct Trip Fuel)"),
        ("Flagged Leakage Investigation & Resolution Rate", 0.60, "% success rate", "Realistic operational recovery rate under active management (60%)")
    ]
    for idx, (lbl, val, unit, note) in enumerate(unit_assumps, 5):
        ws2.row_dimensions[idx].height = 22
        ws2.cell(row=idx, column=1, value=lbl).font = bold_data_font
        ws2.cell(row=idx, column=1).border = thin_border
        
        c_val = ws2.cell(row=idx, column=2, value=val)
        c_val.font = input_data_font
        c_val.fill = PatternFill(start_color=INPUT_FILL, end_color=INPUT_FILL, fill_type="solid")
        c_val.alignment = Alignment(horizontal="right", vertical="center")
        c_val.border = thin_border
        if isinstance(val, float) and val < 1.0:
            c_val.number_format = "0.0%"
        elif isinstance(val, (int, float)) and val > 100:
            c_val.number_format = "₹#,##0"
            
        c_unit = ws2.cell(row=idx, column=3, value=unit)
        c_unit.font = data_font
        c_unit.border = thin_border
        
        ws2.merge_cells(start_row=idx, start_column=4, end_row=idx, end_column=7)
        c_note = ws2.cell(row=idx, column=4, value=note)
        c_note.font = Font(name="Segoe UI", size=9, italic=True, color=SEC_TEXT)
        c_note.border = thin_border

    # Section 2: Fleet Size Cohort Comparison Table
    curr = 13
    ws2.merge_cells(f"A{curr}:G{curr}")
    sec2 = ws2.cell(row=curr, column=1, value="2. FINANCIAL LEAKAGE & RECOVERY MATRIX BY FLEET SIZE COHORT")
    sec2.font = Font(name="Segoe UI", size=11, bold=True, color=WHITE)
    sec2.fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    sec2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[curr].height = 24
    curr += 1

    cohort_headers = [
        "Financial Metric / Scenario Output",
        "Calculation Logic / Formula",
        "10 Trucks Cohort",
        "25 Trucks Cohort",
        "50 Trucks Cohort",
        "100 Trucks Cohort",
        "Annualized Impact (50 Trucks)"
    ]
    for c_idx, h in enumerate(cohort_headers, 1):
        cell = ws2.cell(row=curr, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws2.row_dimensions[curr].height = 26
    curr += 1

    cohort_rows = [
        ("Monthly Fuel Siphoning & Fraud Exposure", "Fleet Size × Monthly Fuel Spend × 6%", "=10*$B$5*$B$6", "=25*$B$5*$B$6", "=50*$B$5*$B$6", "=100*$B$5*$B$6", "=E15*12"),
        ("Monthly Unauthorized Route Detour Cost", "Fleet Size × 180 km × ₹28.50/km", "=10*$B$7*$B$8", "=25*$B$7*$B$8", "=50*$B$7*$B$8", "=100*$B$7*$B$8", "=E16*12"),
        ("Monthly Avoidable Idle Downtime Drag", "Fleet Size × 1.5 Days × ₹2,400 Contribution", "=10*$B$9*$B$10", "=25*$B$9*$B$10", "=50*$B$9*$B$10", "=100*$B$9*$B$10", "=E17*12"),
        ("TOTAL ESTIMATED MONTHLY FINANCIAL EXPOSURE", "Sum of Fuel + Route + Downtime Loss", "=SUM(C15:C17)", "=SUM(D15:D17)", "=SUM(E15:E17)", "=SUM(F15:F17)", "=E18*12"),
        ("Illustrative Monthly Protected Profit (60%)", "Total Exposure × 60% Resolution Rate", "=C18*$B$11", "=D18*$B$11", "=E18*$B$11", "=F18*$B$11", "=E19*12"),
        ("VAHAN Enterprise Subscription Cost (₹1,000/mo)", "Fleet Size × ₹1,000 / truck / mo", "=10*1000", "=25*1000", "=50*1000", "=100*1000", "=E20*12"),
        ("NET FINANCIAL PROTECTION DELTA", "Protected Operating Profit Minus VAHAN Cost", "=C19-C20", "=D19-D20", "=E19-E20", "=F19-F20", "=E21*12")
    ]
    for r_data in cohort_rows:
        ws2.row_dimensions[curr].height = 24
        lbl, form_desc, c10, c25, c50, c100, c_ann = r_data
        is_net = "NET FINANCIAL" in lbl
        is_tot = "TOTAL" in lbl
        is_prot = "Protected Profit" in lbl
        
        ws2.cell(row=curr, column=1, value=lbl).font = bold_data_font if (is_net or is_tot or is_prot) else data_font
        ws2.cell(row=curr, column=1).border = thin_border
        
        ws2.cell(row=curr, column=2, value=form_desc).font = Font(name="Segoe UI", size=9, color=SEC_TEXT)
        ws2.cell(row=curr, column=2).border = thin_border
        
        for c_idx, val in enumerate([c10, c25, c50, c100, c_ann], 3):
            cell = ws2.cell(row=curr, column=c_idx, value=val)
            cell.border = double_bottom_border if is_net else thin_border
            cell.alignment = Alignment(horizontal="right", vertical="center")
            cell.number_format = "₹#,##0"
            if is_net:
                cell.font = formula_font
                cell.fill = PatternFill(start_color=FORMULA_FILL, end_color=FORMULA_FILL, fill_type="solid")
            elif is_tot:
                cell.font = alert_font
                cell.fill = PatternFill(start_color=ALERT_FILL, end_color=ALERT_FILL, fill_type="solid")
            elif is_prot:
                cell.font = formula_font
                cell.fill = PatternFill(start_color=SOFT_GREEN, end_color=SOFT_GREEN, fill_type="solid")
            else:
                cell.font = bold_data_font if c_idx == 7 else data_font
                
        curr += 1

    col_w2 = {1: 42, 2: 36, 3: 18, 4: 18, 5: 18, 6: 18, 7: 24}
    for c, w in col_w2.items():
        ws2.column_dimensions[get_column_letter(c)].width = w

    # =========================================================================
    # SHEET 3: Feature-to-Profitability Matrix
    # =========================================================================
    ws3 = wb.create_sheet(title="Feature Profitability Mapping")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:F1")
    ws3["A1"] = "VAHAN FEATURE-TO-PROFITABILITY VALUE MAPPING"
    ws3["A1"].font = title_font
    ws3["A1"].fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws3.merge_cells("A2:F2")
    ws3["A2"] = "Every Platform Capability Mapped Directly to Loss Mechanisms, Financial Value & Subscription Tiers"
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
        "Operational Control Mechanism",
        "Financial Profit Protection Value",
        "Relevant Subscription Plan"
    ]
    for c_idx, h in enumerate(matrix_headers, 1):
        cell = ws3.cell(row=3, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = PatternFill(start_color=EMERALD, end_color=EMERALD, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    matrix_rows = [
        ("Unnoticed fuel volume drops during highway rest stops", "Direct diesel loss (₹90+/L); inflates running cost per km", "Fuel Siphoning Anomaly AI", "Correlates tank drops with ignition OFF states; logs alert", "Detects fuel loss incidents in real-time with timestamps & GPS coords", "Enterprise (₹1,000)"),
        ("Inflated fuel purchase invoices submitted by drivers", "Paying for diesel that never entered the vehicle fuel tank", "Tank Capacity Physics Check", "Validates fuel receipts against vehicle master physical tank capacity (L)", "Rejects/flags receipts exceeding tank volume (e.g. 420L billed on 350L tank)", "Enterprise (₹1,000)"),
        ("Unapproved route detours & toll bypass shortcuts", "Extra distance burns excess diesel, increases tire wear, delays delivery", "Route Geo-Corridor Detection", "Calculates cross-track error from planned highway corridor; flags detours > threshold", "Alerts dispatchers to unauthorized detours; historical breadcrumb audit", "Professional (₹800)"),
        ("Vehicles sitting idle in depots due to poor status awareness", "Lost contribution margin (₹2,400/day); fixed overhead continues", "Vehicle Lifecycle State Machine", "Deterministic state control (Active, In Transit, Maintenance); availability grid", "Improves fleet availability oversight; stops double-booking and dispatch lag", "Starter (₹500)"),
        ("Dispatching drivers with expired licenses or medical fitness", "Vehicle police impoundment, statutory fines, insurance policy forfeiture", "Driver KYC & Document Review Queue", "Digital document submission with formal review queue; proactive 30/15-day alerts", "Blocks unverified drivers from dispatch; eliminates regulatory exposure", "Starter (₹500)"),
        ("Paper-based pre-trip vehicle safety inspection slips", "Unaddressed brake/tire defects cause catastrophic breakdown delays on highway", "Digital Pre-Trip Mobile Inspection", "Driver completes standardized 5-point safety check on Flutter mobile client", "Enforces roadworthiness compliance before vehicle leaves origin depot", "Professional (₹800)"),
        ("Unstructured trip coordination & lost delivery proofs", "Delayed client freight invoicing, lost toll receipts, customer disputes", "Trip Management & Milestone Engine", "Complete manifest lifecycle: Draft → Dispatched → In Transit → Delivery POD", "Creates verifiable operational timeline for billing and post-trip expense audit", "Starter (₹500)"),
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

    out_xlsx = r"c:\Users\ratho\fleetguard\VAHAN_Visual_Data_And_Assumptions.xlsx"
    wb.save(out_xlsx)
    print(f"Successfully generated: {out_xlsx}")

if __name__ == "__main__":
    build_visual_data_workbook()
