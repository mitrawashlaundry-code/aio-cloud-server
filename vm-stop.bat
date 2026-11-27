@echo off
title Mematikan VM Singapura...
color 0c

set GCLOUD="C:\Users\eardisis\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set PROJECT=proxy-mesh-202611
set ZONE=asia-southeast1-b
set VM_NAME=vm-singapore-master

echo [INFO] Mengirim sinyal STOP ke %VM_NAME%...
%GCLOUD% compute instances stop %VM_NAME% --zone=%ZONE% --project=%PROJECT%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [BERHASIL] Server VM Dimatikan (STOPPED).
    echo ========================================================
) else (
    echo.
    echo [GAGAL] Terjadi kesalahan saat mematikan VM.
)
echo.
pause
