@echo off
title AMINA FDS - Installation
echo ============================================
echo   AMINA FDS - Installation des dependances
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.10+ depuis https://www.python.org/downloads/
    echo IMPORTANT : cochez la case "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)

echo Python detecte. Installation des librairies necessaires...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ============================================
echo   Installation terminee avec succes !
echo   Vous pouvez maintenant lancer le fichier
echo   "2_lancer_AMINA_FDS.bat"
echo ============================================
pause
