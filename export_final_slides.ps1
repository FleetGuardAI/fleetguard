$ErrorActionPreference = "Stop"

$workspace = Get-Location
$pptxPath = Join-Path $workspace "VAHAN_Interactive_Presentation_Final.pptx"
$qaDir = Join-Path $workspace "qa_slides_final"

if (!(Test-Path $qaDir)) {
    New-Item -ItemType Directory -Path $qaDir -Force | Out-Null
}

Write-Host "Opening PowerPoint COM to export final slides..."
$ppt = New-Object -ComObject PowerPoint.Application

try {
    $pres = $ppt.Presentations.Open($pptxPath, $false, $false, $false)
    Write-Host "Opened presentation. Total slides:" $pres.Slides.Count

    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
        $slide = $pres.Slides.Item($i)
        $imgName = ("slide_{0:D2}.png" -f $i)
        $imgPath = Join-Path $qaDir $imgName
        $slide.Export($imgPath, "PNG", 1920, 1080)
        Write-Host "Exported Slide $i -> $imgName"
    }

    $pres.Close()
    Write-Host "All 18 final slides exported successfully to $qaDir"
}
catch {
    Write-Host "Error during slide export:" $_.Exception.Message
    throw
}
finally {
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
