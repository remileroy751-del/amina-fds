@echo off
title AMINA FDS - Creation de l'executable
echo ============================================
echo   Etape 1/2 : Creation du fichier .exe
echo ============================================
echo.

python -m pip install pyinstaller

echo.
echo Compilation en cours, veuillez patienter...
python -m PyInstaller --noconfirm --onefile --windowed --name "AMINA_FDS" --icon "installer\app_icon.ico" main.py

echo.
echo Copie du dossier "assets" (logo + image murale) a cote de l'executable...
if exist assets (
    xcopy /E /I /Y assets dist\assets >nul
)

echo.
echo ============================================
echo   Termine !
echo   L'executable brut se trouve dans
echo   "dist\AMINA_FDS.exe"
echo.
echo   ATTENTION : ce n'est PAS encore un
echo   installateur. Pour creer un vrai
echo   installateur Windows (avec raccourci
echo   Bureau automatique), lancez maintenant
echo   le script "4_creer_installateur.bat".
echo ============================================
pause
