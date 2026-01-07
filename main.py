import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from termcolor import cprint
import logging
logging.basicConfig(level=logging.INFO)


# ===== НАСТРОЙКИ =====
TOKEN = "TOKEN"


HIGH_ADMINS = [
    5046560155,
    1513168841
]

DATA_FILE = "db.json"
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
session = AiohttpSession(
    proxy="http://test.com"
)

bot = Bot(
    token=TOKEN,
    session=session)
dp = Dispatcher()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def get_or_create_client(user_id):
    """Вернуть существующий анонимный ID или создать новый"""
    for cid, info in data["clients"].items():
        if info["tg_id"] == user_id:
            return cid

    # создание нового id
    new_id = str(len(data["clients"]) + 1)
    data["clients"][new_id] = {"tg_id": user_id, "admin": None, "user": None}
    save_data(data)
    return new_id
def find_user(user_id):
    for cid,info in data["clients"].items():
        if info["tg_id"] == user_id:
            return info["admin"],user_id,cid,info["user"]

async def notify_user(user_id,text):
    """Отправить сообщение пользователю"""
    try:
        await bot.send_message(user_id,text)
    except:
        pass

async def notify_admins(text):
    """Отправить сообщение всем админам"""
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
        except:
            pass


# ======= ХЕНДЛЕРЫ =======

@dp.message(Command("start"))
async def start_cmd(msg: Message):
    await msg.answer(
        "Привет! Ты можешь написать сюда любое сообщение, и администратор ответит тебе анонимно."
    )

@dp.message(Command("untake"))
async def un_take_cmd(msg:Message):
    admin_id = msg.from_user.id
    admin_info = find_user(admin_id)
    user_cid = admin_info[3]
    user_id = data["clients"][user_cid]["tg_id"]
    await msg.answer(f"⚠ Убираем вашего активного пользователя: #{user_cid}")
    try:
        data["clients"][user_cid]["admin"] = None
        data["clients"][admin_info[2]]["user"] = None
        await msg.answer(f"✅ Успешно убали вашего активного пользователя!")
        await notify_user(user_id,"✅ Админ прекратил с вами диалог")
        save_data(data)
    except:
        pass
@dp.message(Command("take"))
async def take_cmd(msg: Message):
    admin_id = msg.from_user.id
    if admin_id not in ADMINS:
        return
    admin_cid = find_user(admin_id)[2]
    parts = msg.text.split()

    if len(parts) != 2:
        await msg.answer("Использование: /take ID")
        return

    cid = parts[1]

    if cid not in data["clients"]:
        await msg.answer("Такого пользователя нет.")
        return
    
    if data["clients"][cid]["admin"] != None:
        await msg.answer("⚠ Данного пользователя уже взял другой админ")
        return
    data["clients"][cid]["admin"] = admin_id
    data["clients"][admin_cid]["user"] = cid
    save_data(data)
    await msg.answer(f"Вы взяли пользователя #{cid}")

@dp.message(Command("addadmin"))
async def add_admin_cmd(msg: Message):
    # Проверка прав
    if msg.from_user.id not in HIGH_ADMINS:
        return

    # Парсинг аргументов
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

    # Добавление админа
    data["admins"].append(adder_id)
    save_data(data)

    await msg.answer(f"✅ Успешно удалён админ: {adder_id} \n Username: @{msg.from_user.username}")
    await notify_user(adder_id, "✨ Вы стали админом! Поздравляем")

@dp.message(Command("deladmin"))
async def Del_Admin_Cmd(msg: Message):
    user_id = msg.from_user.id
    if user_id not in HIGH_ADMINS:
        return

    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: /deladmin ID")
        return 

    try:
        deller_id = int(parts[1])
    except ValueError:
        await msg.answer("ID должен быть числом")
        return

    if deller_id in data["admins"]:
        data["admins"].remove(deller_id)
        save_data(data)

        await msg.answer(f"✅ Успешно удалён админ: {deller_id} \n Username: @{msg.from_user.username}")
        await notify_user(deller_id, "🥀 Вы больше не админ")
    else:
        await msg.answer(f"❌ Этот ID не является админом: {deller_id} \n Username: @{msg.from_user.username}")

@dp.message(Command("reply"))
async def reply_cmd(msg: Message):

    admin_id = msg.from_user.id
    if admin_id not in ADMINS:
        return

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        await msg.answer("Использование: /reply ID текст")
        return

    cid = parts[1]
    text = parts[2]

    if cid not in data["clients"]:
        await msg.answer("Такого пользователя нет.")
        return

    user_tg_id = data["clients"][cid]["tg_id"]
    text = f"Админ: {text}"
    await bot.send_message(user_tg_id, text)
    await msg.answer("Отправлено пользователю.")


@dp.message(F.text & ~F.text.startswith("/"))
async def user_message(msg: Message):
    user_id = msg.from_user.id
    user_info = find_user(user_id)
    cid = get_or_create_client(user_id)

    client = data["clients"][cid]
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
    elif user_id in ADMINS and user_info[3] != None:
        # если закреплён пользователь, то ему надо ответить.
        
        sender_info = data["clients"][user_info[3]]
        await notify_user(sender_info["tg_id"],f"💬Админ: \n{msg.text}")

# ==== админ берет диалог ====

# ======= ЗАПУСК =======

if __name__ == "__main__":
    print("🤖 бот жив")
    dp.run_polling(bot)

