@echo off
title AMINA FDS - Creation de l'installateur Windows
echo ================================================
echo   Etape 2/2 : Creation du vrai installateur
echo   (avec raccourci Bureau + menu Demarrer)
echo ================================================
echo.

if not exist "dist\AMINA_FDS.exe" (
    echo ERREUR : le fichier dist\AMINA_FDS.exe est introuvable.
    echo Lancez d'abord "3_creer_executable_exe.bat".
    echo.
    pause
    exit /b 1
)

set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo ================================================
    echo   Inno Setup n'est pas installe sur ce PC.
    echo   C'est un logiciel gratuit necessaire pour
    echo   fabriquer un vrai installateur Windows.
    echo.
    echo   1. Telechargez-le ici :
    echo      https://jrsoftware.org/isdl.php
    echo   2. Installez-le normalement (options par defaut^)
    echo   3. Relancez ce script.
    echo ================================================
    pause
    exit /b 1
)

echo Compilation de l'installateur en cours...
%ISCC% "installer\setup.iss"

echo.
echo ================================================
echo   Termine !
echo   Votre installateur se trouve dans :
echo   "installer\Output\AMINA_FDS_Setup.exe"
echo.
echo   C'est CE fichier qu'il faut envoyer/executer
echo   pour installer le logiciel correctement, avec
echo   creation automatique du raccourci sur le Bureau.
echo ================================================
pause
