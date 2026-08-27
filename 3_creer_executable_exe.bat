@echo off
title AMINA FDS - Creation de l'executable
echo ============================================
echo   Creation d'un fichier .exe autonome
echo   (a executer UNE SEULE FOIS)
echo ============================================
echo.

python -m pip install pyinstaller

echo.
echo Compilation en cours, veuillez patienter...
python -m PyInstaller --noconfirm --onefile --windowed --name "AMINA_FDS" main.py

echo.
echo Copie du dossier "assets" (logo + image murale) a cote de l'executable...
if exist assets (
    xcopy /E /I /Y assets dist\assets >nul
)

echo.
echo ============================================
echo   Termine !
echo   Votre executable se trouve dans le dossier
echo   "dist\AMINA_FDS.exe"
echo   IMPORTANT : gardez le dossier "assets" juste
echo   a cote du fichier .exe (meme dossier), sinon
echo   le logo et les decorations ne s'afficheront pas.
echo   Vous pouvez copier tout le dossier "dist" sur
echo   le Bureau et creer un raccourci vers le .exe.
echo ============================================
pause
