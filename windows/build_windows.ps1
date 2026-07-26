param(
    [string]$Version = "1.0.4"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "=== Red Sprite Filter Windows installer build ==="
Write-Host "Version: $Version"

python -m pip install --upgrade pip
python -m pip install -r src/requirements.txt
python windows/get_ffmpeg.py
pyinstaller windows/red_sprite_filter.spec --noconfirm --clean

$exe = Join-Path $Root "dist/red-sprite-filter.exe"
if (-not (Test-Path $exe)) {
    throw "PyInstaller did not produce $exe"
}

$isccCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "ISCC.exe"
)
$iscc = $null
foreach ($candidate in $isccCandidates) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $iscc = $cmd.Source
        break
    }
}
if (-not $iscc) {
    throw "Inno Setup compiler ISCC.exe was not found. Install Inno Setup 6 first."
}

& $iscc "/DMyAppVersion=$Version" "windows/red_sprite_filter.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}

$installer = Join-Path $Root "dist/installer/red-sprite-filter-setup.exe"
if (-not (Test-Path $installer)) {
    throw "Installer was not produced: $installer"
}

Get-FileHash $installer -Algorithm SHA256 | Format-List
Write-Host "DONE: $installer"
