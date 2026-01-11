import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router as main_router
from middlewares.i18n import L10nMiddleware
from aiogram.types import BotCommand

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Qayta ishga tushirish / Restart"),
        BotCommand(command="settings", description="Tilni sozlash / Language"),
        BotCommand(command="admin", description="Admin Panel"),
    ]
    await bot.set_my_commands(commands)

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Buyruqlar menyusini o'rnatish
    await setup_bot_commands(bot)

    # Middlewarelarni ulaymiz
    dp.message.middleware(L10nMiddleware())
    dp.callback_query.middleware(L10nMiddleware())

    # Routerni ulaymiz
    dp.include_router(main_router)

    print("--- BOT ISHLADI ---")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")