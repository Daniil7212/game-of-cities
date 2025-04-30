import telebot
import config
import random
from mistralai import Mistral

bot = telebot.TeleBot(config.TELEGRAM_BOT_API)
api_key = config.MISTRAL_AI_API
client = Mistral(api_key=api_key)

games = {}
players = {}


def last_char(city):
    if city[-1] in ['ь', 'ъ', 'ы', 'й']:
        return last_char(city[:-1])
    else:
        return city[-1]


def is_city_exists(city_name):
    messages = [
        {
            "role": "user",
            "content": f"Существует ли город '{city_name}'? Ответь 'да' или 'нет'. Не используй символ '.'"
        }
    ]

    chat_response = client.chat.complete(
        model="ministral-8b-latest",
        messages=messages
    )

    print(chat_response.choices[0].message.content.lower())
    if chat_response.choices[0].message.content.lower() == "да":
        return True
    else:
        return False


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     """
                    Это игра в Города
                    Напишите '/play' чтобы создать игру
                    Или '/join [ID_игры]' чтобы присоединиться к игре
                    """)


@bot.message_handler(commands=['play'])
def play(message):
    game_id = str(random.randint(10000, 99999))
    bot.send_message(message.chat.id, f"Игра создана")
    bot.send_message(message.chat.id, f"ID игры: {game_id}")
    players[message.from_user.username] = game_id
    games[game_id] = {
        "cities": [],
        "first_player_id": message.from_user.id,
        "first_player_name": message.from_user.username,
        "turn": None,
        "last_char": None
    }


@bot.message_handler(commands=['join'])
def join(message):
    if len(message.text.split()) != 2:
        bot.send_message(message.chat.id, "Укажите ID игры: `/join [ID_игры]`")

    game_id = message.text.split()[1]

    if game_id not in games:
        bot.send_message(message.chat.id, "Игра не найдена")

    games[game_id]["second_player_id"] = message.from_user.id
    games[game_id]["second_player_name"] = message.from_user.username
    games[game_id]["turn"] = message.from_user.username
    players[message.from_user.username] = game_id

    bot.send_message(message.chat.id, "Вы начинаете")


@bot.message_handler(content_types=['text'])
def playing(message):
    user_name = message.from_user.username
    game_id = players[user_name]
    turn = games[game_id]["turn"]
    city = message.text.lower()

    if user_name == games[game_id]["first_player_name"] == turn:
        if city[0] != games[game_id]["last_char"] and len(games[game_id]["cities"]) != 0:
            bot.send_message(message.chat.id,
                             f"Назвние города должно начинаться на {games[game_id]["last_char"].upper()}")
        elif city in games[game_id]["cities"]:
            bot.send_message(message.chat.id, f"Этот город уже был")
        elif not is_city_exists(city):
            bot.send_message(message.chat.id, f"Этого города не существует")
        else:
            games[game_id]["cities"].append(city)
            bot.send_message(games[game_id]["second_player_id"], f"Оппонент: {city.capitalize()}")
            games[game_id]["last_char"] = last_char(city)
            bot.send_message(games[game_id]["second_player_id"], f"Вам на {games[game_id]["last_char"].upper()}")
            games[game_id]["turn"] = games[game_id]["second_player_name"]

    elif user_name == games[game_id]["second_player_name"] == turn:
        if city[0] != games[game_id]["last_char"] and len(games[game_id]["cities"]) != 0:
            bot.send_message(message.chat.id,
                             f"Назвние города должно начинаться на {games[game_id]["last_char"].upper()}")
        elif city in games[game_id]["cities"]:
            bot.send_message(message.chat.id, f"Этот город уже был")
        elif not is_city_exists(city):
            bot.send_message(message.chat.id, f"Этого города не существует")
        else:
            games[game_id]["cities"].append(city)
            bot.send_message(games[game_id]["first_player_id"], f"Оппонент: {city.capitalize()}")
            games[game_id]["last_char"] = last_char(city)
            bot.send_message(games[game_id]["first_player_id"], f"Вам на {games[game_id]["last_char"].upper()}")
            games[game_id]["turn"] = games[game_id]["first_player_name"]

    else:
        bot.send_message(message.chat.id, "Сейчас не ваш ход!")


bot.polling(none_stop=True)
