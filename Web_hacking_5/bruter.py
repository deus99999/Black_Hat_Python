import queue
import requests
import threading
import sys

AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"
EXTENSIONS = ['.php', '.bak', '.orig', '.inc']
TARGET = "http://testphp.vulnweb.com"
THREADS = 5
WORDLIST = "all.txt"


def get_words(resume=None):
    """возвращает очередь со словами, которые мы будем искать на заданном компьютере"""
    def extend_words(word):
        """Эта вложенная функция добавляет к названиям файлов расширения, которые нужно проверить при выполнении запросов.
         В некоторых случаях имеет смысл проверить не только путь /admin, но и, к примеру, /admin.php, /admin.inc и
         /admin.html. Это позволяет перебрать распространенные расширения, такие как .orig и .bak, а также применяемые
          в языках программирования: они могут использоваться на этапе разработки, но по недосмотру остаться
        в дистрибутиве. Вложенная функция extend_words дает возможность сделать это с помощью таких правил: если слово
        содержит точку (.), мы добавляем его к URL-адресу, а если нет, считаем его названием папки (как в случае с /admin/)."""
        if "." in word:
            words.put(f'/{word}')
        else:
            words.put(f'/{word}/')

        for extension in EXTENSIONS:
            words.put(f'/{word}{extension}')

    with open(WORDLIST) as f:
        """считываем содержимое словаря."""
        raw_words = f.read()

    found_resume = False
    words = queue.Queue()
    for word in raw_words.split():  # перебор каждой строчки соваря
        if resume is not None:  # присваиваем переменной resume последний путь, который проверил скрипт. Это позволит возобновить процесс перебора в случае разрыва сетевого соединения или временных неполадок на атакуемом веб-сайте.
            if found_resume:
                extend_words(word)
            elif word == resume:
                found_resume = True
                print(f'Resuming wordlist from: {resume}')

        else:
            print(word)
            extend_words(word)
    return words


def dir_bruter(words):
    """ принимает объект Queue, содержащий слова, которые мы подготовили в функции get_words. В начале программы мы определили
строку User-Agent, которая будет использоваться в HTTP-запросах, чтобы они выглядели так, будто их отправляют без злых
намерений. Эта информация добавляется в переменную headers . Затем мы перебираем в цикле очередь words. На каждой
итерации создается URL-адрес, по которому будет отправлен запрос к удаленному веб-серверу """
    headers = {'User-Agent': AGENT}
    while not words.empty():
        url = f'{TARGET}{words.get()}'
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            sys.stderr.write('x');
            sys.stderr.flush()
            continue
        if r.status_code == 200:
            print(f'\nSuccess ({r.status_code}: {url})')
        elif r.status_code == 404:
            sys.stderr.write('.');
            sys.stderr.flush()
        else:
            print(f'{r.status_code} => {url}')

""" берем список слов для проверки и запускаем кучу потоков, которые будут его перебирать."""
if __name__ == '__main__':
    words = get_words()
    print('Press return to continue.')
    sys.stdin.readline()
    for _ in range(THREADS):
        t = threading.Thread(target=dir_bruter, args=(words, ))
        t.start()