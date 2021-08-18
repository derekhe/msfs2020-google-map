pyinstaller server.spec --onefile
xcopy  certs .\dist\certs\
copy config.ini .\dist\