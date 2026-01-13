from aiogram import BaseMiddleware
from locales.messages import MESSAGES
from utils.db import db # Bazani import qilamiz

class L10nMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user:
            # Lug'at o'rniga bazadan o'qiymiz
            lang = db.get_language(user.id)
            data['lang'] = lang
            data['l10n'] = MESSAGES.get(lang, MESSAGES['uz'])
        return await handler(event, data)
