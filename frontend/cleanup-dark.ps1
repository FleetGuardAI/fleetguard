Get-ChildItem -Path 'src' -Recurse -Include '*.jsx','*.js' | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match 'dark:') {
        $newContent = $content -replace '\s+dark:[a-zA-Z0-9\-_/\[\]\.]+', ''
        Set-Content $_.FullName $newContent -NoNewline
        Write-Host ("Cleaned: " + $_.Name)
    }
}
