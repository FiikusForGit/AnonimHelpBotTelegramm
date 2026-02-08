# ===== Импорт библиотек =====
import json
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from termcolor import cprint

load_dotenv()

# ===== Включение логв =====
import logging
logging.basicConfig(level=logging.INFO)


# ===== Настройки =====

# ----- выбираем режим (main или test) -----
# можно передать аргумент при запуске
# python main.py main   или python main.py test
mode = input("Введите режим:\n")
BASE_DIR = ""
if mode == "main":
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_main")
elif mode == "test":
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_test")
else:
    raise ValueError("Неверный режим: используйте 'main' или 'test'")

# ----- загружаем .env из выбранной папки -----
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

# ----- получаем токен и файл базы -----
TOKEN = os.getenv("TOKEN")
DATA_FILE = os.path.join(BASE_DIR, os.getenv("DATA_FILE", "db.json"))

print("Используем TOKEN:", TOKEN)
print("Используем DATA_FILE:", DATA_FILE)

HIGH_ADMINS = [
    5046560155,
    1513168841
]

# =====================


# --- загрузка/сохранение данных ---
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"clients": {},"admins":{}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


data = load_data() 
ADMINS = data["admins"]

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

# --- найти/создать пользователя ---
def get_or_create_user(user_id):
    """Вернуть существующий анонимный ID или создать новый"""
    for cid, info in data["clients"].items():
        if info["tg_id"] == user_id:
            return cid

    # создание нового id
    new_id = str(len(data["clients"]) + 1)
    data["clients"][new_id] = {"tg_id": user_id, "admin": None, "user": None,"username": None}
    save_data(data)
    return new_id
# --- получить дату пользователя ---
def find_user(user_id):
    for cid,info in data["clients"].items():
        if info["tg_id"] == user_id:
            return info["admin"],user_id,cid,info["user"]
# --- уведомление пользователя ---
async def notify_user(user_id,text):
    """Отправить сообщение пользователю"""
    try:
        await bot.send_message(user_id,text)
    except:
        pass
# --- уведомление всех админов о новом пользователе ---
async def notify_admins(text):
    """Отправить сообщение всем админам"""
    for admin_id in ADMINS:
        try:
           await bot.send_message(admin_id, text)
        except:
            pass

# ======= Функции =======



# ======= Основные команды =======

# --- команда /start ---
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    await msg.answer(
        f"Привет! Ты можешь написать сюда любое сообщение, и администратор ответит тебе анонимно."
    )
    user_id = msg.from_user.id
    user_cid = get_or_create_user(user_id)
    data["clients"][user_cid]["username"] = msg.from_user.username
    save_data(data)

# --- команда /info ---
@dp.message(Command("info"))
async def info_cmd(msg: Message):
    if not msg.from_user.id in HIGH_ADMINS:
        return
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Использование: /info Номер_Пользователя")
        return
    cid = parts[1]
    target_user = data["clients"][cid]
    print(target_user)
    await msg.answer(
        f"✅ Информация на пользователя #{cid}:\n\n"
        f"{json.dumps(target_user,indent=2)}"
        )

@dp.message(Command("vievdb"))
async def vievdb_cmd(msg: Message):
    if not msg.from_user.id in HIGH_ADMINS:
         return
    await msg.answer(
	f"✅ вся дб: \n"
	f"{json.dumps(data,indent=4)}"
	)
# --- команда /untake чтобы отвязать закреплённого пользователя ---
@dp.message(Command("untake"))
async def un_take_cmd(msg:Message):
    # Создание переменных для удобства:
    # admin_id - получение id телеграма админа
    # admin_info - получение даты админа через id телеграма
    # user_cid - получение уникального номера пользователя через дату админа
    # user_id - получение id телеграма пользователя через дату админа
    admin_id = msg.from_user.id
    admin_info = find_user(admin_id)
    user_cid = admin_info[3]
    user_id = data["clients"][user_cid]["tg_id"]
    await msg.answer(f"⚠ Убираем вашего закреплённого пользователя: #{user_cid}")

    # Попытка убрать закреплённого пользователя
    try:

        # Удаление закреплённого админа у пользователя. И удаление закреплённого пользователя у админа
        data["clients"][user_cid]["admin"] = None
        data["clients"][admin_info[2]]["user"] = None

        # Уведомление об успехе
        await msg.answer(f"✅ Успешно убали вашего закреплённого пользователя!")
        save_data(data)
    except:
        pass
# --- команда /take чтобы сделать пользователя активным ---
@dp.message(Command("take"))
async def take_cmd(msg: Message):
    # Проверка прав
    if msg.from_user.id not in ADMINS:
        return
    # admin_cid - уникальный номер админа
    admin_cid = find_user(msg.from_user.id)[2]

    # Проверка аргументов
    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer("Использование: /take ID")
        return

    # cid - униикальный номер пользователя
    cid = parts[1]

    # проверка на существование данного уникального номера
    if cid not in data["clients"]:
        await msg.answer("Такого пользователя нет.")
        return

    # Если другой админ уже взял данного пользователя, то уведомить админа об этом
    if data["clients"][cid]["admin"] != None:
        await msg.answer("⚠ Данного пользователя уже взял другой админ")
        return
    # Изменение даты, чтобы закрепились закреплённый пользователь/админ
    data["clients"][cid]["admin"] = msg.from_user.id
    data["clients"][admin_cid]["user"] = cid
    data["clients"][cid]["username"] = msg.from_user.first_name
    # Сохранение даты и уведомление админа
    save_data(data)
    await msg.answer(f"Вы взяли пользователя #{cid}")

# --- команда /addadmin для добавления админа ---
@dp.message(Command("addadmin"))
async def add_admin_cmd(msg: Message):
    # Проверка прав
    if msg.from_user.id not in HIGH_ADMINS:
        return

    # Проперка аргументов
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: /addadmin ID")
        return

    # Проверка ID
    try:
        adder_id = int(parts[1])
    except ValueError:
        await msg.answer("ID должен быть числом")
        return

    # Проверка, не админ ли уже
    if adder_id in data["admins"]:
        await msg.answer("⚠️ Этот пользователь уже админ")
        return

    # Добавление "цели" в админы
    data["admins"].append(adder_id)
    save_data(data)

    # Уведомить главного админа и "цель" об успехе
    await msg.answer(f"✅ Успешно удалён админ: {adder_id} \n Username: @{msg.from_user.username}")
    await notify_user(adder_id, "✨ Вы стали админом! Поздравляем")

# --- команда /deladmin для удаления админа ---
@dp.message(Command("deladmin"))
async def Del_Admin_Cmd(msg: Message):
    # Проверка прав
    if msg.from_user.id not in HIGH_ADMINS:
        return
    # Проверка аргументов
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: /deladmin ID")
        return 

    # Проверка ID
    try:
        deller_id = int(parts[1])
    except ValueError:
        await msg.answer("ID должен быть числом")
        return

    # Проверка, является ли "цель" админом
    if deller_id in data["admins"]:
        
        # Сохранение даты
        data["admins"].remove(deller_id)
        save_data(data)

        # Уведомить "цель" и глав. админа об успехе
        await msg.answer(f"✅ Успешно удалён админ: {deller_id} \n Username: @{msg.from_user.username}")
        await notify_user(deller_id, "🥀 Вы больше не админ")
    else:
        # Уведомить глав. админа, что "цель" админом не является
        await msg.answer(f"❌ Этот ID не является админом: {deller_id} \n Username: @{msg.from_user.username}")

# --- команда /reply для ответа пользователю, без взятия диалога ---
@dp.message(Command("reply"))
async def reply_cmd(msg: Message):
    # Проверка прав
    if msg.from_user.id not in ADMINS:
        return

    # Проверка аргументов
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("Использование: /reply ID текст")
        return
    # Деление аргументов на:
    # cid - уникальный номер пользователя
    # text - текст написанный админом
    cid = parts[1]
    text = parts[2]

    # Проверка, есть ли уникальный номер в базе данных
    if cid not in data["clients"]:
        # Уведомить админа, что такого пользователя нет
        await msg.answer("Такого пользователя нет.")
        return

    # Создание переменных для удобства:
    # user_tg_id - получение id в телеграмме пользователя через уникальный номер
    # text - преобразование текста админа
    user_tg_id = data["clients"][cid]["tg_id"]
    text = f"Админ: {text}"

    # Отправить сообшение админа пользователю и уведомить админа об успешной отправке
    await bot.send_message(user_tg_id, text)
    await msg.answer("Отправлено пользователю.")


# --- триггер всех сообщенний, кроме тех, которые начинаются с "/" ---
@dp.message(F.text & ~F.text.startswith("/"))
async def user_message(msg: Message):
    # Создание переменных для удобства:
    # user_id - получение id в телеграме благодаря сообщению
    # user_info - найти дату пользователя по айди в тг
    # cid - получение уникального номера по айди в тг
    user_id = msg.from_user.id
    user_info = find_user(user_id)
    cid = get_or_create_user(user_id)

    # Получение пользователя
    client = data["clients"][cid]
    if not "username" in client or client["username"] == None:
        print(msg.from_user.username)
        client["username"] = msg.from_user.username
        save_data(data)
    # Если пользователь не админ, то его сообещния бот регестрировать не будет
    if user_id not in ADMINS:
            
        # если админ уже закреплен — отправить ему
        if client["admin"]:
            await bot.send_message(
                client["admin"],
                f"👤Пользователь #{cid}\n{msg.text}"
            )
            return

        # иначе — уведомить всех админов
        await notify_admins(
            f"⭐ Новый пользователь! #{cid}\n\n🎫 Сообщение: {msg.text}\n\n"
            f"📳 Чтобы взять диалог: /take {cid}\n"
            f"✅ Чтобы ответить: /reply {cid} текст"
        )

        await msg.answer("Твоё сообщение отправлено! ✅ Админ скоро ответит!😊")
        
    # Если же пользователь админ и у него есть закреплённый пользователь, то ему присылается сообщение админа
    elif user_id in ADMINS and user_info[3] != None:
    
        sender_info = data["clients"][user_info[3]]
        await notify_user(sender_info["tg_id"],f"💬Админ: \n{msg.text}")


# ======= ЗАПУСК =======

if __name__ == "__main__":
    print("🤖 бот жив")
    dp.run_polling(bot)
