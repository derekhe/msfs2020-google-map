@setlocal enableextensions
@cd /d "%~dp0"

python3\python.exe -m pip install -r requirements.txt
python3\python.exe src\app.py