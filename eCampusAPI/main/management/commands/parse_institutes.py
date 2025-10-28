import random
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from main.models import Institute, Specialty, AcademicGroup


class Command(BaseCommand):
    help = "Парсит институты, специальности и группы из ecampus.ncfu.ru/schedule"

    def handle(self, *args, **options):
        url = "https://ecampus.ncfu.ru/schedule"

        self.stdout.write("🔍 Загружаю страницу...")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        script = soup.find("script", type="text/javascript", string=re.compile("viewModel"))
        match = re.search(r"var\s+viewModel\s*=\s*(\{.*\});", script.string, re.S)
        json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', match.group(1))
        data_json = json.loads(json_text)
        institutes = data_json.get("Institutes", [])

        self.stdout.write(f"📘 Найдено институтов: {len(institutes)}")

        # === 1. Парсим и сохраняем институты ===
        for inst in institutes:
            inst_id = inst["Id"] or random.randint(1000000000, 9999999999)
            Institute.objects.update_or_create(
                id=inst_id,
                defaults={
                    "ShortName": inst.get("ShortName", ""),
                    "Name": inst.get("Name", ""),
                    "BranchId": inst.get("BranchId", ""),
                },
            )

        self.stdout.write(f"🏫 Загружено институтов: {Institute.objects.count()}")

        # === 2. Получаем и сохраняем специальности ===
        for institute in Institute.objects.all():
            payload = {
                "instituteId": None if len(str(institute.id)) == 10 else institute.id,
                "branchId": institute.BranchId,
            }
            while True:
                try:
                    start_time = time.time()
                    specialties = requests.post(
                        "https://ecampus.ncfu.ru/schedule/GetSpecialities",
                        data=payload,
                        timeout=3,  
                    )
                    duration = time.time() - start_time

                    if duration > 3:
                        continue  

                    specialties = specialties.json()
                    break  

                except (requests.Timeout, requests.ConnectionError, ValueError):
                    self.stdout.write(f"⚠️ Ошибка при получении специальностей, повтор через 2 сек...")
                    time.sleep(2)

            for spec in specialties:
                Specialty.objects.update_or_create(
                    Name=spec["Name"],
                    InstituteID=institute,
                    defaults={},
                )

            self.stdout.write(f"📚 {institute.Name}: {len(specialties)} специальностей")

        self.stdout.write(f"📘 Всего специальностей: {Specialty.objects.count()}")

        # === 3. Получаем и сохраняем академические группы ===
        for specialty in Specialty.objects.all():
            institute = specialty.InstituteID
            payload = {
                "instituteId": None if len(str(institute.id)) == 10 else institute.id,
                "branchId": institute.BranchId,
                "specialty": specialty.Name,
            }
            while True:
                try:
                    start_time = time.time()
                    groups = requests.post(
                        "https://ecampus.ncfu.ru/schedule/GetAcademicGroups",
                        data=payload,
                        timeout=3,  # максимум 3 секунды ожидания
                    )
                    duration = time.time() - start_time

                    if duration > 3:
                        self.stdout.write(f"⏱ Запрос для '{specialty.Name}' занял {duration:.1f}с — повтор...")
                        continue  # повторить запрос

                    groups_json = groups.json()
                    break  # выйти из while при успешном ответе

                except (requests.Timeout, requests.ConnectionError, ValueError):
                    self.stdout.write(f"⚠️ Ошибка при получении групп '{specialty.Name}', повтор через 2 сек...")
                    time.sleep(2)

            for edu_block in groups_json:
                edu_level = edu_block.get("Key")
                for group in edu_block.get("Value", []):
                    AcademicGroup.objects.update_or_create(
                        id=group["Id"],
                        defaults={
                            "Name": group["Name"],
                            "EduLevel": group.get("EduLevel", edu_level),
                            "SpecialtyId": specialty,
                        },
                    )

            self.stdout.write(f"👥 {specialty.Name}: группы добавлены")

        self.stdout.write(self.style.SUCCESS("✅ Институты, специальности и группы успешно загружены!"))
