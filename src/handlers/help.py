from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("""/login - авторизация,\n/schedule - расписание на эту неделю,\n/grades - оценки и Н-ки""")