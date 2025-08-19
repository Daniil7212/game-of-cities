from app.data import Data

data = Data()


# На какую букву ходить следующим
def last_char(city):
    if city[-1] in ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п',
                    'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'э', 'ю', 'я']:
        return city[:-1]
    else:
        return last_char(city[:-1])


# Проверка существует ли такой город
def is_city_exists(city_name):
    low = 0
    high = len(data.cities) - 1

    while low <= high:
        mid = (low + high) // 2
        guess = data.cities[mid]
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

# def correct_city_ai(city_name):
#     try:
#         messages = [
#             {
#                 "role": "user",
#                 "content": f"Если '{city_name}' это город, то если он написан неправильно напиши правильно. Отправь только итоговый город без лишних знаков."
#             }
#         ]
#
#         chat_response = client.chat.complete(
#             model="mistral-large-latest",
#             messages=messages
#         )
#
#         return chat_response.choices[0].message.content
#     except:
#         return "error"
