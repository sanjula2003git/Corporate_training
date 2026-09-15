@echo off
cd /d "%~dp0"
set "HEART_PY=C:\Users\fersa\Documents\Codex\2026-09-08\b\.deploy-check\Scripts\python.exe"
if not exist "%HEART_PY%" set "HEART_PY=python"
"%HEART_PY%" -m streamlit run app.py --server.address localhost --server.port 8503
pause
