import telebot
import config
import random
from mistralai import Mistral
import codecs

# API
bot = telebot.TeleBot(config.TELEGRAM_BOT_API)
api_key = config.MISTRAL_AI_API
client = Mistral(api_key=api_key)

# Список существующих городов
file = codecs.open("cities.txt", "r", "utf_8_sig")
cities = []
while True:
    c = file.readline()
    if not c:
        break
    cities.append(c[:-2].lower())
file.close()

# Data
games = {}
players = {}
opponent = {}
tele_id = {}
answers = ['Такой город действительно есть', 'Ок', 'Хорошо', 'И вправду', 'Хороший выбор', 'Very good']
is_time_game = False


# На какую букву ходить следующим
def last_char(city):
    if city[-1] in ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'э', 'ю', 'я']:
        return city[:-1]
    else:
        return last_char(city[:-1])


# Проверка существует ли такой город
def is_city_exists(city_name):
    low = 0
    high = len(cities) - 1

    while low <= high:
        mid = (low + high) // 2
        guess = cities[mid]
        if guess == city_name:
            return True
        if guess > city_name:
            high = mid - 1
        else:
            low = mid + 1
    return False


def is_city_new(cities_list, city_name):
    low = 0
    high = len(cities_list) - 1

    while low <= high:
        mid = (low + high) // 2
        guess = cities_list[mid]
        if guess == city_name:
            return False
        if guess > city_name:
            high = mid - 1
        else:
            low = mid + 1
    return True


# Проверка правильно ли написан с помощью нейросети
def correct_city_ai(city_name):
    try:
        messages = [
            {
                "role": "user",
                "content": f"Если '{city_name}' это город, то если он написан неправильно напиши правильно. Отправь только итоговый город без лишних знаков."
            }
        ]

        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=messages
        )

        return chat_response.choices[0].message.content
    except:
        return "error"


# Команда запуска бота
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     """
                    Это игра в Города
                    Напишите '/create' чтобы создать игру
                    Или '/join ID_игры' чтобы присоединиться к игре
                    """)


# Команда создания игры
@bot.message_handler(commands=['create'])
def create(message):
    game_id = str(random.randint(1000, 9999))
    while game_id in games:
        game_id = str(random.randint(1000, 9999))

    bot.send_message(message.chat.id, f"Игра создана")
    bot.send_message(message.chat.id, f"ID игры: {game_id}")
    bot.send_message(message.chat.id, f"Когда все игроки присоединятся напишите '/play' чтобы начать")
    bot.send_message(message.chat.id, f"Если захотите выйти из игры напишите '/leave'")

    players[message.from_user.username] = game_id
    tele_id[message.from_user.username] = message.from_user.id
    games[game_id] = {
        "cities": [],
        "players": [message.from_user.username, ],
        "turn": None,
        "last_char": None,
        "is_times": False
    }

    try:
        if message.text.split()[-1] == "time":
            games[game_id]["is_times"] = True
    except:
        pass


# Команда выхода из игры
@bot.message_handler(commands=['leave'])
def leave(message):
    if len(games[players[message.from_user.username]]["players"]) <= 2:
        bot.send_message(message.from_user.id, "Хорошо, мы удалили вас из игры")

        del tele_id[message.from_user.username]
        games[players[message.from_user.username]]["players"].remove(message.from_user.username)

        if len(games[players[message.from_user.username]]["players"]) == 1:
            pl = games[players[message.from_user.username]]["players"][0]

            bot.send_message(tele_id[pl], "Ваш последний противник вышел из игры. Поздравляем, вы выиграли!")

            del players[pl]
            del tele_id[pl]

        del games[players[message.from_user.username]]
        del players[message.from_user.username]

    else:
        bot.send_message(message.from_user.id, "Хорошо, мы удалили вас из игры")

        group = games[players[message.from_user.username]]["players"]
        if group.index(message.from_user.username) == len(group) - 1:
            games[players[message.from_user.username]]["turn"] = 0
            bot.send_message(tele_id[group[0]], "Ваш ход")
            bot.send_message(tele_id[group[0]], f"Вам на {games[players[message.from_user.username]]["last_char"].upper()}")

        del tele_id[message.from_user.username]
        games[players[message.from_user.username]]["players"].remove(message.from_user.username)

        for i in games[players[message.from_user.username]]["players"]:
            bot.send_message(tele_id[i], f"Из игры вышел игрок: {message.from_user.username}")

        del players[message.from_user.username]


# Команда добавления в игру
@bot.message_handler(commands=['join'])
def join(message):
    if len(message.text.split()) != 2:
        bot.send_message(message.chat.id, "Укажите ID игры: `/join ID_игры`")
        return

    game_id = str(message.text.split()[1])

    if game_id not in games:
        bot.send_message(message.chat.id, "Игра не найдена")
        return

    if games[game_id]["last_char"] is None:
        bot.send_message(message.chat.id, "Игра уже началась, вы не можете к ней присоединиться")
        return

    bot.send_message(message.chat.id, f"Игра найдена")
    bot.send_message(message.chat.id, f"Если вы захотите выйти из игры до или после её начала, напишите '/leave'")
    for i in games[game_id]["players"]:
        bot.send_message(tele_id[i], f"К вам присоединился новый игрок: {message.from_user.username}")

    if games[game_id]["is_times"]:
        bot.send_message(message.chat.id, f"Эта игра на время")

    games[game_id]["players"].append(message.from_user.username)
    players[message.from_user.username] = game_id
    tele_id[message.from_user.username] = message.from_user.id


# Команда начала игры
@bot.message_handler(commands=['play'])
def play(message):
    game_id = players[message.from_user.username]

    if len(games[game_id]["players"]) < 2:
        bot.send_message(message.from_user.id, "Вы не можете начать игру в одиночку. Найдите себе оппонентов.")
        return

    games[game_id]["turn"] = 0
    beginner = games[game_id]["players"][0]
    for i in games[game_id]["players"]:
        bot.send_message(tele_id[i], "Игра начинается!")
        bot.send_message(tele_id[i], f"Очерёдность: {' '.join(games[game_id]["players"])}")

        if i == beginner:
            bot.send_message(tele_id[i], "Вы начинаете")
        else:
            bot.send_message(tele_id[i], f"Начинает: {beginner}")


# Процесс игры
@bot.message_handler(content_types=['text'])
def playing(message):
    try:
        user_name = message.from_user.username
        game_id = players[user_name]
        turn = games[game_id]["turn"]
        city = message.text.lower()
        city.replace(' ', '-')
        group = games[game_id]["players"]
        now = group[turn]
    except KeyError:
        return

    if now == user_name:
        if city[0] != games[game_id]["last_char"] and len(games[game_id]["cities"]) != 0:
            bot.send_message(message.chat.id,
                             f"Назвние города должно начинаться на {games[game_id]["last_char"].upper()}")

        elif is_city_new(games[game_id]["cities"], city):
            bot.send_message(message.chat.id, f"Этот город уже был")

            for i in games[game_id]["players"]:
                if i != now:
                    bot.send_message(tele_id[i], f"Соперник назвал '{city}', но этот город уже был")

        elif not is_city_exists(city):
            bot.send_message(message.chat.id, f"Этого города не существует")

            for i in games[game_id]["players"]:
                if i != now:
                    bot.send_message(tele_id[i], f"Соперник назвал '{city}', но этого города не существует")
            bot.send_message(config.MY_CHAT_ID, f"!!!Был назван и не засчитан город '{city}'!!!")

        else:
            bot.send_message(message.chat.id, random.choice(answers))
            games[game_id]["cities"].append(city)

            for i in games[game_id]["players"]:
                if i != now:
                    bot.send_message(tele_id[i], f"{now} назвал: {city.capitalize()}")

            games[game_id]["last_char"] = last_char(city)

            games[game_id]["turn"] += 1
            if games[game_id]["turn"] >= len(group):
                games[game_id]["turn"] = 0

            for i in games[game_id]["players"]:
                if i == group[games[game_id]["turn"]]:
                    bot.send_message(tele_id[i], f"Вам на {games[game_id]["last_char"].upper()}")
                else:
                    bot.send_message(tele_id[i], f"Сейчас очередь {group[games[game_id]["turn"]]}")
    else:
        bot.send_message(message.chat.id, "Сейчас не ваш ход!")


bot.polling(none_stop=True)
