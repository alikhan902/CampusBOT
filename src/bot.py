import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers import start, help
from handlers.auth import auth
from handlers.grades import grades
from handlers.schedule import schedule
from handlers.local_schedule import local_schedule
from middleware.auth import AuthMiddleware
from middleware.session import SessionMiddleware
from middleware.user_logger import UserLoggerMiddleware
import redis.asyncio as redis_asyncio
from aiogram.fsm.storage.redis import RedisStorage

load_dotenv()

redis_pool = redis_asyncio.Redis(
    host='localhost',   
    port=6379,          
    db=0,             
    decode_responses=True
)

storage = RedisStorage(redis_pool, state_ttl=None)

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

dp.include_router(help.router)
dp.include_router(start.router)
dp.include_router(auth.router)
dp.include_router(schedule.router)
dp.include_router(grades.router)
dp.include_router(local_schedule.router)

dp.message.middleware(AuthMiddleware())
dp.message.middleware(SessionMiddleware())
dp.message.middleware(UserLoggerMiddleware())
dp.callback_query.middleware(UserLoggerMiddleware())