from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import timedelta
from states.states import ScheduleForm
from .utils import get_monday_date

router = Router()


@router.message(Command("locsh"))
async def schedule_start(message: Message, state: FSMContext):
    await message.answer("Введите тип расписания — группа / преподаватель / аудитория:")
    await state.set_state(ScheduleForm.TypeSchedule)


@router.message(ScheduleForm.TypeSchedule)
async def schedule_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text.strip().lower())
    await message.answer("Введите ФИО преподавателя / название группы / аудитории:")
    await state.set_state(ScheduleForm.NameType)


@router.message(ScheduleForm.NameType)
async def schedule_name(message: Message, state: FSMContext, session):
    await state.update_data(typename=message.text.strip())
    data = await state.get_data()
    await state.set_state(None)

    base_url = "http://localhost:8000/api/schedule/"
    type_ = data.get("type")
    name = data.get("typename")

    if "груп" in type_:
        url = f"{base_url}?group={name}"
    elif "преп" in type_:
        url = f"{base_url}?teacher={name}"
    elif "ауд" in type_:
        url = f"{base_url}?room={name}"
    else:
        await message.answer("❌ Неизвестный тип. Введите: группа / преподаватель / аудитория.")
        return

    await message.answer("📡 Получаю расписание...")

    async with session.get(url) as resp:
        if resp.status != 200:
            await message.answer(f"Ошибка запроса: {resp.status}")
            return

        try:
            schedule = await resp.json()
        except Exception:
            await message.answer("Ошибка: сервер вернул не JSON 😕")
            return

    if not schedule:
        await message.answer("Расписание не найдено 😕")
        return

    monday_date = get_monday_date()

    text = f"📅 Расписание начиная с {monday_date.strftime('%Y-%m-%d')} (1 неделя)\n\n"
    day_offset = 0 

    weekdays_order = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ]

    for day in schedule:
        lessons = day.get("lessons", [])
        weekday = lessons[0].get("weekday", "-") if lessons else "—"

        try:
            day_offset = weekdays_order.index(weekday)
        except ValueError:
            day_offset = 0

        day_date = (monday_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")

        text += f"=== {weekday} ({day_date}) ===\n"

        if not lessons:
            text += "  ❌ Нет пар\n\n"
            continue

        for lesson in lessons:
            discipline = lesson.get("discipline", "?")
            lesson_type = lesson.get("lesson_type", "?")
            time_begin = (lesson.get("time_begin", "?"))[:5]
            time_end = (lesson.get("time_end", "?"))[:5]
            teacher = (lesson.get("teacher") or {}).get("Name", "—")
            room = (lesson.get("room") or {}).get("Name", "—")
            group = (lesson.get("group") or {}).get("Name", "—")
            subgroup = lesson.get("subgroup") or ""

            text += (
                f"⏰ {time_begin}–{time_end}\n"
                f"📖 {discipline} ({lesson_type})\n"
                f"👨‍🏫 {teacher}\n"
                f"🏫 Аудитория: {room}\n"
                f"👥 Группа: {group} {subgroup}\n\n"
            )

    for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
        await message.answer(chunk, parse_mode="HTML")
