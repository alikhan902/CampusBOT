from aiogram.fsm.state import State, StatesGroup

# форма авторизации
class AuthForm(StatesGroup):
    login = State()
    password = State()
    captcha_code = State()

# форма полчения расписания    
class ScheduleForm(StatesGroup):
    TypeSchedule = State()
    NameType = State()