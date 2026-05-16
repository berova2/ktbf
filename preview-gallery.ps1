param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$manifestScript = Join-Path $projectRoot "update-manifest.ps1"
$serverScript = Join-Path $projectRoot "local_server.py"

if (-not (Test-Path $manifestScript)) {
    throw "Manifest script not found: $manifestScript"
}

if (-not (Test-Path $serverScript)) {
    throw "Local server script not found: $serverScript"
}

Write-Host "[1/2] Manifestler guncelleniyor..."
& $manifestScript

$openArg = @()
if ($Open) {
    $openArg += "--open"
}

Write-Host "[2/2] Local sunucu baslatiliyor..."

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython $serverScript --host $BindHost --port $Port @openArg
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source $serverScript --host $BindHost --port $Port @openArg
    exit $LASTEXITCODE
}

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & $pyLauncher.Source -3 $serverScript --host $BindHost --port $Port @openArg
    exit $LASTEXITCODE
}

throw "Python bulunamadi. .venv veya sistem Python kurulu olmali."