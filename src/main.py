import time
import os
import asyncio
import re
import os
import uuid
import json
import requests
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from utils import get_monday_date

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# FSM
class AuthForm(StatesGroup):
    login = State()
    password = State()
    captcha_code = State()
    
# /start
@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await login_cmd(message, state)


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
        token=token,
        captcha_filepath=filepath
    )

    await message.answer("Введите логин:")
    await state.set_state(AuthForm.login)


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
    data = await state.get_data()
    captcha_filepath = data.get("captcha_filepath")
    if captcha_filepath:
        await message.answer_photo(FSInputFile(captcha_filepath), caption="Введите капчу:")
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
    print("остановка тут 0")

    model_id = None
    if script:
        text = script.string
        match = re.search(r"var\s+viewModel\s*=\s*(\{.*\});", text, re.S)
        print("остановка тут 1")
        if match:
            print(match)
            json_text = match.group(1)
            json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', json_text)
            data_json = json.loads(json_text)
            print(data_json)
            model_id = data_json["Model"]["Id"]
            print("остановка тут 2")

    await state.update_data(cookies=session.cookies.get_dict(), ecampus_id=model_id)

    await message.answer(f"Вход выполнен ✅ Id={model_id}")
    
    await state.set_state(None)


@router.message(Command("help"))
async def get_schedule(message: Message, state: FSMContext):
    await message.answer("""/login - авторизация,\n/schedule - расписание на эту недулю,\n/grades - оценки и Н-ки""")

# расписание
@router.message(Command("schedule"))
async def get_schedule(message: Message, state: FSMContext):
    data = await state.get_data()
    cookies = data.get("cookies")
    model_id = data.get("ecampus_id")

    monday_date = get_monday_date() 

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
            if isinstance(lesson, dict):
                teacher = lesson.get("Teacher")
                if isinstance(teacher, dict):
                    teacher_name = teacher.get("Name", "Неизвестно")
                else:
                    teacher_name = "Неизвестно"
            else:
                teacher_name = "Неизвестно"
            print(lesson)
            print(teacher_name)
            aud = lesson.get("Aud", {}).get("Name", "—")
            group = ", ".join(g["Name"] for g in lesson.get("Groups", []))

            text += (
                f"⏰ {time_begin}–{time_end}\n"
                f"📖 {discipline} ({lesson_type})\n"
                f"👨‍🏫 {teacher_name}\n"
                f"🏫 Аудитория: {aud}\n"
                f"👥 Группа: {group}\n\n"
            )

    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await message.answer(chunk)

@router.message(Command("grades"))
async def get_grades(message: Message, state: FSMContext):
    start_time = time.perf_counter()
    data = await state.get_data()
    cookies = data.get("cookies")
    model_id = data.get("ecampus_id")

    if not model_id or not cookies:
        await message.answer("Пожалуйста, выполните вход в систему с помощью команды /login.")
        return

    async with aiohttp.ClientSession(cookies=cookies, connector=aiohttp.TCPConnector(limit=5, limit_per_host=3)) as session:
        # --- Получаем страницу с курсами ---
        async with session.get("https://ecampus.ncfu.ru/studies") as resp:
            text = await resp.text()

        soup = BeautifulSoup(text, "html.parser")
        script = soup.find("script", type="text/javascript", string=re.compile("viewModel"))
        courses = []

        if script:
            text_script = script.string
            match = re.search(r"var\s+viewModel\s*=\s*(\{.*\});", text_script, re.S)
            if match:
                json_text = match.group(1)
                json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', json_text)
                data_json = json.loads(json_text)
                courses = data_json.get("specialities", [])

        # --- Извлекаем model_id из HTML ---
        model_text = text
        last = model_text.rfind('"Id"') + 5
        model_text = model_text[last:]
        first = model_text.find(',')
        model_id = int(model_text[:first])

        all_grades = []
        total_n = 0

        # --- Обработка курсов ---
        for course in courses:
            for year in course.get("AcademicYears", []):
                for term in year.get("Terms", []):
                    if term.get("IsCurrent", False):
                        for course_item in term.get("Courses", []):
                            lesson_types = course_item.get("LessonTypes", [])
                            if not lesson_types:
                                continue

                            total_score = 0
                            total_attendance = 0
                            total_lessons = 0
                            n_count = 0

                            for lesson in lesson_types:
                                lesson_id = lesson.get("Id")

                                payload = {
                                    "studentId": model_id,
                                    "lessonTypeId": lesson_id
                                }

                                async with session.post(
                                    "https://ecampus.ncfu.ru/studies/GetLessons", data=payload
                                ) as grades_resp:
                                    print(resp.status)
                                    if grades_resp.status == 200:
                                        grades = await grades_resp.json()
                                        for grade_info in grades:
                                            attendance = grade_info.get("Attendance")
                                            grade_text = grade_info.get("GradeText")

                                            if attendance == 1:
                                                total_attendance += 1
                                            elif attendance == 0:
                                                n_count += 1

                                            if grade_text:
                                                total_score += {
                                                    "отлично": 5,
                                                    "хорошо": 4,
                                                    "удовлетворительно": 3
                                                }.get(grade_text, 0)
                                                total_lessons += 1

                            average_score = total_score / total_lessons if total_lessons > 0 else 0
                            response = (
                                f"Название предмета: {course_item.get('Name')}\n"
                                f"Н: {n_count}\n"
                                f"Средний балл: {average_score:.2f}"
                            )
                            all_grades.append(response)
                            total_n += n_count

    end_time = time.perf_counter()
    elapsed = end_time - start_time 
    print(f"Время {elapsed}")
    # --- Ответ пользователю ---
    if all_grades:
        response = "\n\n".join(all_grades)
        response += f"\n\nОбщее количество Н по всем предметам: {total_n}"
        await message.answer(response)
    else:
        await message.answer("Не удалось получить данные о ваших оценках.")
        
dp.include_router(router)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


