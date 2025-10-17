from aiogram.fsm.state import State, StatesGroup

class AuthForm(StatesGroup):
    login = State()
    password = State()
    captcha_code = State()