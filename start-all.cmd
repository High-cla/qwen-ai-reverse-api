@echo off
title Qwen-API Server (Python 3.14)
cd /d "%~dp0"

:: Use venv Python 3.14
.\venv\Scripts\python.exe start_server.py
