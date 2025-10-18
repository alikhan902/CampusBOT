import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers import start, help
from handlers.auth import auth
from handlers.grades import grades
from handlers.schedule import schedule
from middleware.auth import AuthMiddleware
from middleware.session import SessionMiddleware

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(help.router)
dp.include_router(start.router)
dp.include_router(auth.router)
dp.include_router(schedule.router)
dp.include_router(grades.router)

dp.message.middleware(AuthMiddleware())
dp.message.middleware(SessionMiddleware())