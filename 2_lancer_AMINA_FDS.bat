@echo off
title AMINA FDS
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Une erreur s'est produite. Verifiez que l'installation a bien ete faite
    echo en executant d'abord "1_installer.bat".
    pause
)
