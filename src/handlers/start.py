from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboard.keyboard import keyboard_main

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Это бот для eCampus.\n\n"
        "Выберите нужную функцию:",
        reply_markup=keyboard_main
    )

@router.callback_query(lambda c: c.data == "main_menu")
async def show_main_menu(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        "👋 Выберите нужную функцию:",
        reply_markup=keyboard_main
    )
    await callback_query.answer()
