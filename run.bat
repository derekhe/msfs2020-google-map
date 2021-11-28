@setlocal enableextensions
@cd /d "%~dp0"

if exist .\Python39\python.exe (
    echo "Use embedded python"
    .\Python39\python.exe src\app.py
) else (
    echo "Use user python"
    py -m pip install -r requirements.txt
    py src\app.py
)

pause