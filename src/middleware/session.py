from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiohttp import ClientSession

class SessionMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.sessions = {}

    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            user_id = None

        if user_id is not None:
            if user_id not in self.sessions:
                self.sessions[user_id] = ClientSession()

            data["session"] = self.sessions[user_id]

        result = await handler(event, data)
        return result

    async def close(self):
        for session in self.sessions.values():
            await session.close()
