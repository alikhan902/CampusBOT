import json
from datetime import datetime
from pathlib import Path
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

LOG_FILE = Path("user_actions.json")


class UserLoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = None

        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

        if user_id:
            if LOG_FILE.exists():
                try:
                    with LOG_FILE.open("r", encoding="utf-8") as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
            else:
                logs = []

            logs.append({
                "user_id": user_id,
                "time": datetime.now().isoformat(sep=' ', timespec='seconds')
            })

            with LOG_FILE.open("w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        return await handler(event, data)
