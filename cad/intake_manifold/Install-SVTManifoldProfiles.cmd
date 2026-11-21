@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-SVTManifoldProfiles.ps1"
if errorlevel 1 pause
