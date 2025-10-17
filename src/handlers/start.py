from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboard.keyboard import keyboard_main

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Выбери команду:", reply_markup=keyboard_main)
