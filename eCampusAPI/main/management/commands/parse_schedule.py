from datetime import date
import time
import requests
from  .utils import mondays_between
from django.core.management.base import BaseCommand
from main.models import AcademicGroup, Lesson, Teacher, Room

class Command(BaseCommand):
    help = "Парсинг расписания"

    def handle(self, *args, **options):
        url = "https://ecampus.ncfu.ru/schedule/GetSchedule"
        target_list = mondays_between(date(2025, 9, 1), date(2025, 12, 29))
        
        for target_date in target_list:
            self.stdout.write(f"Загрузка расписаний на {target_date}")
            for group in AcademicGroup.objects.all():
                payload = {
                    "date": target_date,
                    "Id": group.id,
                    "targetType": 2
                }
                
                while True:
                    try:
                        start_time = time.time()
                        response = requests.post(
                            "https://ecampus.ncfu.ru/schedule/GetSchedule",
                            data=payload,
                            timeout=3,  
                        )
                        duration = time.time() - start_time

                        if duration > 3:
                            continue  

                        data = response.json()
                        break  
                    except (requests.Timeout, requests.ConnectionError, ValueError):
                        self.stdout.write(f"⚠️ Ошибка при получении специальностей, повтор через 2 сек...")
                        time.sleep(2)

                for day in data:
                    for les in day["Lessons"]:
                        teacher_data = les.get("Teacher")
                        room_data = les.get("Aud")
                        teacher = None
                        room = None

                        if teacher_data:
                            teacher, _ = Teacher.objects.get_or_create(
                                id=teacher_data["Id"],
                                defaults={"Name": teacher_data["Name"]}
                            )
                        if room_data:
                            room, _ = Room.objects.get_or_create(
                                id=room_data["Id"],
                                defaults={"Name": room_data["Name"]}
                            )

                        subgroup = ""
                        groups = les.get("Groups") or []
                        if groups:
                            subgroup = groups[0].get("Subgroup", "")

                        Lesson.objects.update_or_create(
                            lesson_id=les["Id"],
                            group=group,
                            date=day["Date"].split("T")[0],
                            defaults={
                                "weekday": day["WeekDay"],
                                "discipline": les["Discipline"].strip(),
                                "lesson_type": les["LessonType"].strip(),
                                "time_begin": les["TimeBegin"].split("T")[1][:5],
                                "time_end": les["TimeEnd"].split("T")[1][:5],
                                "teacher": teacher,
                                "room": room,
                                "subgroup": subgroup
                            }
                        )
                self.stdout.write(f" Загружено расписание для {group.Name}")
