import os
import tempfile
from pathlib import Path

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
POPPLER_PATH = r'C:\Users\iskan\Downloads\poppler-25.12.0\Library\bin' 

# DIQQAT: .exe emas, .com bo'lishi shart!
LIBREOFFICE_PATH = r'C:\Program Files\LibreOffice\program\soffice.com'

# Windows vaqtinchalik papkasi
TEMP_DIR = os.path.join(tempfile.gettempdir(), "telegram_file_bot")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)