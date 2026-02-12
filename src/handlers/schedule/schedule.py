from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from .utils import get_monday_date
from keyboard.keyboard import keyboard_back_to_main

router = Router()


# расписание - обработчик для команды (для совместимости)
@router.message(Command("schedule"))
async def get_schedule(message: Message, state: FSMContext, session):
    await handle_schedule(message, state, session)

# расписание - обработчик для inline кнопки
@router.callback_query(lambda c: c.data == "schedule")
async def schedule_callback(callback_query: CallbackQuery, state: FSMContext, session):
    await callback_query.answer()
    await handle_schedule(callback_query.message, state, session)

async def handle_schedule(message: Message, state: FSMContext, session):
    data = await state.get_data()
    model_id = data.get("ecampus_id")

    monday_date = get_monday_date()
    payload = {"Id": model_id, "date": monday_date, "targetType": 4}


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
        await message.answer(chunk, reply_markup=keyboard_back_to_main)
