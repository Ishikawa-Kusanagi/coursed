import json
import requests
from datetime import date
from tqdm import tqdm
import configparser
import time

config = configparser.ConfigParser()
config.read("settings.ini")

user_id_vk = config.get('vk', 'user_id')
token_vk = config.get('vk', 'token_VK')
token_ya = config.get('YANDEX', 'token_ya')

API_BASE_URL = 'https://api.vk.ru/method'

params = {
    'user_id': user_id_vk,
    'extended': 1,
    'access_token': token_vk,
    'v': '5.199'
}

response = requests.get(f'{API_BASE_URL}/account.getProfileInfo', params=params)
first_name = response.json()['response']['first_name']  # Получаем инфомацию о профиле Имя
last_name = response.json()['response']['last_name']  # Фамилия

params = {
    'owner_id': user_id_vk,
    'album_id': 'profile',
    'extended': 1,
    'access_token': token_vk,
    'v': '5.199'
}

response = requests.get(f'{API_BASE_URL}/photos.get', params=params)
profile_photo_info = response.json()  # json-файл с информацией о фотографии профиля
photos_info = {}
for count, photo_info in enumerate(
        profile_photo_info['response']['items']):

    '''
    Используя цикл, мы получим количество лайков и ссылку на фотографию в лучшем качестве.
    Добавьте пару ключ-значение в словарь.
    Проверяем, одинаково ли количество лайков, добавляем дату.
    '''

    name_file = f'{profile_photo_info['response']['items'][count]['likes']['count']}'
    url_file = profile_photo_info['response']['items'][count]['sizes'][-1]['url']
    date_file = date.today()
    new_file_name = f'{name_file}.{date_file}'  # Добавляем дату, к имени, если количество лайков одинаковое
    if name_file not in photos_info:
        photos_info[name_file] = url_file
    else:
        photos_info[new_file_name] = url_file

    '''
    Функция, которая проверяет количество фотографий в профиле пользователя,
    если их количество меньше 5, то переменная file_count принимает значение количества фото.
    Если количество больше 5, пользователю предлагается ввести в ручную количество фотографий, для
    резервного копирования. При пустом вводе пользователем, file_count принимает значение по умолчанию.
    '''


def get_file_count():
    while True:
        try:
            user_input = input("Введите количество файлов для загрузки (по умолчанию 5): ")
            if not user_input:  # Если пользователь ничего не ввел
                return 5  # Возвращаем значение по умолчанию
            file_count = int(user_input)
            if file_count < 0:
                print("Количество файлов должно быть неотрицательным числом.")
            else:
                return file_count
        except ValueError:
            print("Пожалуйста, введите целое неотрицательное число.")


if len(photos_info) > 5:
    print(f'У пользователя {first_name} {last_name} {len(photos_info)} фотографий в профиле')
    file_count = get_file_count()
else:
    file_count = len(photos_info)

    '''
    Создаем новую папку Photos в директории Яндекс диска.
    '''

base_URL = 'https://cloud-api.yandex.net/v1/disk/resources'

headers = {
    'Authorization': token_ya
}

params = {
    'path': 'Photos',
}

response = requests.put(base_URL, headers=headers, params=params)

uploaded_count = 0
with tqdm(total=file_count) as pbar:  # Иннит. прогресс бара
    for photo_url in photos_info:
        if uploaded_count >= file_count:
            break
        headers = {
            'Authorization': token_ya,
            'path': 'Photos'
        }
        params = {
            'path': f'/Photos/{photo_url}',
            'url': photos_info[photo_url]
        }
        response = requests.post(f'{base_URL}/upload', headers=headers, params=params)
        if response.status_code == 202:
            uploaded_count += 1
            pbar.update(1)
            print(f"Фотография успешно загружена: {photo_url}")
        else:
            print(f"Ошибка загрузки фотографии {photo_url}: {response.text}")
print(f"Общее количество загруженных фотографий: {uploaded_count}")

time.sleep(3)  # костыль чтобы в json добавлялись все файлы

base_URL = 'https://cloud-api.yandex.net/v1/disk/resources/files'

headers = {
    'Authorization': token_ya
}

params = {
    'fields': 'name, size',
}

response = requests.get(base_URL, headers=headers, params=params)

profile_photo = response.json()
photos = []
name_photo = {}
for count, photo in enumerate(profile_photo['items']):
    name_photo = {
        'file_name': f'{profile_photo['items'][count]['name']}.jpg',
        'size': f'{profile_photo['items'][count]['size']} kb'
    }
    photos.append(name_photo)
with open('photos.json', 'w', encoding='utf-8') as f:
    json.dump(photos, f)
