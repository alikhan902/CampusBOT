import re
import orjson
from bs4 import BeautifulSoup
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboard.keyboard import keyboard_back_to_main

from .utils import iter_current_courses, post_lesson

router = Router()

@router.message(Command("grades"))
async def get_grades(message: Message, state: FSMContext, session):
    await handle_grades(message, state, session)

@router.callback_query(lambda c: c.data == "grades")
async def grades_callback(callback_query: CallbackQuery, state: FSMContext, session):
    await callback_query.answer()
    await handle_grades(callback_query.message, state, session)

async def handle_grades(message: Message, state: FSMContext, session):
    data = await state.get_data()
    model_id = data.get("ecampus_id")
    cookies = data.get("cookies", {})
    
    session.cookie_jar.update_cookies(cookies)
    
    progress_msg = await message.answer("🔄 Начинаем сбор оценок...")

    async with session.get("https://ecampus.ncfu.ru/studies") as resp:
        text = await resp.text()

    soup = BeautifulSoup(text, "lxml")
    script = soup.find("script", type="text/javascript", string=re.compile("viewModel"))

    match = re.search(r'var\s+viewModel\s*=\s*(\{.*\});', script.string, re.S)
    json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', match.group(1)) if match else None
    
    data_json = orjson.loads(json_text)
    
    courses = data_json.get("specialities", [])

    model_text = text
    last = model_text.rfind('"Id"') + 5
    model_text = model_text[last:]
    first = model_text.find(',')
    model_id = int(model_text[:first])

    total_lessons = sum(
        len(course_item.get("LessonTypes", []) or [])
        for course_item in iter_current_courses(courses)
    )   
    
    all_grades = []
    total_n = 0
    processed_lessons = 0
    
    for course_item in iter_current_courses(courses):
        lesson_types = course_item.get("LessonTypes", [])
        if not lesson_types:
            continue

        total_score = total_attendance = total_lessons_course = n_count = 0

        for lesson in lesson_types:
            payload = {"studentId": model_id, "lessonTypeId": lesson["Id"]}
            grades, success = await post_lesson(session=session, payload=payload)
            processed_lessons += 1

            if processed_lessons % 3 == 0 or processed_lessons == total_lessons:
                progress = (processed_lessons / total_lessons) * 100
                await progress_msg.edit_text(
                    f"🔄 Обрабатываем оценки...\n"
                    f"📊 Прогресс: {processed_lessons}/{total_lessons} ({progress:.1f}%)"
                )

            if not (success and grades):
                continue

            for g in grades:
                att, grade_text = g.get("Attendance"), g.get("GradeText")
                if att == 1:
                    total_attendance += 1
                elif att == 0:
                    n_count += 1
                if grade_text:
                    total_score += {"отлично": 5, "хорошо": 4, "удовлетворительно": 3}.get(grade_text, 0)
                    total_lessons_course += 1

        avg = total_score / total_lessons_course if total_lessons_course else 0
        all_grades.append(f"📖 {course_item['Name']}\n❌ Н: {n_count}\n⭐ Средний балл: {avg:.2f}")
        total_n += n_count
    await progress_msg.delete()

    if all_grades:
        response = "\n\n".join(all_grades)
        response += f"\n\n📊 Общее количество Н: {total_n}"
        
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await message.answer(response[i:i+4096], reply_markup=keyboard_back_to_main)
        else:
            await message.answer(response, reply_markup=keyboard_back_to_main)
    else:
        await message.answer("❌ Не удалось получить данные о ваших оценках.", reply_markup=keyboard_back_to_main)
