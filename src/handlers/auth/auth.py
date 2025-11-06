import asyncio
import os
import uuid
import re
import json
import aiofiles
from bs4 import BeautifulSoup
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from states.states import AuthForm
from aiogram.filters import Command

router = Router()

# /login
@router.message(Command("login"))
async def login_cmd(message: Message, state: FSMContext,session):
    login_url = "https://ecampus.ncfu.ru/account/login"

    await state.clear() 
    session.cookie_jar.clear()

    async with session.get(login_url) as resp:
        text = await resp.text()

    soup = BeautifulSoup(text, "html.parser")
    token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
    captcha_tag = soup.find("img", {"alt": "captcha"})

    if not token_tag or not captcha_tag:
        await message.answer("Не удалось получить токен или капчу 😢")
        return

    token = token_tag["value"]
    captcha_url = "https://ecampus.ncfu.ru" + captcha_tag["src"]

    filename = f"captcha_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join("captcha", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    async with session.get(captcha_url) as captcha_resp:
        content = await captcha_resp.read()
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

    cookies = {cookie.key: cookie.value for cookie in session.cookie_jar}
    await state.update_data(
        cookies=cookies,
        token=token,
        captcha_filepath=filepath
    )

    await message.answer("Введите логин:")
    await state.set_state(AuthForm.login)

# логин
@router.message(AuthForm.login)
async def process_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введите пароль:")
    await state.set_state(AuthForm.password)
    
# пароль
@router.message(AuthForm.password)
async def process_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    captcha_filepath = data.get("captcha_filepath")
    if captcha_filepath:
        await message.answer_photo(FSInputFile(captcha_filepath), caption="Введите капчу:")
        await asyncio.to_thread(os.remove, captcha_filepath)
    await state.set_state(AuthForm.captcha_code)

# капча
@router.message(AuthForm.captcha_code)
async def process_captcha(message: Message, state: FSMContext, session):
    data = await state.get_data()
    token = data["token"]


    payload = {
        "__RequestVerificationToken": token,
        "Login": data["login"],
        "Password": data["password"],
        "Code": message.text,
        "RememberMe": "false",
    }

    async with session.post("https://ecampus.ncfu.ru/account/login", data=payload) as resp:
        await resp.text()

    async with session.get("https://ecampus.ncfu.ru/schedule/my/student") as get_id:
        html = await get_id.text()

    soup2 = BeautifulSoup(html, "html.parser")
    script = soup2.find("script", type="text/javascript", string=re.compile("viewModel"))

    model_id = None
    if script:
        text = script.string
        match = re.search(r"var\s+viewModel\s*=\s*(\{.*\});", text, re.S)
        if match:
            json_text = match.group(1)
            json_text = re.sub(r'JSON\.parse\((\".*?\")\)', r'\1', json_text)
            try:
                data_json = json.loads(json_text)
                model_id = data_json["Model"]["Id"]
            except Exception:
                model_id = None

    new_cookies = {cookie.key: cookie.value for cookie in session.cookie_jar}
    await state.update_data(cookies=new_cookies, ecampus_id=model_id)
    async with session.post('http://127.0.0.1:8000/api/BotUser/', data = {'user_id': message.from_user.id, 'ecampus_id': model_id, 'cookies': json.dumps(new_cookies)}):
        pass
    if model_id is not None:
        await message.answer(f"Вход выполнен ✅")
    else:
        await message.answer("Авторизация не удалась ❌ \nВозможно вы ввели неверные данные, попробуйте снова")

    await state.set_state(None)
