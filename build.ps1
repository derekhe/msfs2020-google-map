rm -r .\dist\
cd Python39
.\Python.exe -m pip install -r ..\requirements.txt
cd ..

copy config-prod.ini config.ini

7z -xr@7zignore a .\dist\msfs2020-google-map-$((Get-Date).ToString("yyyy-MM-dd")).zip