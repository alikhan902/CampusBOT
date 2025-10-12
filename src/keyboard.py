from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/login"), KeyboardButton(text="/schedule")],
        [KeyboardButton(text="/grades"), KeyboardButton(text="/help")]
    ],
    resize_keyboard=True
)
