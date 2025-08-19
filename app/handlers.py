import random

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

import config
import app.utils as utils
import app.keyboards as kb
from app.data import Data

router = Router()
data = Data()

from main import bot


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("""
Это игра в Города.
Напишите '/create' чтобы создать игру
'/join ID_игры' чтобы присоединиться к игре
'/help' чтобы узнать правила игры
""")


@router.message(Command('help'))
async def get_help(message: Message):
    await message.answer("""
<b>1. Начало:</b> Первый игрок называет любой город.
<b>2. Ходы:</b>
- Следующий игрок должен назвать город на последнюю букву предыдущего (например, Москва → Астрахань).
- Если город заканчивается на ь, ъ, ы, й, берётся предпоследняя буква (например, Рязань → Новосибирск).
<b>3. Запрещено:</b>
- Повторять уже названные города.
- Использовать несуществующие города или города существующие в прошлом.
<b>4. Проигрыш:</b> Если игрок не может назвать город, он выбывает.
<b>5. Победа:</b> Последний оставшийся игрок выигрывает.
""", parse_mode='html')


@router.message(Command('create'))
async def create(message: Message):
    game_id = str(random.randint(1000, 9999))
    while game_id in data.games:
        game_id = str(random.randint(1000, 9999))

    await message.answer('Игра создана')
    await message.answer(f"ID игры: {game_id}")
    await message.answer("""
Когда все игроки присоединятся напишите '/play' чтобы начать
Если захотите выйти из игры напишите '/leave'
""")

    data.players[message.from_user.username] = game_id
    data.tele_id[message.from_user.username] = message.from_user.id
    data.games[game_id] = {
        "cities": [],
        "players": [message.from_user.username, ],
        "turn": None,
        "last_char": None,
        "is_times": False
    }

    try:
        if message.text.split()[-1] == "time":
            data.games[game_id]["is_times"] = True
    except:
        pass


@router.message(Command('join'))
async def join(message: Message):
    game_id = str(message.text.split()[1])

    if len(message.text.split()) != 2:
        await message.answer("Укажите ID игры: `/join ID_игры`")
        return

    if game_id not in data.games:
        await message.answer("Игра с таким id не найдена")
        return

    if data.games[game_id]["last_char"] is None:
        await message.answer("Игра уже началась, вы не можете к ней присоединиться")
        return

    await message.answer("Игра найдена")
    await message.answer("Если вы захотите выйти из игры до или после её начала, напишите '/leave'")
    for i in data.games[game_id]["players"]:
        bot.send_message(data.tele_id[i], f"К вам присоединился новый игрок: {message.from_user.username}")

    data.games[game_id]["players"].append(message.from_user.username)
    data.players[message.from_user.username] = game_id
    data.tele_id[message.from_user.username] = message.from_user.id


@router.message(Command('play'))
async def play(message: Message):
    game_id = data.players[message.from_user.username]

    if len(data.games[game_id]["players"]) < 2:
        await message.answer("Вы не можете начать игру в одиночку.")
        return

    data.games[game_id]["turn"] = 0
    beginner = data.games[game_id]["players"][0]
    for i in data.games[game_id]["players"]:
        bot.send_message(data.tele_id[i], "Игра начинается!")
        bot.send_message(data.tele_id[i], f"Очерёдность: {' -> '.join(data.games[game_id]["players"])}")

        if i == beginner:
            bot.send_message(data.tele_id[i], "Вы начинаете")
        else:
            bot.send_message(data.tele_id[i], f"Начинает: {beginner}")


@router.message(Command('leave'))
async def leave(message: Message):
    player = message.from_user.username
    game_id = data.players[player]

    if len(data.games[game_id]["players"]) <= 2:

        del data.tele_id[player]
        data.games[game_id]["players"].remove(player)

        if len(data.games[game_id]["players"]) == 1:
            pl = data.games[game_id]["players"][0]

            await bot.send_message(data.tele_id[pl], "Ваш последний противник вышел из игры. Поздравляем, вы выиграли!")

            del data.players[pl]
            del data.tele_id[pl]

        del data.games[game_id]
        del game_id

        await message.answer('Хорошо, мы удалили вас из игры')

    else:
        group = data.games[game_id]["players"]
        if group.index(player) == len(group) - 1:
            data.games[game_id]["turn"] = 0
            bot.send_message(data.tele_id[group[0]], "Ваш ход")
            bot.send_message(data.tele_id[group[0]],
                             f"Вам на {data.games[game_id]["last_char"].upper()}")

        del data.tele_id[player]
        data.games[game_id]["players"].remove(player)

        for i in data.games[game_id]["players"]:
            bot.send_message(data.tele_id[i], f"Из игры вышел игрок: {player}")

        del data.players[player]

        await message.answer('Хорошо, мы удалили вас из игры')


@router.message(Command('say'))
async def leave(message: Message):
    player = message.from_user.username
    text = message.split(' ', 1)
    if len(text) > 1:
        text = text[1]

    for i in data.games[data.players[player]]['players']:
        if i != player:
            bot.send_message(data.tele_id[i], f"{player}: {text}")


@router.message(F.text)
async def playing(message: Message):
    try:
        user_name = message.from_user.username
        game_id = data.players[user_name]
        turn = data.games[game_id]["turn"]
        city = message.text.lower()
        city.replace(' ', '-')
        group = data.games[game_id]["players"]
        now = group[turn]
        last_char = data.games[game_id]["last_char"]
    except KeyError:
        return

    if now == user_name:
        if city[0] != last_char and len(data.games[game_id]["cities"]) != 0:
            await message.answer(f"Назвние города должно начинаться на {last_char.upper()}")

        elif utils.is_city_new(data.games[game_id]["cities"], city):
            await message.answer("Этот город уже был назван")

            for i in data.games[game_id]["players"]:
                if i != now:
                    bot.send_message(data.tele_id[i], f"Соперник назвал '{city}', но этот город уже был")

        elif not utils.is_city_exists(city):
            await message.answer("Этого города не существует")

            for i in data.games[game_id]["players"]:
                if i != now:
                    bot.send_message(data.tele_id[i], f"Соперник назвал '{city}', но этого города не существует")
            bot.send_message(config.MY_CHAT_ID, f"!!!Был назван и не засчитан город '{city}'!!!")

        else:
            await message.answer(random.choice(data.answers))
            data.games[game_id]["cities"].append(city)

            for i in data.games[game_id]["players"]:
                if i != now:
                    bot.send_message(data.tele_id[i], f"{now} назвал: {city.capitalize()}")

            last_char = utils.last_char(city)

            data.games[game_id]["turn"] += 1
            if data.games[game_id]["turn"] >= len(group):
                data.games[game_id]["turn"] = 0

            for i in data.games[game_id]["players"]:
                if i == group[data.games[game_id]["turn"]]:
                    bot.send_message(data.tele_id[i], f"Вам на {last_char.upper()}")
                else:
                    bot.send_message(data.tele_id[i], f"Сейчас очередь {group[data.games[game_id]["turn"]]}")
    else:
        await message.answer("Сейчас не ваш ход!")
