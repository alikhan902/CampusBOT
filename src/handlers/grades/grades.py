import re
import json
import time
from bs4 import BeautifulSoup
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from .utils import post_lesson

router = Router()

# оценки
@router.message(Command("grades"))
async def get_grades(message: Message, state: FSMContext, session):
    start_time = time.perf_counter()
    data = await state.get_data()
    model_id = data.get("ecampus_id")

    progress_msg = await message.answer("🔄 Начинаем сбор оценок...")

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
    
    # Считаем общее количество предметов для прогресса
    total_lessons = 0
    for course in courses:
        for year in course.get("AcademicYears", []):
            for term in year.get("Terms", []):
                if term.get("IsCurrent", False):
                    for course_item in term.get("Courses", []):
                        lesson_types = course_item.get("LessonTypes", [])
                        total_lessons += len(lesson_types) if lesson_types else 0
    
    processed_lessons = 0

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
                        total_lessons_course = 0
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

                            processed_lessons += 1
                            
                            if processed_lessons % 3 == 0 or processed_lessons == total_lessons:  # Обновляем каждые 3 урока или в конце
                                progress = (processed_lessons / total_lessons) * 100
                                await progress_msg.edit_text(
                                    f"🔄 Обрабатываем оценки...\n"
                                    f"📊 Прогресс: {processed_lessons}/{total_lessons} ({progress:.1f}%)"
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
                                        total_lessons_course += 1

                        average_score = total_score / total_lessons_course if total_lessons_course > 0 else 0
                        response = (
                            f"📖 {course_item.get('Name')}\n"
                            f"❌ Н: {n_count}\n"
                            f"⭐ Средний балл: {average_score:.2f}"
                        )
                        all_grades.append(response)
                        total_n += n_count

    end_time = time.perf_counter()
    elapsed = end_time - start_time

    # Удаляем сообщение о прогрессе
    await progress_msg.delete()

    if all_grades:
        response = "\n\n".join(all_grades)
        response += f"\n\n📊 Общее количество Н: {total_n}"
        
        # Разбиваем длинные сообщения
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await message.answer(response[i:i+4096])
        else:
            await message.answer(response)
    else:
        await message.answer("❌ Не удалось получить данные о ваших оценках.")