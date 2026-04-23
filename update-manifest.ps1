# LegalDocuments klasöründeki tüm dosyaları tarayıp manifest.json'ı günceller.
# Kullanım: ./update-manifest.ps1

$folder  = Join-Path $PSScriptRoot "LegalDocuments"
$output  = Join-Path $folder "manifest.json"

$files = Get-ChildItem -Path $folder -File |
         Where-Object { $_.Name -ne "manifest.json" } |
         Sort-Object Name

$manifest = $files | ForEach-Object {
    $displayName = [System.IO.Path]::GetFileNameWithoutExtension($_.Name) -replace '[_]', ' '
    [ordered]@{
        name = $displayName
        file = $_.Name
    }
}

$json = if ($manifest) {
    $manifest | ConvertTo-Json -AsArray
} else {
    "[]"
}

[System.IO.File]::WriteAllText($output, $json, [System.Text.Encoding]::UTF8)

Write-Host "Manifest güncellendi: $($files.Count) dosya listelendi → $output"
