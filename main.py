# import asyncio
# from aiogram import Bot, Dispatcher, types
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from aiogram.fsm.storage.memory import MemoryStorage
# import requests


# API_TOKEN = "8270550557:AAEu_-4P1SAbpBOqfZ_7FGTXaPQ3J7nAzho"

# # Создаем бота и диспетчер с хранилищем состояний
# bot = Bot(token=API_TOKEN)
# dp = Dispatcher(storage=MemoryStorage())


# # Определяем состояния
# class AuthForm(StatesGroup):
#     login = State()
#     password = State()
#     captcha_code = State()


# # # Хендлер команды /start
# # @dp.message(Command("start"))
# # async def cmd_start(message: types.Message, state: FSMContext):
# #     await state.set_state(Form.name)
# #     await message.answer("Привет! Как тебя зовут?")

# # Хендлер команды /start
# @dp.message(Command("start"))
# async def cmd_start(message: types.Message, state: FSMContext):
#     await state.set_state(AuthForm.login)
#     await message.answer("Привет! Для авторизации введи логин")

# # Хендлер для имени
# @dp.message(AuthForm.login)
# async def process_name(message: types.Message, state: FSMContext):
#     await state.update_data(login=message.text)
#     await state.set_state(AuthForm.password)
#     await message.answer("Пароль:")

# @dp.message(AuthForm.password)
# async def process_name(message: types.Message, state: FSMContext):
#     session = requests.Session()

# # # Хендлер для имени
# # @dp.message(Form.name)
# # async def process_name(message: types.Message, state: FSMContext):
# #     await state.update_data(name=message.text)
# #     await state.set_state(Form.age)
# #     await message.answer("Сколько тебе лет?")


# # # Хендлер для возраста
# # @dp.message(Form.age)
# # async def process_age(message: types.Message, state: FSMContext):
# #     data = await state.get_data()
# #     await message.answer(f"Тебя зовут {data['name']}, тебе {message.text} лет.")
# #     await state.clear()


# # Точка входа
# async def main():
#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import re
import os
import uuid
import json
import requests
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime, timedelta

API_TOKEN = "8270550557:AAEu_-4P1SAbpBOqfZ_7FGTXaPQ3J7nAzho"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# FSM
class AuthForm(StatesGroup):
    login = State()
    password = State()
    captcha_code = State()

# /login
@router.message(F.text == "/login")
async def login_cmd(message: Message, state: FSMContext):
    session = requests.Session()
    login_url = "https://ecampus.ncfu.ru/account/login"
    resp = session.get(login_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
    captcha_tag = soup.find("img", {"alt": "captcha"})

    if not token_tag or not captcha_tag:
        await message.answer("Не удалось получить токен или капчу 😢")
        return

    token = token_tag["value"]
    captcha_url = "https://ecampus.ncfu.ru" + captcha_tag["src"]

    filename = f"captcha_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join("captcha", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    captcha_resp = session.get(captcha_url)
    with open(filepath, "wb") as f:
        f.write(captcha_resp.content)

    # сохраняем токен и куки в FSM
    await state.update_data(
        cookies=session.cookies.get_dict(),
        token=token
    )

    await message.answer("Введите логин:")
    await state.set_state(AuthForm.login)

    # отправляем капчу
    await message.answer_photo(FSInputFile(filepath), caption="Введите код с картинки:")

# логин
@router.message(AuthForm.login)
async def process_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введите пароль:")
    await state.set_state(AuthForm.password)

# пароль
@router.message(AuthForm.password)
async def process_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer("Введите капчу:")
    await state.set_state(AuthForm.captcha_code)

# капча
@router.message(AuthForm.captcha_code)
async def process_captcha(message: Message, state: FSMContext):
    data = await state.get_data()
    cookies = data["cookies"]
    token = data["token"]

    session = requests.Session()
    session.cookies.update(cookies)

    payload = {
        "__RequestVerificationToken": token,
        "Login": data["login"],
        "Password": data["password"],
        "Code": message.text,
        "RememberMe": "false",
    }

    resp = session.post("https://ecampus.ncfu.ru/account/login", data=payload)
    get_id = session.get("https://ecampus.ncfu.ru/schedule/my/student")
    soup2 = BeautifulSoup(get_id.text, "html.parser")
    script = soup2.find("script", type="text/javascript", string=re.compile("viewModel"))

    model_id = None
    if script:
        text = script.string
        match = re.search(r"var\s+viewModel\s*=\s*(\{.*\});", text, re.S)
        if match:
            json_text = match.group(1)
            json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', json_text)
            data_json = json.loads(json_text)
            model_id = data_json["Model"]["Id"]

    await state.update_data(cookies=session.cookies.get_dict(), ecampus_id=model_id)

    await message.answer(f"Вход выполнен ✅ Id={model_id}")
    print(session.cookies.get_dict())
    await state.set_state(None)


def get_monday_date():
    today = datetime.today()
    # Определяем понедельник текущей недели
    monday = today - timedelta(days=today.weekday())
    # Если сегодня после понедельника — используем этот понедельник
    # Если нужно всегда следующий понедельник — добавь timedelta(days=7)
    return monday.strftime("%Y-%m-%dT00:00:00.000Z")

# расписание
@router.message(Command("schedule"))
async def get_schedule(message: Message, state: FSMContext):
    data = await state.get_data()
    cookies = data.get("cookies")
    model_id = data.get("ecampus_id")

    monday_date = get_monday_date()  # функция из прошлого ответа

    payload = {
        "Id": model_id,
        "date": monday_date,
        "targetType": 4
    }

    resp = requests.post(
        "https://ecampus.ncfu.ru/Schedule/GetSchedule",
        cookies=cookies,
        data=payload
    )

    try:
        schedule = resp.json()   # преобразуем в Python-объекты
    except json.JSONDecodeError:
        await message.answer("Ошибка: сервер вернул не JSON")
        return

    if not schedule:
        await message.answer("Расписание пустое.")
        return

    text = f"📅 Расписание на неделю с {monday_date[:10]}:\n\n"

    for day in schedule:
        weekday = day.get("WeekDay")
        date = day.get("Date")[:10]
        text += f"=== {weekday} ({date}) ===\n"

        lessons = day.get("Lessons", [])
        if not lessons:
            text += "  ❌ Нет пар\n\n"
            continue

        for lesson in lessons:
            discipline = lesson.get("Discipline")
            lesson_type = lesson.get("LessonType")
            time_begin = lesson.get("TimeBegin")[11:16]
            time_end = lesson.get("TimeEnd")[11:16]
            teacher = lesson.get("Teacher", {}).get("Name", "Неизвестно")
            aud = lesson.get("Aud", {}).get("Name", "—")
            group = ", ".join(g["Name"] for g in lesson.get("Groups", []))

            text += (
                f"⏰ {time_begin}–{time_end}\n"
                f"📖 {discipline} ({lesson_type})\n"
                f"👨‍🏫 {teacher}\n"
                f"🏫 Аудитория: {aud}\n"
                f"👥 Группа: {group}\n\n"
            )

    # Telegram ограничивает сообщения 4096 символами
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await message.answer(chunk)

dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
