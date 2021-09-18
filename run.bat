@setlocal enableextensions
@cd /d "%~dp0"

py -m pip install -r requirements.txt
py src\app.py
pause