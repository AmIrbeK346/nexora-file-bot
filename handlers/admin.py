from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.db import db
from utils.states import Form

router = Router()

@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_main(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="admin_broadcast")]
    ])
    await message.answer("👑 Admin panelga xush kelibsiz:", reply_markup=kb)

@router.callback_query(F.data == "admin_stats", F.from_user.id == ADMIN_ID)
async def show_stats(callback: CallbackQuery):
    total = db.count_total_users()
    today = db.count_today_users()
    
    text = (f"📈 **Bot statistikasi**\n\n"
            f"👤 Jami foydalanuvchilar: {total}\n"
            f"🆕 Bugun qo'shilganlar: {today}")
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📢 Reklama xabarini yuboring (Matn, rasm yoki video bo'lishi mumkin):")
    await state.set_state(Form.waiting_for_ad)
    await callback.answer()

@router.message(Form.waiting_for_ad, F.from_user.id == ADMIN_ID)
async def send_broadcast(message: Message, state: FSMContext, bot: Bot):
    users = db.get_all_users()
    count = 0
    blocked = 0
    
    msg = await message.answer(f"🚀 Reklama yuborish boshlandi (0/{len(users)})...")
    
    for user_id in users:
        try:
            # Xabarni nusxasini yuboramiz (copy_to har qanday formatni qo'llaydi)
            await message.copy_to(chat_id=user_id)
            count += 1
        except Exception:
            blocked += 1
        
        # Har 10 ta foydalanuvchida statusni yangilash
        if count % 10 == 0:
            try: await msg.edit_text(f"🚀 Reklama yuborilmoqda ({count}/{len(users)})...")
            except: pass

    await message.answer(f"✅ Reklama tugatildi!\n\n👤 Yuborildi: {count}\n🚫 Bloklagan: {blocked}")
    await state.clear()