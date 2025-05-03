import telebot
import config
import random
from mistralai import Mistral
import codecs

bot = telebot.TeleBot(config.TELEGRAM_BOT_API)
api_key = config.MISTRAL_AI_API
client = Mistral(api_key=api_key)

file = codecs.open("cities.txt", "r", "utf_8_sig")
cities = []
while True:
    c = file.readline()
    if not c:
        break
    cities.append(c[:-2])
file.close()

games = {}
players = {}
opponent = {}


def last_char(city):
    if city[-1] in ['ь', 'ъ', 'ы']:
        return last_char(city[:-1])
    else:
        return city[-1]


def is_city_exists(city_name):
    try:
        i = cities.index(city_name)
        return True
    except ValueError:
        return False


def is_city_ai(city_name):
    messages = [
        {
            "role": "user",
            "content": f"Существует ли город '{city_name}'? Ответь лишь 'да' или 'нет'"
        }
    ]

    chat_response = client.chat.complete(
        model="mistral-large-latest",
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


@bot.message_handler(commands=['resign'])
def resign(message):
    user_name = message.from_user.username

    try:
        bot.send_message(opponent[user_name]["id"], "Ваш соперник сдался. Поздравляем, вы выиграли!")

        del players[opponent[user_name]["name"]]
        del opponent[opponent[user_name]["name"]]
        del opponent[user_name]["name"]
    except KeyError:
        pass

    del games[players[user_name]]
    del players[user_name]


@bot.message_handler(commands=['play'])
def play(message):
    game_id = str(random.randint(10000, 99999))
    bot.send_message(message.chat.id, f"Игра создана")
    bot.send_message(message.chat.id, f"Если захотите сдаться или выйти из игры напишите '/resign'")
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
    opponent[message.from_user.username]["name"] = games[game_id]["first_player_name"]
    opponent[games[game_id]["first_player_name"]]["name"] = message.from_user.username
    opponent[message.from_user.username]["id"] = games[game_id]["first_player_id"]
    opponent[games[game_id]["first_player_name"]]["id"] = message.from_user.id

    bot.send_message(message.chat.id, f"Игра найдена")
    bot.send_message(message.chat.id, f"Если захотите сдаться или выйти из игры напишите '/resign'")
    bot.send_message(message.chat.id, "Вы начинаете")
    bot.send_message(opponent[message.from_user.username]["id"], "Второй игрок присоединился. Он начинает.")


@bot.message_handler(content_types=['text'])
def playing(message):
    try:
        user_name = message.from_user.username
        game_id = players[user_name]
        turn = games[game_id]["turn"]
        city = message.text.lower()
    except KeyError:
        return

    if user_name == games[game_id]["first_player_name"] == turn:
        if city[0] != games[game_id]["last_char"] and len(games[game_id]["cities"]) != 0:
            bot.send_message(message.chat.id,
                             f"Назвние города должно начинаться на {games[game_id]["last_char"].upper()}")
        elif city in games[game_id]["cities"]:
            bot.send_message(message.chat.id, f"Этот город уже был")
            bot.send_message(opponent[message.from_user.username]["id"], f"Соперник назвал '{city}', но этот город уже был")
        elif not is_city_exists(city):
            bot.send_message(message.chat.id, f"Этого города не существует")
            bot.send_message(opponent[message.from_user.username]["id"],
                             f"Соперник назвал '{city}', но этого города не существует")
            bot.send_message(config.MY_CHAT_ID, f"!!!Был назван и не засчитан город '{city}'")
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
            bot.send_message(opponent[message.from_user.username]["id"],
                             f"Соперник назвал '{city}', но этот город уже был")
        elif not is_city_exists(city):
            bot.send_message(message.chat.id, f"Этого города не существует")
            bot.send_message(opponent[message.from_user.username]["id"],
                             f"Соперник назвал '{city}', но этого города не существует")
            bot.send_message(config.MY_CHAT_ID, f"!!!Был назван и не засчитан город '{city}'")
        else:
            games[game_id]["cities"].append(city)
            bot.send_message(games[game_id]["first_player_id"], f"Оппонент: {city.capitalize()}")
            games[game_id]["last_char"] = last_char(city)
            bot.send_message(games[game_id]["first_player_id"], f"Вам на {games[game_id]["last_char"].upper()}")
            games[game_id]["turn"] = games[game_id]["first_player_name"]

    else:
        bot.send_message(message.chat.id, "Сейчас не ваш ход!")


bot.polling(none_stop=True)
