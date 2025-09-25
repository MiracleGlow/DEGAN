@echo off
title Installer MG-DEV Degan
echo ========================================
echo  Instalasi MG-DEV Degan
echo ========================================
echo.

:: 1. Buat folder tujuan
mkdir "C:\mg-dev\app\degan"

:: 2. Pindahkan file degan.py dan degan.bat ke folder tujuan
move "%~dp0degan.py" "C:\mg-dev\app\degan\" >nul
move "%~dp0degan.bat" "C:\mg-dev\app\degan\" >nul

:: 3. Tambahkan PATH permanen
setx PATH "%PATH%;C:\mg-dev\app\degan"

echo.
echo Instalasi selesai!
echo Folder: C:\mg-dev\app\degan
echo File sudah dipindahkan dan PATH sudah ditambahkan.
echo Silakan buka terminal baru untuk mulai menggunakan.
pause
