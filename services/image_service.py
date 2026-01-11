from PIL import Image
import os

class ImageService:
    @staticmethod
    async def resize_image(input_path, output_path, width, height):
        # Bu funksiya rasmni o'lchamini o'zgartiradi
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path, "JPEG", quality=90)
        return output_path

    @staticmethod
    async def to_grayscale(input_path, output_path):
        # Bu funksiya rasmni oq-qora qiladi
        with Image.open(input_path) as img:
            gray = img.convert("L")
            gray.save(output_path)
        return output_path

    @staticmethod
    async def add_white_bg(input_path, output_path):
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                background.save(output_path, 'JPEG')
                return output_path
        return input_path