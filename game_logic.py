import random


class GameLogic:
    games = {}  # {game_id: {'player_deck': [], 'bot_deck': [], 'player_hp': 30, 'bot_hp': 30, 'turn': 'player'}}

    @staticmethod
    def start(game_id, user_id, bot_deck, bot, chat_id):
        GameLogic.games[game_id] = {
            'player_deck': [],  # Заполни из bot.py
            'bot_deck': bot_deck,
            'player_hp': 30,
            'bot_hp': 30,
            'turn': 'player'
        }
        # Симулируй бота позже

    @staticmethod
    def make_move(game_id, user_id, data):
        game = GameLogic.games.get(game_id)
        if not game:
            return

        card_id = int(data.split("_")[-1])
        card = next(c for c in game['player_deck'] if c['id'] == card_id)  # Найди карту

        # Атака: Урон = атака карты
        game['bot_hp'] -= card['attack']

        if game['bot_hp'] <= 0:
            # Победа
            bot.send_message(chat_id, "Ты победил! +50 кристаллов")
            # add_crystals(user_id, 50)  # Импорт из bot.py
            del GameLogic.games[game_id]
            return

        # Ход бота
        if game['turn'] == 'player':
            bot_card = random.choice(game['bot_deck'])
            game['player_hp'] -= bot_card['attack']
            bot.send_message(chat_id, f"Бот атакует {bot_card['name']}! Твоё HP: {game['player_hp']}")

            if game['player_hp'] <= 0:
                bot.send_message(chat_id, "Бот победил!")
                del GameLogic.games[game_id]
                return

        # Продолжить игру...