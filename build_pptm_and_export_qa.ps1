# =============================================================================
# VAHAN PPTM BUILDER & SLIDE QA EXPORTER
# =============================================================================
$ErrorActionPreference = "Stop"

$workspace = Get-Location
$pptxPath = Join-Path $workspace "VAHAN_Interactive_Presentation.pptx"
$pptmPath = Join-Path $workspace "VAHAN_Interactive_Presentation.pptm"
$qaDir = Join-Path $workspace "qa_slides"

if (!(Test-Path $qaDir)) {
    New-Item -ItemType Directory -Path $qaDir -Force | Out-Null
}

Write-Host "Starting PowerPoint COM automation..."
$ppt = New-Object -ComObject PowerPoint.Application

try {
    # Open presentation
    $pres = $ppt.Presentations.Open($pptxPath, $false, $false, $false)
    Write-Host "Opened PPTX presentation. Total slides:" $pres.Slides.Count

    # Ensure AccessVBOM is enabled
    $secPath = "HKCU:\Software\Microsoft\Office\16.0\PowerPoint\Security"
    Set-ItemProperty -Path $secPath -Name "AccessVBOM" -Value 1 -Type DWord -ErrorAction SilentlyContinue

    # First save as PPTM
    $pres.SaveAs($pptmPath, 25) # 25 = ppSaveAsOpenXMLPresentationMacroEnabled
    Write-Host "Saved baseline PPTM at: $pptmPath"
    $pres.Close()

    # Re-open the PPTM to configure VBA and macro action settings
    $pres = $ppt.Presentations.Open($pptmPath, $false, $false, $false)

    # 1. Add VBA Module
    $vbaProj = $pres.VBProject
    $module = $vbaProj.VBComponents.Add(1) # 1 = vbext_ct_StdModule
    $module.Name = "VAHAN_ScenarioEngine"

    $vbaCode = @"
Attribute VB_Name = "VAHAN_ScenarioEngine"
' =============================================================================
' VAHAN CONNECTED FLEET MANAGEMENT — INTERACTIVE SCENARIO SIMULATOR
' Dynamic Financial Modeling Engine for Commercial Transport Fleets
' =============================================================================

Public Sub RunScenarioCalculator()
    Dim sInput As String
    Dim fleetSize As Long
    Dim fuelSpend As Double
    Dim fuelDrainPct As Double
    Dim detourKm As Double
    Dim costPerKm As Double
    Dim downtimeDays As Double
    Dim dailyMargin As Double
    Dim recoveryPct As Double
    Dim planRate As Double
    
    ' 1. Prompt Fleet Size
    sInput = InputBox("Enter Commercial Fleet Size (Number of Trucks):", "VAHAN Simulator — Step 1/4", "50")
    If sInput = "" Or Not IsNumeric(sInput) Then Exit Sub
    fleetSize = CLng(sInput)
    If fleetSize <= 0 Then Exit Sub

    ' 2. Prompt Monthly Fuel Spend
    sInput = InputBox("Enter Monthly Fuel Spend per Truck in ₹:" & vbCrLf & "(Baseline: 1,100 Litres @ ₹96/L = ₹1,05,600)", "VAHAN Simulator — Step 2/4", "105600")
    If sInput = "" Or Not IsNumeric(sInput) Then Exit Sub
    fuelSpend = CDbl(sInput)

    ' 3. Prompt Estimated Fuel Leakage %
    sInput = InputBox("Enter Estimated Unexplained Fuel Leakage %:" & vbCrLf & "(Industry average: 4% to 8%)", "VAHAN Simulator — Step 3/4", "6.0")
    If sInput = "" Or Not IsNumeric(sInput) Then Exit Sub
    fuelDrainPct = CDbl(sInput)

    ' 4. Prompt VAHAN Target Recovery Resolution %
    sInput = InputBox("Enter VAHAN Target Leakage Prevention & Recovery %:" & vbCrLf & "(Conservative: 50% | Calibrated: 60% | Aggressive: 75%)", "VAHAN Simulator — Step 4/4", "60.0")
    If sInput = "" Or Not IsNumeric(sInput) Then Exit Sub
    recoveryPct = CDbl(sInput)

    ' Fixed calibrated operational unit economics
    detourKm = 180#        ' km/truck/month
    costPerKm = 28.5       ' ₹/km heavy commercial vehicle
    downtimeDays = 1.5     ' avoidable breakdown days/truck/month
    dailyMargin = 2400#    ' daily vehicle contribution margin
    planRate = 800#        ' Professional tier rate per truck/month

    ' -------------------------------------------------------------------------
    ' MATHEMATICAL LOSS & RECOVERY COMPUTATIONS
    ' -------------------------------------------------------------------------
    Dim moFuelLoss As Double
    Dim moDetourLoss As Double
    Dim moDowntimeLoss As Double
    Dim totalMoLoss As Double
    Dim totalYrLoss As Double
    Dim moProtected As Double
    Dim yrProtected As Double
    Dim moVahanCost As Double
    Dim yrVahanCost As Double
    Dim netMoGain As Double
    Dim netYrGain As Double
    Dim roiMultiple As Double
    Dim paybackDays As Double

    moFuelLoss = fleetSize * fuelSpend * (fuelDrainPct / 100#)
    moDetourLoss = fleetSize * detourKm * costPerKm
    moDowntimeLoss = fleetSize * downtimeDays * dailyMargin
    
    totalMoLoss = moFuelLoss + moDetourLoss + moDowntimeLoss
    totalYrLoss = totalMoLoss * 12#
    
    moProtected = totalMoLoss * (recoveryPct / 100#)
    yrProtected = moProtected * 12#
    
    moVahanCost = fleetSize * planRate
    yrVahanCost = moVahanCost * 12#
    
    netMoGain = moProtected - moVahanCost
    netYrGain = yrProtected - yrVahanCost
    
    If moVahanCost > 0 Then
        roiMultiple = moProtected / moVahanCost
        paybackDays = (moVahanCost / moProtected) * 30#
    Else
        roiMultiple = 0
        paybackDays = 0
    End If

    ' -------------------------------------------------------------------------
    ' UPDATE SLIDE 15 VISUAL SHAPES
    ' -------------------------------------------------------------------------
    On Error Resume Next
    Dim sld15 As Slide
    Set sld15 = ActivePresentation.Slides(15)
    
    Dim shp As Shape
    For Each shp In sld15.Shapes
        If shp.HasTextFrame Then
            Dim txt As String
            txt = shp.TextFrame.TextRange.Text
            If InStr(txt, "₹7,53,300") > 0 Or InStr(txt, "UNMANAGED MONTHLY") > 0 Then
                shp.TextFrame.TextRange.Text = "UNMANAGED MONTHLY FINANCIAL LEAKAGE" & vbCrLf & _
                    FormatCurrency(totalMoLoss, 0) & " / Month  (" & FormatCurrency(totalYrLoss, 0) & " / Year)"
            ElseIf InStr(txt, "₹4,51,980") > 0 Or InStr(txt, "VERIFIED 60% PROFIT") > 0 Then
                shp.TextFrame.TextRange.Text = "VERIFIED " & Format(recoveryPct, "0") & "% PROFIT PROTECTION RECOVERY" & vbCrLf & _
                    FormatCurrency(moProtected, 0) & " / Month  (" & FormatCurrency(yrProtected, 0) & " / Year)"
            ElseIf InStr(txt, "₹4,11,980") > 0 Or InStr(txt, "NET CASH FLOW") > 0 Then
                shp.TextFrame.TextRange.Text = "NET CASH FLOW ADDED TO OWNER BOTTOM LINE" & vbCrLf & _
                    FormatCurrency(netMoGain, 0) & " / Month  (" & FormatCurrency(netYrGain, 0) & " / Year)" & vbCrLf & _
                    "Return Multiple: " & Format(roiMultiple, "0.0") & "x ROI  |  Payback: " & Format(paybackDays, "0.0") & " Days"
            End If
        End If
    Next shp
    On Error GoTo 0

    ' -------------------------------------------------------------------------
    ' DISPLAY EXECUTIVE MODAL SUMMARY
    ' -------------------------------------------------------------------------
    Dim msg As String
    msg = "=========================================" & vbCrLf & _
          "   VAHAN FINANCIAL SCENARIO SIMULATION   " & vbCrLf & _
          "=========================================" & vbCrLf & vbCrLf & _
          "FLEET PARAMETERS:" & vbCrLf & _
          "  • Fleet Size: " & fleetSize & " Commercial Trucks" & vbCrLf & _
          "  • Monthly Fuel Spend: " & FormatCurrency(fuelSpend, 0) & " / truck" & vbCrLf & _
          "  • Fuel Siphoning Rate: " & Format(fuelDrainPct, "0.0") & "%" & vbCrLf & _
          "  • Target Recovery Rate: " & Format(recoveryPct, "0.0") & "%" & vbCrLf & vbCrLf & _
          "IDENTIFIED FINANCIAL EXPOSURE:" & vbCrLf & _
          "  • Fuel Loss: " & FormatCurrency(moFuelLoss, 0) & " / month" & vbCrLf & _
          "  • Route Detours: " & FormatCurrency(moDetourLoss, 0) & " / month" & vbCrLf & _
          "  • Downtime Loss: " & FormatCurrency(moDowntimeLoss, 0) & " / month" & vbCrLf & _
          "  • TOTAL LEAKAGE: " & FormatCurrency(totalMoLoss, 0) & " / mo (" & FormatCurrency(totalYrLoss, 0) & " / yr)" & vbCrLf & vbCrLf & _
          "VAHAN PLATFORM FINANCIAL IMPACT:" & vbCrLf & _
          "  • Protected Cash Flow: " & FormatCurrency(moProtected, 0) & " / mo (" & FormatCurrency(yrProtected, 0) & " / yr)" & vbCrLf & _
          "  • Professional Plan Fee: " & FormatCurrency(moVahanCost, 0) & " / mo" & vbCrLf & _
          "  -------------------------------------------------" & vbCrLf & _
          "  • NET OWNER PROFIT: " & FormatCurrency(netMoGain, 0) & " / mo (" & FormatCurrency(netYrGain, 0) & " / yr)" & vbCrLf & _
          "  • RETURN ON INVESTMENT: " & Format(roiMultiple, "0.0") & "x Multiplier" & vbCrLf & _
          "  • INVESTMENT PAYBACK: " & Format(paybackDays, "0.0") & " Days" & vbCrLf & vbCrLf & _
          "Slide 15 metrics have been dynamically updated."

    MsgBox msg, vbInformation, "VAHAN Fleet Scenario Result"
End Sub

Public Sub ResetScenarioDefaults()
    On Error Resume Next
    Dim sld15 As Slide
    Set sld15 = ActivePresentation.Slides(15)
    
    Dim shp As Shape
    For Each shp In sld15.Shapes
        If shp.HasTextFrame Then
            Dim txt As String
            txt = shp.TextFrame.TextRange.Text
            If InStr(txt, "UNMANAGED MONTHLY") > 0 Then
                shp.TextFrame.TextRange.Text = "UNMANAGED MONTHLY FINANCIAL LEAKAGE" & vbCrLf & _
                    "₹7,53,300 / Month  (₹90,39,600 / Year)"
            ElseIf InStr(txt, "PROFIT PROTECTION RECOVERY") > 0 Then
                shp.TextFrame.TextRange.Text = "VERIFIED 60% PROFIT PROTECTION RECOVERY" & vbCrLf & _
                    "₹4,51,980 / Month  (₹54,23,760 / Year)"
            ElseIf InStr(txt, "NET CASH FLOW") > 0 Then
                shp.TextFrame.TextRange.Text = "NET CASH FLOW ADDED TO OWNER BOTTOM LINE" & vbCrLf & _
                    "₹4,11,980 / Month  (₹49,43,760 / Year)" & vbCrLf & _
                    "Return Multiple: 11.3x ROI  |  Payback: 2.7 Days"
            End If
        End If
    Next shp
    On Error GoTo 0
    
    MsgBox "Simulator metrics reset to 50-Truck Baseline:" & vbCrLf & _
           "• Monthly Leakage: ₹7,53,300" & vbCrLf & _
           "• 60% Protected: ₹4,51,980/mo (₹54.24 Lakh/yr)" & vbCrLf & _
           "• Net Bottom-Line Profit: ₹4,11,980/mo (11.3x ROI)", _
           vbInformation, "VAHAN Simulator — Baseline Restored"
End Sub
"@

    $module.CodeModule.AddFromString($vbaCode)
    Write-Host "VBA Scenario Engine Module injected successfully."

    # 2. Hook up Slide 15 action buttons to call VBA macros
    $slide15 = $pres.Slides.Item(15)
    $hookedCalc = $false
    $hookedReset = $false

    foreach ($shp in $slide15.Shapes) {
        if ($shp.HasTextFrame) {
            $t = $shp.TextFrame.TextRange.Text
            if ($t -like "*Calculate ROI*") {
                # ppActionRunMacro is 8
                $shp.ActionSettings.Item(1).Action = 8
                $shp.ActionSettings.Item(1).Run = "RunScenarioCalculator"
                $hookedCalc = $true
                Write-Host "Hooked 'Calculate ROI' button to RunScenarioCalculator macro."
            }
            elseif ($t -like "*Reset Baseline*") {
                $shp.ActionSettings.Item(1).Action = 8
                $shp.ActionSettings.Item(1).Run = "ResetScenarioDefaults"
                $hookedReset = $true
                Write-Host "Hooked 'Reset Baseline' button to ResetScenarioDefaults macro."
            }
        }
    }

    $pres.Save()
    Write-Host "Macro-enabled presentation saved successfully."

    # 3. Export all 18 slides to high-res PNG for visual QA and reportlab PDF
    Write-Host "Exporting all 18 slides to high-resolution PNG for QA..."
    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
        $slide = $pres.Slides.Item($i)
        $imgName = ("slide_{0:D2}.png" -f $i)
        $imgPath = Join-Path $qaDir $imgName
        # 1920x1080 resolution
        $slide.Export($imgPath, "PNG", 1920, 1080)
        Write-Host "Exported Slide $i -> $imgName"
    }

    $pres.Close()
    Write-Host "PPTM build and slide export completed successfully!"
}
catch {
    Write-Host "Error occurred: " $_.Exception.Message
    throw
}
finally {
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
