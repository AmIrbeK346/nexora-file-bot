import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


if os.name == 'nt':  # Windows uchun
    LIBREOFFICE_PATH = r'C:\Program Files\LibreOffice\program\soffice.com'
    POPPLER_PATH = r'C:\Users\iskan\Downloads\poppler-25.12.0\Library\bin'
else:  # Linux (Railway/Server) uchun
    LIBREOFFICE_PATH = 'soffice'
    POPPLER_PATH = None  
if os.name == 'nt': # Windows uchun (mahalliy test)
    DB_PATH = "bot_database.db"
else: # Linux (Railway) uchun doimiy yo'l
    DB_PATH = "/data/bot_database.db"
TEMP_DIR = "/tmp/telegram_file_bot" # Serverda /tmp papkasi xavfsizroq
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
