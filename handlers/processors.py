import os, re, subprocess, zipfile, asyncio, shutil, time
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from config import TEMP_DIR, LIBREOFFICE_PATH
from utils.states import Form
from services.pdf_service import PDFService
from handlers.start import get_main_menu
from PIL import Image

router = Router()

# --- 1. MERGE PDF QISMI (Tuzatilgan) ---
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
    
    status_msg = await message.answer(l10n['wait'], reply_markup=ReplyKeyboardRemove())
    out = Path(TEMP_DIR).resolve() / f"merged_{message.from_user.id}.pdf"
    try:
        await PDFService.merge_pdfs(files, str(out))
        await message.answer_document(FSInputFile(str(out)), caption=l10n['done'], reply_markup=get_main_menu(lang))
    except Exception as e: await message.answer(l10n['error_generic'].format(e=e))
    finally:
        if status_msg: await status_msg.delete()
        await state.clear()
        for f in files + [str(out)]:
            if os.path.exists(f): os.remove(f)

# --- 2. OFFICE TO PDF (Tuzatilgan) ---
@router.message(Form.waiting_for_docx, F.document)
@router.message(Form.waiting_for_excel, F.document)
async def process_office_to_pdf(message: Message, state: FSMContext, bot: Bot, lang: str, l10n: dict):
    status = await message.answer(l10n['converting_to_pdf'])
    temp_p = Path(TEMP_DIR).resolve()
    ext = Path(message.document.file_name).suffix.lower()
    in_f = temp_p / f"off_{message.from_user.id}_{int(time.time())}{ext}"
    out_f = in_f.with_suffix(".pdf")
    prof = temp_p / f"p_{message.from_user.id}"
    file_name = message.document.file_name.lower()
    if not any(file_name.endswith(ext) for ext in ['.docx', '.doc', '.xlsx', '.xls']):
        return await message.answer(l10n['error_not_office'])
    try:
        await bot.download_file((await bot.get_file(message.document.file_id)).file_path, str(in_f))
        p_str, i_str, t_str = str(prof).replace('\\','/'), str(in_f).replace('\\','/'), str(temp_p).replace('\\','/')
        cmd = [LIBREOFFICE_PATH, f"-env:UserInstallation=file:///{p_str}", "--headless", "--convert-to", "pdf", "--outdir", t_str, i_str]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.communicate()
        
        for _ in range(15):
            if out_f.exists() and out_f.stat().st_size > 0: break
            await asyncio.sleep(0.5)

        await message.answer_document(FSInputFile(str(out_f)), caption=l10n['caption_ready'], reply_markup=get_main_menu(lang))
    except Exception as e: await message.answer(l10n['error_generic'].format(e=e))
    finally:
        if status: await status.delete()
        await state.clear()
        await asyncio.sleep(2)
        try:
            if in_f.exists(): os.remove(str(in_f))
            if out_f.exists(): os.remove(str(out_f))
            if prof.exists(): shutil.rmtree(str(prof), ignore_errors=True)
        except: pass

# --- 3. PARAMETRLARNI QABUL QILISH ---
@router.message(Form.waiting_for_page_params)
async def get_params(message: Message, state: FSMContext, l10n: dict):
    await state.update_data(page_input=message.text)
    await message.answer(l10n['params_saved'].format(text=message.text), parse_mode="Markdown")
    await state.set_state(Form.waiting_for_pdf)

# --- 4. JPG TO PDF VA ARXIV ---
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
    is_image = False
    if message.photo:
        is_image = True
    elif message.document and message.document.mime_type:
        if message.document.mime_type.startswith('image/'):
            is_image = True

    if not is_image:
        return await message.answer(l10n['error_not_image'])

@router.message(Form.waiting_for_photo, F.text, lambda m: any(word in m.text for word in ["Tayyor", "Done", "Готово"]))
async def finalize_jpg(message: Message, state: FSMContext, lang: str, l10n: dict):
    data = await state.get_data()
    files = data.get('jpg_files', [])
    
    if not files:
        return await message.answer(l10n['error_order'], reply_markup=get_main_menu(lang))

    status_msg = await message.answer(l10n['wait'], reply_markup=ReplyKeyboardRemove())
    temp_path = Path(TEMP_DIR).resolve()
    out = temp_path / f"img_res_{message.from_user.id}.pdf"
    
    processed_images = [] # Tozalangan rasmlar ro'yxati

    try:
        import img2pdf
        # 1. Har bir rasmni Pillow orqali "tozalab" JPEG formatiga keltiramiz
        for img_path in files:
            img_path_obj = Path(img_path)
            if img_path_obj.exists():
                clean_img_path = img_path_obj.with_suffix('.tmp.jpg')
                with Image.open(img_path) as img:
                    # Rasmni RGB formatiga o'tkazamiz (PNG alpha channel muammosini yo'qotadi)
                    rgb_img = img.convert('RGB')
                    rgb_img.save(str(clean_img_path), "JPEG", quality=90)
                    processed_images.append(str(clean_img_path))

        # 2. Endi toza rasmlarni PDF-ga aylantiramiz
        if processed_images:
            with open(str(out), "wb") as f:
                f.write(img2pdf.convert(processed_images))
            
            await message.answer_document(
                FSInputFile(str(out)), 
                caption=l10n['done'], 
                reply_markup=get_main_menu(lang)
            )
        else:
            raise Exception("Rasmlarni qayta ishlashda xatolik yuz berdi.")

    except Exception as e:
        print(f"CRITICAL JPG ERROR: {e}")
        await message.answer(f"❌ Xato: {e}", reply_markup=get_main_menu(lang))
    finally:
        if status_msg: await status_msg.delete()
        await state.clear()
        
        # 3. Barcha vaqtinchalik rasmlarni o'chirish
        all_to_delete = files + processed_images + [str(out)]
        for f in all_to_delete:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
#Parolni qabul qilish qismi
@router.message(Form.waiting_for_password)
async def get_pdf_password(message: Message, state: FSMContext, l10n: dict):
    # Faqat parolni yangilaymiz, 'current_tool' (protect/unlock) saqlanib qoladi
    await state.update_data(pdf_password=message.text)
    await message.answer(l10n['password_saved'])
    await state.set_state(Form.waiting_for_pdf)


# --- ARXIVLASH (ZIP) ---
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
        await message.answer_document(FSInputFile(str(out)), caption=l10n['done'], reply_markup=get_main_menu(lang))
    finally:
        if status: await status.delete()
        await state.clear()
        for f in files + [str(out)]:
            if os.path.exists(f): os.remove(f)

# --- 3. PARAMETRLAR VA PDF PROCESSOR (Organize/Security/From PDF) ---
@router.message(Form.waiting_for_page_params)
async def get_params(message: Message, state: FSMContext, l10n: dict):
    await state.update_data(page_input=message.text)
    await message.answer(l10n['params_saved'].format(text=message.text), parse_mode="Markdown")
    await state.set_state(Form.waiting_for_pdf)

@router.message(Form.waiting_for_pdf, F.document)
async def process_pdf_unified(message: Message, state: FSMContext, bot: Bot, l10n: dict, lang: str):
    data = await state.get_data()
    tool = data.get('current_tool')
    params = data.get('page_input', "")
    if not message.document.file_name.lower().endswith('.pdf'):
        return await message.answer(l10n['error_not_pdf'])
    # 1. "Ishlanmoqda" xabarini yuboramiz
    status_msg = await message.answer(l10n['processing'])
    
    # 2. Yo'llarni mutloq va unikal qilish
    temp_path = Path(TEMP_DIR).resolve()
    uid = f"{message.from_user.id}_{int(time.time())}"
    in_p = temp_path / f"in_{uid}.pdf"
    out_p = temp_path / f"out_{uid}.pdf"

    try:
        # 3. Faylni yuklab olish
        await bot.download_file((await bot.get_file(message.document.file_id)).file_path, str(in_p))

        # --- MANTIQIY BO'LIMLAR ---
        caption = l10n.get('done', "✅ Tayyor!")

        # A. CONVERT FROM PDF (WORD)
        if tool == "pdf_to_doc":
            out_doc = in_p.with_suffix(".docx")
            await asyncio.to_thread(PDFService.pdf_to_docx_sync, in_p, out_doc)
            out_p = out_doc # Yuborish uchun yo'lni almashtiramiz

        # B. CONVERT FROM PDF (JPG)
        elif tool == "pdf_to_jpg":
            img_paths = await asyncio.to_thread(PDFService.pdf_to_images_sync, in_p, temp_path)
            await asyncio.sleep(1)
            if img_paths:
                for img in img_paths:
                    if Path(img).exists():
                        await message.answer_photo(FSInputFile(img))
                        os.remove(img)
                return await message.answer(l10n['pages_sent'], reply_markup=get_main_menu(lang))
            else:
                raise Exception("Rasmlar yaratilmadi.")

        # C. ORGANIZE PDF (Split, Extract, Remove)
        elif tool == "split":
            n = re.findall(r'\d+', params)
            await PDFService.split_pdf(str(in_p), str(out_p), int(n[0]), int(n[1]))
        
        elif tool in ["extract", "remove"]:
            pages = [int(p)-1 for p in re.findall(r'\d+', params)]
            await PDFService.process_pages(str(in_p), str(out_p), pages, tool)

        # D. PDF SECURITY (Protect & Unlock)
        elif tool == "protect":
            password = data.get('pdf_password')
            await PDFService.protect_pdf(str(in_p), str(out_p), password)
            caption = l10n.get('password_saved', "🔒 PDF parollangan!")

        elif tool == "unlock":
            password = data.get('pdf_password')
            # Unlock funksiyasini chaqiramiz
            await PDFService.unlock_pdf(str(in_p), str(out_p), password)
            caption = "🔓 PDF paroli olib tashlandi!"

        # E. PDF EDIT (Rotate, Numbers, Watermark)
        elif tool == "rotate":
            angle = data.get('rotate_angle', 90)
            await PDFService.rotate_pdf(str(in_p), str(out_p), angle)
            caption = l10n.get('rotate_selected', "🔄 Aylantirildi!").format(angle=angle)
        
        elif tool == "numbers":
            pos = data.get('number_pos', 'center')
            await PDFService.add_page_numbers(str(in_p), str(out_p), pos)
        
        elif tool == "watermark":
            wm_text = data.get('watermark_text', "FileForge Bot")
            await PDFService.add_watermark(str(in_p), str(out_p), wm_text)

        # --- YAKUNIY PDF YUBORISH (Windows Ready Check) ---
        # Rotate va Security amallari uchun ham tayyorlikni tekshiramiz
        found = False
        for _ in range(15): # 7.5 soniya kutadi
            if out_p.exists() and out_p.stat().st_size > 100:
                found = True
                break
            await asyncio.sleep(0.5)

        if found:
            await asyncio.sleep(0.5) # Final buffer
            await message.answer_document(
                FSInputFile(str(out_p), filename=f"result_{message.document.file_name}"), 
                caption=caption, 
                reply_markup=get_main_menu(lang)
            )
        else:
            raise Exception("Natija fayli yaratilmadi yoki tizim tomonidan band qilingan.")

    except Exception as e:
        print(f"SYSTEM ERROR: {e}") # Xatoni faqat o'zingiz terminalda ko'rasiz
        await message.answer(l10n['error_order'], reply_markup=get_main_menu(lang))
    finally:
        # Xabarni o'chirish va tozalash
        if status_msg:
            try: await status_msg.delete()
            except: pass
        await state.clear()
        # Fayllarni o'chirish
        for f in [str(in_p), str(out_p)]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

    
    
@router.message(Form.waiting_for_watermark_text)
async def get_watermark_text(message: Message, state: FSMContext, l10n: dict):
    # Matnni xotiraga saqlaymiz
    await state.update_data(watermark_text=message.text)
    
    # Xabarni lug'atdan olamiz (Error bermasligi uchun .format() ishlatamiz)
    text = l10n.get('watermark_saved', "✅ Text saved: {text}").format(text=message.text)
    
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(Form.waiting_for_pdf) # Endi fayl kutish holatiga o'tamiz       
    

# --- ERROR HANDLERS ---
@router.message(F.document | F.photo, StateFilter(None))
async def err_no_state(message: Message, l10n: dict):
    await message.answer(l10n['error_order'])