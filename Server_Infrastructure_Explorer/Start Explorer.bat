@echo off
cd /d "%~dp0"
set "EXPLORER_PY=C:\Users\fersa\Documents\Codex\integrations\blender-mcp\venv\Scripts\python.exe"
if exist "%EXPLORER_PY%" goto run
set "EXPLORER_PY=python"
:run
"%EXPLORER_PY%" -m streamlit run app.py --server.address localhost --server.port 8501
pause
