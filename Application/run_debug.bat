@echo off
chcp 65001 >nul
title VaultApp - Console de debug
cd /d "%~dp0"
echo ================================================
echo VaultApp - MODE DEBUG
echo Donnees fictives temporaires, coffre reel protege.
echo Les clics, resultats attendus et erreurs s'affichent ici.
echo Fermez la fenetre de l'application pour terminer.
echo ================================================
echo.
python -u main.py --debug
if errorlevel 1 (
    echo.
    echo [ERREUR] VaultApp s'est arretee avec une erreur.
) else (
    echo.
    echo [FIN] VaultApp s'est fermee normalement.
)
echo.
pause
