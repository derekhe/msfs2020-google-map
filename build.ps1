rm -r .\dist\
pyinstaller server.spec --onefile
pyinstaller offline-cache.spec --onefile
xcopy  certs .\dist\certs\
copy config.ini .\dist\
cd dist
7z a msfs2020-google-map-$((Get-Date).ToString("yyyy-MM-dd")).zip
cd ..