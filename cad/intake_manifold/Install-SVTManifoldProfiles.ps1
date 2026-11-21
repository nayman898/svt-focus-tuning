$ErrorActionPreference = "Stop"

$running = Get-Process -Name "elegoo-slicer" -ErrorAction SilentlyContinue
if ($running) {
    Write-Error "Elegoo Slicer is running. Save your project, close it, and run this installer again."
}

$backupRoot = Join-Path $env:APPDATA "ElegooSlicer\user\default\_svt_manifold_profile_backups"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $backupRoot $stamp
$profileSets = @(
    @{
        Kind = "process"
        Source = Join-Path $PSScriptRoot "profiles\process"
        Target = Join-Path $env:APPDATA "ElegooSlicer\user\default\process"
    },
    @{
        Kind = "filament"
        Source = Join-Path $PSScriptRoot "profiles\filament"
        Target = Join-Path $env:APPDATA "ElegooSlicer\user\default\filament"
    }
)

foreach ($set in $profileSets) {
    if (-not (Test-Path $set.Source)) {
        throw "Profile source directory is missing: $($set.Source)"
    }
    if (-not (Test-Path $set.Target)) {
        throw "Elegoo Slicer $($set.Kind) preset directory was not found: $($set.Target)"
    }
}

New-Item -ItemType Directory -Path $backup -Force | Out-Null

foreach ($set in $profileSets) {
    $setBackup = Join-Path $backup $set.Kind
    New-Item -ItemType Directory -Path $setBackup -Force | Out-Null

    $profiles = Get-ChildItem $set.Source -File |
        Where-Object { $_.Extension -in ".json", ".info" }

    foreach ($profile in $profiles) {
        $destination = Join-Path $set.Target $profile.Name
        if (Test-Path $destination) {
            Copy-Item $destination $setBackup
        }
        Copy-Item $profile.FullName $destination -Force
        Write-Host "Installed $($set.Kind): $($profile.Name)"
    }
}

Write-Host ""
Write-Host "SVT Manifold PLA Pro presets installed successfully."
Write-Host "Backup: $backup"
Write-Host "Process (Manifold Demo): PLAPro_0.4_0.24_SVTManifold_Demo_TreeSupport_CC2"
Write-Host "Process (Fitment Gauges): PLAPro_0.4_0.20_SVTManifold_FitGauges_NoSupport_CC2"
Write-Host "Filament: PLAPro_SVTManifold_Demo_CC2"
