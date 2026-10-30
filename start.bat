@echo off
rem Lancement par double-clic : contourne la politique d'execution des scripts PowerShell.
rem Arguments transmis a start.ps1 (ex. : start.bat console).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
if errorlevel 1 pause
