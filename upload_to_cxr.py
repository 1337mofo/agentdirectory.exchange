"""
Upload crawler to Creative XR Labs server via FTP
"""

from ftplib import FTP
import os

# Creative XR Labs FTP credentials
FTP_HOST = "ftp.creativexrlabs.com"
FTP_USER = "nova@creativexrlabs.com"
FTP_PASS = "573v3BKK2026!"

print("Connecting to Creative XR Labs FTP...")
ftp = FTP(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)

print(f"Connected! Current directory: {ftp.pwd()}")

# Upload crawler script
local_file = "crawler_continuous.py"
remote_file = "crawler_continuous.py"

print(f"Uploading {local_file}...")
with open(local_file, 'rb') as f:
    ftp.storbinary(f'STOR {remote_file}', f)

print("✅ Upload complete!")

# Create cron setup instructions
cron_instructions = """
# Add this to crontab to run crawler every hour
0 * * * * cd /home/nova && /usr/bin/python3 crawler_continuous.py >> crawler.log 2>&1
"""

with open("cron_setup.txt", "w") as f:
    f.write(cron_instructions)

print("\n" + "="*60)
print("CRAWLER UPLOADED TO CREATIVE XR LABS")
print("="*60)
print("\nNext steps (Steve to run via SSH):")
print("1. SSH into server")
print("2. Run: crontab -e")
print("3. Add line: 0 * * * * cd /home/nova && /usr/bin/python3 crawler_continuous.py >> crawler.log 2>&1")
print("4. Save and exit")
print("\nCrawler will run automatically every hour!")
print("="*60)

ftp.quit()
