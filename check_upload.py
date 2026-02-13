from ftplib import FTP

FTP_HOST = "ftp.creativexrlabs.com"
FTP_USER = "nova@creativexrlabs.com"
FTP_PASS = "573v3BKK2026!"

ftp = FTP(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)

print("Files on server:")
ftp.retrlines('LIST')

ftp.quit()
