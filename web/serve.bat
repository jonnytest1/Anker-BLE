@echo off
cd /d "%~dp0"
echo Serving Anker BLE web client at http://127.0.0.1:8765/
echo Press Ctrl+C to stop.
echo.
python -m http.server 8765 --bind 127.0.0.1
if errorlevel 1 (
  echo Python not found. Try: py -m http.server 8765 --bind 127.0.0.1
  pause
)
