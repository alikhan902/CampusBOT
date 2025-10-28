from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

ALLOWED_COMMANDS = {"/start", "/login", "/help", "/locsh"}

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        state: FSMContext = data.get("state")

        text = (event.text or "").strip()
        if text in ALLOWED_COMMANDS:
            return await handler(event, data)

        if state is not None:
            current_state = await state.get_state() 
            if current_state is not None:
                return await handler(event, data)

        user_data = await state.get_data() if state is not None else {}
        if not user_data.get("cookies") or not user_data.get("ecampus_id"):
            await event.answer("❗ Сначала авторизуйся — команда /login")
            return

        return await handler(event, data)