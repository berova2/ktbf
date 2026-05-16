# LegalDocuments ve EtkinlikGalerisi klasörlerindeki dosyaları tarayıp manifestleri günceller.
# Kullanım: ./update-manifest.ps1

function Write-JsonManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FolderPath,

        [Parameter(Mandatory = $true)]
        [scriptblock]$MapFile,

        [string[]]$IncludeExtensions = @()
    )

    $output = Join-Path $FolderPath "manifest.json"
    $allowed = @{}

    foreach ($ext in $IncludeExtensions) {
        $allowed[$ext.ToLowerInvariant()] = $true
    }

    $files = Get-ChildItem -Path $FolderPath -File |
        Where-Object {
            if ($_.Name -eq "manifest.json") { return $false }
            if ($IncludeExtensions.Count -eq 0) { return $true }
            return $allowed.ContainsKey($_.Extension.ToLowerInvariant())
        } |
        Sort-Object Name

    $manifest = $files | ForEach-Object { & $MapFile $_ }

    $json = if ($manifest) {
        $manifest | ConvertTo-Json -AsArray
    }
    else {
        "[]"
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($output, $json, $utf8NoBom)
    Write-Host "Manifest güncellendi: $($files.Count) dosya listelendi → $output"
}

$legalFolder = Join-Path $PSScriptRoot "LegalDocuments"
Write-JsonManifest -FolderPath $legalFolder -MapFile {
    param($file)
    $displayName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) -replace '[_-]', ' '
    [ordered]@{
        name = $displayName
        file = $file.Name
    }
}

$galleryFolder = Join-Path $PSScriptRoot "EtkinlikGalerisi"
if (-not (Test-Path $galleryFolder)) {
    New-Item -Path $galleryFolder -ItemType Directory | Out-Null
}

Write-JsonManifest -FolderPath $galleryFolder -IncludeExtensions @(".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg") -MapFile {
    param($file)
    $altText = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) -replace '[_-]', ' '
    [ordered]@{
        alt  = $altText
        file = $file.Name
    }
}
