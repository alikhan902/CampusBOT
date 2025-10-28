from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboard.keyboard import keyboard_main

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Со списком всех команд вы можете ознакомиться по команде /help\nТакже можете посетить тг канал посвященный боту - https://t.me/mycampusdev", reply_markup=keyboard_main)
