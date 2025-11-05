from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import timedelta, datetime
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
    
    monday_date = get_monday_date()
    
    url += f"&date={(str(monday_date))[:10]}"

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

    # Разделяем на 2 недели
    week1 = {}
    week2 = {}

    for lesson in schedule:
        date_str = lesson.get("date")
        if not date_str:
            continue
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        delta_days = (date_obj - monday_date.date()).days


        if 0 <= delta_days < 7:
            week = week1
        elif 7 <= delta_days < 14:
            week = week2
        else:
            continue

        weekday = lesson.get("weekday", "—")
        week.setdefault(weekday, []).append(lesson)

    weekdays_order = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ]

    async def render_week(week_data, week_number):
        text = f"📅 Расписание — {week_number}-я неделя (начало {monday_date + timedelta(days=(week_number - 1) * 7):%Y-%m-%d})\n\n"

        for weekday in weekdays_order:
            lessons = week_data.get(weekday, [])
            if lessons:
                date = lessons[0].get("date", "")
            else:
                date = (monday_date + timedelta(days=(week_number - 1) * 7 + weekdays_order.index(weekday))).strftime("%Y-%m-%d")

            if lessons:
                text += f"=== {weekday} ({date}) ===\n"
            else:
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
        return text

    if week1:
        text = await render_week(week1, 1)
        for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
            await message.answer(chunk, parse_mode="HTML")

    if week2:
        text = await render_week(week2, 2)
        for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
            await message.answer(chunk, parse_mode="HTML")
