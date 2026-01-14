from aiogram import BaseMiddleware
from locales.messages import MESSAGES
from utils.db import db

class L10nMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            # --- SILENT REGISTRATION (Yashirin ro'yxatga olish) ---
            # Foydalanuvchi nima yuborishidan qat'iy nazar, 
            # uni bazada borligini tekshiramiz va yo'q bo'lsa qo'shib qo'yamiz
            db.add_user(user.id) 
            
            # Tilni bazadan olamiz
            lang = db.get_language(user.id)
            data['lang'] = lang
            data['l10n'] = MESSAGES.get(lang, MESSAGES['uz'])
            
        return await handler(event, data)
