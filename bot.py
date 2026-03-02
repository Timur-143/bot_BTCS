import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = "8754310840:AAFQ4JPyEJUZct02zal_gvR6AaW5EWKC59U"
CHANNEL_ID = "@iruka61"  # ВСТАВЬ ID КАНАЛА
COOLDOWN = 300  # 30 минут (в секундах)

# антиспам словарь
user_cooldowns = {}

class MissStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_choice = State()
    waiting_for_pseudonym = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет 👋\n"
        "Напиши /miss чтобы отправить сообщение в канал.\n"
        "⚠ Можно отправлять 1 сообщение раз в 5 минут."
    )


@dp.message(Command("miss"))
async def miss(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_time = time.time()

    # Проверка КД
    if user_id in user_cooldowns:
        remaining = COOLDOWN - (current_time - user_cooldowns[user_id])
        if remaining > 0:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            await message.answer(
                f"⛔ Подожди {minutes}м {seconds}с перед следующей отправкой."
            )
            return

    await message.answer("Отправь текст, фото или видео.")
    await state.set_state(MissStates.waiting_for_content)


@dp.message(MissStates.waiting_for_content)
async def get_content(message: Message, state: FSMContext):

    data = {}

    if message.text:
        data["type"] = "text"
        data["text"] = message.text

    elif message.photo:
        data["type"] = "photo"
        data["file_id"] = message.photo[-1].file_id
        data["caption"] = message.caption

    elif message.video:
        data["type"] = "video"
        data["file_id"] = message.video.file_id
        data["caption"] = message.caption

    else:
        await message.answer("Поддерживается только текст, фото или видео.")
        return

    await state.update_data(miss=data)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Анонимно", callback_data="anon"),
            InlineKeyboardButton(text="Под псевдонимом", callback_data="pseud")
        ]
    ])

    await message.answer("Как отправить?", reply_markup=kb)
    await state.set_state(MissStates.waiting_for_choice)


@dp.callback_query(F.data == "anon", MissStates.waiting_for_choice)
async def send_anon(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_cooldowns[user_id] = time.time()

    data = await state.get_data()
    miss = data["miss"]

    if miss["type"] == "text":
        await bot.send_message(CHANNEL_ID, f"📩 Анонимное сообщение:\n\n{miss['text']}")

    elif miss["type"] == "photo":
        await bot.send_photo(
            CHANNEL_ID,
            miss["file_id"],
            caption=f"📩 Анонимное фото\n\n{miss.get('caption','')}"
        )

    elif miss["type"] == "video":
        await bot.send_video(
            CHANNEL_ID,
            miss["file_id"],
            caption=f"📩 Анонимное видео\n\n{miss.get('caption','')}"
        )

    await callback.message.answer("✅ Отправлено анонимно!")
    await callback.answer()
    await state.clear()



@dp.callback_query(F.data == "pseud", MissStates.waiting_for_choice)
async def ask_pseud(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи псевдоним:")
    await callback.answer()
    await state.set_state(MissStates.waiting_for_pseudonym)


@dp.message(MissStates.waiting_for_pseudonym)
async def send_pseud(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_cooldowns[user_id] = time.time()

    pseud = message.text
    data = await state.get_data()
    miss = data["miss"]

    header = f"📩 Сообщение от {pseud}:\n\n"

    if miss["type"] == "text":
        await bot.send_message(CHANNEL_ID, header + miss["text"])

    elif miss["type"] == "photo":
        await bot.send_photo(
            CHANNEL_ID,
            miss["file_id"],
            caption=header + miss.get("caption","")
        )

    elif miss["type"] == "video":
        await bot.send_video(
            CHANNEL_ID,
            miss["file_id"],
            caption=header + miss.get("caption","")
        )

    await message.answer("✅ Отправлено под псевдонимом!")
    await state.clear()


async def main():
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())