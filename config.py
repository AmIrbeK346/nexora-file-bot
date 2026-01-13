import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Faqat tizim yo'llari qoladi
if os.name == 'nt':  # Windows uchun
    LIBREOFFICE_PATH = r'C:\Program Files\LibreOffice\program\soffice.com'
    POPPLER_PATH = r'C:\Users\iskan\Downloads\poppler-25.12.0\Library\bin'
else:  # Linux (Railway) uchun
    LIBREOFFICE_PATH = 'soffice'
    POPPLER_PATH = None  

# Bazaga tegishli eski DB_PATH qismlari o'chirildi, 
# chunki db.py DATABASE_URL dan foydalanadi.

TEMP_DIR = "/tmp/telegram_file_bot" 
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
