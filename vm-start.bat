@echo off
title Menyalakan VM Singapura...
color 0a

set GCLOUD="C:\Users\eardisis\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set PROJECT=proxy-mesh-202611
set ZONE=asia-southeast1-b
set VM_NAME=vm-singapore-master

echo [INFO] Mengirim sinyal START ke %VM_NAME%...
%GCLOUD% compute instances start %VM_NAME% --zone=%ZONE% --project=%PROJECT%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [BERHASIL] Server VM Aktif!
    echo   Layanan *.ohana.biz.id akan segera siap (~20 detik).
    echo ========================================================
) else (
    echo.
    echo [GAGAL] Terjadi kesalahan saat menyalakan VM.
)
echo.
pause
