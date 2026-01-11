import os
import pikepdf
import img2pdf
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

class PDFService:
    # 1. PDFlarni birlashtirish (Organize -> Merge)
    @staticmethod
    async def merge_pdfs(input_paths, output_path):
        with pikepdf.Pdf.new() as merged:
            for path in input_paths:
                if os.path.exists(path):
                    with pikepdf.open(path) as src:
                        merged.pages.extend(src.pages)
            merged.save(output_path)

    @staticmethod
    def pdf_to_docx_sync(input_path, output_path):
        from pdf2docx import Converter
        cv = Converter(str(input_path))
        cv.convert(str(output_path), start=0, end=None)
        cv.close()

    @staticmethod
    def pdf_to_images_sync(input_path, output_dir):
        from pdf2image import convert_from_path
        from config import POPPLER_PATH
        images = convert_from_path(str(input_path), poppler_path=POPPLER_PATH)
        paths = []
        for i, img in enumerate(images[:10]):
            p = os.path.join(output_dir, f"p_{i+1}.jpg")
            img.save(p, "JPEG")
            paths.append(p)
        return paths
    # 2. PDFni diapazon bo'yicha bo'lish (Organize -> Split)
    @staticmethod
    async def split_pdf(input_path, output_path, start, end):
        with pikepdf.open(input_path) as pdf:
            with pikepdf.Pdf.new() as new_pdf:
                total = len(pdf.pages)
                # Foydalanuvchi kiritgan raqamlar 1-dan boshlanadi, indeks esa 0-dan
                for i in range(start - 1, min(end, total)):
                    new_pdf.pages.append(pdf.pages[i])
                new_pdf.save(output_path)

    # 3. Sahifalarni sug'urib olish yoki o'chirish (Organize -> Extract/Remove)
    @staticmethod
    async def process_pages(input_path, output_path, page_list, mode="extract"):
        with pikepdf.open(input_path) as pdf:
            with pikepdf.Pdf.new() as new_pdf:
                for i in range(len(pdf.pages)):
                    if mode == "extract" and i in page_list:
                        new_pdf.pages.append(pdf.pages[i])
                    elif mode == "remove" and i not in page_list:
                        new_pdf.pages.append(pdf.pages[i])
                new_pdf.save(output_path)

    # 4. PDFni parollash (Security -> Protect)
    @staticmethod
    async def protect_pdf(input_path, output_path, password):
        with pikepdf.open(input_path) as pdf:
            enc = pikepdf.Encryption(owner=password, user=password, allow=pikepdf.Permissions(accessibility=True))
            pdf.save(output_path, encryption=enc)

    # 5. Rasmlarni PDFga aylantirish (Convert TO PDF -> JPG to PDF)
    @staticmethod
    def convert_images_to_pdf(image_paths, output_path):
        import img2pdf
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_paths))
    
    # PDFni rasmga aylantirish (Convert FROM PDF -> PDF to JPG)
    @staticmethod
    async def pdf_to_images(input_path, output_dir):
        from pdf2image import convert_from_path
        from config import POPPLER_PATH
        # Poppler yo'li config.py da to'g'ri bo'lishi shart
        images = convert_from_path(input_path, poppler_path=POPPLER_PATH)
        paths = []
        for i, img in enumerate(images[:10]): # Xavfsizlik uchun limit 10 bet
            p = os.path.join(output_dir, f"page_{i+1}.jpg")
            img.save(p, "JPEG")
            paths.append(p)
        return paths

    # PDFni Wordga aylantirish (Convert FROM PDF -> PDF to WORD)
    @staticmethod
    async def pdf_to_docx(input_path, output_path):
        from pdf2docx import Converter
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
    # 6. PDFni aylantirish (Edit PDF -> Rotate)
    @staticmethod
    async def rotate_pdf(input_path, output_path, angle):
        with pikepdf.open(input_path) as pdf:
            for page in pdf.pages:
                page.Rotate = angle
            pdf.save(output_path)

    # 7. Parolni olib tashlash (Security -> Unlock)
    @staticmethod
    async def unlock_pdf(input_path, output_path, password):
        # Parol bilan ochamiz va parolsiz saqlaymiz
        with pikepdf.open(input_path, password=password) as pdf:
            pdf.save(output_path)
    
    @staticmethod
    async def add_page_numbers(input_path, output_path, position):
        reader = pikepdf.Pdf.open(input_path)
        
        for i, page in enumerate(reader.pages):
            packet = BytesIO()
            # Sahifa o'lchamini olamiz
            width = float(page.trimbox[2])
            height = float(page.trimbox[3])
            
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFont("Helvetica", 12)
            
            # Koordinatalarni hisoblash (pastdan 30 birim yuqorida)
            y = 30
            if position == "left":
                can.drawString(30, y, f"{i + 1}")
            elif position == "center":
                can.drawCentredString(width / 2, y, f"{i + 1}")
            elif position == "right":
                can.drawRightString(width - 30, y, f"{i + 1}")
            
            can.save()
            packet.seek(0)
            
            with pikepdf.open(packet) as overlay_pdf:
                page.add_overlay(overlay_pdf.pages[0])
        
        reader.save(output_path)
        reader.close()

    @staticmethod
    async def add_watermark(input_path, output_path, text):
        import pikepdf
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        reader = pikepdf.Pdf.open(input_path)
        for page in reader.pages:
            packet = BytesIO()
            width = float(page.trimbox[2])
            height = float(page.trimbox[3])
            
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFont("Helvetica-Bold", 50)
            can.setFillGray(0.5, 0.3) # 30% shaffoflik
            can.saveState()
            can.translate(width/2, height/2)
            can.rotate(45)
            can.drawCentredString(0, 0, text)
            can.restoreState()
            can.save()
            packet.seek(0)
            
            with pikepdf.open(packet) as overlay_pdf:
                page.add_overlay(overlay_pdf.pages[0])
        
        reader.save(output_path)
        reader.close()