# Python 3.11 bazasidan foydalanamiz
FROM python:3.11-slim

# Tizim paketlarini yangilash va LibreOffice hamda Popplerni o'rnatish
RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ishchi papkani yaratish
WORKDIR /app

# Kutubxonalar ro'yxatini ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Hamma fayllarni serverga ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]