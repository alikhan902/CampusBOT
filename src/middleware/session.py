from aiogram import BaseMiddleware
from aiohttp import ClientSession, CookieJar

class SessionMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.sessions = {}

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        if user_id not in self.sessions:
            self.sessions[user_id] = ClientSession(cookie_jar=CookieJar())

        data["session"] = self.sessions[user_id]

        result = await handler(event, data)
        return result

    async def close(self):
        for session in self.sessions.values():
            await session.close()
