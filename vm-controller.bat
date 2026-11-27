@echo off
title VM Controller - vm-singapore-master
color 0b

set GCLOUD="C:\Users\eardisis\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set PROJECT=proxy-mesh-202611
set ZONE=asia-southeast1-b
set VM_NAME=vm-singapore-master

echo ========================================================
echo   GCP Remote VM Controller - %VM_NAME%
echo   Project: %PROJECT% | Zone: %ZONE%
echo ========================================================
echo.
echo   [1] Nyalakan Server VM (START / ON)
echo   [2] Matikan Server VM (STOP / OFF)
echo   [3] Cek Status Server VM
echo   [4] Keluar
echo.
echo ========================================================
set /p choice="Pilih menu [1-4]: "

if "%choice%"=="1" goto START_VM
if "%choice%"=="2" goto STOP_VM
if "%choice%"=="3" goto STATUS_VM
if "%choice%"=="4" goto END

echo Pilihan tidak valid.
goto END

:START_VM
echo.
echo [INFO] Menyalakan VM %VM_NAME%...
%GCLOUD% compute instances start %VM_NAME% --zone=%ZONE% --project=%PROJECT%
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [BERHASIL] VM telah dinyalakan!
    echo   Cloudflare Tunnel & Layanan *.ohana.biz.id akan
    echo   aktif otomatis dalam waktu ~15-30 detik.
    echo ========================================================
) else (
    echo.
    echo [ERROR] Gagal menyalakan VM. Pastikan koneksi internet aktif.
)
goto PAUSE_EXIT

:STOP_VM
echo.
echo [PERINGATAN] Anda akan mematikan VM %VM_NAME%.
set /p confirm="Lanjutkan mematikan VM? (y/n): "
if /i not "%confirm%"=="y" (
    echo Dibatalkan.
    goto END
)

echo.
echo [INFO] Mematikan VM %VM_NAME%...
%GCLOUD% compute instances stop %VM_NAME% --zone=%ZONE% --project=%PROJECT%
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [BERHASIL] VM telah dimatikan (STOPPED).
    echo   Penggunaan Compute Engine berhenti.
    echo ========================================================
) else (
    echo.
    echo [ERROR] Gagal mematikan VM.
)
goto PAUSE_EXIT

:STATUS_VM
echo.
echo [INFO] Memeriksa status VM...
%GCLOUD% compute instances describe %VM_NAME% --zone=%ZONE% --project=%PROJECT% --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
goto PAUSE_EXIT

:PAUSE_EXIT
echo.
pause

:END
