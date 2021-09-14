@setlocal enableextensions
@cd /d "%~dp0"

python\python.exe -m pip install -r requirements.txt
python\python.exe src\app.py