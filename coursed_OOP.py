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


class VK_API:
    API_BASE_URL = 'https://api.vk.ru/method'

    def __init__(self, token):
        self.token = token

    def get_common_params(self, user_id):
        return {
            'user_id': user_id,
            'extended': 1,
            'access_token': token_vk,
            'v': '5.199'
        }

    def get_photo_info(self, user_id):
        params = self.get_common_params(user_id)
        params.update({'album_id': 'profile'})
        response = requests.get(f'{self.API_BASE_URL}/photos.get', params=params)
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
        # print(photos_info)
        return photos_info


class YA_API:
    base_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {
        'Authorization': token_ya
    }

    def __init__(self, vk_token, vk_user_id, ya_token, folder_name):
        self.token = ya_token
        self.folder_name = folder_name
        self.vk_api = VK_API(token=vk_token, user_id=vk_user_id)


    def get_common_params(self):
        return {
            'path': self.folder_name,
        }

    def create_new_folder(self):
        response = requests.put(self.base_URL, headers=self.headers, params=self.get_common_params())

    def upload_photos(self, file_count=5):
        photos_info = self.vk_api.get_photo_info()
        uploaded_count = 0
        with tqdm(total=file_count) as pbar:  # Иннит. прогресс бара
            for photo_url in photos_info:
                if uploaded_count >= file_count:
                    break
                headers = {
                    'Authorization': self.token,
                    'path': 'Photos'
                }
                params = {
                    'path': f'/Photos/{photo_url}',
                    'url': photos_info[photo_url]
                }
                response = requests.post(f'{self.base_URL}/upload', headers=headers, params=params)
                if response.status_code == 202:
                    uploaded_count += 1
                    pbar.update(1)
                    print(f"Фотография успешно загружена: {photo_url}")
                else:
                    print(f"Ошибка загрузки фотографии {photo_url}: {response.text}")
        print(f"Общее количество загруженных фотографий: {uploaded_count}")

        time.sleep(3)  # костыль чтобы в json добавлялись все файлы

    def create_json(self):
        params = {
            'fields': 'name, size',
        }

        response = requests.get(f'{self.base_URL}/files', headers=self.headers, params=params)

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


user = YA_API(token_vk, user_id_vk, token_ya)
user.create_new_folder()
user.upload_photos(4)
user.create_json()
