from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    waiting_for_page_params = State()   # Split, Extract, Remove uchun raqamlar
    waiting_for_pdf = State()         
    waiting_for_zip_files = State()
    waiting_for_merge_files = State()   # Merge uchun bir nechta PDF
    waiting_for_zip_files = State()     # ZIP qilish uchun fayllar yig'ish
    waiting_for_password = State()      # PDF Security uchun
    waiting_for_docx = State()          # Word to PDF uchun
    waiting_for_photo = State()         # Rasm asboblari uchun
    waiting_for_excel = State()
    waiting_for_watermark_text = State()
    waiting_for_number_pos = State()
    waiting_for_ad = State() # Reklama matnini kutish
    waiting_for_rename_choice = State() # Ha yoki Yo'q tanlovi uchun
    waiting_for_new_file_name = State() # Yangi nomni yozish uchun
