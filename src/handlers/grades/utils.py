
import asyncio
import time

from aiohttp import ClientTimeout

async def post_lesson(session, payload, start_time_lesson):
    try:
        timeout = ClientTimeout(total=3)
        async with session.post(
            "https://ecampus.ncfu.ru/studies/GetLessons", data=payload, timeout=timeout
        ) as grades_resp:
            end_time_lesson = time.perf_counter()
            elapsed_lesson = end_time_lesson - start_time_lesson
            print(f"Время лессон запроса {elapsed_lesson}")
            
            if grades_resp.status == 200:
                grades = await grades_resp.json()
                return grades, True
            return None, False
            
    except asyncio.exceptions.TimeoutError:
        return await post_lesson(session, payload, start_time_lesson)
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None, False
        
        
    