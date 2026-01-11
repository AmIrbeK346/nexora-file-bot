import subprocess
from config import LIBREOFFICE_PATH

class DocService:
    @staticmethod
    async def docx_to_pdf(input_path, output_dir):
        # LibreOffice buyrug'i orqali konvertatsiya
        args = [
            LIBREOFFICE_PATH,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_path
        ]
        subprocess.run(args, check=True)
        return input_path.replace(".docx", ".pdf")