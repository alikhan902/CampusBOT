import time
import os
import asyncio
import re
import uuid
import json
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command


from utils import get_monday_date, post_lesson
from keyboard import keyboard_main

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
    await message.answer("Привет! Выбери команду:", reply_markup=keyboard_main)



# /login
@router.message(F.text == "/login")
async def login_cmd(message: Message, state: FSMContext):
    login_url = "https://ecampus.ncfu.ru/account/login"

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        async with session.get(login_url) as resp:
            text = await resp.text()

        soup = BeautifulSoup(text, "html.parser")
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

        async with session.get(captcha_url) as captcha_resp:
            content = await captcha_resp.read()
            with open(filepath, "wb") as f:
                f.write(content)

        # сохраняем токен и куки
        cookies = {cookie.key: cookie.value for cookie in session.cookie_jar}
        await state.update_data(
            cookies=cookies,
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

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        session.cookie_jar.update_cookies(cookies)

        payload = {
            "__RequestVerificationToken": token,
            "Login": data["login"],
            "Password": data["password"],
            "Code": message.text,
            "RememberMe": "false",
        }

        async with session.post("https://ecampus.ncfu.ru/account/login", data=payload) as resp:
            await resp.text()

        async with session.get("https://ecampus.ncfu.ru/schedule/my/student") as get_id:
            html = await get_id.text()

        soup2 = BeautifulSoup(html, "html.parser")
        script = soup2.find("script", type="text/javascript", string=re.compile("viewModel"))

        model_id = None
        if script:
            text = script.string
            match = re.search(r"var\s+viewModel\s*=\s*(\{.*\});", text, re.S)
            if match:
                json_text = match.group(1)
                json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', json_text)
                try:
                    data_json = json.loads(json_text)
                    model_id = data_json["Model"]["Id"]
                except Exception:
                    model_id = None

        new_cookies = {cookie.key: cookie.value for cookie in session.cookie_jar}
        await state.update_data(cookies=new_cookies, ecampus_id=model_id)

    if model_id is not None:
        await message.answer(f"Вход выполнен ✅")
    else:
        await message.answer("Авторизация не удалась ❌ \nВозможно вы ввели неверные данные, попробуйте снова")

    await state.set_state(None)


@router.message(Command("help"))
async def help_cmd(message: Message, state: FSMContext):
    await message.answer("""/login - авторизация,\n/schedule - расписание на эту неделю,\n/grades - оценки и Н-ки""")


# расписание
@router.message(Command("schedule"))
async def get_schedule(message: Message, state: FSMContext):
    data = await state.get_data()
    cookies = data.get("cookies")
    model_id = data.get("ecampus_id")

    if not model_id or not cookies:
        await message.answer("Пожалуйста, выполните вход через /login.")
        return

    monday_date = get_monday_date()
    payload = {"Id": model_id, "date": monday_date, "targetType": 4}

    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        session.cookie_jar.update_cookies(cookies)
        async with session.post("https://ecampus.ncfu.ru/Schedule/GetSchedule", data=payload) as resp:
            try:
                schedule = await resp.json(content_type=None)
            except Exception:
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
            teacher = lesson.get("Teacher")
            teacher_name = teacher.get("Name", "Неизвестно") if isinstance(teacher, dict) else "Неизвестно"
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


# оценки
@router.message(Command("grades"))
async def get_grades(message: Message, state: FSMContext):
    start_time = time.perf_counter()
    data = await state.get_data()
    cookies = data.get("cookies")
    model_id = data.get("ecampus_id")

    if not model_id or not cookies:
        await message.answer("Пожалуйста, выполните вход в систему с помощью команды /login.")
        return

    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(), timeout=timeout) as session:
        session.cookie_jar.update_cookies(cookies)

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

        model_text = text
        last = model_text.rfind('"Id"') + 5
        model_text = model_text[last:]
        first = model_text.find(',')
        model_id = int(model_text[:first])

        all_grades = []
        total_n = 0

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
                                payload = {"studentId": model_id, "lessonTypeId": lesson_id}
                                start_time_lesson = time.perf_counter()
                                grades, success = await post_lesson(
                                    session=session,
                                    payload=payload,
                                    start_time_lesson=start_time_lesson
                                )

                                if success and grades:
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
    print(f"Время {elapsed:.2f} сек")

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
