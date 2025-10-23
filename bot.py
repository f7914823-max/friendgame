import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import json
import random
import os
from game_logic import GameLogic  # Импорт логики (см. ниже)

TOKEN = '8401872579:AAELPVJQyDTIErFg-M-UsxSV2wFCzQbno6U'
bot = telebot.TeleBot(TOKEN)

# Инициализация БД
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, username TEXT, crystals INTEGER DEFAULT 100, level INTEGER DEFAULT 1)''')
conn.commit()

# Загрузка карт
with open('cards.json', 'r') as f:
    CARDS = json.load(f)['cards']


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, crystals) VALUES (?, ?, 100)", (user_id, username))
    conn.commit()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Играть с ботом", callback_data="play_bot"))
    markup.add(InlineKeyboardButton("Играть с другом", callback_data="play_pvp"))
    markup.add(InlineKeyboardButton("Магазин", callback_data="shop"))
    markup.add(InlineKeyboardButton("Баланс", callback_data="balance"))
    markup.add(InlineKeyboardButton("Открыть Mini App", web_app=InlineKeyboardButton("Mini Игра",
                                                                                     url="https://your-host.github.io/game.html")))  # Замени URL на свой хост

    bot.send_message(message.chat.id,
                     f"Привет, {username}! Добро пожаловать в Clash Royale Bot.\nТвои кристаллы: {get_crystals(user_id)}",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    if call.data == "balance":
        crystals = get_crystals(user_id)
        bot.answer_callback_query(call.id, f"Кристаллы: {crystals}")
        bot.edit_message_text(f"Твои кристаллы: {crystals}", call.message.chat.id, call.message.message_id)
    elif call.data == "shop":
        show_shop(call.message.chat.id, call.message.message_id, user_id)
    elif call.data == "play_bot":
        start_game(call.message.chat.id, user_id, is_bot=True)
    elif call.data == "play_pvp":
        bot.send_message(call.message.chat.id, "Пришли ссылку на этот чат другу или добавь бота в группу для PvP!")
        # Для PvP: В группах бот отслеживает ходы по user_id
    elif call.data.startswith("card_"):
        card_id = int(call.data.split("_")[1])
        buy_card(user_id, card_id, call.message.chat.id, call.message.message_id)
    elif call.data.startswith("play_"):
        # Ход в игре
        game_id = call.data.split("_")[1]
        GameLogic.make_move(game_id, user_id, call.data)


def get_crystals(user_id):
    cursor.execute("SELECT crystals FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()[0] or 100


def add_crystals(user_id, amount):
    cursor.execute("UPDATE users SET crystals = crystals + ? WHERE user_id=?", (amount, user_id))
    conn.commit()


def show_shop(chat_id, message_id, user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    for card in CARDS[:3]:  # Первые 3 карты для примера
        markup.add(
            InlineKeyboardButton(f"{card['name']} ({card['cost']} кристаллов)", callback_data=f"card_{card['id']}"))
    bot.edit_message_text("Магазин карт:", chat_id, message_id, reply_markup=markup)


def buy_card(user_id, card_id, chat_id, message_id):
    card = next(c for c in CARDS if c['id'] == card_id)
    crystals = get_crystals(user_id)
    if crystals >= card['cost']:
        add_crystals(user_id, -card['cost'])
        # Сохрани карту в инвентаре (добавь таблицу inventory)
        bot.edit_message_text(f"Купил {card['name']}!", chat_id, message_id)
    else:
        bot.answer_callback_query("Недостаточно кристаллов!")


def start_game(chat_id, user_id, is_bot=False):
    game_id = f"{user_id}_{random.randint(1000, 9999)}"
    player_deck = random.sample(CARDS, 4)  # 4 карты
    bot_deck = random.sample(CARDS, 4) if is_bot else None

    markup = InlineKeyboardMarkup(row_width=2)
    for card in player_deck:
        markup.add(InlineKeyboardButton(card['name'], callback_data=f"play_{game_id}_{card['id']}"))

    bot.send_message(chat_id, f"Игра началась! Твоя колода: {', '.join(c['name'] for c in player_deck)}\nВыбери карту:",
                     reply_markup=markup)

    if is_bot:
        GameLogic.start(game_id, user_id, bot_deck, bot, chat_id)
    # Для PvP: Жди хода второго игрока в том же чате


if __name__ == '__main__':
    bot.polling(none_stop=True)