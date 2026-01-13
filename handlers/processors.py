import os, re, subprocess, zipfile, asyncio, shutil, time
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, FSInputFile, ReplyKeyboardRemove, 
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from config import TEMP_DIR, LIBREOFFICE_PATH
from utils.states import Form
from services.pdf_service import PDFService
from handlers.start import get_main_menu
from PIL import Image

router = Router()

# ==========================================
# 1. YORDAMCHI FUNKSIYALAR (Eng tepada bo'lishi shart)
# ==========================================

async def ask_rename_preference(message: Message, state: FSMContext, file_path: str, l10n: dict):
    """Fayl tayyor bo'lgach nom qo'yishni so'rash"""
    await state.update_data(final_file_path=file_path)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l10n['btn_ha'], callback_data="rename_yes"),
         InlineKeyboardButton(text=l10n['btn_yoq'], callback_data="rename_no")]
    ])
    await message.answer(l10n['ask_rename'], reply_markup=kb)
    await state.set_state(Form.waiting_for_rename_choice)

# ==========================================
# 2. NOM QO'YISH HANDLERLARI (Rename Logic)
# ==========================================

@router.callback_query(F.data == "rename_no", Form.waiting_for_rename_choice)
async def finalize_without_rename(callback: CallbackQuery, state: FSMContext, bot: Bot, l10n: dict, lang: str):
    data = await state.get_data()
    file_path = data.get('final_file_path')
    
    if not file_path or not os.path.exists(file_path):
        return await callback.message.answer(l10n['error_order'], reply_markup=get_main_menu(lang))

    await bot.send_chat_action(chat_id=callback.message.chat.id, action="upload_document")
    await callback.message.answer_document(FSInputFile(file_path), caption=l10n['done'], reply_markup=get_main_menu(lang))
    
    await callback.message.delete()
    await state.clear()
    if os.path.exists(file_path): os.remove(file_path)

@router.callback_query(F.data == "rename_yes", Form.waiting_for_rename_choice)
async def ask_for_name(callback: CallbackQuery, state: FSMContext, l10n: dict):
    await callback.message.answer(l10n['ask_new_name'])
    await state.set_state(Form.waiting_for_new_file_name)
    await callback.answer()

@router.message(Form.waiting_for_new_file_name)
async def finalize_with_custom_name(message: Message, state: FSMContext, bot: Bot, l10n: dict, lang: str):
    data = await state.get_data()
    file_path = data.get('final_file_path')
    new_name = message.text.strip()
    
    if not file_path or not os.path.exists(file_path):
        return await message.answer(l10n['error_order'], reply_markup=get_main_menu(lang))

    ext = Path(file_path).suffix
    full_name = f"{new_name}{ext}"
    
    await bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
    await message.answer_document(FSInputFile(file_path, filename=full_name), caption=l10n['done'], reply_markup=get_main_menu(lang))
    
    await state.clear()
    if os.path.exists(file_path): os.remove(file_path)

# ==========================================
# 3. ASOSIY PDF PROCESSOR (Barcha amallar)
# ==========================================

@router.message(Form.waiting_for_pdf, F.document)
async def process_pdf_unified(message: Message, state: FSMContext, bot: Bot, l10n: dict, lang: str):
    if not message.document.file_name.lower().endswith('.pdf'):
        return await message.answer(l10n['error_not_pdf'])
    
    data = await state.get_data()
    tool = data.get('current_tool')
    params = data.get('page_input', "")
    
    status_msg = await message.answer(l10n['processing'])
    temp_path = Path(TEMP_DIR).resolve()
    uid = f"{message.from_user.id}_{int(time.time())}"
    in_p = temp_path / f"in_{uid}.pdf"
    out_p = temp_path / f"out_{uid}.pdf"

    try:
        await bot.download_file((await bot.get_file(message.document.file_id)).file_path, str(in_p))

        # --- A. ORGANIZE ---
        if tool == "split":
            n = re.findall(r'\d+', params)
            await PDFService.split_pdf(str(in_p), str(out_p), int(n[0]), int(n[1]))
        elif tool in ["extract", "remove"]:
            pages = [int(p)-1 for p in re.findall(r'\d+', params)]
            await PDFService.process_pages(str(in_p), str(out_p), pages, tool)
        
        # --- B. SECURITY & EDIT ---
        elif tool == "protect":
            await PDFService.protect_pdf(str(in_p), str(out_p), data.get('pdf_password'))
        elif tool == "unlock":
            await PDFService.unlock_pdf(str(in_p), str(out_p), data.get('pdf_password'))
        elif tool == "rotate":
            await PDFService.rotate_pdf(str(in_p), str(out_p), data.get('rotate_angle', 90))
        elif tool == "numbers":
            await PDFService.add_page_numbers(str(in_p), str(out_p), data.get('number_pos', 'center'))
        elif tool == "watermark":
            await PDFService.add_watermark(str(in_p), str(out_p), data.get('watermark_text', "Nexora"))
        
        # --- C. CONVERT FROM PDF ---
        elif tool == "pdf_to_doc":
            out_doc = out_p.with_suffix(".docx")
            await asyncio.to_thread(PDFService.pdf_to_docx_sync, str(in_p), str(out_doc))
            out_p = out_doc
        elif tool == "pdf_to_jpg":
            img_paths = await asyncio.to_thread(PDFService.pdf_to_images_sync, str(in_p), str(temp_path))
            await status_msg.delete()
            for img in img_paths: await message.answer_photo(FSInputFile(img))
            await state.clear(); os.remove(str(in_p))
            return await message.answer(l10n['pages_sent'], reply_markup=get_main_menu(lang))

        # Windows Ready Check
        found = False
        for _ in range(15):
            if out_p.exists() and out_p.stat().st_size > 100:
                found = True; break
            await asyncio.sleep(0.5)

        if found:
            await status_msg.delete()
            await ask_rename_preference(message, state, str(out_p), l10n)
        else:
            raise Exception("Natija fayli yaratilmadi.")

    except Exception as e:
        await message.answer(l10n['error_generic'].format(e=e), reply_markup=get_main_menu(lang))
        if status_msg: await status_msg.delete()
        await state.clear()
    finally:
        if in_p.exists(): os.remove(str(in_p))

# ==========================================
# 4. MERGE, OFFICE VA JPG HANDLERLARI
# ==========================================

@router.message(Form.waiting_for_merge_files, F.document)
async def collect_merge(message: Message, state: FSMContext, bot: Bot, l10n: dict):
    data = await state.get_data()
    files = data.get('merge_files', [])
    path = Path(TEMP_DIR).resolve() / f"m_{message.from_user.id}_{len(files)}.pdf"
    await bot.download_file((await bot.get_file(message.document.file_id)).file_path, str(path))
    files.append(str(path))
    await state.update_data(merge_files=files)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=l10n['btn_ready'])]], resize_keyboard=True)
    await message.answer(l10n['file_added'].format(count=len(files)), reply_markup=kb)

@router.message(Form.waiting_for_merge_files, F.text, lambda m: any(word in m.text for word in ["Tayyor", "Done", "Готово"]))
async def finalize_merge(message: Message, state: FSMContext, bot: Bot, l10n: dict, lang: str):
    data = await state.get_data()
    files = data.get('merge_files', [])
    if len(files) < 2: return await message.answer(l10n['error_min_files'])
    
    status = await message.answer(l10n['wait'], reply_markup=ReplyKeyboardRemove())
    out = Path(TEMP_DIR).resolve() / f"merged_{message.from_user.id}.pdf"
    try:
        await PDFService.merge_pdfs(files, str(out))
        await status.delete()
        await ask_rename_preference(message, state, str(out), l10n)
    except Exception as e: await message.answer(l10n['error_generic'].format(e=e))
    finally:
        for f in files: 
            if os.path.exists(f): os.remove(f)

@router.message(Form.waiting_for_docx, F.document)
@router.message(Form.waiting_for_excel, F.document)
async def process_office_to_pdf(message: Message, state: FSMContext, bot: Bot, lang: str, l10n: dict):
    status = await message.answer(l10n['converting_to_pdf'])
    temp_p = Path(TEMP_DIR).resolve()
    ext = Path(message.document.file_name).suffix.lower()
    in_f = temp_p / f"off_{message.from_user.id}_{int(time.time())}{ext}"
    out_f = in_f.with_suffix(".pdf")
    prof = temp_p / f"p_{message.from_user.id}"

    try:
        await bot.download_file((await bot.get_file(message.document.file_id)).file_path, str(in_f))
        p_str, i_str, t_str = str(prof).replace('\\','/'), str(in_f).replace('\\','/'), str(temp_p).replace('\\','/')
        cmd = [LIBREOFFICE_PATH, f"-env:UserInstallation=file:///{p_str}", "--headless", "--convert-to", "pdf", "--outdir", t_str, i_str]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.communicate()
        
        for _ in range(20):
            if out_f.exists() and out_f.stat().st_size > 0: break
            await asyncio.sleep(0.5)

        if out_f.exists():
            await status.delete()
            await ask_rename_preference(message, state, str(out_f), l10n)
        else: raise Exception("Office conversion failed")
    except Exception as e: await message.answer(f"❌ Xato: {e}")
    finally:
        if in_f.exists(): os.remove(str(in_f))
        if prof.exists(): shutil.rmtree(str(prof), ignore_errors=True)

@router.message(Form.waiting_for_photo, F.photo | F.document)
async def collect_jpgs(message: Message, state: FSMContext, bot: Bot, l10n: dict):
    data = await state.get_data()
    files = data.get('jpg_files', [])
    f_id = message.photo[-1].file_id if message.photo else message.document.file_id
    ext = ".jpg" if message.photo else Path(message.document.file_name).suffix
    p = Path(TEMP_DIR).resolve() / f"j_{message.from_user.id}_{len(files)}{ext}"
    await bot.download_file((await bot.get_file(f_id)).file_path, str(p))
    files.append(str(p))
    await state.update_data(jpg_files=files)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=l10n['btn_ready'])]], resize_keyboard=True)
    await message.answer(l10n['images_added'].format(count=len(files)), reply_markup=kb)

@router.message(Form.waiting_for_photo, F.text, lambda m: any(word in m.text for word in ["Tayyor", "Done", "Готово"]))
async def finalize_jpg(message: Message, state: FSMContext, lang: str, l10n: dict):
    data = await state.get_data()
    files = data.get('jpg_files', [])
    if not files: return await message.answer(l10n['error_order'])
    status = await message.answer(l10n['wait'], reply_markup=ReplyKeyboardRemove())
    out = Path(TEMP_DIR).resolve() / f"img_res_{message.from_user.id}.pdf"
    processed = []
    try:
        import img2pdf
        for img_p in files:
            clean_p = Path(img_p).with_suffix('.tmp.jpg')
            with Image.open(img_p) as img:
                img.convert('RGB').save(str(clean_p), "JPEG", quality=90)
                processed.append(str(clean_p))
        with open(str(out), "wb") as f: f.write(img2pdf.convert(processed))
        await status.delete()
        await ask_rename_preference(message, state, str(out), l10n)
    except Exception as e: await message.answer(f"❌ Xato: {e}")
    finally:
        for f in files + processed:
            if os.path.exists(f): os.remove(f)

# ==========================================
# 5. QOLGAN PARAMETR HANDLERLARI
# ==========================================

@router.message(Form.waiting_for_zip_files, F.document | F.photo)
async def collect_zip(message: Message, state: FSMContext, bot: Bot, l10n: dict):
    data = await state.get_data()
    files = data.get('zip_files', [])
    f_id = message.document.file_id if message.document else message.photo[-1].file_id
    f_name = message.document.file_name if message.document else f"p_{len(files)}.jpg"
    p = Path(TEMP_DIR).resolve() / f"z_{message.from_user.id}_{f_name}"
    await bot.download_file((await bot.get_file(f_id)).file_path, str(p))
    files.append(str(p))
    await state.update_data(zip_files=files)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=l10n['btn_ready'])]], resize_keyboard=True)
    await message.answer(l10n['files_added'].format(count=len(files)), reply_markup=kb)

@router.message(Form.waiting_for_zip_files, F.text, lambda m: any(word in m.text for word in ["Tayyor", "Done", "Готово"]))
async def do_zip(message: Message, state: FSMContext, lang: str, l10n: dict):
    data = await state.get_data()
    files = data.get('zip_files', [])
    if not files: return await message.answer(l10n['error_order'])
    status = await message.answer(l10n['wait'], reply_markup=ReplyKeyboardRemove())
    out = Path(TEMP_DIR).resolve() / f"arch_{message.from_user.id}_{int(time.time())}.zip"
    try:
        with zipfile.ZipFile(str(out), 'w') as z:
            for f in files: z.write(f, Path(f).name)
        await status.delete()
        await ask_rename_preference(message, state, str(out), l10n)
    except Exception as e: await message.answer(f"❌ Xato: {e}")
    finally:
        for f in files:
            if os.path.exists(f): os.remove(f)

@router.message(Form.waiting_for_page_params)
async def get_page_params(message: Message, state: FSMContext, l10n: dict):
    await state.update_data(page_input=message.text)
    await message.answer(l10n['params_saved'].format(text=message.text), parse_mode="Markdown")
    await state.set_state(Form.waiting_for_pdf)

@router.message(Form.waiting_for_password)
async def get_pdf_password(message: Message, state: FSMContext, l10n: dict):
    await state.update_data(pdf_password=message.text)
    await message.answer(l10n['password_saved'])
    await state.set_state(Form.waiting_for_pdf)

@router.message(Form.waiting_for_watermark_text)
async def get_watermark_text(message: Message, state: FSMContext, l10n: dict):
    await state.update_data(watermark_text=message.text)
    await message.answer(l10n['watermark_saved'].format(text=message.text))
    await state.set_state(Form.waiting_for_pdf)

@router.message(F.document | F.photo, StateFilter(None))
async def err_no_state(message: Message, l10n: dict):
    await message.answer(l10n['error_order'])
