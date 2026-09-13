@echo off
title DentiFlow Multi-Device & Network Launcher
cd /d "%~dp0"

echo ===============================================================
echo  Starting DentiFlow Multi-Device Server...
echo ===============================================================

if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" share_network.py
pause
