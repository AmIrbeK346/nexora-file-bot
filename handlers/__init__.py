from aiogram import Router
from . import start, menu_handler, processors
from . import start, menu_handler, processors, admin

router = Router()

# Har bir routerni faqat BIR MARTA qo'shamiz
router.include_router(start.router)
router.include_router(menu_handler.router)
router.include_router(processors.router)
router.include_router(admin.router)