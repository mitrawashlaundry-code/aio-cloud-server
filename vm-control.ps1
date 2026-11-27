<#
.SYNOPSIS
    Remote VM Management Script for vm-singapore-master
.DESCRIPTION
    Nyalakan, matikan, atau cek status server VM Singapura tanpa membuka Google Cloud Console.
.EXAMPLE
    .\vm-control.ps1 -Action start
    .\vm-control.ps1 -Action stop
    .\vm-control.ps1 -Action status
#>
[CmdletBinding()]
param (
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'restart')]
    [string]$Action
)

$gcloud = "C:\Users\eardisis\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$project = "proxy-mesh-202611"
$zone = "asia-southeast1-b"
$vm = "vm-singapore-master"

if (-not (Test-Path $gcloud)) {
    Write-Error "gcloud executable tidak ditemukan di: $gcloud"
    exit 1
}

function Show-Menu {
    Clear-Host
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "  GCP Remote VM Controller - $vm" -ForegroundColor Yellow
    Write-Host "  Project: $project | Zone: $zone" -ForegroundColor DarkGray
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host " [1] Nyalakan Server (START)" -ForegroundColor Green
    Write-Host " [2] Matikan Server (STOP)" -ForegroundColor Red
    Write-Host " [3] Restart Server" -ForegroundColor Yellow
    Write-Host " [4] Cek Status Server" -ForegroundColor Cyan
    Write-Host " [5] Keluar" -ForegroundColor Gray
    Write-Host "========================================================" -ForegroundColor Cyan
    
    $choice = Read-Host "Pilih menu [1-5]"
    switch ($choice) {
        "1" { return "start" }
        "2" { return "stop" }
        "3" { return "restart" }
        "4" { return "status" }
        default { return "exit" }
    }
}

if (-not $Action) {
    $Action = Show-Menu
}

if ($Action -eq "exit") {
    Write-Host "Selesai."
    exit 0
}

switch ($Action) {
    "start" {
        Write-Host "`n[INFO] Menyalakan VM $vm..." -ForegroundColor Cyan
        & $gcloud compute instances start $vm --zone=$zone --project=$project
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[SUKSES] VM telah aktif! Layanan di *.ohana.biz.id akan online sesaat lagi." -ForegroundColor Green
        }
    }
    "stop" {
        Write-Host "`n[INFO] Menghentikan VM $vm..." -ForegroundColor Yellow
        & $gcloud compute instances stop $vm --zone=$zone --project=$project
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[SUKSES] VM telah dimatikan (STOPPED). Penggunaan compute engine berhenti." -ForegroundColor Green
        }
    }
    "restart" {
        Write-Host "`n[INFO] Me-restart VM $vm..." -ForegroundColor Yellow
        & $gcloud compute instances reset $vm --zone=$zone --project=$project
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[SUKSES] Perintah reset VM berhasil dikirim." -ForegroundColor Green
        }
    }
    "status" {
        Write-Host "`n[INFO] Memeriksa status VM..." -ForegroundColor Cyan
        & $gcloud compute instances describe $vm --zone=$zone --project=$project --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
    }
}
