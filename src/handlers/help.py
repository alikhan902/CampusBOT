from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboard.keyboard import keyboard_back_to_main

router = Router()

@router.message(Command("help"))
async def help_cmd(message: Message):
    help_text = (
        "📖 <b>Справка по функциям бота:</b>\n\n"
        "<b>🔐 Войти</b> - авторизация в eCampus\n"
        "<b>📅 Расписание</b> - расписание на эту неделю\n"
        "<b>⭐ Оценки</b> - оценки и Н-ки\n"
        "<b>🔍 Поиск расписания</b> - получение расписания по названию (работает при проблемах с eCampus)\n\n"
        "💬 Посетите наш канал - https://t.me/mycampusdev"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard_back_to_main)

@router.callback_query(lambda c: c.data == "help")
async def help_callback(callback_query: CallbackQuery):
    help_text = (
        "📖 <b>Справка по функциям бота:</b>\n\n"
        "<b>🔐 Войти</b> - авторизация в eCampus\n"
        "<b>📅 Расписание</b> - расписание на эту неделю\n"
        "<b>⭐ Оценки</b> - оценки и Н-ки\n"
        "<b>🔍 Поиск расписания</b> - получение расписания по названию (работает при проблемах с eCampus)\n\n"
        "💬 Посетите наш канал - https://t.me/mycampusdev"
    )
    await callback_query.message.edit_text(help_text, parse_mode="HTML", reply_markup=keyboard_back_to_main)
    await callback_query.answer()
