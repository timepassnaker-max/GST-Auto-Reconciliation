@echo off
echo Starting GST Reco AI...
echo.
REM Open Browser immediately
start http://127.0.0.1:8000

REM Run the backend server
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause
