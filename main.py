import requests
import time
import os
import json
import sys

# Для корректной работы требуется токен с разрешением friends и photos
VK_ACCESS_TOKEN = ''
VK_BASE_URL = 'https://api.vk.com/method/'
VK_PATH = 'C:\\vk_dir\\'

YA_OAUTH_TOKEN = ''
YA_BASE_URL = "https://cloud-api.yandex.net:443"
YA_RESOURCE_PATH = "/v1/disk/resources/"
ya_headers = {'Authorization': YA_OAUTH_TOKEN}


def check_path(path=VK_PATH):
    if not os.path.exists(path):
        os.mkdir(path)
        print('Создана папка для VK')
    else:
        print('Папка для Vk существует')


def write_file(file_path, data):
    with open(file_path, 'wb') as f:
        f.write(data)


def progress(current_value, max_value, complete_message):
    step = 100 / max_value
    progress_bar = '#' * round(step)
    if current_value == max_value:
        print(f']\n{complete_message}')
    else:
        print(progress_bar, end='')
    time.sleep(.5)


class VkUser:

    def __init__(self, user_id):
        self.user_id = user_id

    def get_params(self):
        return {
            'access_token': VK_ACCESS_TOKEN,
            'v': 5.77
        }

    def get_albums(self):
        print('Получаю информацию о всех несервисных альбомах пользователя')
        params = self.get_params()
        params['owner_id'] = self.user_id
        params['need_system'] = 0
        params['photo_sizes'] = 1
        action = 'photos.getAlbums'
        response = requests.get(f'{VK_BASE_URL}{action}', params).json()
        albums_dict = {albums['id']: albums['title'] for albums in response['response']['items']}
        return albums_dict

    def get_photos(self, method, album_property, album_property_value):
        photos_size_formats = ['s', 'm', 'x', 'o', 'p', 'q', 'r', 'y', 'z', 'w']
        photos_dict = {}
        params = self.get_params()
        params['owner_id'] = self.user_id
        params[album_property] = album_property_value
        params['extended'] = 1
        params['photo_sizes'] = 1
        print('Получение данных из VK')
        response = requests.get(f'{VK_BASE_URL}{method}', params)
        print(f'Получено байт: {len(response.content)} \n')
        response = response.json()
        print('Создаём список для загрузки')
        for profile_photos in response['response']['items']:
            count = -1
            href = ''
            size = ''
            for user_photo_sizes in profile_photos['sizes']:
                if photos_size_formats.index(user_photo_sizes['type']) > count:
                    count = photos_size_formats.index(user_photo_sizes['type'])
                    size = user_photo_sizes['type']
                    if 'src' in profile_photos['sizes']:
                        href = user_photo_sizes['src']
                    else:
                        href = user_photo_sizes['url']
            photos_dict[href] = [profile_photos['likes']['count'], time.ctime(profile_photos['date']).split(), size]
        print('Завершено.', sep='', end='')
        return photos_dict

    def get_profile_photos(self):
        photos_dict = self.get_photos('photos.get', 'album_id', 'profile')
        return photos_dict

    def save_vk_photos_to_disk(self, string_path, albums):
        to_json = {}
        to_json['files'] = []
        photos_dict = {}
        if albums == 'profile':
            photos_dict = self.get_profile_photos()
        else:
            photos_dict = self.get_photos('photos.get', 'album_id', albums)
        print('\nЗагружаем файлы на локальный диск:')
        i = 0
        print('[', end='')
        for href, properties in photos_dict.items():
            data = requests.get(href).content
            if os.path.exists(f'{string_path}{properties[0]}.jpg'):
                file_name = string_path + str(properties[0]) + '_' + '-'.join(properties[1][1:3]) + '-' + properties[1][
                    4] + '.jpg'
                write_file(file_name, data)
            else:
                file_name = f'{string_path}{properties[0]}.jpg'
                write_file(file_name, data)
            i += 1
            progress(i, len(photos_dict), 'Сохранение на диск завершено.')
            to_json['files'].append({'file_name': os.path.basename(file_name), 'size': properties[2]})
        with open(string_path + 'files.json', 'w') as f:
            json.dump(to_json, f)
        print('Информация о сохранённых файлах записана в файл JSON')


class YaUploader:
    ya_folder_name = '/from_socials/'

    def __init__(self, file_path):
        self.file_path = file_path

    def upload(self):
        ya_params = {}
        with open(self.file_path, 'rb') as f:
            data = f.read()
        ya_params['overwrite'] = 'false'
        ya_params['path'] = self.ya_folder_name + os.path.basename(self.file_path)
        resp = requests.get(f'{YA_BASE_URL}{YA_RESOURCE_PATH}upload', params=ya_params, headers=ya_headers).json()
        upload_file = requests.put(resp["href"], data=data)
        return upload_file

    def check_ya_folder(self, folder_name):
        print("Проверяем наличие папки на Я.Диске")
        ya_params = {}
        ya_params['path'] = folder_name
        resp = requests.get(f'{YA_BASE_URL}{YA_RESOURCE_PATH}', params=ya_params, headers=ya_headers).json()
        if 'error' in resp:
            print('Папка отсутствует. Создаю папку')
            requests.put(f'{YA_BASE_URL}{YA_RESOURCE_PATH}', params=ya_params, headers=ya_headers).json()
            print('Папка создана.')
        else:
            print('Папка существует!')


def command():
    print('p - Скачать фотографии профиля ', 'all - Скачать фото из всех несервисных альбомов',
          'Либо введите номер альбома для его загрузки. ', 'ya - скачать сохраненные фотографии на Яндекс.Диск ',
          'list - получить список всех несервисных альбомов', 'stop - завершить программу', sep='\n')
    return input('Введите команду: ')


def main():
    command_input = command()
    if command_input == 'stop':
        sys.exit()
    if command_input == 'p':
        me_as_user.save_vk_photos_to_disk(VK_PATH, 'profile')
        main()
    elif command_input == 'all':
        user_albums = me_as_user.get_albums()
        i = 0
        for albums, names in user_albums.items():
            print(f'Получаю фотографии из альбома {names}')
            me_as_user.save_vk_photos_to_disk(VK_PATH, albums)
            i += 1
            progress(i, len(user_albums), 'Операция завершена.')
        main()
    elif command_input == 'ya':
        uploader = YaUploader(VK_PATH)
        uploader.ya_folder_name = '/from_vk/'
        uploader.check_ya_folder(uploader.ya_folder_name)
        i = 0
        for files in os.listdir(VK_PATH):
            uploader.file_path = VK_PATH + files
            uploader.upload()
            i += 1
            progress(i, len(os.listdir(VK_PATH)), 'Загрузка на Я.Диск завершена')
        main()
    elif command_input == 'list':
        user_albums = me_as_user.get_albums()
        for albums_id, albums in user_albums.items():
            print(f'{albums} - {albums_id}')
        print('\n')
        main()
    else:
        if command_input.isdigit():
            me_as_user.save_vk_photos_to_disk(VK_PATH, int(command_input))
        else:
            print('Команда не найдена')
        main()


if __name__ == '__main__':
    check_path(VK_PATH)
    user_id = int(input('Введите id пользователя VK: '))
    me_as_user = VkUser(user_id)
    main()
