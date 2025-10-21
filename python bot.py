import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

# Токен твоего бота
TOKEN = "8401872579:AAELPVJQyDTIErFg-M-UsxSV2wFCzQbno6U"

# URL твоего Mini App (замени на реальный после хостинга)
MINI_APP_URL = "https://твой-username.github.io/gamefriend-miniapp/"

# Файл для хранения данных (аккаунты, друзья)
DATA_FILE = "gamefriend_data.json"


# Загрузка/сохранение данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"users": {}, "friend_requests": {}, "game_invites": {}}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


data = load_data()
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Без_юзернейма"

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "username": username,
            "balance": 1000,  # Игровая валюта
            "friends": []
        }
        save_data(data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть с друзьями", web_app=types.WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👥 Добавить друга", callback_data="add_friend")],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile")]
    ])

    await message.answer(
        f"🎉 Добро пожаловать в GameFriend, {username}!\n"
        "Играй с друзьями на игровую валюту!\n"
        "Добавь друзей и приглашай в битвы. Твой баланс: {data['users'][user_id]['balance']} 💰",
        reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data == "profile")
async def profile_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = data["users"][user_id]
    friends_count = len(user["friends"])

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))

    await callback.message.edit_text(
        f"👤 Профиль @{user['username']}\n"
        f"💰 Баланс: {user['balance']}\n"
        f"👫 Друзей: {friends_count}\n"
        f"Играй и зарабатывай валюту!",
        reply_markup=keyboard.as_markup()
    )


@dp.callback_query(lambda c: c.data == "add_friend")
async def add_friend_handler(callback: CallbackQuery):
    # Здесь можно добавить поиск по username, но для простоты — inline для приглашения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Ввести username друга", callback_data="input_username")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(
        "👥 Добавить друга:\n"
        "Нажми кнопку ниже и введи username (без @).",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.reply_to_message and message.reply_to_message.text == "Введи username друга:")
async def process_username(message: types.Message):
    target_username = message.text.strip().replace('@', '')
    sender_id = message.from_user.id
    sender_username = data["users"][sender_id]["username"]

    # Поиск target_user по username
    target_id = None
    for uid, u in data["users"].items():
        if u["username"].lower() == target_username.lower():
            target_id = uid
            break

    if not target_id:
        await message.answer("❌ Пользователь не найден. Убедись, что он запускал /start.")
        return

    if target_id == sender_id:
        await message.answer("❌ Нельзя добавить себя.")
        return

    if target_id in data["users"][sender_id]["friends"]:
        await message.answer("✅ Вы уже друзья!")
        return

    # Отправка запроса
    data["friend_requests"][f"{sender_id}_{target_id}"] = {"from": sender_id, "to": target_id, "type": "friend"}
    save_data(data)

    # Уведомление получателю
    await bot.send_message(
        target_id,
        f"🤝 @{sender_username} предложил тебе дружить!\n"
        f"Прими в Mini App или ответь /accept_friend_{sender_id}"
    )

    await message.answer(f"✅ Запрос отправлен @{target_username}!")


@dp.message(Command("accept_friend_"))
async def accept_friend_handler(message: types.Message):
    parts = message.text.split('_')
    if len(parts) < 3:
        return
    sender_id = int(parts[2])
    user_id = message.from_user.id

    if f"{sender_id}_{user_id}" in data["friend_requests"]:
        del data["friend_requests"][f"{sender_id}_{user_id}"]
        data["users"][user_id]["friends"].append(sender_id)
        data["users"][sender_id]["friends"].append(user_id)
        save_data(data)

        sender_username = data["users"][sender_id]["username"]
        await message.answer(f"✅ Ты принял дружбу с @{sender_username}!")

        await bot.send_message(sender_id, f"🎉 @{data['users'][user_id]['username']} принял твою заявку в друзья!")


@dp.callback_query(lambda c: c.data == "invite_game")
async def invite_game_handler(callback: CallbackQuery):
    # Приглашение в игру (аналогично, но для игры)
    user_id = callback.from_user.id
    # Для простоты — текстовая команда, но можно расширить
    await callback.answer("📢 Отправь /invite_game_@username_описание_игры", show_alert=True)


@dp.message(Command("invite_game_"))
async def process_game_invite(message: types.Message):
    parts = message.text.split('_', 3)
    if len(parts) < 4:
        await message.answer("Формат: /invite_game_@username_описание")
        return

    target_username = parts[1].replace('@', '')
    description = parts[3]
    sender_id = message.from_user.id
    sender_username = data["users"][sender_id]["username"]

    target_id = None
    for uid, u in data["users"].items():
        if u["username"].lower() == target_username.lower():
            target_id = uid
            break

    if not target_id:
        await message.answer("❌ Пользователь не найден.")
        return

    # Отправка приглашения
    data["game_invites"][f"{sender_id}_{target_id}"] = {"from": sender_id, "to": target_id, "desc": description}
    save_data(data)

    await bot.send_message(
        target_id,
        f"🎮 @{sender_username} приглашает тебя в игру!\n"
        f"Описание: {description}\n"
        f"Прими: /accept_game_{sender_id}"
    )

    await message.answer(f"✅ Приглашение отправлено @{target_username}!")


@dp.message(Command("accept_game_"))
async def accept_game_handler(message: types.Message):
    parts = message.text.split('_')
    if len(parts) < 3:
        return
    sender_id = int(parts[2])
    user_id = message.from_user.id

    if f"{sender_id}_{user_id}" in data["game_invites"]:
        invite = data["game_invites"].pop(f"{sender_id}_{user_id}")
        del data["game_invites"][f"{sender_id}_{user_id}"]
        save_data(data)

        sender_username = data["users"][sender_id]["username"]
        await message.answer(
            f"🚀 Ты принял приглашение от @{sender_username}!\n"
            f"Запусти Mini App для игры: 🎮 Играть с друзьями",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Играть", web_app=types.WebAppInfo(url=MINI_APP_URL))]
            ])
        )

        await bot.send_message(sender_id,
                               f"✅ @{data['users'][user_id]['username']} присоединился к игре! Описание: {invite['desc']}")


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть с друзьями", web_app=types.WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="👥 Добавить друга", callback_data="add_friend")],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile")]
    ])
    await callback.message.edit_text(
        f"🏠 Главное меню\nТвой баланс: {data['users'][user_id]['balance']} 💰",
        reply_markup=keyboard
    )


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "/start — Запуск\n"
        "/profile — Профиль\n"
        "Для друзей: Добавь username в Mini App или через бота.\n"
        "Приглашения приходят как уведомления!"
    )


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())