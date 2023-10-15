""" определяем удаленный веб-сайт  и создаем список расширений файлов, которые нас не интересуют. Этот список может
различаться в зависимости от атакуемого приложения, но в данном случае мы решили игнорировать изображения и таблицы
стилей. Нам нужны файлы с HTML-кодом или текстом, которые с более высокой вероятностью содержат информацию, полезную для
 взлома сервера. Переменная answers — это объект Queue, в который будут записываться пути к файлам, найденным локально.
 Еще один объект Queue, переменная web_paths , будет хранить файлы, которые мы попытаемся найти на удаленном сервере.
 В функции gather_paths используется вызов os.walk  для перебора всех файлов и каталогов локальной копии
 веб-приложения. В ходе этого процесса мы формируем полные пути к файлам и сопоставляем их со списком, хранящимся в
 переменной FILTERED, чтобы отобрать только нужные нам файлы. Каждый подходящий файл, найденный локально, добавляется в
 очередь web_paths. Следует отдельно остановиться на диспетчере контекста chdir . Это довольно удобная конструкция для
 тех, кто страдает забывчивостью или просто хочет упростить себе жизнь. Диспетчеры контекста помогают в ситуациях,
когда вы что-то открыли и должны закрыть, что-то заблокировали и должны освободить или что-то изменили и должны вернуть
в исходное состояние. Вам уже, наверное, знакомы встроенные диспетчеры контекста, такие как open для открытия файлов или
 socket для работы с сокетами."""

import contextlib
import os
import queue
import requests
import sys
import threading
import time


FILTERED = [".jpg", ".gif", ".png", ".css"]
TARGET = "https://ponchik99.pythonanywhere.com/"
THREADS = 10

answers = queue.Queue()
web_paths = queue.Queue()


def gather_paths():
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERED:
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]
            print(path)
            web_paths.put(path)


@contextlib.contextmanager
def chdir(path):
    """@contextlib.contextmanager — позволяет превратить функцию-генератор в простой диспетчер контекста.
     Мы применяем его к функции chdir, которая позволяет выполнять код в другой папке и гарантирует, что при выходе из
     нее мы вернемся в исходную папку. Функция-генератор chdir инициализирует контекст, сохраняя исходный путь,
     переходит по новому пути, передает управление обратно функции gather_paths  и затем возвращается в папку, с
     которой мы начинали работу ."""
    this_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(this_dir)


def test_remote():
    """анализ удаленного приложения"""
    while not web_paths.empty():
        path = web_paths.get()
        url = f'{TARGET}{path}'
        time.sleep(2)
        r = requests.get(url)
        if r.status_code == 200:
            answers.put(url)
            sys.stdout.write('+')
        else:
            sys.stdout.write('x')
        sys.stdout.flush()


def run():
    """ run управляет анализом структуры каталогов, вызывая функции
в строго определенном порядке. Мы запускаем 10 потоков (определенных
в начале скрипта) , каждый из которых выполняет функцию test_remote .
После этого ждем, пока все эти потоки не завершатся (для этого предусмотрен
вызов thread.join), и прекращаем работу """
    mythreads = list()
    for i in range(THREADS):
        print(f'Spawning thread {i}')
        t = threading.Thread(target=test_remote())
        mythreads.append(t)
        t.start()

    for thread in mythreads:
        thread.join()


if __name__ == '__main__':
    with chdir('wordpress'):
    # with chdir('/home/tim/Downloads/wordpress'):
        gather_paths()
    input('Press return to continue')

    run()
    with open('myanswers.txt', 'w') as f:
        f.write(f'{answers.get()}\n')
    print('done')
