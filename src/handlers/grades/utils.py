
import asyncio
import time

from aiohttp import ClientTimeout

async def post_lesson(session, payload):
    try:
        timeout = ClientTimeout(total=3)
        async with session.post(
            "https://ecampus.ncfu.ru/studies/GetLessons", data=payload, timeout=timeout
        ) as grades_resp:
            
            if grades_resp.status == 200:
                grades = await grades_resp.json()
                return grades, True
            return None, False
            
    except asyncio.exceptions.TimeoutError:
        return await post_lesson(session, payload)
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None, False
        
        
    