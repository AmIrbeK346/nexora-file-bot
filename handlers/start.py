from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from locales.messages import MESSAGES
from utils.db import db # O'rniga bazani import qiling
from config import ADMIN_ID

router = Router()

def get_main_menu(lang):
    l = MESSAGES[lang]
    kb = [
        [KeyboardButton(text=l['btn_organize']), KeyboardButton(text=l['btn_archive'])],
        [KeyboardButton(text=l['btn_to_pdf']), KeyboardButton(text=l['btn_from_pdf'])],
        [KeyboardButton(text=l['btn_edit']), KeyboardButton(text=l['btn_security'])]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message):
    db.add_user(message.from_user.id)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ])
    await message.answer("Please select language / Tilni tanlang:", reply_markup=kb)

@router.message(CommandStart())
@router.message(Command("settings"))
async def cmd_start(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ])
    await message.answer("Select language / Tilni tanlang / Выберите язык:", reply_markup=kb)


@router.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    # Lug'at o'rniga bazaga saqlash:
    db.set_language(callback.from_user.id, lang) 
    
    await callback.message.delete()
    await callback.message.answer(MESSAGES[lang]['main_menu'], reply_markup=get_main_menu(lang))
