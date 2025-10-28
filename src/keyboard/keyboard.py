from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

keyboard_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/login"), KeyboardButton(text="/schedule")],
        [KeyboardButton(text="/grades"), KeyboardButton(text="/help")],
        [KeyboardButton(text="/locsh")]
    ],
    resize_keyboard=True
)
