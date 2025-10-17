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
    cookies = data.get("cookies")
    model_id = data.get("ecampus_id")

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
        