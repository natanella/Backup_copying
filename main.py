import requests
from time import gmtime, strftime
import json
from tqdm import tqdm

class Backup:

    VK_API_BASE_URL = "https://api.vk.com/method/"
    VK_ACCESS_TOKEN = "vk1.a.DjGme_mmrG5yhEPI0IGJ0YM8mzK94BSgtWazhbh0Vbt4err51gpm_AZOj1b8udQ6X6qKvVAW7ACfSq_JRherWr2z52ZF9H39cN8PENXHJAAp-H6wSwca00fIpIwxQwwSNZH_4GspJwDAMNs_AkXTQ6fqujBozQO9tWyFvTMNDf-0JFqZ8iDbenSdxc7diHYF"
    YA_API_BASE_URL = "https://cloud-api.yandex.net/v1/disk/resources"

    def start(self):
        vk_user_id = input("Введите ID пользователя VK, чьи фото нужно сохранить: ")
        ya_token = input("Введите токен Яндекс Диска: ")

        target_album = "profile"
        albums = self._get_albums(vk_user_id)
        if albums:
            target_album_title = input(f"Выберите альбом из списка: {', '.join(albums.keys())}: ")
            if target_album_title:
                target_album = albums[target_album_title]

        count = input("Введите количество фотографий(необязательно): ") or 5
        count = int(count)

        self.backup_save(vk_user_id, ya_token, target_album, count)

    def backup_save(self, vk_user_id, ya_token, target_album, count):
        photos = self._get_photos(vk_user_id, target_album, count)

        if photos:
            self._create_folder(ya_token)

            url = f"{self.YA_API_BASE_URL}/upload"
            headers = self._ya_headers(ya_token)

            photos_info = []
            photos_list = []

            for photo in tqdm(photos):
                name = photo["likes"]
                if name in photos_list:
                    name = f"{name} {photo['date']}"
                params = {
                    'url': photo['url'],
                    'path': f"disk:/vk_photos/{name}.jpeg"
                }
                requests.post(url, headers=headers, params=params)

                photo_info = {
                    'file_name': f'{name}.jpeg',
                    'size': photo['size']
                }
                photos_info.append(photo_info)
                photos_list.append(name)

            with open('photos_info.json', 'w') as file:
                json.dump(photos_info, file, indent=2)

            if len(photos_list) == count:
                print(f"Загрузка {count} фотографий завершена")
            else:
                print(f"Не удалось загрузить {count} фотографий")
                print(f"Загрузка {len(photos_list)} фотографий завершена")

        if not photos:
            print(f"Не удалось загрузить {count} фотографий")
    
    def _get_photos(self, vk_user_id, target_album, count):
        params = self._vk_base_params(vk_user_id)
        params.update(
            {
                'album_id': target_album,
                'count': count,
                'extended': '1'
            }
        )
        response = requests.get(f'{self.VK_API_BASE_URL}photos.get', params=params)
        photos = []

        try:
            for item in response.json()['response']['items']:
                sort_rule = ['s', 'm', 'x', 'o', 'p', 'q', 'r', 'y', 'z', 'w']

                largest = sorted(item['sizes'], key=lambda x: sort_rule.index(x['type']))[-1]

                photos.append(
                    {
                        'url': largest['url'],
                        'likes': item['likes']['count'],
                        'date': strftime("%d.%m.%Y %H:%M", gmtime(int(item['date']))),
                        'size': largest['type']
                    }
                )
            return photos
        except:
            return None
    
    def _vk_base_params(self, vk_user_id):
        return {
            'access_token': self.VK_ACCESS_TOKEN,
            'v': '5.131',
            'owner_id': vk_user_id
        }
    
    def _get_albums(self, vk_user_id):
        params = self._vk_base_params(vk_user_id)
        response = requests.get(f'{self.VK_API_BASE_URL}photos.getAlbums', params=params)
    
        try:
            if response.json()['response']['count'] > 0:
                albums = {}

                for item in response.json()['response']['items']:
                    albums[item['title']] = item['id']
                return albums
            else:
                return None
        except:
            return None
    
    def _create_folder(self, ya_token):
        headers = self._ya_headers(ya_token)
        params = {
            'path': 'vk_photos'
        }
        requests.put(self.YA_API_BASE_URL, headers=headers, params=params)
    
    def _ya_headers(self, ya_token):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {ya_token}'
        }

backup = Backup()

backup.start()

# backup.backup_save("vk_user_id", "ya_token", "profile", 7)