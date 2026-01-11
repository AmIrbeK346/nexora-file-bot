from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import Form

router = Router()

# ==========================================
# 1. ASOSIY REPLAY MENYU TUGMALARI
# ==========================================

@router.message(F.text.contains("Organize PDF"))
async def menu_organize(message: Message, l10n: dict):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Merge PDF", callback_data="tool_merge")],
        [InlineKeyboardButton(text="✂️ Split PDF", callback_data="tool_split")],
        [InlineKeyboardButton(text="🗑 Remove pages", callback_data="tool_remove")],
        [InlineKeyboardButton(text="📤 Extract pages", callback_data="tool_extract")]
    ])
    await message.answer(l10n['organize_menu'], reply_markup=kb)

@router.message(F.text.contains("ZIP"))
async def menu_archive(message: Message, state: FSMContext, l10n: dict):
    await state.update_data(zip_files=[])
    await message.answer(l10n['zip_prompt'])
    await state.set_state(Form.waiting_for_zip_files)

@router.message(F.text.contains("Convert TO PDF"))
async def menu_to_pdf(message: Message, l10n: dict):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 JPG to PDF", callback_data="tool_jpg")],
        [InlineKeyboardButton(text="📝 WORD to PDF", callback_data="tool_docx")],
        [InlineKeyboardButton(text="📊 EXCEL to PDF", callback_data="tool_excel")]
    ])
    await message.answer(l10n['to_pdf_menu'], reply_markup=kb)

@router.message(F.text.contains("Convert FROM PDF"))
async def menu_from_pdf(message: Message, l10n: dict):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼 PDF to JPG", callback_data="tool_pdf_to_jpg")],
        [InlineKeyboardButton(text="📝 PDF to WORD", callback_data="tool_pdf_to_doc")]
    ])
    await message.answer(l10n['from_pdf_menu'], reply_markup=kb)

@router.message(F.text.contains("Edit PDF"))
async def menu_edit(message: Message, l10n: dict):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Rotate PDF", callback_data="tool_rotate")],
        [InlineKeyboardButton(text="🔢 Add page numbers", callback_data="tool_numbers")],
        [InlineKeyboardButton(text="🖋 Add watermark", callback_data="tool_watermark")]
    ])
    await message.answer(l10n['edit_menu'], reply_markup=kb)

@router.message(F.text.contains("PDF Security"))
async def menu_security(message: Message, l10n: dict):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔒 Protect PDF", callback_data="tool_protect")],
        [InlineKeyboardButton(text="🔓 Unlock PDF", callback_data="tool_unlock")]
    ])
    await message.answer(l10n['security_menu'], reply_markup=kb)

# ==========================================
# 2. UNIVERSAL ICHKI TUGMALAR (CALLBACKS)
# ==========================================

@router.callback_query(F.data.startswith("tool_"))
async def universal_tool_handler(callback: CallbackQuery, state: FSMContext, l10n: dict):
    tool = callback.data.replace("tool_", "")
    await state.update_data(current_tool=tool)
    
    # --- A. JPG BO'LIMI ---
    if tool == "jpg":
        await state.update_data(jpg_files=[])
        await callback.message.answer(l10n['jpg_prompt'])
        await state.set_state(Form.waiting_for_photo)
    
    # --- B. WORD/EXCEL BO'LIMI ---
    elif tool in ["docx", "excel"]:
        msg = l10n['docx_prompt'] if tool == "docx" else l10n['excel_prompt']
        await callback.message.answer(msg)
        await state.set_state(Form.waiting_for_docx if tool == "docx" else Form.waiting_for_excel)
        
    # --- C. ORGANIZE (Split/Extract/Remove) ---
    elif tool in ["split", "extract", "remove"]:
        prompts = {"split": "split_prompt", "extract": "extract_prompt", "remove": "remove_prompt"}
        await callback.message.answer(l10n[prompts[tool]])
        await state.set_state(Form.waiting_for_page_params)
        
    # --- D. CONVERT FROM PDF ---
    elif tool in ["pdf_to_jpg", "pdf_to_doc"]:
        prompts = {"pdf_to_jpg": "pdf_to_jpg_prompt", "pdf_to_doc": "pdf_to_doc_prompt"}
        await callback.message.answer(l10n[prompts[tool]])
        await state.set_state(Form.waiting_for_pdf)
        
    # --- E. MERGE ---
    elif tool == "merge":
        await state.update_data(merge_files=[])
        await callback.message.answer(l10n['merge_start'])
        await state.set_state(Form.waiting_for_merge_files)
        
    # --- F. SECURITY (TUZATILDI) ---
    elif tool in ["protect", "unlock"]:
        # MUHIM: Avval tool nomini saqlaymiz, keyin holatni o'zgartiramiz
        await state.update_data(current_tool=tool)
        prompt = l10n['password_prompt'] if tool == "protect" else l10n['unlock_prompt']
        await callback.message.answer(prompt)
        await state.set_state(Form.waiting_for_password)
    
    # --- G. EDIT (Rotate, Numbers, Watermark) ---
    elif tool == "rotate":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↪️ 90°", callback_data="angle_90"),
             InlineKeyboardButton(text="🔄 180°", callback_data="angle_180"),
             InlineKeyboardButton(text="↩️ 270°", callback_data="angle_270")]
        ])
        await callback.message.answer(l10n['rotate_prompt'], reply_markup=kb)

    elif tool == "numbers":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=l10n['left'], callback_data="numpos_left"),
             InlineKeyboardButton(text=l10n['center'], callback_data="numpos_center"),
             InlineKeyboardButton(text=l10n['right'], callback_data="numpos_right")]
        ])
        await callback.message.answer(l10n['number_pos_prompt'], reply_markup=kb)

    elif tool == "watermark":
        await callback.message.answer(l10n['watermark_prompt'])
        await state.set_state(Form.waiting_for_watermark_text)
    
    await callback.answer()

# ==========================================
# 3. MAXSUS CALLBACKLAR (Angle va Position)
# ==========================================

@router.callback_query(F.data.startswith("angle_"))
async def set_rotate_angle(callback: CallbackQuery, state: FSMContext, l10n: dict):
    angle = int(callback.data.split("_")[1])
    await state.update_data(rotate_angle=angle, current_tool="rotate")
    await callback.message.answer(l10n['rotate_selected'].format(angle=angle))
    await state.set_state(Form.waiting_for_pdf)
    await callback.answer()

@router.callback_query(F.data.startswith("numpos_"))
async def set_number_position(callback: CallbackQuery, state: FSMContext, l10n: dict):
    pos = callback.data.split("_")[1]
    await state.update_data(number_pos=pos, current_tool="numbers")
    pos_name = l10n.get(pos, pos)
    text = l10n['number_pos_selected'].format(pos=pos_name)
    await callback.message.answer(text)
    await state.set_state(Form.waiting_for_pdf)
    await callback.answer()