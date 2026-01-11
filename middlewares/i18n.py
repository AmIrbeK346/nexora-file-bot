from aiogram import BaseMiddleware
from locales.messages import MESSAGES


user_lang_db = {}

class L10nMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        
        if user:
            user_id = user.id
            # Foydalanuvchi tili bazada bo'lmasa, default 'uz'
            lang = user_lang_db.get(user_id, 'uz')
            data['lang'] = lang
            data['l10n'] = MESSAGES.get(lang, MESSAGES['uz'])
        
        return await handler(event, data)