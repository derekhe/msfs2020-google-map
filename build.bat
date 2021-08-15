pyinstaller server.spec --onefile
copy -R certs .\dist\
copy config.ini .\dist\