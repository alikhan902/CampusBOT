from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

keyboard_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔐 Войти", callback_data="login"),
            InlineKeyboardButton(text="📅 Расписание", callback_data="schedule"),
        ],
        [
            InlineKeyboardButton(text="⭐ Оценки", callback_data="grades"),
            InlineKeyboardButton(text="🔍 Поиск расписания", callback_data="locsh"),
        ],
        [
            InlineKeyboardButton(text="❓ Справка", callback_data="help"),
        ]
    ]
)

keyboard_back_to_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="main_menu")]
    ]
)

keyboard_locsh_type = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Группа", callback_data="schedule_group"),
            InlineKeyboardButton(text="👨‍🏫 Преподаватель", callback_data="schedule_teacher"),
        ],
        [
            InlineKeyboardButton(text="🏫 Аудитория", callback_data="schedule_room"),
        ],
        [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="main_menu")]
    ]
)

# Old keyboard - deprecated
keyboard_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Войти", callback_data="login"),
            InlineKeyboardButton(text="Расписание по поиску", callback_data="locsh"),
        ]
    ]
)