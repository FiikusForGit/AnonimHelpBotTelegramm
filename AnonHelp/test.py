import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession

TOKEN = "8260007631:AAEKwhr7LiWbTmKul50fcCSuEwKGDlGaktc"

session = AiohttpSession(
    proxy="http://user347683:74picw@194.87.150.73:5110"
)

bot = Bot(
    token=TOKEN,
    session=session)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Я твой первый бот 🤖")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
